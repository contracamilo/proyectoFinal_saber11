"""Calibración de Platt: convierte el puntaje del modelo en una probabilidad real."""
import numpy as np
from numpy.typing import ArrayLike

Calibracion = dict[str, float]

LIMITE_PUNTAJE = 1e-6


def logit(puntaje: ArrayLike) -> np.ndarray:
    """Pasa un puntaje entre 0 y 1 a la escala lineal de la calibración."""
    acotado = np.clip(puntaje, LIMITE_PUNTAJE, 1 - LIMITE_PUNTAJE)
    return np.log(acotado / (1 - acotado))


def calibrar(puntaje: ArrayLike, calibracion: Calibracion) -> np.ndarray:
    """Convierte el puntaje en probabilidad; conserva el orden entre perfiles."""
    escala = calibracion["pendiente"] * logit(puntaje) + calibracion["intercepto"]
    return 1 / (1 + np.exp(-escala))
