"""Pruebas de la capa de modelo con datos fabricados."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from saber11.calibracion import calibrar
from saber11.features.preprocessing import FEATURES, TARGET, build_preprocessor
from saber11.models.analisis import PARTICIONES, importancia_variables, validar_cruzado
from saber11.models.evaluate import evaluar_calibracion
from saber11.models.fairness import MINIMO_POR_GRUPO, SIN_DATO, brecha_recall, metricas_por_grupo
from saber11.models.train import ajustar_calibracion, calcular_metricas


def datos(n: int = 300) -> pd.DataFrame:
    """Crea datos donde el riesgo depende de una variable de entrada."""
    generador = np.random.default_rng(42)
    df = pd.DataFrame({c: generador.choice(["A", "B"], n) for c in FEATURES if c != "edad"})
    df["edad"] = generador.integers(15, 20, n).astype(float)
    df[TARGET] = (df["cole_jornada"] == "A").astype(int)
    return df


def modelo_entrenado(df: pd.DataFrame) -> Pipeline:
    """Entrena una regresión logística con los datos fabricados."""
    return Pipeline(
        [("prep", build_preprocessor()), ("clf", LogisticRegression(max_iter=1000))]
    ).fit(df[FEATURES], df[TARGET])


def datos_con_ruido(n: int = 2000) -> pd.DataFrame:
    """Crea datos con clase minoritaria y una etiqueta que no es determinista."""
    df = datos(n)
    generador = np.random.default_rng(7)
    probabilidad = np.where(df["cole_jornada"] == "A", 0.4, 0.1)
    df[TARGET] = (generador.random(n) < probabilidad).astype(int)
    return df


def test_calcular_metricas_devuelve_las_cinco_metricas():
    df = datos()
    modelo = modelo_entrenado(df)
    metricas = calcular_metricas(modelo, df)
    assert set(metricas) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
    assert metricas["f1"] == 1.0


def test_calibracion_corrige_puntajes_inflados():
    df = datos_con_ruido()
    modelo = Pipeline(
        [
            ("prep", build_preprocessor()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    ).fit(df[FEATURES], df[TARGET])
    resultado = evaluar_calibracion(
        modelo,
        ajustar_calibracion(modelo, df),
        df,
        float(df[TARGET].mean()),
    )
    assert resultado["media_puntaje"] > resultado["tasa_real"] + 0.1
    assert abs(resultado["media_probabilidad"] - resultado["tasa_real"]) < 0.01
    assert resultado["brier_probabilidad"] < resultado["brier_puntaje"]


def test_calibrar_conserva_el_orden_de_los_puntajes():
    puntajes = np.array([0.1, 0.5, 0.9])
    calibradas = calibrar(puntajes, {"pendiente": 0.8, "intercepto": -1.2})
    assert np.all(np.diff(calibradas) > 0)


def test_validacion_cruzada_resume_f1_y_roc_auc():
    df = datos_con_ruido(500)
    resumen = validar_cruzado(modelo_entrenado(df), df, semilla=42)
    assert PARTICIONES == 5
    assert set(resumen) == {"f1_media", "f1_desviacion", "roc_auc_media", "roc_auc_desviacion"}
    assert 0 < resumen["roc_auc_media"] <= 1


def test_importancia_ubica_primero_la_variable_que_define_el_riesgo():
    df = datos()
    tabla = importancia_variables(modelo_entrenado(df), df, semilla=42)
    assert len(tabla) == len(FEATURES)
    assert tabla.loc[0, "variable"] == "cole_jornada"


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
