"""Evaluación en test del modelo seleccionado y de los candidatos."""
import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.pipeline import Pipeline

from saber11.config import load_config
from saber11.data.repository import read_raw
from saber11.features.preprocessing import FEATURES, TARGET, build_target, clean, split
from saber11.models.train import calcular_metricas

CANDIDATOS = ("baseline", "logreg", "tree")
RUTA_REPORTES = Path("reports")


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


def evaluar() -> dict[str, Any]:
    """Evalúa los candidatos en test y guarda los reportes."""
    cfg = load_config()
    _, _, test = cargar_particiones(cfg)
    seleccionado = cargar_metadatos(cfg)["model_name"]

    metricas = {
        nombre: calcular_metricas(_cargar_candidato(cfg, nombre), test)
        for nombre in CANDIDATOS
    }
    prediccion = _cargar_candidato(cfg, seleccionado).predict(test[FEATURES])
    matriz = confusion_matrix(test[TARGET], prediccion).tolist()
    resultado = {"selected_model": seleccionado, "test": metricas, "confusion_matrix": matriz}

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
        f"| Real 0 | VN = {vn} | FP = {fp} |\n| Real 1 | FN = {fn} | VP = {vp} |\n",
        encoding="utf-8",
    )
    return resultado


if __name__ == "__main__":
    salida = evaluar()
    print(f"Modelo seleccionado: {salida['selected_model']}")
    print(_tabla_metricas(salida["test"]))
    print(f"Matriz de confusión [[VN, FP], [FN, VP]]: {salida['confusion_matrix']}")
