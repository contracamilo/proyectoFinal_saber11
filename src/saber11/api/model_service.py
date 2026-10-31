"""Carga del modelo y predicción de riesgo."""
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

UMBRAL_DECISION = 0.5


class ServicioPrediccion:
    """Mantiene el Pipeline en memoria y convierte probabilidades en riesgo."""

    def __init__(self, modelo: Pipeline, metadatos: dict[str, Any]) -> None:
        self.modelo = modelo
        self.nombre = metadatos["model_name"]
        self.variables = metadatos["features"]

    @classmethod
    def cargar(cls, ruta_modelo: str) -> "ServicioPrediccion":
        """Carga el modelo y sus metadatos; se llama una sola vez al iniciar la API."""
        ruta = Path(ruta_modelo)
        ruta_metadatos = ruta.parent / "model_meta.json"
        if not ruta.exists() or not ruta_metadatos.exists():
            raise FileNotFoundError(
                f"No se encontró {ruta}. Ejecuta primero: python -m saber11.models.train"
            )
        metadatos = json.loads(ruta_metadatos.read_text(encoding="utf-8"))
        return cls(joblib.load(ruta), metadatos)

    def predecir(self, perfil: dict[str, Any]) -> tuple[int, float]:
        """Devuelve el riesgo (0 o 1) y la probabilidad de la clase 1."""
        fila = pd.DataFrame([perfil], columns=self.variables)
        probabilidad = float(self.modelo.predict_proba(fila)[0, 1])
        return int(probabilidad >= UMBRAL_DECISION), probabilidad
