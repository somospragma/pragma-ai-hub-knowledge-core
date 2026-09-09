---
id: calidad-cross-platform-learning-propagation
version: 1.2.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Disciplina para entregas multiplataforma: llevar un libro de aprendizajes que clasifica cada corrección en compartida o específica, y aplicar todas las compartidas antes de arrancar la plataforma siguiente. Evita volver a descubrir test por test lo ya estabilizado en la plataforma anterior."
tags: [multiplataforma, mobile, web, android, ios, propagacion, correcciones, brownfield, universal, mandatory]
enforcement: mandatory
verification:
  - check: "antes de generar o ejecutar una plataforma nueva se revisó .evidence/platform-learnings.md y se emitió la lista de correcciones compartidas aplicadas"
    failure_message: "Bloqueado: se arrancó una plataforma sin aplicar lo aprendido en las anteriores. Ese es el patrón que hace que el segundo canal cueste lo mismo que el primero."
  - check: "toda corrección aplicada quedó clasificada como compartida o específica de plataforma, con su razón"
    failure_message: "Bloqueado: hay correcciones sin clasificar. Sin la clasificación no se sabe qué propagar y se propaga todo o nada."
  - check: "antes de escribir cada interacción nueva se consultó si existe un escenario en verde que toque la misma pantalla o componente, y la respuesta quedó citada en .evidence/platform-learnings.md"
    failure_message: "Bloqueado: se escribió una interacción nueva sin comprobar si el mecanismo ya existía en verde. Reinventar lo que ya está demostrado es el desperdicio más caro y más evitable."
---

# Cross-Platform Learning Propagation — Aprender una Vez, Aplicar en Todas

## Problema que resuelve

Cuando una historia se automatiza para varias plataformas, el agente estabiliza la primera a costa de varias iteraciones —esperas, datos, orden del flujo, anclas de aserción, nombres de steps— y al pasar a la segunda **vuelve a tropezar test por test con los mismos problemas ya resueltos**.

Verificado en campo: una historia con tres canales, resuelta canal por canal, donde el segundo repitió íntegro el ciclo de descubrimiento del primero. El costo se multiplica por el número de plataformas y crece con cada iteración.

La causa estructural suele ser que el código está duplicado por plataforma, así que corregir uno no corrige el otro. Eso no se cambia unilateralmente, pero **sí obliga a propagar de forma explícita**.

## Cuándo aplicar

En toda entrega que cubra más de una plataforma o canal, desde la primera corrección de la primera plataforma. Aplica a móvil (variantes de sistema operativo, tableta, navegador móvil) y a web con más de un navegador o resolución con implementación separada.

## Instrucción

### 1. Antes de nada, mirar si el repositorio ya ejecuta todo junto

Consultar el mapa de `[[calidad-repo-capability-discovery]]`. Si el repositorio provee un ejecutor multiplataforma, **se usa**: buena parte de la disciplina de este skill la resuelve una sola corrida que expone los fallos de todas las plataformas a la vez, en lugar de descubrirlos en serie.

Solo cuando la ejecución es necesariamente secuencial aplica el ciclo completo de abajo.

### 2. Libro de aprendizajes

`.evidence/platform-learnings.md`, actualizado en el mismo turno en que se aplica cada corrección:

```markdown
| # | Corrección aplicada | Plataforma origen | Clase | Razón | Propagada a |
|---|---|---|---|---|---|
| 1 | Esperar el fin de la carga antes de tocar la lista | android | compartida | el patrón de carga es del producto, no del sistema | ios (pend.), web (pend.) |
| 2 | Ancla por rótulo en vez de por contenido del registro | android | compartida | el contenido es volátil en cualquier plataforma | ios (pend.), web (pend.) |
| 3 | Gesto de scroll por coordenadas | android | específica | la jerarquía nativa difiere; en web no aplica | — |
```

**Clasificación:**

- **Compartida** — vale en toda plataforma: esperas ligadas al comportamiento del producto, datos y precondiciones, orden del flujo funcional, anclas de aserción (`[[calidad-data-volatility-and-assertion-anchoring]]`), nomenclatura y especificidad de steps, criterios de verificación.
- **Específica** — atada a la tecnología de la plataforma: jerarquía de elementos nativos, gestos, capabilities, contextos híbridos, particularidades del motor del navegador.

Ante la duda, **compartida**: revisar una corrección que no aplicaba cuesta minutos; volver a diagnosticarla en el otro canal cuesta la iteración entera.

### 3. Gate de arranque de plataforma

Antes de generar o ejecutar la plataforma siguiente, es **obligatorio**:

1. Leer el libro de aprendizajes completo.
2. Aplicar **todas** las correcciones `compartidas` pendientes a la plataforma que arranca.
3. Emitir la lista de las aplicadas y de las descartadas con su razón.
4. Marcar la propagación en el libro.

