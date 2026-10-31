import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

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

def split(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Separa en train, validación y test de forma estratificada."""
    parametros = cfg["split"]
    semilla = parametros["random_state"]
    train_val, test = train_test_split(
        df, test_size=parametros["test_size"], stratify=df[TARGET], random_state=semilla
    )
    proporcion_val = parametros["val_size"] / (1 - parametros["test_size"])
    train, val = train_test_split(
        train_val, test_size=proporcion_val, stratify=train_val[TARGET], random_state=semilla
    )
    return train, val, test


def _verificar_fuga(features: list[str]) -> None:
    """Lanza ValueError si alguna variable contiene el resultado de la prueba."""
    prohibidas = [c for c in features if c.startswith(LEAKAGE_PREFIXES)]
    if prohibidas:
        raise ValueError(f"Fuga de información en las variables: {prohibidas}")


def build_preprocessor(features: list[str] = FEATURES) -> ColumnTransformer:
    """Construye el preprocesador sin ajustar; se ajusta dentro del Pipeline solo con train."""
    _verificar_fuga(features)
    numericas = [c for c in features if c in NUMERICAS]
    categoricas = [c for c in features if c not in NUMERICAS]
    return ColumnTransformer(
        [
            (
                "categoricas",
                Pipeline(
                    [
                        ("imputar", SimpleImputer(strategy="most_frequent")),
                        ("codificar", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categoricas,
            ),
            (
                "numericas",
                Pipeline(
                    [
                        ("imputar", SimpleImputer(strategy="median")),
                        ("escalar", StandardScaler()),
                    ]
                ),
                numericas,
            ),
        ]
    )