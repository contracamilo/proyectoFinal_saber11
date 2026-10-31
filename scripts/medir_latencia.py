"""Mide la latencia de POST /predict con clientes concurrentes (escenario QA1)."""
import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from saber11.api.schemas import PerfilEntrada

UMBRAL_P95_MS = 300
RUTA_SALIDA = Path("reports/latencia.json")


def _medir(cliente: httpx.Client, perfil: dict) -> tuple[float, int]:
    """Envía una solicitud y devuelve su duración en milisegundos y su estado."""
    inicio = time.perf_counter()
    respuesta = cliente.post("/predict", json=perfil)
    return (time.perf_counter() - inicio) * 1000, respuesta.status_code


def medir(url: str, solicitudes: int, clientes: int) -> dict:
    """Envía las solicitudes en paralelo y resume la latencia."""
    perfil = PerfilEntrada.model_config["json_schema_extra"]["example"]
    with httpx.Client(base_url=url, timeout=30) as cliente:
        with ThreadPoolExecutor(max_workers=clientes) as hilos:
            resultados = list(hilos.map(lambda _: _medir(cliente, perfil), range(solicitudes)))

    tiempos = sorted(duracion for duracion, _ in resultados)
    p95 = tiempos[round(0.95 * len(tiempos)) - 1]
    return {
        "solicitudes": solicitudes,
        "clientes": clientes,
        "errores": sum(1 for _, estado in resultados if estado != 200),
        "p50_ms": round(statistics.median(tiempos), 2),
        "p95_ms": round(p95, 2),
        "max_ms": round(tiempos[-1], 2),
        "cumple_qa1": p95 < UMBRAL_P95_MS,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mide la latencia de la API.")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--solicitudes", type=int, default=500)
    parser.add_argument("--clientes", type=int, default=10)
    args = parser.parse_args()

    resumen = medir(args.url, args.solicitudes, args.clientes)
    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    RUTA_SALIDA.write_text(json.dumps(resumen, indent=2), encoding="utf-8")
    print(json.dumps(resumen, indent=2))
