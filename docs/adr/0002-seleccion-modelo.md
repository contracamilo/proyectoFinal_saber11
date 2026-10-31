# ADR-002: Selección del modelo de clasificación

- **Estado:** Aceptada
- **Fecha:** 2026-10-31
- **Autor(es):** Richardo Caicedo

## Contexto

El proyecto estima si un estudiante pertenece a la clase de riesgo de bajo
desempeño, definida como un puntaje global por debajo del percentil 25 del
periodo estudiado. El uso previsto es apoyar la focalización **agregada** de
programas de refuerzo; el modelo no debe tomar decisiones individuales sobre
estudiantes.

La clase positiva es `riesgo_bajo_desempeno = 1` y representa aproximadamente
una cuarta parte de los registros. Por el desbalance, la exactitud global no
basta para comparar modelos: es importante medir cuántos casos de riesgo se
detectan y cuántas predicciones positivas son correctas. La selección se hace
con validación; el conjunto de prueba se conserva para la evaluación final.

## Alternativas consideradas

| Alternativa | Papel y ventajas | Desventajas |
|---|---|---|
| `DummyClassifier` | Línea base sencilla; permite comprobar si los modelos aprenden más que una regla trivial. | No aprende relaciones útiles entre las variables; no se propone como modelo de producción. |
| Regresión Logística | Modelo relativamente interpretable, eficiente y adecuado como primera alternativa para clasificación binaria. `class_weight="balanced"` ayuda a considerar el desbalance. | Sus relaciones son principalmente lineales en el espacio transformado; puede no capturar interacciones complejas. |
| Árbol de Decisión | Captura reglas e interacciones no lineales y puede explicarse mediante divisiones. Se limita su complejidad con profundidad y tamaño mínimo de hoja. | Puede ser inestable y sobreajustarse; sus reglas pueden volverse difíciles de comunicar si crece demasiado. |
| K-Nearest Neighbors (KNN) | Método no paramétrico que puede modelar fronteras no lineales. | La predicción puede ser costosa en conjuntos grandes y depende de la escala y de la métrica de distancia; explicar una decisión individual requiere inspeccionar vecinos. |
| Random Forest | Conjunto de árboles que puede capturar patrones no lineales y reducir la variabilidad de un árbol individual. | Menor interpretabilidad que un árbol individual y mayor costo de cómputo; se descarta para esta primera versión por priorizar explicabilidad y sencillez. |

## Criterios / métricas de evaluación

- **F1 de la clase 1 en validación:** métrica principal del proceso de selección,
  porque resume precision y recall en la clase de riesgo.
- **Recall de la clase 1 en validación:** se revisa explícitamente porque un
  falso negativo representa un caso de riesgo que el modelo no detecta y que
  podría quedar fuera de una estrategia de apoyo.
- **Interpretabilidad:** se prefiere regresión logística cuando su F1 es
  comparable al del árbol, para facilitar la explicación de la decisión.
- **Costo de cómputo:** se consideran el ajuste y la predicción sobre un
  conjunto de datos de tamaño considerable; se favorecen alternativas
  relativamente ligeras.
- **Equidad:** se deben inspeccionar recall y tasa de falsos positivos por
  grupos sensibles. El desempeño global no basta para justificar el uso del
  modelo, y excluir variables sensibles no garantiza por sí solo equidad.

## Decisión

Se entrenan `DummyClassifier`, Regresión Logística y Árbol de Decisión. Se
selecciona el árbol con mayor F1 de clase 1 en validación; si la Regresión
Logística queda a no más de 0,01 puntos de F1 del mejor árbol, se prefiere la
Regresión Logística por su mayor facilidad de interpretación. La línea base se
conserva únicamente como referencia. KNN y Random Forest quedan fuera de esta
primera comparación.

Los hiperparámetros del árbol se comparan usando validación. El conjunto de
prueba no interviene en la selección ni en el ajuste.

## Consecuencias

- **Positivas:**
  - Hay una regla de selección explícita y reproducible basada en validación.
  - La Regresión Logística se favorece cuando su desempeño es prácticamente
    equivalente al del mejor árbol.
  - La línea base permite contextualizar si los modelos candidatos aportan
    valor frente a una predicción trivial.
  - La auditoría por grupos y la comparación con un modelo sin variables
    sensibles aportan evidencia adicional para la discusión ética.
- **Negativas / riesgos / deuda técnica:**
  - La selección por F1 no representa por sí sola el costo social de cada tipo
    de error ni las restricciones reales de capacidad para ofrecer apoyos.
  - El margen de 0,01 es una regla práctica del proyecto, no una prueba de
    equivalencia estadística.
  - La interpretabilidad de la Regresión Logística no implica causalidad ni
    ausencia de sesgo; variables no sensibles también pueden actuar como
    aproximaciones indirectas.
  - La decisión se limita al periodo y población evaluados y debe revisarse
    ante cambios de datos o de propósito.

## Trade-offs

Se acepta que el árbol pueda obtener un F1 ligeramente mayor para favorecer la
explicabilidad de la Regresión Logística cuando la diferencia es de hasta
0,01. Si la ventaja del árbol supera ese margen, se prioriza el F1 medido en
validación, sujeto a la revisión de recall, equidad y limitaciones de uso.
Ninguna de las dos métricas globales sustituye el análisis de errores y de
consecuencias para los grupos.

## Validación

La implementación de `saber11.models.train` compara los candidatos con una
partición estratificada y selecciona usando validación. La evaluación final y
la matriz de confusión se generan por separado sobre test; la auditoría
`saber11.models.fairness` calcula métricas por grupo y compara el modelo
seleccionado con otro reentrenado sin variables sensibles.

**Resultados empíricos pendientes de incorporar:** en el workspace disponible
al redactar este ADR no están generados `reports/metrics.json` ni
`reports/equidad.csv`. Por ello no se consignan valores ni se afirma cuál
modelo ganó empíricamente. Tras ejecutar entrenamiento, evaluación y auditoría
con los datos reales, actualizar esta sección con el nombre seleccionado, las
métricas de validación y test, el F1 de test del modelo sin variables
sensibles y las brechas de recall por variable para ambos modelos. No usar
valores de test para volver a seleccionar hiperparámetros o modelos.
