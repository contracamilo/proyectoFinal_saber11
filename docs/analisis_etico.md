# Análisis ético del modelo

## 1. Propósito y uso responsable

Este proyecto hace la búsqueda de las variables de contexto disponibles antes de la prueba que puedan ayudar a identificar de forma **agregada**, grupos de estudiantes que podrían beneficiarse de programas de refuerzo académico. La etiqueta de riesgo se detalla como un puntaje global inferior al percentil 25 del periodo estudiado. El modelo es una herramienta experimental de apoyo a la planeación; no señala por qué un estudiante logra cierto resultado ni mide su capacidad y/o potencial.

El resultado podría orientar análisis institucionales y la distribución de recursos complementarios, siempre que una persona juiciosa revise la información complementada con otras fuentes y el contexto local. No debe usarse para calificar, admitir, excluir, sancionar o asignar oportunidades a estudiantes; tampoco para clasificar abiertamente a personas o colegios, ni para reemplazar el criterio de docentes, orientadores o autoridades educativas.

## 2. Sesgos y limitaciones de los datos

El conjunto analizado se limita a estudiantes y colegios de Bogotá y a un único periodo (periodo 20224, con 76.253 estudiantes únicos después de quitar las 76.331 filas duplicadas de la fuente). Por ello, sus patrones no necesariamente representan a otras ciudades, zonas rurales, cohortes o años. Cambios en el examen, en las condiciones sociales o en la población pueden reducir la validez de las predicciones. Antes de aplicar el modelo en otro lugar o periodo, sería necesario evaluarlo de nuevo con datos pertinentes.

Variables como estrato de vivienda, naturaleza del colegio y bienes del hogar pueden reflejar diferencias en el acceso a recursos educativos. También pueden actuar como aproximaciones indirectas de condiciones socioeconómicas. El modelo podría propagar desigualdades históricas presentes en los datos.

La selección de registros, los datos faltantes, la forma de definir el percentil y la representación desigual de algunos grupos también pueden afectar los resultados. En el conjunto analizado hay 39.883 mujeres y 36.370 hombres; 43.909 estudiantes de colegios oficiales y 32.344 de no oficiales; y 75.590 en zona urbana frente a solo 663 en zona rural. Por estrato, los grupos más grandes son el 2 (31.453) y el 3 (26.286), mientras que el 5 (1.163), el 6 (417) y "Sin Estrato" (556) son pequeños, y 3.254 estudiantes no reportan el dato. Por eso no se deben generalizar las conclusiones más allá de la población estudiada.

## 3. Equidad y evaluación por grupos

En este contexto, una posible señal de trato desigual sería que el modelo detectara con menor frecuencia a estudiantes que realmente están en riesgo en algunos grupos, o que marcara como riesgo a estudiantes que no lo están con mayor frecuencia en otros. Esto podría producir diferencias en quién recibe atención si las predicciones se usaran para focalizar apoyos.

Para explorar estas diferencias se calcularon en el conjunto de prueba, por grupos de género, estrato, naturaleza del colegio y área de ubicación, el tamaño del grupo, la proporción real y predicha de casos de riesgo, el recall, la precision y la tasa de falsos positivos ([`reports/equidad.md`](../reports/equidad.md)). Siguiendo el escenario QA7 de `docs/arquitectura/drivers-calidad.md`, toda brecha de recall mayor a 0,10 entre grupos con al menos 30 personas se marca como hallazgo. **Las cuatro variables superan ese criterio:**

| Variable | Grupo con mayor recall | Grupo con menor recall | Brecha |
|---|---|---|---|
| Estrato | Sin Estrato: 0,9565 | Estrato 4: 0,5424 | 0,4141 |
| Naturaleza del colegio | Oficial: 0,7902 | No oficial: 0,5509 | 0,2393 |
| Área de ubicación | Rural: 0,8636 | Urbano: 0,7256 | 0,1380 |
| Género | Femenino: 0,7832 | Masculino: 0,6473 | 0,1359 |

El patrón va más allá del recall: el modelo marca mucho más a los grupos de menor nivel socioeconómico. En estrato 1 señala al 77,07 % de los estudiantes, cuando el riesgo real es de 35,50 %, y su tasa de falsos positivos es de 71,09 %. En colegios oficiales esa tasa es de 58,83 %, frente a 10,53 % en los no oficiales. Es decir, en esos grupos se detecta más riesgo, pero a cambio se etiqueta como "en riesgo" a muchos estudiantes que no lo están. En los grupos con menor recall ocurre lo contrario: casi la mitad de los estudiantes de colegios no oficiales que están en riesgo no se detecta.

Estas métricas son herramientas de diagnóstico. Una diferencia puede estar relacionada con el tamaño reducido de un grupo, la calidad de sus datos o desigualdades estructurales. Se interpretarán las cifras junto con los tamaños de muestra y el contexto, y no se asumirá que una brecha pequeña basta para autorizar un uso individual del modelo.

## 4. Privacidad y manejo de la información

