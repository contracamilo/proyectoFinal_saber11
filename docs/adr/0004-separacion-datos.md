# ADR-004: Estrategia de separación de datos

- **Estado:** Aceptada
- **Fecha:** 2026-10-31
- **Autor(es):** Camilo Rivera Quintero

## Contexto
Para demostrar que el modelo funciona hay que medirlo con datos que no vio. Estos son los drivers que condicionan la decisión:

- **Clases desbalanceadas:** 24,57 % de clase 1. Una separación al azar podría dejar proporciones distintas en cada conjunto.
- **Fuga de información (QA6):** ninguna información de validación o test puede influir en el entrenamiento.
- **Reproducibilidad (QA5):** cualquier integrante debe obtener la misma separación.
- **Duplicados en la fuente:** de 152.584 filas solo 76.253 son estudiantes únicos. Sin quitarlos, un estudiante podría quedar en train y en test.
- **Alcance:** solo se usa un periodo (20224).

## Alternativas consideradas
| Alternativa | Ventajas | Desventajas |
|---|---|---|
| **70/15/15 estratificado** | Validación para elegir el modelo y test intacto para el resultado final; misma proporción de clases; rápido | Menos datos para entrenar que con k-fold |
| 80/20 simple, sin validación | Lo más sencillo | Elegir el modelo con test contamina el resultado final |
| Validación cruzada k-fold | Aprovecha mejor los datos; da una estimación más estable | Multiplica el tiempo de entrenamiento; con 76.253 estudiantes la ganancia es menor. Se usa solo para confirmar la selección, no para reemplazar esta separación |
| Separación temporal por periodo | Simula el uso real: entrenar con el pasado y predecir el futuro | Requiere varios periodos y el alcance actual solo tiene uno |

## Criterios / métricas de evaluación
| Criterio | 70/15/15 estratificado |
|---|---|
| Evaluación honesta | ✅ Test solo se usa al final |
| Proporción de clases estable | ✅ 24,57 % de clase 1 en los tres conjuntos |
| Reproducibilidad | ✅ `random_state=42` en `config.yaml` |
| Tiempo de cómputo | ✅ El entrenamiento completo tarda menos de 10 segundos |

## Decisión
Separar los datos **70/15/15, estratificando por el target, con `random_state=42`**, después de dejar una fila por `estu_consecutivo`. El preprocesamiento va dentro de un `Pipeline` de scikit-learn, ajustado solo con train.

| Conjunto | Estudiantes | Clase 1 |
|---|---|---|
| Train | 53.377 | 24,57 % |
| Validación | 11.438 | 24,57 % |
| Test | 11.438 | 24,57 % |

## Consecuencias
- **Positivas:**
  - Las métricas de test son una estimación honesta: el modelo no vio esos estudiantes y ninguno está repetido en otro conjunto.
  - La imputación y la codificación se calculan solo con train, sin fuga de estadísticas.
  - Cualquier integrante obtiene la misma separación.
- **Negativas / riesgos / deuda técnica:**
  - Un solo periodo no demuestra que el modelo funcione en años futuros.
  - La separación es por estudiante, no por colegio: un mismo colegio aparece en los tres conjuntos.
  - El umbral del target (234) se calcula sobre todo el periodo. Es una definición del problema y no entra al modelo como variable.

## Trade-offs
- Se sacrifica algo de **datos para entrenar y de estabilidad de la estimación** (frente a k-fold) a cambio de **simplicidad y rapidez**.
- Se sacrifica **realismo temporal** a cambio de **poder trabajar con un solo periodo**.

## Validación
- `tests/test_data.py` comprueba que la proporción de clases se mantiene (±2 %), que no hay filas repetidas entre conjuntos y que `clean()` quita los duplicados.
- El notebook `notebooks/01_eda.ipynb` muestra 0 duplicados de `estu_consecutivo` y los tamaños reales de cada conjunto.
- La fuga de variables se bloquea con `ValueError` (QA6) y se valida con un test.
