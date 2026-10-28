# Plan de trabajo — Proyecto final: Predicción de riesgo de bajo desempeño en Saber 11

**Equipo (Grupo 3)**

| Integrante | Rama individual | Rol principal (capa) |
|---|---|---|
| Camilo Rivera Quintero | `dev_crivera52` | Arquitectura, capa de servicio (API) e integración |
| Danielo Charry | `dev_dcharry55` | Capa de datos: ingesta, almacenamiento, EDA y preprocesamiento |
| Richardo Caicedo | `dev_rcaicedo05` | Capa de modelo: entrenamiento, evaluación, equidad y análisis ético |

**Entrega:** martes 3 de noviembre de 2026, 11:00 p. m. (Moodle).
**Rama que revisa el profesor:** `develop`. URL a enviar: `https://github.com/contracamilo/proyectoFinal_saber11/tree/develop`

---

## 1. Qué pide el profesor (síntesis de rúbrica + clase)

### 1.1 Requisitos formales (si fallan, el resto no se revisa)
- [ ] Repositorio llamado `proyectoFinal_<nombre>` → `proyectoFinal_saber11`.
- [ ] Título del proyecto en el README empieza por **"Proyecto final:"**.
- [ ] Cada integrante trabaja **ÚNICAMENTE** en su rama `dev_<usuarioCorreo>` con **varios commits con valor** (no uno solo).
- [ ] Todo consolidado en la rama **`develop`** (merge que conserve los commits de cada autor).
- [ ] Profesor invitado al repo con permisos suficientes (rol *Admin* o *Maintain*).
- [ ] Equipo notificado al profesor por correo (Grupo 3: Camilo, Danielo, Richardo).

### 1.2 Contenido obligatorio del `README.md`
- [ ] Problema, contexto, datos, cómo funciona la solución y cómo se demuestra que los resultados son válidos.
- [ ] **Alcance:** qué hará y qué NO hará el sistema.
- [ ] **Diagrama C4 de contexto** (usuarios, sistema, fuentes externas de datos). En clase pidió también el de **contenedores**.
- [ ] **Estilo arquitectónico** (capas) y diagrama de componentes.
- [ ] **ADR (mínimo 3):** enfoque de implementación (lenguaje + framework + BD), selección de modelo, almacenamiento/despliegue. Cada uno con estado, fecha, contexto, decisión, consecuencias, *trade-offs*, alternativas y criterios/métricas.
- [ ] **Calidad y evaluación:** métricas de ML, estrategia de separación de datos, comparación con **modelo de referencia (baseline)** y **criterios de aceptación del software**.
- [ ] **Drivers / atributos de calidad medibles** (p. ej. "p95 de /predict < 300 ms").
- [ ] **Riesgos técnicos (3 a 5)** con impacto y mitigación: datos insuficientes, fuga de información, sobreajuste, sesgos, cómputo.
- [ ] **Glosario y referencias** (dataset, herramientas, decisiones).

### 1.3 Contenido del análisis (puede ir en el PDF de evidencias)
- [ ] Modelo sencillo + por qué se eligió.
- [ ] Descripción del dataset, tabla pequeña de ejemplo, variables y objetivo.
- [ ] Tabla de métricas (Accuracy, Precision, Recall, F1) con interpretación sencilla de cada una.
- [ ] Matriz de confusión + explicación de VP, FP, VN, FN en el contexto del problema.
- [ ] Análisis ético: sesgos, equidad, privacidad, impacto social, uso responsable, justicia y transparencia.
- [ ] Conclusiones técnicas y recomendaciones de mejora.
- [ ] **Evidencias** de cada etapa del workflow ML (capturas de ejecución, commits) consolidadas en `docs/evidencias/evidencias.pdf`.
- [ ] **Set de pruebas** (`tests/`) que evidencie el funcionamiento.

### 1.4 Rúbrica (5 puntos)
| Criterio | Pts | Cómo lo cubrimos |
|---|---|---|
| Modelo adecuado, bien descrito, propósito y tipo de datos | 1 | README §Problema/Datos + ADR-002 |
| Métricas aplicadas y explicadas | 1 *(2 en el detalle de Moodle)* | `reports/metricas.md`, matriz de confusión, comparación con baseline |
| Sesgos, riesgos, limitaciones y ética | 1 | `docs/analisis_etico.md` + métricas por grupo + riesgos en README |
| Arquitectura clara + implementación funcional por etapas del workflow | 2 | C4, capas en `src/saber11/`, API funcionando, evidencias |
| Organización del repo / documento, tablas, conclusiones | 1 | Estructura, README, PDF, ramas correctas |