Arrancar sin este paso es blocker `platform_learnings_not_applied`.

### 4. Propagación inmediata cuando el código está duplicado

Si las plataformas duplican lógica, una corrección `compartida` **se replica en el mismo turno en que se descubre**, no cuando la otra plataforma falle. Esperar al fallo es exactamente el patrón que este skill elimina.

Si en cambio la lógica está compartida (steps comunes, capa de pantallas con contrato común por plataforma), la corrección ya alcanza a todas y solo se verifica.

### 5. Reportar la deuda, no resolverla por cuenta propia

Cuando la duplicación entre plataformas es el origen del retrabajo, el agente lo **reporta** como oportunidad de mejora del arquetipo, con el punto concreto de reutilización posible. **No** reestructura el arquetipo del cliente por iniciativa propia: eso es brownfield tocando lo preexistente (`[[calidad-brownfield-vs-greenfield]]`).

## Restricciones

- **NUNCA** declarar una plataforma "lista" sin haber marcado en el libro qué se propagó hacia ella.
- **NUNCA** propagar una corrección `específica` sin verificarla en la plataforma destino: lo que arregla una jerarquía puede romper otra.
- **NUNCA** usar la propagación como excusa para modificar tests preexistentes de otras historias: el libro aplica a los tests de la entrega en curso.
- El libro se arrastra entre sesiones junto con `[[calidad-pipeline-state-tracking]]` y se relee al abrir cada una.

## El hermano estable: la consulta obligatoria antes de escribir una interacción

El libro de aprendizajes resuelve la propagación **entre plataformas**. Falta la de dentro de una misma plataforma, que es la que más veces se salta y la que más barata sale de corregir.

> **Antes de escribir cualquier interacción nueva, se busca si ya existe un escenario en verde que toque esa misma pantalla, ese mismo menú o ese mismo componente. Si existe, se reutiliza su mecanismo verbatim y se cita dónde está.**

Verificado en campo: un flujo pulsaba un control de un menú de forma perfectamente estable; al automatizar el **control hermano del mismo menú**, en vez de repetir el mecanismo se inventó otro por coordenadas. Costó del orden de doscientos créditos de iteración llegar a la conclusión de que era el mismo control de al lado y se pulsaba igual.

**La consulta no es un ejercicio de memoria: es una búsqueda determinista** sobre el repositorio —qué escenarios verdes tocan esta pantalla o este componente, y con qué mecanismo—. Por tanto la resuelve una herramienta del proyecto, no el recuerdo del agente, que es justo lo que falla cuando la sesión lleva doscientos mensajes. Si no existe, se construye una vez según `[[calidad-deterministic-work-to-tooling]]`.

La consulta produce una de tres respuestas, y las tres se registran en el turno donde se escribe el código:

1. **Existe y se reutiliza** — se cita el archivo y la línea del mecanismo reutilizado.
2. **Existe pero no aplica** — se cita igual, y se justifica en una línea por qué no sirve. Esta es la respuesta que hay que sospechar: casi siempre el motivo real es que se prefería escribir algo nuevo.
3. **No existe** — se declara, y lo que se escriba pasa a ser candidato a hermano estable de lo que venga después.

Un mecanismo que ya está en verde tiene una propiedad que ningún diseño nuevo tiene por bueno que sea: **está demostrado contra la aplicación real**.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | antes de generar o ejecutar una plataforma nueva se revisó .evidence/platform-learnings.md y se emitió la lista de correcciones compartidas aplicadas | Bloqueado: se arrancó una plataforma sin aplicar lo aprendido en las anteriores. Ese es el patrón que hace que el segundo canal cueste lo mismo que el primero. |
| 2 | toda corrección aplicada quedó clasificada como compartida o específica de plataforma, con su razón | Bloqueado: hay correcciones sin clasificar. Sin la clasificación no se sabe qué propagar y se propaga todo o nada. |
| 3 | antes de escribir cada interacción nueva se consultó si existe un escenario en verde que toque la misma pantalla o componente, y la respuesta quedó citada en .evidence/platform-learnings.md | Bloqueado: se escribió una interacción nueva sin comprobar si el mecanismo ya existía en verde. Reinventar lo que ya está demostrado es el desperdicio más caro y más evitable. |

## Cross-links

`[[calidad-repo-capability-discovery]]`, `[[calidad-pipeline-state-tracking]]`, `[[calidad-test-self-correction-loop]]`, `[[calidad-data-volatility-and-assertion-anchoring]]`, `[[calidad-cucumber-bdd-conventions]]`, `[[calidad-brownfield-vs-greenfield]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-cold-audit-before-execution]]`, `[[calidad-human-fix-request-protocol]]`, `[[calidad-deterministic-work-to-tooling]]`.
