"""Pruebas de la capa de datos y procesamiento, sin usar internet."""
import numpy as np
import pandas as pd
import pytest

from saber11.features.preprocessing import (
    FEATURES,
    LEAKAGE_PREFIXES,
    TARGET,
    build_preprocessor,
    build_target,
    clean,
    split,
)

CFG = {"split": {"test_size": 0.15, "val_size": 0.15, "random_state": 42}}


def perfiles(n: int = 400) -> pd.DataFrame:
    """Crea un DataFrame pequeño con las columnas que el código necesita."""
    generador = np.random.default_rng(42)
    df = pd.DataFrame({c: generador.choice(["A", "B"], n) for c in FEATURES if c != "edad"})
    df["edad"] = generador.integers(15, 20, n).astype(float)
    df["punt_global"] = generador.integers(100, 450, n)
    return df


def crudo() -> pd.DataFrame:
    """Crea filas con el formato de texto que entrega la API."""
    return pd.DataFrame(
        {
            "estu_consecutivo": ["SB1", "SB2", "SB3", "SB3"],
            "periodo": ["20224", "20224", "20224", "20224"],
            "punt_global": ["300", "250", "200", "200"],
            "estu_fechanacimiento": ["14/10/2005", "99/99/2005", "01/01/1950", "01/01/1950"],
        }
    )


def test_features_sin_fuga():
    assert not [c for c in FEATURES if c.startswith(LEAKAGE_PREFIXES)]


def test_preprocesador_rechaza_fuga():
    with pytest.raises(ValueError):
        build_preprocessor(["edad", "punt_ingles"])


def test_build_target_binario_y_umbral():
    df, umbral = build_target(perfiles(), 25)
    assert set(df[TARGET].unique()) == {0, 1}
    assert umbral == df["punt_global"].quantile(0.25)


def test_split_estratificado_y_sin_repetidos():
    df, _ = build_target(perfiles(), 25)
    train, val, test = split(df, CFG)
    proporcion = df[TARGET].mean()
    for parte in (train, val, test):
        assert abs(parte[TARGET].mean() - proporcion) <= 0.02
    assert not set(train.index) & set(val.index)
    assert not set(train.index) & set(test.index)
    assert not set(val.index) & set(test.index)
    assert len(train) + len(val) + len(test) == len(df)


def test_preprocesador_tolera_categoria_nueva():
    df = perfiles()
    prep = build_preprocessor()
    prep.fit(df[FEATURES])
    nuevo = df[FEATURES].head(1).copy()
    nuevo["cole_jornada"] = "CATEGORIA_NUEVA"
    assert prep.transform(nuevo).shape[0] == 1


def test_clean_quita_duplicados():
    limpio = clean(crudo())
    assert limpio["estu_consecutivo"].is_unique


def test_clean_calcula_edad_y_marca_fechas_invalidas():
    limpio = clean(crudo())
    assert limpio["edad"].iloc[0] == 17
    assert limpio["edad"].iloc[1:].isna().all()
