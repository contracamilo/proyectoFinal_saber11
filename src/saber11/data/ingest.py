from pathlib import Path

import pandas as pd
import requests

from saber11.config import load_config

TIMEOUT_SEGUNDOS = 120


def download(cfg: dict) -> Path:
    """Descarga el dataset filtrado, página por página, y lo guarda como CSV."""
    datos = cfg["data"]
    ruta = Path(datos["raw_path"])
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
        respuesta = requests.get(datos["source_url"], params=params, timeout=TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()
        lote = respuesta.json()
        if not lote:
            break
        filas.extend(lote)
        print(f"Página {pagina}: {len(filas)} filas acumuladas")
        if len(lote) < datos["page_size"]:
            break
        offset += datos["page_size"]
        pagina += 1

    ruta.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas).to_csv(ruta, index=False, encoding="utf-8")
    print(f"Guardadas {len(filas)} filas en {ruta}")
    return ruta


if __name__ == "__main__":
    download(load_config())
