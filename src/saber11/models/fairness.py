"""Métricas de equidad por grupo sensible en el conjunto de test."""
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

from saber11.config import load_config
from saber11.features.preprocessing import FEATURES, SENSITIVE, TARGET, build_preprocessor
from saber11.models.evaluate import cargar_particiones

BRECHA_MAXIMA = 0.10
MINIMO_POR_GRUPO = 30
SIN_DATO = "Sin dato"
RUTA_REPORTES = Path("reports")


def metricas_por_grupo(y_real: pd.Series, y_predicho: np.ndarray, grupos: pd.Series) -> pd.DataFrame:
    """Calcula tamaño, tasas, recall, precision y falsos positivos por grupo."""
    datos = pd.DataFrame(
        {
            "real": np.asarray(y_real),
            "predicho": np.asarray(y_predicho),
            "grupo": grupos.astype(object).where(grupos.notna(), SIN_DATO).to_numpy(),
        }
    )
    filas = []
    for grupo, parte in datos.groupby("grupo"):
        vp = int(((parte["real"] == 1) & (parte["predicho"] == 1)).sum())
        fp = int(((parte["real"] == 0) & (parte["predicho"] == 1)).sum())
        positivos = int((parte["real"] == 1).sum())
        negativos = int((parte["real"] == 0).sum())
        predichos = vp + fp
        filas.append(
            {
                "grupo": grupo,
                "n": len(parte),
                "tasa_real": parte["real"].mean(),
                "tasa_predicha": parte["predicho"].mean(),
                "recall": vp / positivos if positivos else np.nan,
                "precision": vp / predichos if predichos else np.nan,
                "tasa_falsos_positivos": fp / negativos if negativos else np.nan,
            }
        )
    return pd.DataFrame(filas)


def brecha_recall(tabla: pd.DataFrame) -> float:
    """Devuelve la diferencia de recall entre grupos con tamaño suficiente."""
    recall = tabla.loc[tabla["n"] >= MINIMO_POR_GRUPO, "recall"].dropna()
    return float(recall.max() - recall.min()) if len(recall) > 1 else 0.0


def _auditar(y_real: pd.Series, y_predicho: np.ndarray, test: pd.DataFrame) -> pd.DataFrame:
    """Calcula las métricas por grupo para todas las variables sensibles."""
    tablas = [
        metricas_por_grupo(y_real, y_predicho, test[variable]).assign(variable=variable)
        for variable in SENSITIVE
    ]
    return pd.concat(tablas, ignore_index=True)


def _entrenar_sin_sensibles(modelo: Pipeline, train: pd.DataFrame) -> tuple[Pipeline, list[str]]:
    """Reentrena el mismo clasificador sin las variables sensibles."""
    variables = [c for c in FEATURES if c not in SENSITIVE]
    pipeline = Pipeline(
        [
            ("prep", build_preprocessor(features=variables)),
            ("clf", clone(modelo.named_steps["clf"])),
        ]
    )
    pipeline.fit(train[variables], train[TARGET])
    return pipeline, variables


def _graficar(resultados: pd.DataFrame) -> None:
    """Guarda un gráfico de recall por grupo para cada variable sensible."""
    for variable, tabla in resultados.groupby("variable"):
        ax = tabla.set_index("grupo")["recall"].sort_values().plot.barh(
            title=f"Recall por {variable}", xlim=(0, 1)
        )
        ax.set_xlabel("Recall")
        ax.set_ylabel("")
        plt.savefig(
            RUTA_REPORTES / "figures" / f"equidad_recall_{variable}.png",
            dpi=120,
            bbox_inches="tight",
        )
        plt.close()


def _informe(resultados: pd.DataFrame, comparacion: pd.DataFrame) -> str:
    """Construye el informe Markdown de equidad."""
    partes = [
        "# Equidad por grupo (conjunto de test)\n",
        f"Una brecha de recall mayor a {BRECHA_MAXIMA:.2f} se marca como hallazgo (QA7). "
        f"La brecha solo compara grupos con al menos {MINIMO_POR_GRUPO} personas.\n",
        "## Comparación con un modelo sin variables sensibles\n",
        comparacion.to_markdown(index=False, floatfmt=".4f"),
    ]
    for variable, tabla in resultados.groupby("variable", sort=False):
        brecha = brecha_recall(tabla)
        marca = "**Hallazgo**" if brecha > BRECHA_MAXIMA else "Dentro del criterio"
        partes += [
            f"\n## {variable}\n",
            f"Brecha de recall: {brecha:.4f}. {marca}.\n",
            tabla.drop(columns="variable").to_markdown(index=False, floatfmt=".4f"),
        ]
    return "\n".join(partes) + "\n"


def auditar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Audita el modelo seleccionado y guarda los reportes de equidad."""
    cfg: dict[str, Any] = load_config()
    train, _, test = cargar_particiones(cfg)
    modelo = joblib.load(cfg["model"]["artifact_path"])
    y_real = test[TARGET]

    prediccion = modelo.predict(test[FEATURES])
    resultados = _auditar(y_real, prediccion, test)

    sin_sensibles, variables = _entrenar_sin_sensibles(modelo, train)
    prediccion_sin = sin_sensibles.predict(test[variables])
    resultados_sin = _auditar(y_real, prediccion_sin, test)

    comparacion = pd.DataFrame(
        [
            {
                "modelo": nombre,
                "f1": f1_score(y_real, y_predicho),
                **{
                    f"brecha_{variable}": brecha_recall(tabla[tabla["variable"] == variable])
                    for variable in SENSITIVE
                },
            }
            for nombre, y_predicho, tabla in [
                ("completo", prediccion, resultados),
                ("sin_sensibles", prediccion_sin, resultados_sin),
            ]
        ]
    )

    (RUTA_REPORTES / "figures").mkdir(parents=True, exist_ok=True)
    resultados.to_csv(RUTA_REPORTES / "equidad.csv", index=False, encoding="utf-8")
    (RUTA_REPORTES / "equidad.md").write_text(_informe(resultados, comparacion), encoding="utf-8")
    _graficar(resultados)
    return resultados, comparacion


if __name__ == "__main__":
    tabla_final, resumen = auditar()
    print(resumen.round(4).to_string(index=False))
    for nombre_variable, parte_tabla in tabla_final.groupby("variable", sort=False):
        print(f"{nombre_variable}: brecha de recall {brecha_recall(parte_tabla):.4f}")
