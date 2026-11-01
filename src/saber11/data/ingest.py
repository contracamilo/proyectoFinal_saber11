import argparse
import time
from pathlib import Path

import pandas as pd
import requests

from saber11.config import load_config

TIMEOUT_SEGUNDOS = 120
MAX_REINTENTOS = 3
ESPERA_SEGUNDOS = 5


def _pedir_pagina(url: str, params: dict) -> list[dict]:
    """Pide una página a la API. Reintenta si falla y lanza error si no lo logra."""
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            respuesta = requests.get(url, params=params, timeout=TIMEOUT_SEGUNDOS)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.RequestException as error:
            print(f"Intento {intento} de {MAX_REINTENTOS} falló: {error}")
            if intento == MAX_REINTENTOS:
                raise
            time.sleep(ESPERA_SEGUNDOS * intento)
    return []


def download(cfg: dict, force: bool = False) -> Path:
    """Descarga el dataset filtrado y lo guarda como CSV.

    Es idempotente: si el CSV ya existe y force es False, no descarga de nuevo.
    """
    datos = cfg["data"]
    ruta = Path(datos["raw_path"])
    if ruta.exists() and not force:
        print(f"{ruta} ya existe; no se descarga de nuevo (usa --force para repetir).")
        return ruta

    filtro = (
        f"periodo='{datos['periodo']}' "
        f"AND cole_depto_ubicacion='{datos['cole_depto_ubicacion']}'"
    )
    filas = []
    offset = 0
    pagina = 1
    while True:
        params = {
            "$where": filtro,
            "$order": "estu_consecutivo",
            "$limit": datos["page_size"],
            "$offset": offset,
        }
        lote = _pedir_pagina(datos["source_url"], params)
        if not lote:
            break
        filas.extend(lote)
        print(f"Página {pagina}: {len(filas)} filas acumuladas")
        if len(lote) < datos["page_size"]:
            break
        offset += datos["page_size"]
        pagina += 1

    if not filas:
        raise ValueError("La API no devolvió filas. Revisa el filtro en config.yaml.")

    # Se escribe al final: si una página falla, el CSV anterior queda intacto.
    ruta.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas).to_csv(ruta, index=False, encoding="utf-8")
    print(f"Guardadas {len(filas)} filas en {ruta}")
    return ruta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga los datos de Saber 11.")
    parser.add_argument("--force", action="store_true", help="Descarga aunque ya exista el CSV.")
    args = parser.parse_args()
    download(load_config(), force=args.force)
    