Que los datos sean abiertos y estén anonimizados reduce ciertos riesgos, pero no garantiza que sea imposible identificar a alguien. La combinación de colegio, edad o fecha de nacimiento, género y otras características poco comunes podría facilitar una reidentificación al cruzarse con información externa. Por tanto, los datos deben tratarse con cuidado y la publicación de resultados debe limitarse a estadísticas agregadas o ejemplos que no expongan grupos muy pequeños.

El modelo debe usar solamente variables de contexto disponibles antes de la prueba y necesarias para el análisis. No se deben incluir nombres, documentos, identificadores personales, fechas exactas de nacimiento ni puntajes de la prueba como variables de entrada. Las columnas con los prefijos `punt_*`, `desemp_*` y `percentil_*` se excluyen (`LEAKAGE_PREFIXES` en `docs/arquitectura/contratos.md`) porque ocurren como resultado de la prueba: usarlas implicaría que el modelo utiliza información que no estaría disponible para el propósito predictivo, es decir, fuga de información. Por eso el pipeline falla si alguna de ellas aparece (QA6). La edad puede considerarse como variable de entrada si está prevista en el contrato del proyecto, pero debe evaluarse si aporta valor y si aumenta riesgos de privacidad o sesgo.

Se recomienda conservar únicamente los datos necesarios, restringir el acceso a archivos de trabajo y artefactos, no compartir filas individuales en informes y revisar los resultados antes de publicarlos.

## 5. Impacto social

Una aplicación inadecuada podría señalar a estudiantes, familias o colegios al etiquetarlos como “de riesgo”. También podría generar una profecía autocumplida si las predicciones reducen expectativas, oportunidades o acceso a recursos, en lugar de facilitar apoyo. Por esta razón, el lenguaje y la comunicación deben describir necesidades potenciales de apoyo.

El beneficio esperado es ayudar a planear apoyos académicos y distribuir recursos de manera informada. Para que ese beneficio sea real, los resultados deben conducir a intervenciones constructivas y su efectividad debe revisarse.

## 6. Justicia y transparencia

La regresión logística se considera como una alternativa relativamente interpretable: permite examinar cómo se asocian las variables con la probabilidad estimada, manteniendo constantes las demás variables del modelo. La interpretación debe acompañarse de las métricas de evaluación y de las limitaciones de los datos.

El género y el estrato son variables sensibles o relacionadas con características sensibles. Su inclusión puede ayudar a evaluar desempeño y diferencias entre grupos, pero también puede reproducir patrones de desigualdad. Como análisis complementario, se comparó el modelo completo con uno entrenado sin las cuatro variables sensibles:

| Modelo | F1 (test) | Brecha género | Brecha estrato | Brecha naturaleza | Brecha área |
|---|---|---|---|---|---|
| Completo | 0,5126 | 0,1359 | 0,4141 | 0,2393 | 0,1380 |
| Sin variables sensibles | 0,5129 | 0,0158 | 0,4433 | 0,2487 | 0,0421 |

Quitar esas variables casi no cambia el F1. Reduce las brechas de género y de área, pero las de estrato y naturaleza incluso aumentan un poco. Esto confirma que excluirlas no garantiza por sí solo equidad: otras variables, como la educación de los padres o los bienes del hogar, funcionan como proxies del nivel socioeconómico.

Como el modelo sin esas variables tiene el mismo desempeño y menores brechas de género y área, es una alternativa que debería preferirse si el sistema llegara a usarse; este *product concept* conserva el modelo completo para poder documentar la comparación. La decisión final requiere justificar el propósito, revisar los resultados por grupo y valorar las consecuencias de los errores. En ningún caso el modelo debe utilizarse para tomar decisiones individuales automatizadas. La documentación de variables, definición del objetivo, métricas y limitaciones busca hacer el análisis comprensible y revisable por el equipo y las personas responsables.

## 7. Recomendaciones de uso responsable

1. Limitar el uso a análisis agregados para planear apoyos educativos; no emplearlo para decisiones individuales de alto impacto.
2. Comunicar que el resultado es una estimación con incertidumbre, no una etiqueta, diagnóstico ni explicación causal.
3. Revisar recall, precision, falsos positivos, tamaños de grupo y brechas antes de considerar cualquier aplicación; investigar diferencias relevantes en vez de ocultarlas en una métrica global.
4. No usar puntajes de la prueba ni identificadores personales como variables de entrada, y reducir el detalle de los datos que se publican.
5. Validar de nuevo el modelo antes de aplicarlo a otro periodo o población y monitorear cambios en datos y desempeño.
6. Combinar los resultados con conocimiento local y revisión humana; ofrecer apoyos de forma inclusiva y evitar que una predicción negativa limite oportunidades.
7. Documentar las decisiones, responsables, limitaciones y resultados de cada evaluación, y suspender el uso si aparecen daños o disparidades que no puedan justificarse y mitigarse.

## Origen de las cifras

Todas las cifras de grupos y métricas salen del conjunto de prueba (11.438 estudiantes) y se reproducen con `python -m saber11.models.fairness`. Los tamaños por grupo de la sección 2 corresponden a los 76.253 estudiantes únicos.