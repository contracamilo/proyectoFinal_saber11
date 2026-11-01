# C4 — Nivel 2: Diagrama de contenedores

Abre la caja del sistema y muestra sus piezas ejecutables o de almacenamiento (contenedores), la tecnología de cada una y cómo se comunican.

```mermaid
flowchart LR
    usuario(["👤 Analista / Orientador"])
    equipo(["👤 Equipo de ciencia de datos"])
    datosgov[("<b>datos.gov.co</b><br/>[Sistema externo]<br/>API Socrata")]

    subgraph sistema["Sistema de riesgo Saber 11"]
        direction LR
        ingesta["<b>Ingesta y carga</b><br/>[Python, requests, sqlite3]<br/>Descarga paginada e idempotente,<br/>guarda el CSV y carga SQLite"]
        db[("<b>Base de datos</b><br/>[SQLite]<br/>Tabla resultados")]
        pipeline["<b>Pipeline de entrenamiento</b><br/>[Python, pandas, scikit-learn]<br/>Preprocesa, entrena, evalúa<br/>y mide equidad"]
        artefactos[("<b>Artefactos</b><br/>[Archivos joblib / JSON / MD]<br/>model.joblib, metrics.json,<br/>reportes y figuras")]
        api["<b>API de predicción</b><br/>[Python, FastAPI, uvicorn]<br/>/health, /predict, /metrics"]
        docs["<b>Documentación interactiva</b><br/>[Swagger UI de FastAPI]"]
    end

    equipo -- "Ejecuta [CLI]" --> ingesta
    equipo -- "Ejecuta [CLI]" --> pipeline
    ingesta -- "GET paginado [HTTPS/JSON]" --> datosgov
    ingesta -- "Carga el CSV en la tabla [SQL]" --> db
    pipeline -- "Lee datos [SQL]" --> db
    pipeline -- "Escribe modelo y métricas [archivos]" --> artefactos
    api -- "Carga al iniciar [joblib/JSON]" --> artefactos
    usuario -- "Consulta [HTTPS/JSON]" --> api
    usuario -- "Prueba la API [navegador]" --> docs
    docs -- "Llama [HTTP/JSON]" --> api

    classDef persona fill:#08427b,color:#fff,stroke:#052e56
    classDef contenedor fill:#438dd5,color:#fff,stroke:#2e6295
    classDef almacen fill:#438dd5,color:#fff,stroke:#2e6295
    classDef externo fill:#999999,color:#fff,stroke:#6b6b6b
    class usuario,equipo persona
    class ingesta,pipeline,api,docs contenedor
    class db,artefactos almacen
    class datosgov externo
```

| Contenedor | Tecnología | Responsabilidad | Capa | Código |
|---|---|---|---|---|
| Ingesta y carga | Python, requests, sqlite3 | Descarga los resultados del periodo y la región configurados a un CSV y los carga en SQLite. Re-ejecutarla no duplica datos. | Datos | `src/saber11/data/ingest.py`, `src/saber11/data/repository.py` |
| Base de datos | SQLite | Guarda los datos crudos en la tabla `resultados`. | Datos | `data/saber11.db` |
| Pipeline de entrenamiento | Python, pandas, scikit-learn | Limpia, construye el target, separa los datos, entrena, evalúa y calcula métricas por grupo. | Procesamiento y modelo | `src/saber11/features/`, `src/saber11/models/` |
| Artefactos | joblib, JSON, Markdown, PNG | Modelo entrenado, métricas y reportes. Son el contrato entre el entrenamiento y la API. | Modelo | `models/`, `reports/` |
| API de predicción | Python, FastAPI, uvicorn (publicada en Render) | Valida la entrada, predice con el modelo cargado en memoria y expone las métricas. | Servicio | `src/saber11/api/main.py` |
| Documentación interactiva | Swagger UI (incluida en FastAPI) | Permite probar la API desde el navegador sin escribir código. | Presentación | `/docs` |

**Decisiones relacionadas:** [ADR-001](../adr/0001-lenguaje-framework-estilo.md) (Python, FastAPI y capas) y ADR-003 (almacenamiento y despliegue).
