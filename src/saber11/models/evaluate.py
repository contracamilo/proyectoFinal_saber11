"""Evaluación final de los modelos en el conjunto de prueba."""

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.pipeline import Pipeline

from saber11.config import load_config
from saber11.data.repository import read_raw
from saber11.features.preprocessing import (
    FEATURES,
    TARGET,
    build_target,
    clean,
    split,
)
from saber11.models.train import (
    Metricas,
    _calcular_metricas,
    _entrenar_candidatos,
)

NOMBRES_MODELOS = ("baseline", "logreg", "tree")
NOMBRES_CLASES = ("Sin riesgo", "En riesgo")


def _cargar_modelo_seleccionado(
    cfg: dict[str, Any],
) -> tuple[str, Pipeline]:
    """Carga el modelo y su nombre guardados durante el entrenamiento."""
    ruta_modelo = Path(cfg["model"]["artifact_path"])
    ruta_metadatos = ruta_modelo.parent / "model_meta.json"
    if not ruta_modelo.is_file():
        raise FileNotFoundError(
            f"No se encontró {ruta_modelo}. Ejecuta primero "
            "`python -m saber11.models.train`."
        )
    if not ruta_metadatos.is_file():
        raise FileNotFoundError(
            f"No se encontró {ruta_metadatos}. Ejecuta primero "
            "`python -m saber11.models.train`."
        )

    metadatos = json.loads(ruta_metadatos.read_text(encoding="utf-8"))
    nombre_modelo = metadatos.get("model_name")
    if nombre_modelo not in NOMBRES_MODELOS:
        raise ValueError(
            f"Nombre de modelo no reconocido en {ruta_metadatos}: "
            f"{nombre_modelo!r}."
        )

    modelo = joblib.load(ruta_modelo)
    if not isinstance(modelo, Pipeline):
        raise TypeError(f"El artefacto {ruta_modelo} no contiene un Pipeline.")
    return nombre_modelo, modelo


def _guardar_matriz_confusion(
    y_real: pd.Series,
    y_predicho: np.ndarray,
    ruta_salida: Path,
) -> list[list[int]]:
    """Guarda la matriz con conteos y porcentaje del total de prueba."""
    matriz = confusion_matrix(y_real, y_predicho, labels=[0, 1])
    total = int(matriz.sum())
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    figura, eje = plt.subplots(figsize=(7, 6))
    imagen = eje.imshow(matriz, cmap="Blues")
    figura.colorbar(imagen, ax=eje, label="Número de estudiantes")
    eje.set(
        xticks=[0, 1],
        xticklabels=NOMBRES_CLASES,
        yticks=[0, 1],
        yticklabels=NOMBRES_CLASES,
        xlabel="Predicción del modelo",
        ylabel="Resultado real",
        title="Matriz de confusión — conjunto de prueba",
    )
    limite_color = matriz.max() / 2 if matriz.size else 0
    for fila in range(2):
        for columna in range(2):
            conteo = int(matriz[fila, columna])
            porcentaje = 100 * conteo / total if total else 0.0
            color = "white" if conteo > limite_color else "black"
            eje.text(
                columna,
                fila,
                f"{conteo:,}\n({porcentaje:.1f}%)",
                ha="center",
                va="center",
                color=color,
                fontsize=12,
            )
    figura.tight_layout()
    figura.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(figura)
    return matriz.astype(int).tolist()


