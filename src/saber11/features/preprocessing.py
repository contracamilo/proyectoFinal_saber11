"""Limpieza, construcción del target, separación y preprocesamiento."""
import pandas as pd

TARGET = "riesgo_bajo_desempeno"
FEATURES = [
    "cole_area_ubicacion",
    "cole_bilingue",
    "cole_calendario",
    "cole_caracter",
    "cole_genero",
    "cole_jornada",
    "cole_naturaleza",
    "estu_genero",
    "fami_cuartoshogar",
    "fami_educacionmadre",
    "fami_educacionpadre",
    "fami_estratovivienda",
    "fami_personashogar",
    "fami_tieneautomovil",
    "fami_tienecomputador",
    "fami_tieneinternet",
    "fami_tienelavadora",
    "edad",
]
SENSITIVE = ["estu_genero", "fami_estratovivienda", "cole_naturaleza", "cole_area_ubicacion"]
LEAKAGE_PREFIXES = ("punt_", "desemp_", "percentil_")

NUMERICAS = ["edad"]
VALORES_VACIOS = ["", "-"]
EDAD_MINIMA = 13
EDAD_MAXIMA = 30


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Quita duplicados, convierte tipos, calcula la edad y normaliza los valores vacíos."""
    df = df.drop_duplicates(subset="estu_consecutivo").copy()
    df["punt_global"] = pd.to_numeric(df["punt_global"], errors="coerce")
    df = df.dropna(subset=["punt_global"]).copy()

    nacimiento = pd.to_datetime(df["estu_fechanacimiento"], format="%d/%m/%Y", errors="coerce")
    anio_prueba = pd.to_numeric(df["periodo"].astype(str).str[:4], errors="coerce")
    edad = anio_prueba - nacimiento.dt.year
    df["edad"] = edad.where(edad.between(EDAD_MINIMA, EDAD_MAXIMA))

    for columna in FEATURES:
        if columna not in NUMERICAS and columna in df.columns:
            df[columna] = df[columna].where(~df[columna].isin(VALORES_VACIOS))
    return df


def build_target(df: pd.DataFrame, percentile: int) -> tuple[pd.DataFrame, float]:
    """Agrega el target: 1 si punt_global está por debajo del percentil pedido."""
    df = df.copy()
    umbral = float(df["punt_global"].quantile(percentile / 100))
    df[TARGET] = (df["punt_global"] < umbral).astype(int)
    return df, umbral
