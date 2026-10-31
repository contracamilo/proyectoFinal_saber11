"""Pruebas de la capa de datos y procesamiento, sin usar internet."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import requests

from saber11.config import load_config
from saber11.data import ingest
from saber11.data.repository import load_to_db, read_raw
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


class RespuestaFalsa:
    """Imita una respuesta de la API con una lista de filas."""

    def __init__(self, filas: list[dict]) -> None:
        self.filas = filas

    def raise_for_status(self) -> None:
        pass

    def json(self) -> list[dict]:
        return self.filas


def cfg_datos(carpeta: Path, page_size: int = 2) -> dict:
    """Crea una configuración con rutas temporales."""
    return {
        "data": {
            "source_url": "https://ejemplo.test",
            "periodo": "20224",
            "cole_depto_ubicacion": "BOGOTÁ",
            "page_size": page_size,
            "raw_path": str(carpeta / "crudo.csv"),
            "db_path": str(carpeta / "saber11.db"),
        }
    }


def api_falsa(monkeypatch, paginas: list) -> list[dict]:
    """Reemplaza requests.get por respuestas fijas y registra los parámetros."""
    llamadas = []
    restantes = iter(paginas)

    def get(url, params, timeout):
        llamadas.append(params)
        pagina = next(restantes)
        if isinstance(pagina, Exception):
            raise pagina
        return RespuestaFalsa(pagina)

    monkeypatch.setattr(ingest.requests, "get", get)
    monkeypatch.setattr(ingest.time, "sleep", lambda _: None)
    return llamadas


def test_load_config_lee_tildes_en_utf8(tmp_path):
    ruta = tmp_path / "config.yaml"
    ruta.write_bytes('data:\n  depto: "BOGOTÁ"\n'.encode("utf-8"))
    assert load_config(str(ruta))["data"]["depto"] == "BOGOTÁ"


def test_load_config_sin_archivo_da_un_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError, match="raíz del repositorio"):
        load_config(str(tmp_path / "no_existe.yaml"))


def test_download_pagina_hasta_la_ultima_pagina(tmp_path, monkeypatch):
    llamadas = api_falsa(monkeypatch, [[{"a": "1"}, {"a": "2"}], [{"a": "3"}]])
    ruta = ingest.download(cfg_datos(tmp_path))
    assert len(pd.read_csv(ruta)) == 3
    assert [p["$offset"] for p in llamadas] == [0, 2]
    assert "BOGOTÁ" in llamadas[0]["$where"]


def test_download_es_idempotente(tmp_path, monkeypatch):
    llamadas = api_falsa(monkeypatch, [[{"a": "1"}]])
    cfg = cfg_datos(tmp_path)
    ingest.download(cfg)
    ingest.download(cfg)
    assert len(llamadas) == 1


def test_download_reintenta_si_una_pagina_falla(tmp_path, monkeypatch):
    fallo = requests.ConnectionError("sin conexión")
    llamadas = api_falsa(monkeypatch, [fallo, fallo, [{"a": "1"}]])
    ingest.download(cfg_datos(tmp_path))
    assert len(llamadas) == 3


def test_download_fallido_no_corrompe_el_csv_existente(tmp_path, monkeypatch):
    cfg = cfg_datos(tmp_path)
    ruta = Path(cfg["data"]["raw_path"])
    ruta.write_text("a\n1\n", encoding="utf-8")
    fallo = requests.ConnectionError("sin conexión")
    api_falsa(monkeypatch, [[{"a": "9"}, {"a": "8"}], fallo, fallo, fallo])
    with pytest.raises(requests.ConnectionError):
        ingest.download(cfg, force=True)
    assert ruta.read_text(encoding="utf-8") == "a\n1\n"


def test_load_to_db_es_idempotente_y_conserva_el_texto(tmp_path):
    cfg = cfg_datos(tmp_path)
    Path(cfg["data"]["raw_path"]).write_text(
        "cole_codigo_icfes\n032730\n045678\n", encoding="utf-8"
    )
    assert load_to_db(cfg) == 2
    assert load_to_db(cfg) == 2
    datos = read_raw(cfg)
    assert len(datos) == 2
    assert datos["cole_codigo_icfes"].iloc[0] == "032730"
