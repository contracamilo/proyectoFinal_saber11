# ADR-002: Selección del modelo

- **Estado:** Aceptada
- **Fecha:** 2026-10-31
- **Autor(es):** Camilo Rivera Quintero

## Contexto
Hay que clasificar el riesgo de bajo desempeño (`punt_global` < 234) con un modelo básico de Machine Learning, usando solo variables previas a la prueba. Estos son los drivers que condicionan la decisión:

- **Restricción de la actividad:** modelo básico, sin redes neuronales (RS4).
- **Clases desbalanceadas:** 24,57 % de clase 1. La accuracy por sí sola engaña: el baseline alcanza 75,43 % sin detectar a nadie.
- **Costo de los errores:** para focalizar apoyos pesa más no dejar por fuera a quien está en riesgo (recall), aunque se generen falsas alarmas.
- **Transparencia:** el modelo debe poder explicarse en el análisis ético.
- **Mantenibilidad:** cambiar de modelo no debe tocar la API (QA8).

## Alternativas consideradas
| Alternativa | Ventajas | Desventajas |
|---|---|---|
| **Regresión logística** con `class_weight="balanced"` | Coeficientes interpretables; rápida; da puntajes que se pueden calibrar; funciona bien con variables one-hot | Solo captura relaciones lineales; menor recall que el árbol en este caso |
| Árbol de decisión (se probaron `max_depth` 3, 5, 8 y 12, y `min_samples_leaf` 20 y 50) | Reglas fáciles de leer si es poco profundo; captura interacciones | El mejor árbol tiene 321 hojas, por lo que deja de ser legible; más propenso al sobreajuste |
| KNN | Sin entrenamiento | Predecir exige comparar contra todo train, lo que pone en riesgo el p95 < 300 ms; difícil de explicar |
| `DummyClassifier` (baseline) | Da el piso de comparación | No detecta casos de riesgo; no es candidato a producción |

## Criterios / métricas de evaluación
Selección por **F1 de la clase 1 en validación**. Si la regresión logística queda a menos de 0,01 del mejor F1, se prefiere por su interpretabilidad.

| Modelo (validación) | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| baseline | 0,7543 | 0,0000 | 0,0000 | 0,0000 | 0,5000 |
| **logreg** | 0,6554 | 0,3900 | 0,7139 | **0,5044** | 0,7486 |
| tree (`max_depth=12`, `min_samples_leaf=50`) | 0,6276 | 0,3711 | 0,7431 | 0,4950 | 0,7360 |

La validación cruzada de 5 particiones sobre train y validación confirma la selección ([`reports/analisis_modelo.md`](../../reports/analisis_modelo.md)): logreg obtiene F1 de 0,5164 ± 0,0038 y ROC-AUC de 0,7575 ± 0,0034; el árbol, F1 de 0,5055 ± 0,0037 y ROC-AUC de 0,7425 ± 0,0041.

## Decisión
Usar **regresión logística** (`LogisticRegression(max_iter=1000, class_weight="balanced")`) dentro de un `Pipeline` de scikit-learn. Tiene el mejor F1 y el mejor ROC-AUC en validación, y es el modelo más fácil de explicar.

La API convierte el puntaje en probabilidad con una **calibración de Platt** ajustada en validación. `riesgo` se sigue decidiendo con el puntaje original y el umbral de 0,5.

## Consecuencias
- **Positivas:**
  - Cada coeficiente muestra cómo se asocia una categoría con el riesgo, lo que apoya el análisis ético.
  - Predecir toma milisegundos: el p95 medido es de 43,95 ms.
  - La API no cambia si se reemplaza el modelo, porque consume el `Pipeline` serializado.
- **Negativas / riesgos / deuda técnica:**
  - `class_weight="balanced"` aumenta el recall a costa de la precision y la accuracy: en test, la accuracy (0,6604) queda por debajo del baseline (0,7543).
  - El mismo peso infla el puntaje: promedia 0,4499 frente a una tasa real de 0,2457. Por eso la API no lo expone como probabilidad. Tras calibrar, el Brier en test baja de 0,2035 a 0,1574.
  - La precision es baja (0,3959): cerca de 6 de cada 10 alertas son falsas. No sirve para decisiones individuales.
  - El modelo presenta brechas de recall por grupo mayores a 0,10 ([`reports/equidad.md`](../../reports/equidad.md)).

## Trade-offs
- Se acepta **menor accuracy** a cambio de **detectar más casos de riesgo**, que es el objetivo del sistema.
- Se acepta **menor recall que el árbol** (0,7139 frente a 0,7431) a cambio de **mejor F1 y más interpretabilidad**.
- Se acepta **gastar el conjunto de validación también en calibrar** a cambio de no reservar otro conjunto. El efecto es mínimo porque la calibración solo ajusta dos parámetros.

## Validación
- `python -m saber11.models.train` regenera el modelo y sus métricas de validación.
- `python -m saber11.models.evaluate` confirma el resultado en test: F1 de 0,5126 y ROC-AUC de 0,7539, frente a F1 de 0 y ROC-AUC de 0,5 del baseline.
- `python -m saber11.models.analisis` repite la comparación con validación cruzada.
- Dos ejecuciones seguidas producen un `reports/metrics.json` idéntico (QA5).
