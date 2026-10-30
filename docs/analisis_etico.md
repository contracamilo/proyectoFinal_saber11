# Análisis ético del modelo

## 1. Propósito y uso responsable

Este proyecto hace la busqueda de las variables de contexto disponibles, antes de la prueba puedan ayudar a identificar de forma **agregada**, grupos de estudiantes que podrían beneficiarse de programas de refuerzo académico. La etiqueta de riesgo se detalla como un puntaje global inferior al percentil 25 del periodo estudiado. El modelo es una herramienta experimental de apoyo a la planeación; no señala por qué un estudiante logra cierto resultado ni mide su capacidad y/o potencial.

El resultado podría situaar análisis institucionales y la distribución de recursos complementarios, siempre que una persona juiciosa revise la información adicionado con otras fuentes y el contexto local. No debe usar para calificar, admitir, excluir, sancionar o asignar oportunidades a estudiantes; tampoco para clasificar abiertamente a personas o colegios, ni para reemplazar el criterio de docentes, orientadores o autoridades educativas.

## 2. Sesgos y limitaciones de los datos

El conjunto analizado se limita a estudiantes y colegios de Bogotá y a un único periodo ([CIFRA: periodo y número de registros utilizados]). Por ello, sus patrones no necesariamente representan a otras ciudades, zonas rurales, cohortes o años. Cambios en el examen, en las condiciones sociales o en la población pueden reducir la validez de las predicciones. Antes de aplicar el modelo en otro lugar o periodo, sería necesario evaluarlo de nuevo con datos pertinentes.

Variables como estrato de vivienda, naturaleza del colegio y bienes del hogar pueden reflejar diferencias en el acceso a recursos educativos. También pueden actuar como aproximaciones indirectas de condiciones socioeconómicas. El modelo podría propagar desigualdades históricas presentes en los datos.

La selección de registros, los datos faltantes, la forma de definir el percentil y la representación desigual de algunos grupos también pueden afectar los resultados. Se debe documentar cuántos registros y observaciones de cada grupo se usaron ([CIFRA: distribución por grupo]) y evitar generalizar conclusiones más allá de la población estudiada.

## 3. Equidad y evaluación por grupos

En este contexto, una posible señal de trato desigual por lo que el modelo detectara con menor frecuencia a estudiantes que realmente están en riesgo en algunos grupos, o que marcara como riesgo a estudiantes que no lo están con mayor frecuencia en otros. Esto podría producir diferencias en quién recibe atención si las predicciones se usaran para focalizar apoyos.

Para explorar estas diferencias, se calcularán en el conjunto de prueba, por grupos de género, estrato, naturaleza del colegio y área de ubicación, el tamaño del grupo, la proporción real y predicha de casos de riesgo, el recall, la precision y la tasa de falsos positivos. También se reportará la mayor brecha de recall observada para cada variable ([CIFRA: brechas de recall y métricas por grupo]).

Estas métricas son herramientas de diagnóstico. Una diferencia puede estar relacionada con el tamaño reducido de un grupo, la calidad de sus datos o desigualdades estructurales. Se interpretarán las cifras junto con los tamaños de muestra y el contexto, y no se asumirá que una brecha pequeña basta para autorizar un uso individual del modelo.

## 4. Privacidad y manejo de la información

Que los datos sean abiertos y estén anonimizados reduce ciertos riesgos, pero no garantiza que sea imposible identificar a alguien. La combinación de colegio, edad o fecha de nacimiento, género y otras características poco comunes podría facilitar una reidentificación al cruzarse con información externa. Por tanto, los datos deben tratarse con cuidado y la publicación de resultados debe limitarse a estadísticas agregadas o ejemplos que expongan grupos muy pequeños.

El modelo debe usar solamente variables de contexto disponibles antes de la prueba y necesarias para el análisis. No se deben incluir nombres, documentos, identificadores personales, fechas exactas de nacimiento ni puntajes de la prueba como variables de entrada. Los puntajes `punt_*` se excluyen porque ocurren como resultado de la prueba, el modelo estaría utilizando información que no estaría disponible para el propósito predictivo. La edad puede considerarse como variable de entrada si está prevista en el contrato del proyecto, pero debe evaluarse si aporta valor y si aumenta riesgos de privacidad o sesgo.

Se recomienda conservar únicamente los datos necesarios, restringir el acceso a archivos de trabajo y artefactos, no compartir filas individuales en informes y revisar los resultados antes de publicarlos.

## 5. Impacto social

Una aplicación inadecuada podría señalar a estudiantes, familias o colegios al etiquetarlos como “de riesgo”. También podría generar una profecía autocumplida si las predicciones reducen expectativas, oportunidades o acceso a recursos, en lugar de facilitar apoyo. Por esta razón, el lenguaje y la comunicación deben describir necesidades potenciales de apoyo.

El beneficio esperado es ayudar a planear apoyos académicos y distribuir recursos de manera informada. Para que ese beneficio sea real, los resultados deben conducir a intervenciones constructivas y su efectividad debe revisarse.

## 6. Justicia y transparencia

La regresión logística se considera como una alternativa relativamente interpretable: permite examinar cómo se asocian las variables con la probabilidad estimada, manteniendo constantes las demás variables del modelo. La interpretación debe acompañarse de las métricas de evaluación y de las limitaciones de los datos.

El género y el estrato son variables sensibles o relacionadas con características sensibles. Su inclusión puede ayudar a evaluar desempeño y diferencias entre grupos, pero también puede reproducir patrones de desigualdad. El proyecto medirá el modelo completo y, como análisis complementario, comparará su desempeño y sus brechas con un modelo que no use las variables sensibles ([CIFRA: F1 y brechas de ambos modelos]). Excluirlas no garantiza por sí solo equidad, porque otras variables pueden funcionar como proxies.

La decisión final sobre incluir estas variables requiere justificar el propósito, revisar los resultados por grupo y valorar las consecuencias de los errores. En ningún caso el modelo debe utilizarse para tomar decisiones individuales automatizadas. La documentación de variables, definición del objetivo, métricas y limitaciones busca hacer el análisis comprensible y revisable por el equipo y las personas responsables.

## 7. Recomendaciones de uso responsable

1. Limitar el uso a análisis agregados para planear apoyos educativos; no emplearlo para decisiones individuales de alto impacto.
2. Comunicar que el resultado es una estimación con incertidumbre, no una etiqueta, diagnóstico ni explicación causal.
3. Revisar recall, precision, falsos positivos, tamaños de grupo y brechas antes de considerar cualquier aplicación; investigar diferencias relevantes en vez de ocultarlas en una métrica global.
4. No usar puntajes de la prueba ni identificadores personales como variables de entrada, y reducir el detalle de los datos que se publican.
5. Validar de nuevo el modelo antes de aplicarlo a otro periodo o población y monitorear cambios en datos y desempeño.
6. Combinar los resultados con conocimiento local y revisión humana; ofrecer apoyos de forma inclusiva y evitar que una predicción negativa limite oportunidades.
7. Documentar las decisiones, responsables, limitaciones y resultados de cada evaluación, y suspender el uso si aparecen daños o disparidades que no puedan justificarse y mitigarse.

## Resultados pendientes de completar

Este documento es un borrador previo a la evaluación final. Los marcadores `[CIFRA]` deben sustituirse únicamente por resultados reproducibles obtenidos en validación o en el conjunto de prueba, indicando claramente a cuál conjunto corresponden. Si una métrica no se calculó, debe indicarse como no disponible en lugar de estimarla o inventarla.