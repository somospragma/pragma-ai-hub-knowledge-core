# Estrategia de pruebas — {{hu}} · {{titulo}}

Fecha: {{fecha}} · Épica: {{epica}} · Criterios en la historia: {{criterios}}
Fuente: `{{fuente}}`

## Naturaleza de lo que se prueba

_Qué clase de comportamiento es: render, flujo de interfaz, regla de negocio, contrato de
servicio, temporizador, persistencia, analítica. De esto sale todo lo demás._

## En qué capa vive cada criterio

Un criterio se prueba donde vive su lógica, no donde se ve su efecto. Una normalización que
hace el servicio se prueba contra el servicio, aunque se note en la pantalla.

| Criterio | Qué afirma | Capa que lo prueba | Repositorio / stack | Por qué ahí |
|---|---|---|---|---|
| CA-1 |  |  |  |  |

El mapa de repositorios por capa es conocimiento de la cuenta, no del chapter: se consulta
antes de llenar la columna, no se supone.

## Matriz de cobertura

Todas las plataformas del alcance desde el inicio, aunque se estabilicen en serie
(`[[calidad-mandatory-inputs-protocol]]`).

| Criterio | Plataformas | Escenario propuesto | Estado de dato que exige | Reuso | Etiqueta |
|---|---|---|---|---|---|

## Qué se automatiza y qué no

| Criterio | Automatizable | Razón si no | Cómo se cubre entonces |
|---|---|---|---|

Un dato imposible de obtener es una razón legítima de no automatizable
(`[[calidad-automation-feasibility-assessment]]`); "es difícil" no lo es.

## Riesgos de esta historia

Lo que puede hacer que la prueba diga algo falso: datos volátiles, dependencias de otro
equipo, comportamiento que cambia según el momento del día, estado compartido entre casos.

| Riesgo | Efecto si se materializa | Mitigación |
|---|---|---|

## Dependencias que bloquean la ejecución

Historias técnicas, contratos, despliegues. Con su estado real en el gestor, no supuesto.

| Dependencia | Tipo | Estado | Qué bloquea |
|---|---|---|---|
