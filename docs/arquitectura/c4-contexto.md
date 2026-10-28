# C4 — Nivel 1: Diagrama de contexto (borrador)

```mermaid
C4Context
    title Contexto — Sistema de riesgo de bajo desempeño Saber 11

    Person(analista, "Analista de secretaría de educación", "Consulta el riesgo agregado para focalizar programas de refuerzo")
    Person(orientador, "Orientador escolar", "Consulta el riesgo de un perfil de contexto de su colegio")
    Person(cientifico, "Equipo de ciencia de datos", "Entrena, evalúa y audita el modelo")

    System(sistema, "Sistema de riesgo Saber 11", "Ingesta datos abiertos, entrena un modelo de clasificación y expone predicciones y métricas")

    System_Ext(datosgov, "datos.gov.co (ICFES)", "API Socrata con resultados únicos Saber 11")
    System_Ext(simat, "SIMAT (futuro)", "Sistema de matrícula; fuente de datos de contexto en una versión 2")

    Rel(analista, sistema, "Consulta riesgo y métricas", "HTTPS/JSON")
    Rel(orientador, sistema, "Consulta riesgo de un perfil", "HTTPS/JSON")
    Rel(cientifico, sistema, "Ejecuta ingesta, entrenamiento y evaluación", "CLI")
    Rel(sistema, datosgov, "Descarga resultados del periodo configurado", "HTTPS/JSON")
    Rel(sistema, simat, "Consumiría datos de matrícula", "Futuro")

    UpdateElementStyle(simat, $bgColor="#9e9e9e", $borderColor="#616161")
    UpdateRelStyle(sistema, simat, $lineColor="#9e9e9e")
```

**Lectura:** el sistema se ve como una sola caja. Los elementos en gris representan integraciones futuras fuera del alcance actual.

TODO (Camilo): validar actores con los user persona y agregar el diagrama de contenedores en `c4-contenedores.md`.
