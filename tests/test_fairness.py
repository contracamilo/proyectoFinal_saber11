"""Pruebas de métricas de equidad por grupo."""

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from saber11.models.fairness import (
    brecha_maxima_recall,
    calcular_metricas_por_grupo,
    _entrenar_sin_sensibles,
)


def test_metricas_por_grupo_calcula_porcentajes_y_tasas() -> None:
    y_real = pd.Series([1, 1, 0, 0])
    y_predicho = np.array([1, 0, 1, 0])
    grupos = pd.Series(["A", "A", "A", "A"])

    resultado = calcular_metricas_por_grupo(
        y_real,
        y_predicho,
        grupos,
        "grupo_demo",
    ).iloc[0]

    assert resultado["grupo"] == "A"
    assert resultado["n"] == 4
    assert resultado["riesgo_real_pct"] == pytest.approx(50)
    assert resultado["riesgo_predicho_pct"] == pytest.approx(50)
    assert resultado["recall"] == pytest.approx(0.5)
    assert resultado["precision"] == pytest.approx(0.5)
    assert resultado["tasa_falsos_positivos"] == pytest.approx(0.5)


def test_metricas_por_grupo_conserva_faltantes_como_categoria() -> None:
    resultado = calcular_metricas_por_grupo(
        pd.Series([0, 1]),
        np.array([0, 1]),
        pd.Series([None, "B"]),
        "grupo_demo",
    )

    assert set(resultado["grupo"]) == {"Sin dato", "B"}


def test_brecha_maxima_recall_ignora_metricas_no_definidas() -> None:
    metricas = pd.DataFrame({"recall": [0.25, 0.8, np.nan]})

    assert brecha_maxima_recall(metricas) == pytest.approx(0.55)


def test_brecha_maxima_recall_devuelve_cero_con_un_grupo() -> None:
    metricas = pd.DataFrame({"recall": [0.7, np.nan]})

    assert brecha_maxima_recall(metricas) == 0.0


def test_reentrena_el_estimador_sin_variables_sensibles() -> None:
    entrenamiento = pd.DataFrame(
        {
            "contexto": [0, 1, 0, 1],
            "sensible": ["A", "A", "B", "B"],
            "objetivo": [0, 1, 0, 1],
        }
    )
    modelo = Pipeline(
        [
            ("prep", FunctionTransformer()),
            ("clf", DummyClassifier(strategy="most_frequent")),
        ]
    )

    modelo_sin_sensibles, variables = _entrenar_sin_sensibles(
        modelo,
        entrenamiento,
        ["contexto", "sensible"],
        ["sensible"],
        "objetivo",
        lambda features: FunctionTransformer(),
    )

    assert variables == ["contexto"]
    assert list(modelo_sin_sensibles.feature_names_in_) == ["contexto"]
    assert modelo_sin_sensibles.named_steps["clf"].classes_.tolist() == [0, 1]
