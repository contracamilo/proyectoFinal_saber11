"""Pruebas de métricas de equidad por grupo."""

import numpy as np
import pandas as pd
import pytest

from saber11.models.fairness import (
    MINIMO_POR_GRUPO,
    SIN_DATO,
    brecha_recall,
    metricas_por_grupo,
)


def test_metricas_por_grupo_calcula_tasas_y_conteo() -> None:
    y_real = pd.Series([1, 1, 0, 0])
    y_predicho = np.array([1, 0, 1, 0])

    resultado = metricas_por_grupo(
        y_real,
        y_predicho,
        pd.Series(["A", "A", "A", "A"]),
    ).iloc[0]

    assert resultado["grupo"] == "A"
    assert resultado["n"] == 4
    assert resultado["tasa_real"] == pytest.approx(0.5)
    assert resultado["tasa_predicha"] == pytest.approx(0.5)
    assert resultado["recall"] == pytest.approx(0.5)
    assert resultado["precision"] == pytest.approx(0.5)
    assert resultado["tasa_falsos_positivos"] == pytest.approx(0.5)


def test_metricas_por_grupo_conserva_faltantes_como_categoria() -> None:
    resultado = metricas_por_grupo(
        pd.Series([0, 1]),
        np.array([0, 1]),
        pd.Series([None, "B"]),
    )

    assert set(resultado["grupo"]) == {SIN_DATO, "B"}


def test_brecha_recall_excluye_grupos_pequenos_y_recall_indefinido() -> None:
    metricas = pd.DataFrame(
        {
            "n": [MINIMO_POR_GRUPO, MINIMO_POR_GRUPO, 1],
            "recall": [0.25, 0.8, np.nan],
        }
    )

    assert brecha_recall(metricas) == pytest.approx(0.55)


def test_brecha_recall_devuelve_cero_con_un_grupo_valido() -> None:
    metricas = pd.DataFrame(
        {
            "n": [MINIMO_POR_GRUPO, 1],
            "recall": [0.7, np.nan],
        }
    )

    assert brecha_recall(metricas) == 0.0
