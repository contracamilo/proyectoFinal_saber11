"""Validación cruzada de los candidatos e importancia de variables del modelo final."""
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from saber11.config import load_config
from saber11.features.preprocessing import FEATURES, TARGET
from saber11.models.evaluate import cargar_metadatos, cargar_particiones

PARTICIONES = 5
REPETICIONES = 10
CANDIDATOS = ("logreg", "tree")
RUTA_REPORTES = Path("reports")


def validar_cruzado(modelo: Pipeline, datos: pd.DataFrame, semilla: int) -> dict[str, float]:
    """Reentrena una copia del modelo en cada partición y resume F1 y ROC-AUC."""
    particiones = StratifiedKFold(PARTICIONES, shuffle=True, random_state=semilla)
    resultados = cross_validate(
        clone(modelo),
        datos[FEATURES],
        datos[TARGET],
        cv=particiones,
        scoring=("f1", "roc_auc"),
    )
    return {
        "f1_media": float(resultados["test_f1"].mean()),
        "f1_desviacion": float(resultados["test_f1"].std()),
        "roc_auc_media": float(resultados["test_roc_auc"].mean()),
        "roc_auc_desviacion": float(resultados["test_roc_auc"].std()),
    }


def importancia_variables(modelo: Pipeline, datos: pd.DataFrame, semilla: int) -> pd.DataFrame:
    """Mide cuánto cae el ROC-AUC al desordenar cada variable de entrada."""
    resultado = permutation_importance(
        modelo,
        datos[FEATURES],
        datos[TARGET],
        scoring="roc_auc",
        n_repeats=REPETICIONES,
        random_state=semilla,
    )
    tabla = pd.DataFrame(
        {
            "variable": FEATURES,
            "caida_roc_auc": resultado.importances_mean,
            "desviacion": resultado.importances_std,
        }
    )
    return tabla.sort_values("caida_roc_auc", ascending=False, ignore_index=True)


def _guardar_figura(tabla: pd.DataFrame, ruta: Path) -> None:
    """Guarda la gráfica de las diez variables más importantes."""
    principales = tabla.head(10).iloc[::-1]
    plt.figure(figsize=(8, 4.5))
    plt.barh(principales["variable"], principales["caida_roc_auc"], color="#2f6db3")
    plt.xlabel("Caída del ROC-AUC al desordenar la variable")
    plt.title("Importancia de variables en test")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(ruta, dpi=120, bbox_inches="tight")
    plt.close()


def _reporte(validacion: dict[str, dict[str, float]], tabla: pd.DataFrame) -> str:
    """Construye el reporte Markdown."""
    filas = [
        "# Validación cruzada e importancia de variables",
        "",
        f"## Validación cruzada de {PARTICIONES} particiones sobre entrenamiento y validación",
        "",
        "| Modelo | F1 | ROC-AUC |",
        "|---|---|---|",
    ]
    for nombre, valores in validacion.items():
        filas.append(
            f"| {nombre} | {valores['f1_media']:.4f} ± {valores['f1_desviacion']:.4f} "
            f"| {valores['roc_auc_media']:.4f} ± {valores['roc_auc_desviacion']:.4f} |"
        )
    filas += [
        "",
        "## Importancia por permutación en test",
        "",
        "Las variables están correlacionadas: una importancia baja no significa que la "
        "variable no se relacione con el riesgo.",
        "",
        "| Variable | Caída del ROC-AUC | Desviación |",
        "|---|---|---|",
    ]
    for fila in tabla.itertuples():
        filas.append(f"| `{fila.variable}` | {fila.caida_roc_auc:.4f} | {fila.desviacion:.4f} |")
    return "\n".join(filas) + "\n"


def analizar() -> str:
    """Genera los reportes de validación cruzada e importancia de variables."""
    cfg = load_config()
    semilla = cfg["split"]["random_state"]
    entrenamiento, validacion, test = cargar_particiones(cfg)
    desarrollo = pd.concat([entrenamiento, validacion])
    carpeta = Path(cfg["model"]["artifact_path"]).parent

    resumen = {
        nombre: validar_cruzado(joblib.load(carpeta / f"{nombre}.joblib"), desarrollo, semilla)
        for nombre in CANDIDATOS
    }
    final = joblib.load(carpeta / f"{cargar_metadatos(cfg)['model_name']}.joblib")
    tabla = importancia_variables(final, test, semilla)

    RUTA_REPORTES.mkdir(exist_ok=True)
    tabla.to_csv(RUTA_REPORTES / "importancia_variables.csv", index=False)
    _guardar_figura(tabla, RUTA_REPORTES / "figures" / "importancia_variables.png")
    reporte = _reporte(resumen, tabla)
    (RUTA_REPORTES / "analisis_modelo.md").write_text(reporte, encoding="utf-8")
    return reporte


if __name__ == "__main__":
    print(analizar())
