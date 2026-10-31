# ADR-004: Estrategia de separación de datos

- **Estado:** Aceptada
- **Fecha:** 31/10/2026
- **Autor:** Daniel Charry

## Contexto

Para saber si el modelo sirve, hay que medirlo con datos que no vio al entrenar. Además, el target `riesgo_bajo_desempeno` está desbalanceado: cerca de 25 % de los estudiantes está en riesgo (clase 1) y 75 % no (clase 0). Si la separación no respeta esa proporción, un conjunto puede quedar con más o menos casos de riesgo que otro y las métricas dejan de ser comparables.

También hay riesgo de fuga de información (data leakage): que el modelo vea, directa o indirectamente, datos que no debería. Esto puede pasar si se usan columnas que ya contienen el resultado (como los puntajes), si un mismo estudiante queda en dos conjuntos distintos o si el preprocesamiento se ajusta con todos los datos antes de separar.

## Alternativas

| Alternativa | Ventajas | Desventajas |
|---|---|---|
| 70/15/15 estratificado | Mantiene la proporción de clases en los tres conjuntos. Deja un conjunto de validación para ajustar y uno de prueba que se usa una sola vez. Es rápido y fácil de reproducir. | Entrena con menos datos que otras opciones. El resultado depende de una sola partición. |
| 80/20 simple sin validación | Más datos para entrenar. Es muy sencillo. | No hay conjunto para ajustar el modelo, así que se tendría que ajustar con el de prueba y la evaluación dejaría de ser honesta. Sin estratificar, la proporción de clases puede variar. |
| Validación cruzada k-fold | Usa todos los datos para entrenar y evaluar. Da una estimación más estable. | Cuesta más tiempo de cómputo. Sigue necesitando un conjunto de prueba aparte. Es más complejo de reproducir y explicar. |
| Separación temporal por periodo | Simula mejor el uso real (entrenar con el pasado y predecir el futuro). | Nuestros datos son de un solo periodo (20224), así que no se puede aplicar. |

## Criterios

- **Evaluación honesta:** medir el modelo con datos que nunca vio.
- **Proporción de clases estable:** que train, val y test tengan casi el mismo porcentaje de clase 1.
- **Reproducibilidad:** que cualquiera obtenga la misma partición.
- **Tiempo de cómputo:** que el proceso sea razonable para el equipo.

## Decisión

Separar los datos en 70 % entrenamiento, 15 % validación y 15 % prueba, de forma estratificada por el target y con `random_state=42`. El preprocesamiento va dentro de un `Pipeline` que se ajusta solo con los datos de entrenamiento.

## Consecuencias

**Positivas**
- Los tres conjuntos mantienen la misma proporción de clase 1, así que las métricas se pueden comparar entre ellos.
- El conjunto de prueba queda intacto hasta la evaluación final.
- La partición se puede repetir exactamente gracias a `random_state=42`.

**Negativas**
- El modelo entrena con 70 % de los datos y no con todos.
- El resultado depende de una sola partición, y otra semilla podría dar métricas algo distintas.

**Tamaños reales** (76.253 estudiantes únicos, umbral del target = 234):

| Conjunto | Estudiantes | % de clase 1 |
|---|---|---|
| Train | 53.377 | 24,57 % |
| Val | 11.438 | 24,57 % |
| Test | 11.438 | 24,57 % |

## Trade-offs

Se sacrifica algo de datos de entrenamiento y la estabilidad extra que daría el k-fold, que usa todos los datos. A cambio se gana una evaluación honesta, un proceso simple y rápido, resultados reproducibles y proporciones de clase iguales en los tres conjuntos.

## Validación

- Los tests de `tests/test_data.py` comprueban la partición.
- Se verifica que no haya estudiantes repetidos entre train, val y test (0 duplicados de `estu_consecutivo` tras la limpieza).
- Se confirma que el porcentaje de clase 1 sea casi igual en los tres conjuntos (24,57 % en cada uno).

## Riesgo de fuga y mitigación

| Riesgo | Mitigación |
|---|---|
| Usar columnas que ya contienen el resultado | Excluir las columnas `punt_*`, `desemp_*` y `percentil_*` de las variables de entrada. `punt_global` se usa solo para construir el target. |
| Un mismo estudiante en dos conjuntos | Quitar duplicados por `estu_consecutivo` antes de separar. |
| Preprocesamiento ajustado con datos que el modelo no debería ver | Ajustar el preprocesamiento solo con train, dentro del `Pipeline`. |