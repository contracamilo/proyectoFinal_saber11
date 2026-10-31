# Equidad por grupo (conjunto de test)

Una brecha de recall mayor a 0.10 se marca como hallazgo (QA7). La brecha solo compara grupos con al menos 30 personas.

## Comparación con un modelo sin variables sensibles

| modelo        |     f1 |   brecha_estu_genero |   brecha_fami_estratovivienda |   brecha_cole_naturaleza |   brecha_cole_area_ubicacion |
|:--------------|-------:|---------------------:|------------------------------:|-------------------------:|-----------------------------:|
| completo      | 0.5126 |               0.1359 |                        0.4141 |                   0.2393 |                       0.1380 |
| sin_sensibles | 0.5129 |               0.0158 |                        0.4433 |                   0.2487 |                       0.0421 |

## estu_genero

Brecha de recall: 0.1359. **Hallazgo**.

| grupo   |    n |   tasa_real |   tasa_predicha |   recall |   precision |   tasa_falsos_positivos |
|:--------|-----:|------------:|----------------:|---------:|------------:|------------------------:|
| F       | 6002 |      0.2736 |          0.5100 |   0.7832 |      0.4201 |                  0.4071 |
| M       | 5436 |      0.2149 |          0.3858 |   0.6473 |      0.3605 |                  0.3142 |

## fami_estratovivienda

Brecha de recall: 0.4141. **Hallazgo**.

| grupo       |    n |   tasa_real |   tasa_predicha |   recall |   precision |   tasa_falsos_positivos |
|:------------|-----:|------------:|----------------:|---------:|------------:|------------------------:|
| Estrato 1   | 1121 |      0.3550 |          0.7707 |   0.8794 |      0.4051 |                  0.7109 |
| Estrato 2   | 4706 |      0.2688 |          0.5480 |   0.7431 |      0.3645 |                  0.4763 |
| Estrato 3   | 3951 |      0.1875 |          0.2898 |   0.6032 |      0.3904 |                  0.2174 |
| Estrato 4   |  835 |      0.1413 |          0.1281 |   0.5424 |      0.5981 |                  0.0600 |
| Estrato 5   |  163 |      0.1656 |          0.2270 |   0.6296 |      0.4595 |                  0.1471 |
| Estrato 6   |   56 |      0.1786 |          0.3214 |   0.8000 |      0.4444 |                  0.2174 |
| Sin Estrato |   91 |      0.5055 |          0.8022 |   0.9565 |      0.6027 |                  0.6444 |
| Sin dato    |  515 |      0.3981 |          0.6505 |   0.8390 |      0.5134 |                  0.5258 |

## cole_naturaleza

Brecha de recall: 0.2393. **Hallazgo**.

| grupo      |    n |   tasa_real |   tasa_predicha |   recall |   precision |   tasa_falsos_positivos |
|:-----------|-----:|------------:|----------------:|---------:|------------:|------------------------:|
| NO OFICIAL | 4803 |      0.1553 |          0.1745 |   0.5509 |      0.4905 |                  0.1053 |
| OFICIAL    | 6635 |      0.3111 |          0.6511 |   0.7902 |      0.3775 |                  0.5883 |

## cole_area_ubicacion

Brecha de recall: 0.1380. **Hallazgo**.

| grupo   |     n |   tasa_real |   tasa_predicha |   recall |   precision |   tasa_falsos_positivos |
|:--------|------:|------------:|----------------:|---------:|------------:|------------------------:|
| RURAL   |    85 |      0.2588 |          0.5529 |   0.8636 |      0.4043 |                  0.4444 |
| URBANO  | 11353 |      0.2456 |          0.4502 |   0.7256 |      0.3958 |                  0.3605 |
