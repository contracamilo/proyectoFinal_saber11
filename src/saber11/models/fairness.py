"""Auditoría de equidad por grupo para el modelo de riesgo de Saber 11."""

from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

RUTA_REPORTES = Path("reports")
SIN_DATO = "Sin dato"


def calcular_metricas_por_grupo(
    y_real: pd.Series,
    y_predicho: np.ndarray,
    grupos: pd.Series,
    variable: str,
) -> pd.DataFrame:
    """Calcula prevalencia, predicción y errores para cada grupo."""
    datos = pd.DataFrame(
        {
            "real": np.asarray(y_real),
            "predicho": np.asarray(y_predicho),
            "grupo": grupos.astype("string").fillna(SIN_DATO).to_numpy(),
        }
    )
    filas: list[dict[str, Any]] = []
    for grupo, parte in datos.groupby("grupo", sort=True, dropna=False):
        verdaderos_positivos = int(
            ((parte["real"] == 1) & (parte["predicho"] == 1)).sum()
        )
        falsos_positivos = int(
            ((parte["real"] == 0) & (parte["predicho"] == 1)).sum()
        )
        positivos_reales = int((parte["real"] == 1).sum())
        negativos_reales = int((parte["real"] == 0).sum())
        positivos_predichos = verdaderos_positivos + falsos_positivos

        filas.append(
            {
                "variable": variable,
                "grupo": str(grupo),
                "n": int(len(parte)),
                "riesgo_real_pct": 100 * positivos_reales / len(parte),
                "riesgo_predicho_pct": 100
                * int((parte["predicho"] == 1).sum())
                / len(parte),
                "recall": (
                    verdaderos_positivos / positivos_reales
                    if positivos_reales
                    else np.nan
                ),
                "precision": (
                    verdaderos_positivos / positivos_predichos
                    if positivos_predichos
                    else np.nan
                ),
                "tasa_falsos_positivos": (
                    falsos_positivos / negativos_reales
                    if negativos_reales
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(filas)


def brecha_maxima_recall(metricas: pd.DataFrame) -> float:
    """Calcula la diferencia entre el recall mayor y menor de los grupos."""
    recalls = metricas["recall"].dropna()
    if len(recalls) < 2:
        return 0.0
    return float(recalls.max() - recalls.min())


def _entrenar_sin_sensibles(
    modelo: Pipeline,
    entrenamiento: pd.DataFrame,
    features: list[str],
    sensibles: list[str],
    objetivo: str,
    construir_preprocesador: Callable[..., ColumnTransformer],
) -> tuple[Pipeline, list[str]]:
    """Reentrena el estimador elegido excluyendo las variables sensibles."""
    variables = [columna for columna in features if columna not in sensibles]
    if not variables:
        raise ValueError(
            "No quedan variables de entrada al excluir las variables sensibles."
        )

    modelo_sin_sensibles = Pipeline(
        [
            ("prep", construir_preprocesador(features=variables)),
            ("clf", clone(modelo.named_steps["clf"])),
        ]
    )
    modelo_sin_sensibles.fit(
        entrenamiento[variables],
        entrenamiento[objetivo],
    )
    return modelo_sin_sensibles, variables


def _auditar_grupos(
    test: pd.DataFrame,
    prediccion: np.ndarray,
    sensibles: list[str],
    objetivo: str,
    nombre_modelo: str,
) -> pd.DataFrame:
    """Calcula métricas para las variables sensibles del conjunto de test."""
    faltantes = [columna for columna in sensibles if columna not in test.columns]
    if faltantes:
        raise ValueError(
            f"Faltan variables sensibles en el conjunto de test: {faltantes}."
        )

    tablas = [
        calcular_metricas_por_grupo(
            test[objetivo],
            prediccion,
            test[variable],
            variable,
        )
        for variable in sensibles
    ]
    if not tablas:
        raise ValueError("No hay variables sensibles definidas para la auditoría.")
    return pd.concat(tablas, ignore_index=True).assign(modelo=nombre_modelo)


def _formatear_valor(valor: Any, decimales: int = 4) -> str:
    """Formatea valores numéricos y representa los no disponibles como N/D."""
    if pd.isna(valor):
        return "N/D"
    if isinstance(valor, (int, np.integer)):
        return f"{valor:,}"
    return f"{valor:.{decimales}f}"


def _tabla_markdown(tabla: pd.DataFrame) -> str:
    """Convierte una tabla pequeña a Markdown sin dependencias opcionales."""
    columnas = list(tabla.columns)
    lineas = [
        "| " + " | ".join(columnas) + " |",
        "| " + " | ".join("---" for _ in columnas) + " |",
    ]
    for _, fila in tabla.iterrows():
        valores = [
            _formatear_valor(fila[columna])
            if isinstance(fila[columna], (int, float, np.number))
            else str(fila[columna]).replace("|", r"\|")
            for columna in columnas
        ]
        lineas.append("| " + " | ".join(valores) + " |")
    return "\n".join(lineas)


def _crear_informe(
    resultados: pd.DataFrame,
    comparacion: pd.DataFrame,
    nombre_modelo: str,
) -> str:
    """Redacta el informe de equidad y la comparación de modelos."""
    secciones = [
        "# Auditoría de equidad por grupo",
        "",
        f"Modelo evaluado: **{nombre_modelo}**. Métricas calculadas sobre el "
        "conjunto de test, que no se usa para ajustar el modelo.",
        "",
        "La proporción de riesgo se presenta como porcentaje; recall, "
        "precision y tasa de falsos positivos se expresan entre 0 y 1. "
        "N/D indica que la métrica no está definida para ese grupo "
        "(por ejemplo, si no hay casos positivos reales).",
        "",
        "## Resultados por grupo del modelo seleccionado",
        "",
    ]
    columnas = [
        "grupo",
        "n",
        "riesgo_real_pct",
        "riesgo_predicho_pct",
        "recall",
        "precision",
        "tasa_falsos_positivos",
    ]
    for variable, tabla in resultados[
        resultados["modelo"] == nombre_modelo
    ].groupby("variable", sort=False):
        brecha = brecha_maxima_recall(tabla)
        secciones.extend(
            [
                f"### {variable}",
                "",
                f"Brecha máxima de recall entre grupos: **{brecha:.4f}** "
                f"({brecha * 100:.2f} puntos porcentuales).",
                "",
                _tabla_markdown(tabla[columnas]),
                "",
                f"![Recall por grupo: {variable}]"
                f"(figures/equidad_recall_{variable}.png)",
                "",
            ]
        )

    secciones.extend(
        [
            "## Modelo completo frente a modelo sin variables sensibles",
            "",
            "El modelo sin variables sensibles se reentrena con las mismas "
            "filas de entrenamiento y el mismo tipo de estimador seleccionado. "
            "Ambos se comparan en el mismo conjunto de test. Excluir estas "
            "variables no garantiza equidad: otras entradas pueden actuar "
            "como aproximaciones indirectas.",
            "",
            _tabla_markdown(comparacion),
            "",
            "Las brechas describen diferencias observadas en esta muestra; "
            "no prueban por sí solas discriminación ni causalidad. Deben "
            "interpretarse junto con el tamaño de cada grupo y el contexto. "
            "El análisis es agregado y no justifica decisiones automatizadas "
            "sobre estudiantes individuales.",
            "",
        ]
    )
    return "\n".join(secciones)


def _guardar_graficos(resultados: pd.DataFrame, nombre_modelo: str) -> None:
    """Guarda un gráfico horizontal de recall para cada variable sensible."""
    seleccion = resultados[resultados["modelo"] == nombre_modelo]
    for variable, tabla in seleccion.groupby("variable", sort=False):
        tabla = tabla.sort_values("recall", na_position="first")
        alto = max(4.0, 0.45 * len(tabla))
        figura, eje = plt.subplots(figsize=(9, alto))
        eje.barh(tabla["grupo"], tabla["recall"], color="#4472C4")
        eje.set_xlim(0, 1)
        eje.set_xlabel("Recall de la clase en riesgo")
        eje.set_ylabel("Grupo")
        eje.set_title(f"Recall por grupo: {variable}")
        eje.grid(axis="x", alpha=0.25)
        figura.tight_layout()
        figura.savefig(
            RUTA_REPORTES
            / "figures"
            / f"equidad_recall_{variable}.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(figura)


def auditar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evalúa la equidad en test y guarda CSV, Markdown y gráficos."""
    from saber11.config import load_config
    from saber11.data.repository import read_raw
    from saber11.features.preprocessing import (
        FEATURES,
        SENSITIVE,
        TARGET,
        build_preprocessor,
        build_target,
        clean,
        split,
    )
    from saber11.models.evaluate import _cargar_modelo_seleccionado

    cfg = load_config()
    df = clean(read_raw(cfg))
    df, _ = build_target(df, cfg["target"]["threshold_percentile"])
    entrenamiento, _, test = split(df, cfg)
    nombre_modelo, modelo = _cargar_modelo_seleccionado(cfg)

    y_real = test[TARGET]
    prediccion = modelo.predict(test[FEATURES])
    resultados_completo = _auditar_grupos(
        test,
        prediccion,
        SENSITIVE,
        TARGET,
        nombre_modelo,
    )

    modelo_sin_sensibles, variables_sin_sensibles = _entrenar_sin_sensibles(
        modelo,
        entrenamiento,
        FEATURES,
        SENSITIVE,
        TARGET,
        build_preprocessor,
    )
    prediccion_sin_sensibles = modelo_sin_sensibles.predict(
        test[variables_sin_sensibles]
    )
    resultados_sin_sensibles = _auditar_grupos(
        test,
        prediccion_sin_sensibles,
        SENSITIVE,
        TARGET,
        "sin_sensibles",
    )
    resultados = pd.concat(
        [resultados_completo, resultados_sin_sensibles],
        ignore_index=True,
    )

    comparacion_filas: list[dict[str, Any]] = []
    for nombre, y_predicho, tabla in (
        (nombre_modelo, prediccion, resultados_completo),
        ("sin_sensibles", prediccion_sin_sensibles, resultados_sin_sensibles),
    ):
        fila: dict[str, Any] = {
            "modelo": nombre,
            "f1": float(f1_score(y_real, y_predicho, zero_division=0)),
        }
        for variable in SENSITIVE:
            metricas_variable = tabla[tabla["variable"] == variable]
            fila[f"brecha_recall_{variable}"] = brecha_maxima_recall(
                metricas_variable
            )
        comparacion_filas.append(fila)
    comparacion = pd.DataFrame(comparacion_filas)

    (RUTA_REPORTES / "figures").mkdir(parents=True, exist_ok=True)
    resultados.to_csv(
        RUTA_REPORTES / "equidad.csv",
        index=False,
        encoding="utf-8",
    )
    (RUTA_REPORTES / "equidad.md").write_text(
        _crear_informe(resultados, comparacion, nombre_modelo),
        encoding="utf-8",
    )
    _guardar_graficos(resultados, nombre_modelo)
    return resultados, comparacion


if __name__ == "__main__":
    tabla_final, resumen = auditar()
    print("Comparación en el conjunto de test")
    print(_tabla_markdown(resumen))
    print("\nBrechas máximas de recall por variable y modelo")
    for (modelo, variable), tabla in tabla_final.groupby(
        ["modelo", "variable"],
        sort=False,
    ):
        print(
            f"{modelo} / {variable}: "
            f"{brecha_maxima_recall(tabla):.4f}"
        )
    print(f"\nReportes y gráficos guardados en {RUTA_REPORTES}")
