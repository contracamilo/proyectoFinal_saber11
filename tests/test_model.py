"""Pruebas de la capa de modelo con datos fabricados."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from saber11.features.preprocessing import FEATURES, TARGET, build_preprocessor
from saber11.models.fairness import MINIMO_POR_GRUPO, SIN_DATO, brecha_recall, metricas_por_grupo
from saber11.models.train import calcular_metricas


def datos(n: int = 300) -> pd.DataFrame:
    """Crea datos donde el riesgo depende de una variable de entrada."""
    generador = np.random.default_rng(42)
    df = pd.DataFrame({c: generador.choice(["A", "B"], n) for c in FEATURES if c != "edad"})
    df["edad"] = generador.integers(15, 20, n).astype(float)
    df[TARGET] = (df["cole_jornada"] == "A").astype(int)
    return df


def test_calcular_metricas_devuelve_las_cinco_metricas():
    df = datos()
    modelo = Pipeline(
        [("prep", build_preprocessor()), ("clf", LogisticRegression(max_iter=1000))]
    ).fit(df[FEATURES], df[TARGET])
    metricas = calcular_metricas(modelo, df)
    assert set(metricas) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
    assert metricas["f1"] == 1.0


def test_metricas_por_grupo_calcula_recall_y_falsos_positivos():
    y_real = pd.Series([1, 1, 0, 0, 1, 0])
    y_predicho = np.array([1, 0, 1, 0, 1, 0])
    grupos = pd.Series(["A", "A", "A", "A", "B", "B"])
    tabla = metricas_por_grupo(y_real, y_predicho, grupos).set_index("grupo")
    assert tabla.loc["A", "recall"] == 0.5
    assert tabla.loc["A", "tasa_falsos_positivos"] == 0.5
    assert tabla.loc["B", "recall"] == 1.0


def test_metricas_por_grupo_conserva_los_valores_faltantes():
    tabla = metricas_por_grupo(pd.Series([1, 0]), np.array([1, 0]), pd.Series(["A", None]))
    assert SIN_DATO in set(tabla["grupo"])


def test_brecha_ignora_grupos_pequenos():
    tabla = pd.DataFrame(
        {
            "n": [MINIMO_POR_GRUPO, MINIMO_POR_GRUPO, MINIMO_POR_GRUPO - 1],
            "recall": [0.7, 0.6, 0.0],
        }
    )
    assert round(brecha_recall(tabla), 4) == 0.1
