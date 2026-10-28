# Proyecto final: Predicción de riesgo de bajo desempeño en Saber 11

> Product concept de Machine Learning — Teoría de la Computación, Universidad de La Salle (2026-2).
> Grupo 3: Camilo Rivera Quintero (`dev_crivera52`), Danielo Charry (`dev_dcharry55`), Richardo Caicedo (`dev_rcaicedo05`).

> 🚧 Documento en construcción. Cada sección indica su responsable; ver [`docs/PLAN_DE_TRABAJO.md`](docs/PLAN_DE_TRABAJO.md).

## Tabla de contenido
1. [Problema y contexto](#1-problema-y-contexto)
2. [Alcance: qué hará y qué no hará](#2-alcance-qué-hará-y-qué-no-hará)
3. [Datos](#3-datos)
4. [Arquitectura](#4-arquitectura)
5. [Decisiones de arquitectura (ADR)](#5-decisiones-de-arquitectura-adr)
6. [Modelo](#6-modelo)
7. [Calidad y evaluación](#7-calidad-y-evaluación)
8. [Análisis ético](#8-análisis-ético)
9. [Riesgos técnicos](#9-riesgos-técnicos)
10. [Cómo ejecutar](#10-cómo-ejecutar)
11. [Estructura del repositorio](#11-estructura-del-repositorio)
12. [Conclusiones y recomendaciones](#12-conclusiones-y-recomendaciones)
13. [Glosario](#13-glosario)
14. [Referencias](#14-referencias)
15. [Evidencias](#15-evidencias)

---

## 1. Problema y contexto
*Responsable: Camilo*

Las secretarías de educación y los equipos de orientación de los colegios necesitan focalizar programas de refuerzo **antes** de la prueba Saber 11. Hoy esa focalización se hace de forma reactiva, cuando ya se conocen los resultados.

Este proyecto propone un modelo de clasificación que, a partir de información de contexto disponible antes de la prueba (características del colegio y condiciones del hogar), estima el **riesgo de bajo desempeño** en Saber 11, para apoyar decisiones **agregadas** de asignación de recursos.

- **Pregunta:** ¿qué tan bien puede un modelo sencillo identificar contextos con riesgo de bajo desempeño usando solo variables previas a la prueba?
- **Usuarios (user persona):** TODO — analista de la secretaría de educación, orientador escolar.
- **Variable objetivo:** `riesgo_bajo_desempeno` (1 si `punt_global` < umbral definido en el EDA; propuesta: percentil 25).

## 2. Alcance: qué hará y qué no hará
*Responsable: Camilo*

| El sistema **SÍ** | El sistema **NO** |
|---|---|
| Descarga y almacena resultados Saber 11 del periodo y región configurados | Toma decisiones individuales sobre estudiantes (becas, admisión, sanciones) |
| Entrena y evalúa un modelo de clasificación binaria | Predice el puntaje exacto |
| Expone una API para consultar el riesgo de un perfil de contexto | Usa datos personales identificables |
| Reporta métricas globales y por grupo poblacional | Usa los puntajes de la prueba como variables de entrada |

TODO: confirmar periodo y región tras el EDA.

## 3. Datos
*Responsable: Danielo*

- **Fuente:** [Resultados únicos Saber 11 — datos.gov.co](https://www.datos.gov.co/Educaci-n/Resultados-nicos-Saber-11/kgxf-xxbe) (ICFES), API Socrata `kgxf-xxbe`.
- TODO: licencia, número de registros, diccionario de variables, tabla de 5 filas de ejemplo, resumen del EDA.

## 4. Arquitectura
*Responsable: Camilo*

### 4.1 Estilo arquitectónico
Arquitectura **en capas**: Datos → Procesamiento → Modelo → Servicio → Presentación. Ver [`src/saber11/`](src/saber11/).

### 4.2 Diagrama C4 — Contexto
Ver [`docs/arquitectura/c4-contexto.md`](docs/arquitectura/c4-contexto.md).

### 4.3 Diagrama C4 — Contenedores
TODO.

### 4.4 Componentes
TODO.

### 4.5 Drivers y atributos de calidad
TODO: escenarios medibles (p. ej. *p95 de `POST /predict` < 300 ms con 50 solicitudes concurrentes*) y tácticas aplicadas.

## 5. Decisiones de arquitectura (ADR)
Índice en [`docs/adr/`](docs/adr/README.md).

| ADR | Decisión | Responsable | Estado |
|---|---|---|---|
| 001 | Lenguaje, framework y estilo arquitectónico | Camilo | Pendiente |
| 002 | Selección del modelo | Richardo | Pendiente |
| 003 | Almacenamiento y despliegue | Camilo | Pendiente |
| 004 | Estrategia de separación de datos | Danielo | Pendiente |

## 6. Modelo
*Responsable: Richardo*

TODO: modelo seleccionado, justificación, hiperparámetros, entrenamiento.

## 7. Calidad y evaluación
*Responsables: Richardo (métricas), Danielo (separación de datos), Camilo (criterios de aceptación)*

- **Estrategia de separación:** TODO (ver ADR-004).
- **Modelo de referencia (baseline):** TODO.
- **Tabla de métricas:** TODO (Accuracy, Precision, Recall, F1, ROC-AUC vs baseline).
- **Matriz de confusión** e interpretación de VP, FP, VN, FN: TODO.
- **Criterios de aceptación del software:** TODO.

## 8. Análisis ético
*Responsable: Richardo*

TODO: resumen; análisis completo en `docs/analisis_etico.md`.

## 9. Riesgos técnicos
*Responsables: todos*

| # | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| R1 | Fuga de información (usar `punt_*` como entrada) | TODO | TODO |
| R2 | Desbalance de clases | TODO | TODO |
| R3 | Sesgo socioeconómico / discriminación por variables *proxy* | TODO | TODO |
| R4 | Sobreajuste del árbol de decisión | TODO | TODO |
| R5 | Volumen de datos y límites de la API | TODO | TODO |

## 10. Cómo ejecutar
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# TODO: comandos de ingesta, entrenamiento, evaluación y API
pytest
```

## 11. Estructura del repositorio
```
├── config/            # Parámetros (periodo, región, umbral, semillas)
├── data/              # raw/ y processed/ (no versionados)
├── docs/
│   ├── adr/           # Architecture Decision Records
│   ├── arquitectura/  # Diagramas C4
│   └── evidencias/    # Capturas y evidencias.pdf
├── models/            # Artefactos entrenados (.joblib)
├── notebooks/         # EDA y experimentos
├── reports/           # Métricas y figuras
├── src/saber11/
│   ├── data/          # Capa de datos: ingesta y almacenamiento
│   ├── features/      # Capa de procesamiento: limpieza y features
│   ├── models/        # Capa de modelo: entrenamiento y evaluación
│   └── api/           # Capa de servicio: FastAPI
└── tests/             # Set de pruebas
```

## 12. Conclusiones y recomendaciones
TODO.

## 13. Glosario
| Término | Definición |
|---|---|
| ADR | *Architecture Decision Record*: registro de una decisión de arquitectura, su contexto y consecuencias. |
| C4 | Modelo para describir arquitectura en cuatro niveles: contexto, contenedores, componentes y código. |
| TODO | — |

## 14. Referencias
- ICFES. *Resultados únicos Saber 11*. datos.gov.co. https://www.datos.gov.co/Educaci-n/Resultados-nicos-Saber-11/kgxf-xxbe
- Brown, S. *The C4 model for visualising software architecture*. https://c4model.com
- Nygard, M. *Documenting Architecture Decisions*. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- TODO: scikit-learn, FastAPI, referencias de ética/equidad.

## 15. Evidencias
Capturas de cada etapa del workflow de ML consolidadas en [`docs/evidencias/evidencias.pdf`](docs/evidencias/).
