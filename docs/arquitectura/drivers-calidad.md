# Drivers arquitectónicos, atributos de calidad y tácticas

Los **drivers** son los requisitos y restricciones que condicionan la arquitectura. Cada atributo de calidad se expresa como un **escenario medible**, y cada escenario se atiende con una o más **tácticas** concretas.

## 1. Restricciones

| Id | Restricción | Origen | Impacto en la arquitectura |
|---|---|---|---|
| RS1 | Solo herramientas **open source** | Lineamientos del curso | Python, scikit-learn, FastAPI, SQLite ([ADR-001](../adr/0001-lenguaje-framework-estilo.md), [ADR-003](../adr/0003-almacenamiento-despliegue.md)) |
| RS2 | **Sin AWS ni servicios de pago**; el entrenamiento y los datos corren en local | Lineamientos del curso | Base de datos embebida; API publicada en el plan gratuito de Render ([ADR-003](../adr/0003-almacenamiento-despliegue.md)) |
| RS3 | Datos **tabulares** de una API pública con límites de velocidad | Fuente datos.gov.co | Ingesta paginada con reintentos y copia local |
| RS4 | Modelo **básico** de ML (regresión logística, árbol, KNN…) | Rúbrica | Modelos de scikit-learn, sin redes neuronales |
| RS5 | **6 días** y 3 integrantes en paralelo | Calendario | Capas con contratos explícitos, una capa por integrante |
| RS6 | Solo variables **previas a la prueba** | Validez del modelo | Prohibición de `punt_*`, `desemp_*` y `percentil_*` como entrada |

## 2. Escenarios de calidad

Formato: *fuente → estímulo → entorno → respuesta → **medida***.

| Id | Atributo | Escenario | Medida de aceptación | Cómo se verifica |
|---|---|---|---|---|
| QA1 | **Rendimiento** | Un usuario envía `POST /predict` con un perfil válido, con la API en ejecución local y 10 clientes concurrentes | **p95 < 300 ms** en 500 solicitudes | `scripts/medir_latencia.py` → `reports/latencia.json` |
| QA2 | **Confiabilidad** | Un cliente envía un JSON incompleto o con una categoría inválida | Respuesta **422** con el campo que falla; **0 %** de respuestas 500 | Tests de la API con entradas inválidas |
| QA3 | **Integridad de datos (idempotencia)** | El equipo ejecuta la ingesta y la carga a SQLite dos veces seguidas | El número de filas de `resultados` es **idéntico** en ambas ejecuciones; 0 duplicados de `estu_consecutivo` tras `clean()` | Test de datos + captura de las dos ejecuciones |
| QA4 | **Disponibilidad de la fuente** | La API de datos.gov.co tarda o falla en una página | Hasta **3 reintentos** por página con timeout de 120 s; si persiste, error claro sin corromper el CSV existente | Revisión de `ingest.py` + log de ejecución |
| QA5 | **Reproducibilidad** | Otro integrante clona el repo y ejecuta el pipeline completo | Las métricas de test coinciden **exactamente** (misma semilla y mismos datos) | Comparar `reports/metrics.json` entre dos ejecuciones |
| QA6 | **Validez del modelo** | Se entrena con variables que contienen la respuesta (fuga de información) | El pipeline **falla** con `ValueError` si alguna variable de entrada empieza por `punt_`, `desemp_` o `percentil_` | Test automático de fuga en `tests/test_data.py` |
| QA7 | **Equidad** | Se evalúa el modelo en test por género, estrato, naturaleza del colegio y área | Se reporta el recall por grupo; una **brecha > 0,10** entre grupos se marca como hallazgo y se discute en el análisis ético | `reports/equidad.md` |
| QA8 | **Mantenibilidad** | El equipo quiere probar un modelo nuevo (por ejemplo KNN) | El cambio solo toca `src/saber11/models/train.py`; la API **no cambia** porque consume el `Pipeline` serializado | Revisión del diff + contratos |
| QA9 | **Privacidad** | Alguien intenta usar identificadores para entrenar o consultar | Ningún identificador (`estu_consecutivo`, códigos DANE/ICFES, nombres de colegio) llega al modelo ni a la API | Lista `FEATURES` + test |

## 3. Tácticas

| Táctica | Atributo(s) | Qué hace | Dónde se implementa |
|---|---|---|---|
| **Cargar el modelo una sola vez** al iniciar la API | Rendimiento (QA1) | Evita leer el `.joblib` del disco en cada petición | `src/saber11/api/main.py` (evento de inicio) |
| **Separar entrenamiento y predicción** | Rendimiento, mantenibilidad (QA1, QA8) | La API solo usa artefactos; nunca reentrena ni lee la base de datos | Contenedores separados ([C4 contenedores](c4-contenedores.md)) |
| **Validación de entrada con Pydantic** | Confiabilidad (QA2) | Rechaza peticiones mal formadas antes de llegar al modelo | Esquemas de la API |
| **Ingesta idempotente** (no redescargar si existe; `replace` en la tabla) | Integridad (QA3) | Re-ejecutar deja el mismo estado final | `ingest.py`, `repository.py` |
| **Reintentos con espera y timeout** | Disponibilidad (QA4) | Tolera fallos transitorios de la API externa | `ingest.py` |
| **Copia local de los datos** (caché del dataset) | Disponibilidad, rendimiento (QA4) | El entrenamiento no depende de que datos.gov.co esté disponible | `data/raw/`, `data/saber11.db` |
| **Semilla fija y parámetros en `config.yaml`** | Reproducibilidad (QA5) | Mismo split y mismos resultados en cualquier equipo | `config/config.yaml`, `split()` |
| **Preprocesamiento dentro del `Pipeline`**, ajustado solo con train | Validez (QA6) | Evita fuga de estadísticas de validación y test | `preprocessing.py`, `train.py` |
| **Lista blanca de variables** + verificación de prefijos prohibidos | Validez, privacidad (QA6, QA9) | Solo entran variables previas a la prueba y no identificadoras | `FEATURES`, `LEAKAGE_PREFIXES` |
| **Métricas por grupo sensible** | Equidad (QA7) | Hace visibles las diferencias de desempeño entre grupos | `fairness.py` |
| **Calibración de Platt** de la probabilidad, sin cambiar la decisión | Validez, transparencia (QA6, QA7) | Evita informar un riesgo inflado por `class_weight="balanced"` | `calibracion.py`, `train.py`, `model_service.py` |
| **Pruebas automáticas en cada PR** y **versiones fijas** | Mantenibilidad, reproducibilidad (QA5, QA8) | Detecta regresiones antes del merge y mantiene el mismo entorno | `.github/workflows/tests.yml`, `requirements.txt` |
| **Contratos entre capas** | Mantenibilidad (QA8) | Cada capa cambia sin romper las demás mientras respete su interfaz | [`contratos.md`](contratos.md) |

## 4. Proyección a un entorno real

El *product concept* no implementa estos escenarios, pero la arquitectura los permite:

| Escenario real | Táctica prevista |
|---|---|
| 8.000 orientadores consultando al mismo tiempo durante la planeación anual | Varias réplicas de la API (no guarda estado) detrás de un balanceador; caché (Redis) para perfiles repetidos |
| Reentrenamiento con millones de filas de varios periodos | PostgreSQL y procesamiento por lotes; entrenamiento programado fuera de la API |
| Acceso solo para personal autorizado de las secretarías | Autenticación con JWT y registro de auditoría de las consultas |
| Deriva de datos entre periodos | Monitoreo de métricas y equidad por periodo, con alerta si el recall cae más de 0,05 |
