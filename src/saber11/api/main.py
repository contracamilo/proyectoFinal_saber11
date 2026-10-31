"""Rutas HTTP de la API de predicción."""
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from saber11.api.model_service import ServicioPrediccion
from saber11.api.schemas import Estado, PerfilEntrada, Prediccion
from saber11.config import load_config

RUTA_METRICAS = Path("reports/metrics.json")


@asynccontextmanager
async def ciclo_de_vida(aplicacion: FastAPI) -> AsyncIterator[None]:
    """Carga el modelo una sola vez al iniciar la API."""
    cfg = load_config()
    aplicacion.state.servicio = ServicioPrediccion.cargar(cfg["model"]["artifact_path"])
    yield


app = FastAPI(
    title="Riesgo de bajo desempeño en Saber 11",
    description="Estimación con fines de planeación agregada. No usar para decisiones individuales.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


@app.get("/health", response_model=Estado)
def health(request: Request) -> Estado:
    """Indica que el servicio responde y qué modelo tiene cargado."""
    return Estado(status="ok", model=request.app.state.servicio.nombre)


@app.post("/predict", response_model=Prediccion)
def predict(perfil: PerfilEntrada, request: Request) -> Prediccion:
    """Estima el riesgo de un perfil de contexto."""
    riesgo, probabilidad = request.app.state.servicio.predecir(perfil.model_dump())
    return Prediccion(riesgo=riesgo, probabilidad=probabilidad)


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    """Devuelve las métricas de test del modelo."""
    if not RUTA_METRICAS.exists():
        raise HTTPException(
            status_code=404,
            detail="No hay métricas. Ejecuta: python -m saber11.models.evaluate",
        )
    return json.loads(RUTA_METRICAS.read_text(encoding="utf-8"))