> Nota: la rúbrica PDF y la tabla de Moodle reparten los puntos distinto; cubrimos ambas versiones.

---

## 2. Definición del proyecto (propuesta a validar el día 1)

- **Problema:** las secretarías de educación necesitan focalizar programas de refuerzo antes de la prueba Saber 11, pero no tienen una forma temprana de identificar en qué contextos (colegio + condiciones del hogar) se concentra el riesgo de bajo desempeño.
- **Objetivo del modelo:** clasificación binaria → `riesgo_bajo_desempeno = 1` si `punt_global` está por debajo del umbral definido en el EDA (propuesta: percentil 25 del periodo).
- **Datos:** *Resultados únicos Saber 11* — datos.gov.co, recurso `kgxf-xxbe` (API Socrata, CSV/JSON).
- **Alcance (propuesta):** periodo `20224` (calendario A), estudiantes de colegios ubicados en Bogotá (~152.000 registros). Configurable en `config/config.yaml`.
- **Fuera de alcance:** decisiones individuales sobre estudiantes (admisión, becas, sanciones); predicción del puntaje exacto; otros periodos o departamentos; datos personales identificables.
- **Variables de entrada:** solo contexto previo a la prueba (`cole_*`, `fami_*`, `estu_genero`, edad). **Prohibido** usar `punt_*` y `desemp_*` como entrada (fuga de información).
- **Modelos:** baseline `DummyClassifier` → **Regresión Logística** (principal, interpretable) vs **Árbol de Decisión**.
- **Stack (open source):** Python 3.11+, pandas, scikit-learn, SQLite, FastAPI, pytest, matplotlib/seaborn, Jupyter.
- **Arquitectura:** en capas → Datos → Procesamiento → Modelo → Servicio (API) → Presentación (Swagger UI / notebook).

---

## 3. Reparto de trabajo

Cada tarea = varios commits pequeños en la rama propia + Pull Request hacia `develop`.

### Camilo — `dev_crivera52` (arquitectura, servicio, integración)
1. Estructura del repositorio, `README` base, plantilla ADR, guía de contribución. *(hecho en el kickoff)*
2. Diagrama C4 de **contexto** y de **contenedores** (Mermaid) + diagrama de componentes por capas.
3. **ADR-001** Lenguaje, framework y estilo (Python + FastAPI + capas).
4. **ADR-003** Almacenamiento y despliegue (SQLite + artefacto `joblib` + ejecución local con `uvicorn`).
5. Drivers arquitectónicos y atributos de calidad medibles; tácticas (validación de entrada con Pydantic, carga única del modelo en memoria, ingesta idempotente).
6. Capa de servicio `src/saber11/api/`: `GET /health`, `POST /predict`, `GET /metrics`.
7. Tests de la API (`tests/test_api.py`) y medición de latencia p95.
8. Revisión de PRs, merge a `develop`, README final y checklist de entrega.

### Danielo — `dev_dcharry55` (capa de datos)
1. `src/saber11/data/ingest.py`: descarga paginada desde la API de datos.gov.co con filtros del `config.yaml` → `data/raw/`. Idempotente (no duplica si se re-ejecuta).
2. `src/saber11/data/repository.py`: carga a SQLite (`data/saber11.db`).
3. `notebooks/01_eda.ipynb`: tamaño, tipos, nulos, distribución de `punt_global`, desbalance de clases, variables por estrato/naturaleza/área. Gráficos en `reports/figures/`.
4. Sección **Datos** del README: fuente, licencia, diccionario de variables, tabla de 5 filas de ejemplo.
5. `src/saber11/features/preprocessing.py`: limpieza justificada, construcción del target, `ColumnTransformer` (one-hot / ordinal), exclusión de `punt_*`.
6. **ADR-004** Estrategia de separación de datos (70/15/15 estratificado, `random_state` fijo, preprocesamiento dentro del `Pipeline`).
7. Tests de datos (`tests/test_data.py`): esquema, sin columnas de fuga, target binario.
8. Riesgos técnicos de datos (insuficiencia, fuga, cómputo/volumen API).

