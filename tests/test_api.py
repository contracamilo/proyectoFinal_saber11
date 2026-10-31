"""Pruebas de la API con un modelo falso, sin archivos entrenados."""
import ast
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from saber11.api import main
from saber11.api.model_service import ServicioPrediccion
from saber11.api.schemas import PerfilEntrada
from saber11.features.preprocessing import FEATURES

PERFIL = PerfilEntrada.model_config["json_schema_extra"]["example"]


class ModeloFalso:
    """Imita predict_proba y registra las columnas que recibe."""

    def __init__(self, probabilidad: float) -> None:
        self.probabilidad = probabilidad
        self.columnas: list[str] = []

    def predict_proba(self, fila) -> np.ndarray:
        self.columnas = list(fila.columns)
        return np.array([[1 - self.probabilidad, self.probabilidad]])


@pytest.fixture
def cliente():
    """Crea un cliente con el servicio ya cargado, sin ejecutar el arranque real."""
    metadatos = {"model_name": "falso", "features": FEATURES}
    main.app.state.servicio = ServicioPrediccion(ModeloFalso(0.71), metadatos)
    return TestClient(main.app)


def test_inicio_redirige_a_la_documentacion(cliente):
    respuesta = cliente.get("/", follow_redirects=False)
    assert respuesta.status_code == 307
    assert respuesta.headers["location"] == "/docs"


def test_health_informa_el_modelo(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "model": "falso"}


def test_predict_devuelve_riesgo_y_probabilidad(cliente):
    respuesta = cliente.post("/predict", json=PERFIL)
    assert respuesta.status_code == 200
    assert respuesta.json() == {"riesgo": 1, "probabilidad": 0.71}


def test_predict_respeta_el_orden_de_las_variables(cliente):
    cliente.post("/predict", json=PERFIL)
    assert main.app.state.servicio.modelo.columnas == FEATURES


def test_umbral_de_decision():
    servicio = ServicioPrediccion(ModeloFalso(0.49), {"model_name": "falso", "features": FEATURES})
    assert servicio.predecir(PERFIL) == (0, 0.49)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("fami_estratovivienda", "Estrato 9"),
        ("edad", 8),
        ("estu_genero", None),
    ],
)
def test_predict_rechaza_valores_invalidos(cliente, campo, valor):
    respuesta = cliente.post("/predict", json={**PERFIL, campo: valor})
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"][0]["loc"][-1] == campo


def test_predict_rechaza_perfil_incompleto(cliente):
    incompleto = {k: v for k, v in PERFIL.items() if k != "edad"}
    assert cliente.post("/predict", json=incompleto).status_code == 422


def test_predict_rechaza_puntajes_e_identificadores(cliente):
    for campo in ("punt_global", "estu_consecutivo"):
        assert cliente.post("/predict", json={**PERFIL, campo: "1"}).status_code == 422


def test_metrics_devuelve_el_reporte(cliente, tmp_path, monkeypatch):
    ruta = tmp_path / "metrics.json"
    ruta.write_text(json.dumps({"selected_model": "logreg"}), encoding="utf-8")
    monkeypatch.setattr(main, "RUTA_METRICAS", ruta)
    assert cliente.get("/metrics").json() == {"selected_model": "logreg"}


def test_metrics_sin_reporte_responde_404(cliente, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "RUTA_METRICAS", tmp_path / "no_existe.json")
    assert cliente.get("/metrics").status_code == 404


def test_esquema_coincide_con_las_variables_del_modelo():
    assert list(PerfilEntrada.model_fields) == FEATURES


def test_carga_sin_artefactos_da_un_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError, match="saber11.models.train"):
        ServicioPrediccion.cargar(str(tmp_path / "model.joblib"))


def test_la_api_no_depende_de_datos_ni_procesamiento():
    prohibidos = ("saber11.data", "saber11.features", "saber11.models")
    for archivo in Path("src/saber11/api").glob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ImportFrom) and nodo.module:
                assert not nodo.module.startswith(prohibidos), archivo
