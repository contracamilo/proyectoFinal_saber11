# ADR-001: Lenguaje, framework y estilo arquitectónico

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Autor(es):** Camilo Rivera Quintero

## Contexto
Hay que construir un *product concept* de Machine Learning que descargue datos abiertos de Saber 11, entrene y evalúe un clasificador sencillo y exponga sus predicciones a otros sistemas. Estos son los drivers que condicionan la decisión:

- **Restricción del curso:** solo herramientas **open source**. No se usan los servicios de AWS de actividades anteriores.
- **Tipo de datos:** datos tabulares estructurados (~76.000 estudiantes únicos y ~20 variables categóricas) que vienen de una API REST con respuestas JSON.
- **Tiempo:** seis días de trabajo, con tres integrantes en paralelo.
- **Mantenibilidad:** cada integrante es dueño de una etapa del workflow de ML, y el profesor debe poder ver qué hizo cada uno. El código no puede quedar en un solo archivo.
- **Rendimiento esperado:** `POST /predict` con p95 < 300 ms en local.
- **Integración:** la solución debe poder consultarse desde fuera (otro sistema o una interfaz), no solo desde un notebook.

## Alternativas consideradas

**Lenguaje y ecosistema**

| Alternativa | Ventajas | Desventajas |
|---|---|---|
| **Python** (pandas, scikit-learn) | Ecosistema de ML más completo y documentado; scikit-learn trae los modelos, el preprocesamiento y las métricas que pide la actividad; notebooks para el EDA | Más lento que los lenguajes compilados; tipado dinámico |
| Java (Weka / Tribuo + Spring Boot) | Tipado fuerte, buen rendimiento, robusto en entornos empresariales | Ecosistema de ML mucho más reducido; más código repetitivo; no hay un equivalente a los notebooks para el EDA |
| JavaScript / TypeScript (TensorFlow.js + Express) | Un solo lenguaje para el backend y una futura interfaz web | Librerías de ML clásico inmaduras; pocas utilidades de análisis tabular |

**Framework para exponer el modelo**

| Alternativa | Ventajas | Desventajas |
|---|---|---|
| **FastAPI** | Valida la entrada automáticamente con Pydantic; genera documentación Swagger sin código adicional; buen rendimiento; poco código | Más reciente que Flask; su soporte asíncrono no se aprovecha en este caso |
| Flask | Simple y muy conocido | La validación y la documentación se escriben a mano |
| Django + DRF | Completo (ORM, autenticación, panel de administración) | Demasiado pesado para un servicio con 3 endpoints |
| Solo notebook, sin API | Cero infraestructura | No se puede integrar con otros sistemas; no demuestra arquitectura |

**Estilo arquitectónico**

| Alternativa | Ventajas | Desventajas |
|---|---|---|
| **Capas** (datos → procesamiento → modelo → servicio → presentación) | Cada capa tiene una sola responsabilidad; coincide con las etapas del workflow de ML; permite repartir el trabajo por capa | Más archivos e interfaces que un script único |
| Script o notebook monolítico | Rápido de empezar | Difícil de probar, mantener y repartir; el profesor lo señaló como antipatrón |
| Microservicios | Escalado y despliegue independientes | Complejidad operativa (red, contenedores, orquestación) desproporcionada para un *product concept* |

## Criterios / métricas de evaluación
| Criterio | Peso | Python + FastAPI + capas |
|---|---|---|
| Open source | Obligatorio | ✅ Python (PSF), scikit-learn (BSD), FastAPI (MIT), SQLite (dominio público) |
| Cobertura de lo que pide la actividad (modelos básicos, métricas, matriz de confusión) | Alto | ✅ Todo está en scikit-learn, sin implementar algoritmos a mano |
| Experiencia del equipo y curva de aprendizaje | Alto | ✅ Es el lenguaje con el que el equipo ha trabajado en el curso |
| Esfuerzo para exponer el modelo (validación y documentación) | Medio | ✅ Pydantic y Swagger vienen incluidos |
| Rendimiento suficiente (p95 < 300 ms) | Medio | ✅ Predecir con un modelo lineal ya cargado en memoria toma milisegundos |
| Separación de responsabilidades y trabajo en paralelo | Alto | ✅ Una capa por integrante, con [contratos](../arquitectura/contratos.md) explícitos |

## Decisión
Construir el sistema en **Python 3.11+** con **pandas y scikit-learn** para los datos y el modelo, y **FastAPI** (servido con uvicorn) para exponer las predicciones. El código se organiza en una **arquitectura en capas** dentro del paquete `src/saber11/`:

| Capa | Paquete | Depende de |
|---|---|---|
| Datos | `saber11.data` | — |
| Procesamiento | `saber11.features` | Datos |
| Modelo | `saber11.models` | Procesamiento |
| Servicio | `saber11.api` | Artefactos del modelo |
| Presentación | Swagger UI (`/docs`) | Servicio |

Regla: una capa solo usa la capa inmediatamente inferior, a través de las interfaces de `docs/arquitectura/contratos.md`.

## Consecuencias
- **Positivas:**
  - Los modelos, el preprocesamiento y las métricas salen de una librería probada, lo que reduce errores.
  - La API valida la entrada sin código adicional: una petición mal formada devuelve 422 en vez de un error del servidor.
  - El diseño (C4 y capas) se ve en la estructura de carpetas, lo que facilita revisar que lo implementado coincide con lo diseñado.
  - Cada integrante trabaja en su capa con pocos conflictos de Git.
- **Negativas / riesgos / deuda técnica:**
  - Python no es la opción más eficiente para un volumen mucho mayor (millones de predicciones por segundo). Habría que escalar horizontalmente o cambiar de tecnología en la parte crítica.
  - Las interfaces entre capas deben respetarse con disciplina; un cambio de contrato obliga a coordinar al equipo.
  - La API queda acoplada al formato del artefacto (`joblib`) y a la versión de scikit-learn con la que se entrenó.

## Trade-offs
- Se acepta **menor rendimiento bruto** (frente a Java) a cambio de **productividad y un ecosistema de ML completo**, que es lo crítico con 6 días de plazo.
- Se acepta **más estructura** (archivos, interfaces) que un notebook único, a cambio de **mantenibilidad, pruebas por capa y trazabilidad del aporte** de cada integrante.
- Se descartan los microservicios: se pierde escalado independiente a cambio de **simplicidad operativa**, adecuada para un *product concept*.

## Validación
- El pipeline completo (`ingest` → `repository` → `train` → `evaluate`) corre de principio a fin con los comandos del README.
- `pytest` verifica las interfaces de cada capa (`tests/test_data.py`, `tests/test_model.py`, `tests/test_api.py`).
- La medición de latencia de `POST /predict` (p95 < 300 ms) queda registrada en las evidencias.
- La estructura de `src/saber11/` corresponde uno a uno con el [diagrama de contenedores](../arquitectura/c4-contenedores.md).
