# Métricas en test

Modelo seleccionado: **logreg**

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| baseline | 0.7543 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| logreg | 0.6604 | 0.3959 | 0.7267 | 0.5126 | 0.7539 |
| tree | 0.6299 | 0.3736 | 0.7480 | 0.4983 | 0.7420 |

## Matriz de confusión

| | Predicho 0 | Predicho 1 |
|---|---|---|
| Real 0 | VN = 5512 | FP = 3116 |
| Real 1 | FN = 768 | VP = 2042 |

## Calibración

| Medida | Puntaje del modelo | Probabilidad calibrada |
|---|---|---|
| Media (tasa real: 0.2457) | 0.4499 | 0.2458 |
| Brier (tasa base: 0.1853) | 0.2035 | 0.1574 |

El modelo emite una alerta desde una probabilidad calibrada de 0.2471.
