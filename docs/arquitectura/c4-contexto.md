# C4 — Nivel 1: Diagrama de contexto

Muestra el sistema como una sola caja, quién lo usa y con qué sistemas externos se comunica. No muestra tecnologías ni detalles internos.

```mermaid
flowchart LR
    analista(["👤 Analista de secretaría de educación<br/><i>Focaliza programas de refuerzo<br/>con el riesgo agregado</i>"])
    orientador(["👤 Orientador escolar<br/><i>Consulta el riesgo de un perfil<br/>de contexto de su colegio</i>"])
    equipo(["👤 Equipo de ciencia de datos<br/><i>Entrena, evalúa y audita el modelo</i>"])

    sistema[["<b>Sistema de riesgo Saber 11</b><br/>Descarga datos abiertos, entrena un clasificador<br/>y expone predicciones y métricas"]]

    datosgov[("<b>datos.gov.co — ICFES</b><br/>[Sistema externo]<br/>Resultados únicos Saber 11<br/>API Socrata kgxf-xxbe")]
    simat[("<b>SIMAT</b><br/>[Sistema externo — futuro v2]<br/>Datos de matrícula")]

    analista -- "Consulta riesgo y métricas<br/>[HTTPS/JSON]" --> sistema
    orientador -- "Consulta riesgo de un perfil<br/>[HTTPS/JSON]" --> sistema
    equipo -- "Ejecuta ingesta, entrenamiento<br/>y evaluación [CLI]" --> sistema
    sistema -- "Descarga resultados del periodo<br/>configurado [HTTPS/JSON]" --> datosgov
    sistema -. "Consumiría datos de matrícula<br/>[futuro]" .-> simat

    classDef persona fill:#08427b,color:#fff,stroke:#052e56
    classDef interno fill:#1168bd,color:#fff,stroke:#0b4884
    classDef externo fill:#999999,color:#fff,stroke:#6b6b6b
    classDef futuro fill:#d9d9d9,color:#555,stroke:#9e9e9e,stroke-dasharray: 5 5
    class analista,orientador,equipo persona
    class sistema interno
    class datosgov externo
    class simat futuro
```

| Elemento | Tipo | Responsabilidad |
|---|---|---|
| Analista de secretaría de educación | Persona | Usa el riesgo agregado por colegio o localidad para decidir dónde asignar programas de refuerzo. |
| Orientador escolar | Persona | Consulta el nivel de riesgo de perfiles de contexto de su institución para planear acompañamiento. |
| Equipo de ciencia de datos | Persona | Ejecuta el pipeline, revisa métricas y equidad, y reentrena cuando cambian los datos. |
| Sistema de riesgo Saber 11 | Sistema (este proyecto) | Obtiene y almacena los datos, entrena y evalúa el modelo, y expone predicciones y métricas por API. |
| datos.gov.co (ICFES) | Sistema externo | Fuente oficial y abierta de los resultados de Saber 11. |
| SIMAT | Sistema externo futuro | Fuente de matrícula para una versión 2. Está **fuera del alcance** actual (gris y punteado). |
