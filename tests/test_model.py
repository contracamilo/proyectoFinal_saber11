"""Pruebas offline del pipeline de clasificación y sus métricas."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from saber11.models.fairness import calcular_metricas_por_grupo

TARGET = "riesgo_bajo_desempeno"
CLAVES_METRICAS = {
    "accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
}


@pytest.fixture
def datos_sinteticos() -> pd.DataFrame:
    """Crea una muestra balanceada con una señal numérica separable."""
    objetivo = np.tile([0, 1], 60)
    ruido = np.linspace(-0.2, 0.2, len(objetivo))
    return pd.DataFrame(
        {
            "indicador_contexto": objetivo * 2 - 1 + ruido,
            "grupo": np.where(np.arange(len(objetivo)) % 3, "A", "B"),
            TARGET: objetivo,
        }
    )


def _crear_pipeline(clasificador: object) -> Pipeline:
    """Construye el pipeline numérico mínimo usado por esta prueba sintética."""
    return Pipeline(
        [
            ("prep", StandardScaler()),
            ("clf", clasificador),
        ]
    )


def test_pipeline_predice_clases_binarias_y_probabilidades_validas(
    datos_sinteticos: pd.DataFrame,
) -> None:
    """El pipeline ajustado predice clases binarias y probabilidades válidas."""
    entradas = datos_sinteticos[["indicador_contexto"]]
    etiquetas = datos_sinteticos[TARGET]
    modelo = _crear_pipeline(LogisticRegression(random_state=42))
    modelo.fit(entradas, etiquetas)

    predicciones = modelo.predict(entradas)
    probabilidades = modelo.predict_proba(entradas)

    assert set(np.unique(predicciones)).issubset({0, 1})
    assert probabilidades.shape == (len(datos_sinteticos), 2)
    assert np.all((probabilidades >= 0) & (probabilidades <= 1))
    assert np.allclose(probabilidades.sum(axis=1), 1)


def test_modelo_seleccionado_supera_baseline_en_f1(
    datos_sinteticos: pd.DataFrame,
) -> None:
    """La logística detecta la señal y supera al baseline mayoritario."""
    entradas = datos_sinteticos[["indicador_contexto"]]
    etiquetas = datos_sinteticos[TARGET]

    seleccionado = _crear_pipeline(LogisticRegression(random_state=42))
    baseline = _crear_pipeline(DummyClassifier(strategy="most_frequent"))
    seleccionado.fit(entradas, etiquetas)
    baseline.fit(entradas, etiquetas)

    f1_seleccionado = f1_score(etiquetas, seleccionado.predict(entradas))
    f1_baseline = f1_score(etiquetas, baseline.predict(entradas))

    assert f1_seleccionado > f1_baseline


def test_metrics_json_cumple_contrato_si_existe() -> None:
    """Si el reporte está generado, verifica sus claves y métricas requeridas."""
    ruta = Path("reports/metrics.json")
    if not ruta.is_file():
        pytest.skip("reports/metrics.json aún no se ha generado.")

    reporte = json.loads(ruta.read_text(encoding="utf-8"))
    assert {"selected_model", "test", "confusion_matrix"} <= reporte.keys()
    assert {"baseline", "logreg", "tree"} <= reporte["test"].keys()
    for metricas in reporte["test"].values():
        assert CLAVES_METRICAS <= metricas.keys()

    matriz = reporte["confusion_matrix"]
    assert len(matriz) == 2
    assert all(len(fila) == 2 for fila in matriz)


def test_metricas_de_equidad_devueltas_por_grupo(
    datos_sinteticos: pd.DataFrame,
) -> None:
    """La auditoría devuelve una fila para cada grupo presente."""
    entradas = datos_sinteticos[["indicador_contexto"]]
    etiquetas = datos_sinteticos[TARGET]
    modelo = _crear_pipeline(LogisticRegression(random_state=42))
    modelo.fit(entradas, etiquetas)
    predicciones = modelo.predict(entradas)

    metricas = calcular_metricas_por_grupo(
        etiquetas,
        predicciones,
        datos_sinteticos["grupo"],
        "grupo",
    )

    assert len(metricas) == datos_sinteticos["grupo"].nunique()
    assert set(metricas["grupo"]) == set(datos_sinteticos["grupo"])
