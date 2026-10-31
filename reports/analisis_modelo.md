# Validación cruzada e importancia de variables

## Validación cruzada de 5 particiones sobre entrenamiento y validación

| Modelo | F1 | ROC-AUC |
|---|---|---|
| logreg | 0.5164 ± 0.0038 | 0.7575 ± 0.0034 |
| tree | 0.5055 ± 0.0037 | 0.7425 ± 0.0041 |

## Importancia por permutación en test

Las variables están correlacionadas: una importancia baja no significa que la variable no se relacione con el riesgo.

| Variable | Caída del ROC-AUC | Desviación |
|---|---|---|
| `cole_jornada` | 0.0837 | 0.0031 |
| `edad` | 0.0229 | 0.0019 |
| `fami_educacionmadre` | 0.0141 | 0.0023 |
| `fami_educacionpadre` | 0.0122 | 0.0025 |
| `estu_genero` | 0.0061 | 0.0008 |
| `fami_tienecomputador` | 0.0035 | 0.0006 |
| `cole_genero` | 0.0027 | 0.0005 |
| `fami_cuartoshogar` | 0.0022 | 0.0007 |
| `fami_estratovivienda` | 0.0012 | 0.0004 |
| `fami_personashogar` | 0.0011 | 0.0005 |
| `fami_tieneinternet` | 0.0005 | 0.0002 |
| `cole_caracter` | 0.0004 | 0.0003 |
| `fami_tienelavadora` | 0.0004 | 0.0002 |
| `fami_tieneautomovil` | 0.0001 | 0.0001 |
| `cole_bilingue` | 0.0001 | 0.0001 |
| `cole_area_ubicacion` | 0.0001 | 0.0001 |
| `cole_naturaleza` | -0.0000 | 0.0000 |
| `cole_calendario` | -0.0000 | 0.0001 |
