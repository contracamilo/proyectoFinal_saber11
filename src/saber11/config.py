from pathlib import Path

import yaml


def load_config(path: str = "config/config.yaml") -> dict:
    """Lee el archivo YAML de configuración y lo devuelve como diccionario."""
    ruta = Path(path)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta}. Ejecuta el comando desde la raíz del repositorio."
        )
    # encoding="utf-8" es obligatorio en Windows: sin él, "BOGOTÁ" se lee mal.
    with ruta.open(encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)