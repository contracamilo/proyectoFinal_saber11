import sqlite3
from pathlib import Path

import pandas as pd

from saber11.config import load_config

TABLA = "resultados"


def load_to_db(cfg: dict) -> int:
    """Carga el CSV crudo en SQLite reemplazando la tabla. Devuelve el número de filas."""
    ruta_db = Path(cfg["data"]["db_path"])
    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    # dtype=str conserva el texto original, por ejemplo los ceros iniciales de los códigos.
    df = pd.read_csv(cfg["data"]["raw_path"], dtype=str, encoding="utf-8")
    with sqlite3.connect(ruta_db) as conexion:
        df.to_sql(TABLA, conexion, if_exists="replace", index=False)
    return len(df)


def read_raw(cfg: dict) -> pd.DataFrame:
    """Lee la tabla de resultados completa."""
    with sqlite3.connect(cfg["data"]["db_path"]) as conexion:
        return pd.read_sql(f"SELECT * FROM {TABLA}", conexion)


if __name__ == "__main__":
    configuracion = load_config()
    filas = load_to_db(configuracion)
    print(f"Tabla '{TABLA}' con {filas} filas en {configuracion['data']['db_path']}")