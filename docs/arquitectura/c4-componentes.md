# C4 — Nivel 3: Diagrama de componentes

Muestra los componentes internos de los dos contenedores con lógica propia, **Pipeline de entrenamiento** y **API de predicción**, y cómo se relacionan. Cada componente es un módulo de `src/saber11/`, y sus funciones están definidas en [`contratos.md`](contratos.md).

## 3.1 Pipeline de entrenamiento (capas de datos, procesamiento y modelo)

```mermaid
flowchart TB
    cfg["<b>Configuración</b><br/>[config.py]<br/>Lee config.yaml"]
    datosgov[("datos.gov.co<br/>[externo]")]
    db[("SQLite<br/>saber11.db")]
    art[("Artefactos<br/>model.joblib, model_meta.json")]
    rep[("Reportes<br/>metrics.json, metricas.md, equidad.md,<br/>analisis_modelo.md, figuras")]

    subgraph datos["Capa de datos — saber11.data"]
        ing["<b>Ingesta</b><br/>[ingest.py]<br/>download()"]
        repo["<b>Repositorio</b><br/>[repository.py]<br/>load_to_db(), read_raw()"]
    end

    subgraph proc["Capa de procesamiento — saber11.features"]
        clean["<b>Limpieza</b><br/>clean()"]
        target["<b>Constructor del target</b><br/>build_target()"]
        split["<b>Separador</b><br/>split()"]
        prep["<b>Preprocesador</b><br/>build_preprocessor()<br/>FEATURES, SENSITIVE"]
    end

    subgraph modelo["Capa de modelo — saber11.models"]
        train["<b>Entrenador</b><br/>[train.py]<br/>baseline, logreg, tree"]
        evalc["<b>Evaluador</b><br/>[evaluate.py]<br/>métricas + matriz de confusión"]
        fair["<b>Auditor de equidad</b><br/>[fairness.py]<br/>métricas por grupo"]
        anal["<b>Analizador</b><br/>[analisis.py]<br/>validación cruzada, importancia"]
    end

    ing -- "GET paginado" --> datosgov
    ing -- "CSV crudo" --> repo
    repo -- "escribe / lee" --> db
    repo -- "DataFrame" --> clean
    clean --> target --> split
    split -- "train / val / test" --> train
    prep -- "ColumnTransformer" --> train
    train -- "guarda Pipeline" --> art
    art --> evalc
    art --> fair
    art --> anal
    split -- "test" --> evalc
    split -- "test" --> fair
    split -- "particiones" --> anal
    evalc --> rep
    fair --> rep
    anal --> rep
    cfg -.-> ing
    cfg -.-> repo
    cfg -.-> split
    cfg -.-> train
```

## 3.2 API de predicción (capa de servicio)

```mermaid
flowchart TB
    usuario(["👤 Usuario / Swagger UI"])
    art[("model.joblib<br/>model_meta.json")]
    rep[("reports/metrics.json")]

    subgraph api["Capa de servicio — saber11.api"]
        router["<b>Rutas HTTP</b><br/>[main.py]<br/>GET /health · POST /predict · GET /metrics"]
        schemas["<b>Esquemas</b><br/>[schemas.py]<br/>PerfilEntrada, Prediccion (Pydantic)"]
        loader["<b>Cargador del modelo</b><br/>[model_service.py]<br/>carga una vez al iniciar"]
        predictor["<b>Servicio de predicción</b><br/>[model_service.py]<br/>puntaje → riesgo 0/1 y probabilidad calibrada"]
    end

    usuario -- "HTTP/JSON" --> router
    router -- "valida entrada / salida" --> schemas
    router -- "perfil validado" --> predictor
    predictor -- "usa Pipeline en memoria" --> loader
    loader -- "lee al iniciar" --> art
    router -- "lee" --> rep
```

## Responsabilidades y relaciones

| Componente | Módulo | Responsabilidad | Usa a | Responsable |
|---|---|---|---|---|
| Configuración | `config.py` | Cargar parámetros de `config.yaml` | — | Daniel |
| Ingesta | `data/ingest.py` | Descarga paginada, idempotente y con reintentos | Configuración | Daniel |
| Repositorio | `data/repository.py` | Persistir y leer la tabla `resultados` | Configuración | Daniel |
| Limpieza, target, separador, preprocesador | `features/preprocessing.py` | Dejar los datos listos y separados sin fuga | Repositorio | Daniel |
| Entrenador | `models/train.py` | Entrenar, comparar en validación y guardar el mejor `Pipeline` | Procesamiento | Richard |
| Evaluador | `models/evaluate.py` | Métricas en test, matriz de confusión, comparación con baseline | Artefactos, separador | Richard |
| Auditor de equidad | `models/fairness.py` | Métricas por grupo sensible | Artefactos, separador | Richard |
| Analizador | `models/analisis.py` | Validación cruzada e importancia de variables | Artefactos, separador | Camilo |
| Calibración | `calibracion.py` | Convertir el puntaje en probabilidad; lo comparten entrenamiento y API | — | Camilo |
| Rutas HTTP | `api/main.py` | Exponer los endpoints | Esquemas, servicio de predicción | Camilo |
| Esquemas | `api/schemas.py` | Validar la entrada (422 si es inválida) y dar forma a la salida | — | Camilo |
| Cargador y servicio de predicción | `api/model_service.py` | Cargar el modelo una vez y convertir el puntaje en riesgo y probabilidad | Artefactos, Calibración | Camilo |

**Relaciones que NO existen, por diseño:** la API no usa la capa de datos ni la de procesamiento. Solo conoce el `Pipeline` serializado, que ya incluye el preprocesamiento. Si el código importara `saber11.data` desde `saber11.api`, se rompería la arquitectura en capas.
