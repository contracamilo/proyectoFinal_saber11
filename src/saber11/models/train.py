"""Entrenamiento y selección de modelos para predecir riesgo en Saber 11."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from saber11.config import load_config
from saber11.data.repository import read_raw
from saber11.features.preprocessing import (
    FEATURES,
    TARGET,
    build_preprocessor,
    build_target,
    clean,
    split,
)

Metricas = dict[str, float]


def _crear_pipeline(clasificador: BaseEstimator) -> Pipeline:
    """Construye un pipeline con un preprocesador nuevo y el clasificador."""
    return Pipeline(
        [
            ("prep", build_preprocessor(features=FEATURES)),
            ("clf", clasificador),
        ]
    )


def _calcular_metricas(modelo: Pipeline, datos: pd.DataFrame) -> Metricas:
    """Calcula métricas binarias usando la clase 1 como clase positiva."""
    y_real = datos[TARGET]
    y_predicho = modelo.predict(datos[FEATURES])
    probabilidades = modelo.predict_proba(datos[FEATURES])[:, 1]

    return {
        "accuracy": float(accuracy_score(y_real, y_predicho)),
        "precision": float(precision_score(y_real, y_predicho, zero_division=0)),
        "recall": float(recall_score(y_real, y_predicho, zero_division=0)),
        "f1": float(f1_score(y_real, y_predicho, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_real, probabilidades)),
    }


def _entrenar_candidatos(
    entrenamiento: pd.DataFrame,
    validacion: pd.DataFrame,
    random_state: int,
) -> tuple[dict[str, Pipeline], dict[str, Metricas]]:
    """Entrena los candidatos y escoge el árbol usando solo validación."""
    x_train = entrenamiento[FEATURES]
    y_train = entrenamiento[TARGET]

    baseline = _crear_pipeline(DummyClassifier(strategy="most_frequent"))
    baseline.fit(x_train, y_train)
    modelos = {"baseline": baseline}

    logreg = _crear_pipeline(
        LogisticRegression(max_iter=1000, class_weight="balanced")
    )
    logreg.fit(x_train, y_train)
    modelos["logreg"] = logreg

    mejor_arbol: Pipeline | None = None
    mejores_metricas_arbol: Metricas | None = None
    for max_depth in (3, 5, 8, 12):
        for min_samples_leaf in (20, 50):
            arbol = _crear_pipeline(
                DecisionTreeClassifier(
                    max_depth=max_depth,
                    min_samples_leaf=min_samples_leaf,
                    class_weight="balanced",
                    random_state=random_state,
                )
            )
            arbol.fit(x_train, y_train)
            metricas_arbol = _calcular_metricas(arbol, validacion)
            if (
                mejores_metricas_arbol is None
                or metricas_arbol["f1"] > mejores_metricas_arbol["f1"]
            ):
                mejor_arbol = arbol
                mejores_metricas_arbol = metricas_arbol

    if mejor_arbol is None or mejores_metricas_arbol is None:
        raise RuntimeError("No fue posible entrenar los candidatos de árbol.")

    modelos["tree"] = mejor_arbol
    metricas = {
        nombre: _calcular_metricas(modelo, validacion)
        for nombre, modelo in modelos.items()
    }
    return modelos, metricas


def _seleccionar_modelo(metricas: dict[str, Metricas]) -> str:
    """Prefiere regresión logística cuando queda a 0,01 del mejor F1."""
    mejor_f1 = max(metricas["logreg"]["f1"], metricas["tree"]["f1"])
    if metricas["logreg"]["f1"] >= mejor_f1 - 0.01:
        return "logreg"
    return "tree"


def _entrenar_modelos(
    entrenamiento: pd.DataFrame,
    validacion: pd.DataFrame,
    random_state: int,
) -> tuple[dict[str, Metricas], str, Pipeline]:
    """Entrena los candidatos y selecciona el mejor según F1 en validación."""
    modelos, metricas = _entrenar_candidatos(
        entrenamiento,
        validacion,
        random_state,
    )
    nombre_modelo = _seleccionar_modelo(metricas)
    return metricas, nombre_modelo, modelos[nombre_modelo]


def _guardar_resultados(
    cfg: dict[str, Any],
    umbral: float,
    metricas: dict[str, Metricas],
    nombre_modelo: str,
    modelo: Pipeline,
) -> None:
    """Guarda el pipeline seleccionado y sus metadatos."""
    ruta_modelo = Path(cfg["model"]["artifact_path"])
    ruta_modelo.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, ruta_modelo)

    metadatos = {
        "model_name": nombre_modelo,
        "threshold_punt_global": float(umbral),
        "features": list(FEATURES),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics_val": metricas[nombre_modelo],
    }
    ruta_metadatos = ruta_modelo.parent / "model_meta.json"
    ruta_metadatos.write_text(
        json.dumps(metadatos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def entrenar() -> None:
    """Carga los datos, entrena los modelos y guarda el mejor según validación."""
    cfg = load_config()
    df = clean(read_raw(cfg))
    df, umbral = build_target(df, cfg["target"]["threshold_percentile"])
    entrenamiento, validacion, _ = split(df, cfg)

    metricas, nombre_modelo, modelo = _entrenar_modelos(
        entrenamiento,
        validacion,
        cfg["split"]["random_state"],
    )
    _guardar_resultados(cfg, umbral, metricas, nombre_modelo, modelo)

    print("Métricas en validación (clase positiva: riesgo = 1)")
    encabezado = (
        f"{'Modelo':<12} {'Accuracy':>10} {'Precision':>10} "
        f"{'Recall':>10} {'F1':>10} {'ROC-AUC':>10}"
    )
    print(encabezado)
    for nombre, valores in metricas.items():
        print(
            f"{nombre:<12} {valores['accuracy']:>10.4f} "
            f"{valores['precision']:>10.4f} {valores['recall']:>10.4f} "
            f"{valores['f1']:>10.4f} {valores['roc_auc']:>10.4f}"
        )
    print(f"Modelo seleccionado: {nombre_modelo}")


if __name__ == "__main__":
    entrenar()