def _crear_reporte_markdown(
    nombre_seleccionado: str,
    metricas_test: dict[str, Metricas],
    matriz: list[list[int]],
) -> str:
    """Redacta el informe de métricas y errores de clasificación."""
    vn, fp = matriz[0]
    fn, vp = matriz[1]
    filas = [
        "| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for nombre in NOMBRES_MODELOS:
        valores = metricas_test[nombre]
        marca = " (seleccionado)" if nombre == nombre_seleccionado else ""
        filas.append(
            f"| {nombre}{marca} | {valores['accuracy']:.4f} "
            f"| {valores['precision']:.4f} | {valores['recall']:.4f} "
            f"| {valores['f1']:.4f} | {valores['roc_auc']:.4f} |"
        )

    return "\n".join(
        [
            "# Evaluación de modelos en test",
            "",
            f"Modelo seleccionado en validación: **{nombre_seleccionado}**.",
            "El conjunto de prueba se reserva para esta evaluación final; "
            "sus resultados no se usan para seleccionar modelos ni ajustar "
            "hiperparámetros.",
            "",
            "## Comparación de modelos",
            "",
            *filas,
            "",
            "## Interpretación de las métricas",
            "",
            "- **Accuracy:** proporción total de predicciones correctas, tanto "
            "para estudiantes con riesgo como sin riesgo. Puede ser engañosa "
            "si las clases están desbalanceadas.",
            "- **Precision:** entre quienes el modelo marca en riesgo, qué "
            "proporción realmente pertenece a la clase de riesgo. Una precision "
            "baja implica más falsas alarmas.",
            "- **Recall:** entre los casos que realmente están en riesgo, qué "
            "proporción detecta el modelo. Un recall bajo significa más casos "
            "de riesgo no detectados.",
            "- **F1:** equilibrio entre precision y recall; es útil para "
            "comparar el desempeño sobre la clase minoritaria.",
            "- **ROC-AUC:** capacidad para ordenar casos de riesgo por encima "
            "de casos sin riesgo a través de distintos umbrales; 0.5 equivale "
            "aproximadamente al azar.",
            "",
            "## Matriz de confusión",
            "",
            "Las filas representan el resultado real y las columnas la "
            "predicción. La figura muestra conteos y porcentaje del total.",
            "",
            "![Matriz de confusión](figures/matriz_confusion.png)",
            "",
            f"- **VN (verdaderos negativos): {vn:,}** — casos sin riesgo "
            "clasificados correctamente como sin riesgo.",
            f"- **FP (falsos positivos): {fp:,}** — casos sin riesgo marcados "
            "como en riesgo; podrían recibir atención prioritaria aunque no "
            "pertenezcan a la clase de riesgo definida para este análisis.",
            f"- **FN (falsos negativos): {fn:,}** — casos en riesgo que el "
            "modelo no detecta; podrían quedar fuera de una focalización de "
            "apoyos.",
            f"- **VP (verdaderos positivos): {vp:,}** — casos en riesgo "
            "detectados correctamente.",
            "",
            "## Costo de los errores y prioridad",
            "",
            "Para el propósito de focalizar apoyos, un falso negativo puede "
            "ser más costoso que un falso positivo: el primero puede dejar sin "
            "detectar a un grupo que podría beneficiarse del refuerzo, mientras "
            "que el segundo puede dirigir recursos a alguien que no pertenece "
            "a la clase definida como riesgo. Por eso se presta especial "
            "atención al recall de la clase 1, sin ignorar precision, capacidad "
            "disponible ni las consecuencias de las falsas alarmas. Esta "
            "prioridad no justifica decisiones automatizadas individuales.",
            "",
        ]
    )


def evaluar() -> None:
    """Reconstruye la partición, evalúa los modelos y guarda los reportes."""
    cfg = load_config()
    df = clean(read_raw(cfg))
    df, _ = build_target(df, cfg["target"]["threshold_percentile"])
    entrenamiento, validacion, test = split(df, cfg)

    modelos, _ = _entrenar_candidatos(
        entrenamiento,
        validacion,
        cfg["split"]["random_state"],
    )
    nombre_seleccionado, modelo_guardado = _cargar_modelo_seleccionado(cfg)
    modelos[nombre_seleccionado] = modelo_guardado

    metricas_test = {
        nombre: _calcular_metricas(modelos[nombre], test)
        for nombre in NOMBRES_MODELOS
    }

    y_predicho = modelos[nombre_seleccionado].predict(test[FEATURES])
    ruta_matriz = Path("reports/figures/matriz_confusion.png")
    matriz = _guardar_matriz_confusion(test[TARGET], y_predicho, ruta_matriz)

    reporte = {
        "selected_model": nombre_seleccionado,
        "test": metricas_test,
        "confusion_matrix": matriz,
    }
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/metrics.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    Path("reports/metricas.md").write_text(
        _crear_reporte_markdown(nombre_seleccionado, metricas_test, matriz),
        encoding="utf-8",
    )

    print("Métricas en test (clase positiva: riesgo = 1)")
    print(
        f"{'Modelo':<12} {'Accuracy':>10} {'Precision':>10} "
        f"{'Recall':>10} {'F1':>10} {'ROC-AUC':>10}"
    )
    for nombre in NOMBRES_MODELOS:
        valores = metricas_test[nombre]
        print(
            f"{nombre:<12} {valores['accuracy']:>10.4f} "
            f"{valores['precision']:>10.4f} {valores['recall']:>10.4f} "
            f"{valores['f1']:>10.4f} {valores['roc_auc']:>10.4f}"
        )
    print(f"Modelo seleccionado: {nombre_seleccionado}")
    print(f"Matriz de confusión: {matriz}")
    print(f"Figura guardada en: {ruta_matriz}")
    print("Reportes guardados en reports/metrics.json y reports/metricas.md")


if __name__ == "__main__":
    evaluar()
