"""Evaluación en test del modelo seleccionado y de los candidatos."""
import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, brier_score_loss, confusion_matrix
from sklearn.pipeline import Pipeline

from saber11.calibracion import Calibracion, calibrar
from saber11.config import load_config
from saber11.data.repository import read_raw
from saber11.features.preprocessing import FEATURES, TARGET, build_target, clean, split
from saber11.models.train import calcular_metricas

CANDIDATOS = ("baseline", "logreg", "tree")
RUTA_REPORTES = Path("reports")
UMBRAL_DECISION = 0.5


def cargar_particiones(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Reconstruye las particiones con la misma semilla usada al entrenar."""
    df, _ = build_target(clean(read_raw(cfg)), cfg["target"]["threshold_percentile"])
    return split(df, cfg)


def cargar_metadatos(cfg: dict[str, Any]) -> dict[str, Any]:
    """Lee los metadatos del modelo seleccionado."""
    ruta = Path(cfg["model"]["artifact_path"]).parent / "model_meta.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


def _cargar_candidato(cfg: dict[str, Any], nombre: str) -> Pipeline:
    """Carga un candidato guardado por el entrenamiento."""
    return joblib.load(Path(cfg["model"]["artifact_path"]).parent / f"{nombre}.joblib")


def _tabla_metricas(metricas: dict[str, dict[str, float]]) -> str:
    """Construye la tabla Markdown de métricas por modelo."""
    filas = [
        "| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "|---|---|---|---|---|---|",
    ]
    for nombre, valores in metricas.items():
        filas.append(
            f"| {nombre} | {valores['accuracy']:.4f} | {valores['precision']:.4f} "
            f"| {valores['recall']:.4f} | {valores['f1']:.4f} | {valores['roc_auc']:.4f} |"
        )
    return "\n".join(filas)


def _guardar_matriz(matriz: list[list[int]], ruta: Path) -> None:
    """Guarda la figura de la matriz de confusión."""
    grafico = ConfusionMatrixDisplay(
        confusion_matrix=pd.DataFrame(matriz).to_numpy(),
        display_labels=["Sin riesgo (0)", "Riesgo (1)"],
    )
    grafico.plot(cmap="Blues", values_format="d")
    grafico.ax_.set_title("Matriz de confusión en test")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(ruta, dpi=120, bbox_inches="tight")
    plt.close()


def evaluar_calibracion(
    modelo: Pipeline,
    calibracion: Calibracion,
    test: pd.DataFrame,
    tasa_base: float,
) -> dict[str, float]:
    """Compara en test el puntaje del modelo con la probabilidad calibrada."""
    puntajes = modelo.predict_proba(test[FEATURES])[:, 1]
    probabilidades = calibrar(puntajes, calibracion)
    constante = [tasa_base] * len(test)
    return {
        "tasa_real": float(test[TARGET].mean()),
        "media_puntaje": float(puntajes.mean()),
        "media_probabilidad": float(probabilidades.mean()),
        "brier_tasa_base": float(brier_score_loss(test[TARGET], constante)),
        "brier_puntaje": float(brier_score_loss(test[TARGET], puntajes)),
        "brier_probabilidad": float(brier_score_loss(test[TARGET], probabilidades)),
        "probabilidad_en_el_umbral": float(calibrar(UMBRAL_DECISION, calibracion)),
    }


def _tabla_calibracion(calibracion: dict[str, float]) -> str:
    """Construye la tabla Markdown de calibración."""
    return (
        "| Medida | Puntaje del modelo | Probabilidad calibrada |\n"
        "|---|---|---|\n"
        f"| Media (tasa real: {calibracion['tasa_real']:.4f}) "
        f"| {calibracion['media_puntaje']:.4f} | {calibracion['media_probabilidad']:.4f} |\n"
        f"| Brier (tasa base: {calibracion['brier_tasa_base']:.4f}) "
        f"| {calibracion['brier_puntaje']:.4f} | {calibracion['brier_probabilidad']:.4f} |"
    )


def evaluar() -> dict[str, Any]:
    """Evalúa los candidatos en test y guarda los reportes."""
    cfg = load_config()
    entrenamiento, _, test = cargar_particiones(cfg)
    metadatos = cargar_metadatos(cfg)
    seleccionado = metadatos["model_name"]

    metricas = {
        nombre: calcular_metricas(_cargar_candidato(cfg, nombre), test)
        for nombre in CANDIDATOS
    }
    modelo = _cargar_candidato(cfg, seleccionado)
    prediccion = modelo.predict(test[FEATURES])
    matriz = confusion_matrix(test[TARGET], prediccion).tolist()
    calibracion = evaluar_calibracion(
        modelo,
        metadatos["calibracion"],
        test,
        float(entrenamiento[TARGET].mean()),
    )
    resultado = {
        "selected_model": seleccionado,
        "test": metricas,
        "confusion_matrix": matriz,
        "calibration": calibracion,
    }

    RUTA_REPORTES.mkdir(exist_ok=True)
    (RUTA_REPORTES / "metrics.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _guardar_matriz(matriz, RUTA_REPORTES / "figures" / "matriz_confusion.png")
    (vn, fp), (fn, vp) = matriz
    (RUTA_REPORTES / "metricas.md").write_text(
        f"# Métricas en test\n\nModelo seleccionado: **{seleccionado}**\n\n"
        f"{_tabla_metricas(metricas)}\n\n## Matriz de confusión\n\n"
        f"| | Predicho 0 | Predicho 1 |\n|---|---|---|\n"
        f"| Real 0 | VN = {vn} | FP = {fp} |\n| Real 1 | FN = {fn} | VP = {vp} |\n\n"
        f"## Calibración\n\n{_tabla_calibracion(calibracion)}\n\n"
        f"El modelo emite una alerta desde una probabilidad calibrada de "
        f"{calibracion['probabilidad_en_el_umbral']:.4f}.\n",
        encoding="utf-8",
    )
    return resultado


if __name__ == "__main__":
    salida = evaluar()
    print(f"Modelo seleccionado: {salida['selected_model']}")
    print(_tabla_metricas(salida["test"]))
    print(f"Matriz de confusión [[VN, FP], [FN, VP]]: {salida['confusion_matrix']}")
    print(_tabla_calibracion(salida["calibration"]))
