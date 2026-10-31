"""Esquemas de entrada y salida de la API."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SiNo = Literal["Si", "No"]
EducacionFamiliar = Literal[
    "Educación profesional completa",
    "Educación profesional incompleta",
    "Ninguno",
    "No Aplica",
    "No sabe",
    "Postgrado",
    "Primaria completa",
    "Primaria incompleta",
    "Secundaria (Bachillerato) completa",
    "Secundaria (Bachillerato) incompleta",
    "Técnica o tecnológica completa",
    "Técnica o tecnológica incompleta",
]


class PerfilEntrada(BaseModel):
    """Perfil de contexto previo a la prueba. No incluye identificadores ni puntajes."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "cole_area_ubicacion": "URBANO",
                "cole_bilingue": "N",
                "cole_calendario": "A",
                "cole_caracter": "ACADÉMICO",
                "cole_genero": "MIXTO",
                "cole_jornada": "MAÑANA",
                "cole_naturaleza": "OFICIAL",
                "estu_genero": "F",
                "fami_cuartoshogar": "Tres",
                "fami_educacionmadre": "Secundaria (Bachillerato) completa",
                "fami_educacionpadre": "Primaria completa",
                "fami_estratovivienda": "Estrato 2",
                "fami_personashogar": "3 a 4",
                "fami_tieneautomovil": "No",
                "fami_tienecomputador": "Si",
                "fami_tieneinternet": "Si",
                "fami_tienelavadora": "Si",
                "edad": 17,
            }
        },
    )

    cole_area_ubicacion: Literal["RURAL", "URBANO"]
    cole_bilingue: Literal["N", "S"]
    cole_calendario: Literal["A", "B", "OTRO"]
    cole_caracter: Literal["ACADÉMICO", "NO APLICA", "TÉCNICO", "TÉCNICO/ACADÉMICO"]
    cole_genero: Literal["FEMENINO", "MASCULINO", "MIXTO"]
    cole_jornada: Literal["COMPLETA", "MAÑANA", "NOCHE", "SABATINA", "TARDE", "UNICA"]
    cole_naturaleza: Literal["NO OFICIAL", "OFICIAL"]
    estu_genero: Literal["F", "M"]
    fami_cuartoshogar: Literal["Uno", "Dos", "Tres", "Cuatro", "Cinco", "Seis o mas"]
    fami_educacionmadre: EducacionFamiliar
    fami_educacionpadre: EducacionFamiliar
    fami_estratovivienda: Literal[
        "Estrato 1",
        "Estrato 2",
        "Estrato 3",
        "Estrato 4",
        "Estrato 5",
        "Estrato 6",
        "Sin Estrato",
    ]
    fami_personashogar: Literal["1 a 2", "3 a 4", "5 a 6", "7 a 8", "9 o más"]
    fami_tieneautomovil: SiNo
    fami_tienecomputador: SiNo
    fami_tieneinternet: SiNo
    fami_tienelavadora: SiNo
    edad: int = Field(ge=13, le=30)


class Prediccion(BaseModel):
    """Resultado de una predicción de riesgo."""

    riesgo: Literal[0, 1]
    probabilidad: float = Field(ge=0, le=1)


class Estado(BaseModel):
    """Estado del servicio y modelo cargado."""

    status: str
    model: str