### Richardo — `dev_rcaicedo05` (capa de modelo y ética)
1. `src/saber11/models/train.py`: baseline + Regresión Logística + Árbol de Decisión; guarda el mejor en `models/model.joblib`.
2. `src/saber11/models/evaluate.py`: Accuracy, Precision, Recall, F1, ROC-AUC; matriz de confusión (figura); comparación con baseline → `reports/metricas.md` y `reports/metrics.json`.
3. **ADR-002** Selección del modelo (alternativas, métricas, por qué se priorizó *recall* de la clase en riesgo).
4. Métricas de equidad por grupo (estrato, género, oficial/no oficial, urbano/rural): recall y tasa de falsos positivos por grupo.
5. `docs/analisis_etico.md`: sesgos, equidad, privacidad, impacto social, justicia y transparencia, uso responsable.
6. Explicación de VP/FP/VN/FN en el contexto Saber 11; interpretación de cada métrica.
7. Tests del modelo (`tests/test_model.py`): el modelo supera al baseline en F1, predice 0/1.
8. Conclusiones técnicas y recomendaciones; riesgos de sobreajuste y sesgo.

### Todos
- Glosario y referencias (cada uno aporta los términos de su capa).
- Capturas de pantalla de su parte → `docs/evidencias/capturas/` (se consolidan en `evidencias.pdf`).
- Revisar al menos un PR de otro integrante.

---

## 4. Cronograma (6 días)

| Fecha | Camilo | Danielo | Richardo | Hito |
|---|---|---|---|---|
| **Mié 28 oct** | Repo, ramas, plan, invitaciones | Clonar, crear entorno, explorar API | Clonar, crear entorno, revisar dataset | Kickoff: validar tema, alcance y umbral |
| **Jue 29 oct** | C4 contexto + contenedores, ADR-001 | `ingest.py` + SQLite | Esqueleto `train.py` con datos de muestra | Datos descargados |
| **Vie 30 oct** | ADR-003, drivers y tácticas | EDA + sección Datos | Baseline + Regresión Logística | **PR #1 de cada uno a `develop`** |
| **Sáb 31 oct** | API `/health` `/predict` | `preprocessing.py` + ADR-004 | Árbol de Decisión, `evaluate.py` | Pipeline completo extremo a extremo |
| **Dom 1 nov** | Integrar modelo en API, tests API | Tests de datos, riesgos de datos | Métricas por grupo, ADR-002 | **PR #2 de cada uno** |
| **Lun 2 nov** | README final, diagrama componentes | Capturas + glosario | Análisis ético, conclusiones, tests modelo | Evidencias PDF armado |
| **Mar 3 nov** | Checklist final, merge, enviar URL antes de **8:00 p. m.** | Revisión cruzada | Revisión cruzada | **Congelar `develop` a las 6:00 p. m.** |

Reunión diaria corta (15 min) por WhatsApp/Meet: qué hice, qué haré, bloqueos.

---

## 5. Flujo de Git (obligatorio)

Ver [`CONTRIBUTING.md`](../CONTRIBUTING.md). Resumen:

```bash
git clone https://github.com/contracamilo/proyectoFinal_saber11.git
cd proyectoFinal_saber11
git switch dev_<tuUsuario>          # dev_crivera52 | dev_dcharry55 | dev_rcaicedo05
git pull origin develop             # traer lo último antes de empezar
# ...trabajar, commits pequeños...
git push origin dev_<tuUsuario>
# Abrir PR: dev_<tuUsuario> → develop  (usar "Create a merge commit", NUNCA "Squash")
```

- Nunca hacer commit directo en `develop` ni en `main`.
- Commits pequeños y descriptivos (`feat(data): descarga paginada desde datos.gov.co`). Meta: **≥ 8 commits por persona**.
- El correo de `git config user.email` debe estar asociado a tu cuenta de GitHub para que los commits cuenten como tuyos.

---

## 6. Checklist final de entrega (martes 3 nov)

- [ ] `develop` contiene los commits de los tres integrantes (`git log develop --format='%an' | sort | uniq -c`).
- [ ] Existen las ramas `dev_crivera52`, `dev_dcharry55`, `dev_rcaicedo05` en GitHub.
- [ ] README completo (todas las secciones de §1.2) y renderiza bien los diagramas.
- [ ] ≥ 3 ADR en `docs/adr/`.
- [ ] `docs/evidencias/evidencias.pdf` con capturas de cada etapa.
- [ ] `pytest` pasa; instrucciones de ejecución probadas en una máquina limpia.
- [ ] Profesor con acceso al repo.
- [ ] URL enviada en Moodle: `https://github.com/contracamilo/proyectoFinal_saber11/tree/develop`.
