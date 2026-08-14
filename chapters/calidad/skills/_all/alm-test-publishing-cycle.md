---
id: calidad-alm-test-publishing-cycle
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Ciclo completo de publicación de casos en el ALM: de la historia al caso, del caso de vuelta al feature y del feature a las evidencias. Escalonado por capacidad confirmada (escritura en el gestor de pruebas, solo creación de incidencias, o ninguna), con el mismo artefacto en los tres niveles."
tags: [alm, jira, xray, azure-devops, casos-de-prueba, trazabilidad, importacion, publicacion, ciclo, mandatory]
enforcement: mandatory
verification:
  - check: "la capacidad usada para publicar fue verificada con una operación real y registrada, no supuesta"
    failure_message: "Bloqueado: se asumió una capacidad de escritura sin verificarla. Suponer permisos produce lotes a medias y procesos manuales que nadie diseñó."
  - check: "toda escritura del ciclo pasó por la ficha de autorización de calidad-alm-write-authorization-gate"
    failure_message: "Bloqueado: se publicó en el ALM del cliente sin autorización humana explícita."
  - check: "la sincronización de identificadores hacia los features se hizo sobre una tabla de emparejamiento sin ambigüedades, aprobada antes de escribir"
    failure_message: "Bloqueado: se escribieron identificadores de trazabilidad por inferencia. Un identificador mal puesto rompe la trazabilidad y nadie lo nota hasta la auditoría."
---

# ALM Test Publishing Cycle — De la Historia al Caso y de Vuelta al Feature

## Problema que resuelve

El ciclo que va de la historia al caso en el gestor de pruebas, del caso de vuelta al archivo de escenarios y del archivo a las evidencias suele estar partido entre herramientas sueltas, cargas masivas que ejecuta un tercero y correcciones manuales posteriores. Cada tramo manual es una oportunidad de desincronizar la trazabilidad, y el costo se paga en cada historia.

El agente puede absorber casi todo el ciclo, pero **cuánto depende de permisos que se verifican, no que se suponen**. Este skill define el ciclo una sola vez y lo escalona por capacidad confirmada.

## Cuándo aplicar

Cuando haya que llevar casos diseñados al ALM del cliente, sincronizar identificadores hacia los archivos de escenarios, o publicar resultados de ejecución. Lo usan la ruta funcional (`[[calidad-design-test-cases]]`) y las rutas de automatización tras generar los escenarios.

## Las dos capacidades que hay que verificar

No son la misma y suelen confundirse, lo que produce diagnósticos falsos del tipo "no tenemos permisos":

1. **Crear incidencias en el gestor de proyectos** — permiso del proyecto sobre el tipo de incidencia que usan los casos de prueba. Que la credencial cree defectos no implica que cree casos: el tipo de incidencia puede no estar habilitado o su pantalla puede exigir campos que la credencial no puede escribir.
2. **Escribir en el gestor de pruebas** — normalmente un producto aparte, con su propia API y **su propia autenticación**, independiente de los permisos del usuario en el gestor de proyectos. Esta es la que suele estar disponible sin que el equipo lo sepa.

**Regla:** cada capacidad se verifica con una operación real sobre un elemento desechable, se registra su resultado, y hasta entonces se declara `sin verificar`. La verificación **es una escritura** y pasa por `[[calidad-alm-write-authorization-gate]]`.

## Las cinco etapas

| # | Etapa | Qué produce |
|---|---|---|
| 1 | **Ingesta de la historia** | historia con sus criterios de aceptación reales, leída del ALM (lectura, sin autorización) |
| 2 | **Diseño y generación del artefacto** | casos redactados desde los criterios reales + artefacto de publicación |
| 3 | **Publicación** | casos existentes en el gestor de pruebas, con su tipo, su contenido y su ubicación |
| 4 | **Sincronización de identificadores** | los identificadores escritos como etiquetas de trazabilidad en los archivos de escenarios |
| 5 | **Ejecución y evidencias** | resultados y evidencias publicados contra el ciclo correspondiente |

## Escalonado por capacidad

| Capacidad confirmada | Etapa 3 — Publicación | Etapa 4 — Sincronización |
|---|---|---|
| **Escritura en el gestor de pruebas** | creación directa del caso con su tipo, su contenido Gherkin y su ubicación en una sola operación | trivial: la creación devuelve el identificador y se escribe en el archivo |
| **Solo creación de incidencias** | se crea el caso y se vincula a la historia; tipo, contenido y ubicación quedan pendientes por vía manual | trivial: la creación devuelve el identificador |
| **Ninguna** | se genera el artefacto de importación masiva y su runbook; la carga la ejecuta un humano con permisos | por emparejamiento contra los casos ya cargados (abajo) |

**Regla de diseño que mantiene esto sano: el artefacto de la etapa 2 se produce igual en los tres niveles.** Lo único que cambia es quién lo aplica. Un solo camino de generación, sin ramas que se desincronicen, y el runbook del humano sale del mismo sitio. Subir de nivel **activa** un camino de publicación; no reescribe el ciclo.

## Etapa 2 — El artefacto

- Los casos se redactan desde los **criterios de aceptación reales de la historia**, no desde el texto de los escenarios. Derivar los criterios del Gherkin es inventarlos al revés: el Gherkin ya es una interpretación.
- Todo campo sale del escenario, de la historia o de la configuración del proyecto. **Ningún campo se inventa.**
- El contrato del artefacto (columnas, valores fijos, formato, escapado, codificación) es específico de la instancia del cliente y vive en su asset de cuenta, junto con un **ejemplar de oro** —un archivo que el ALM aceptó sin errores— versionado como prueba de regresión del contrato.
- **Idempotencia antes de publicar**: se consulta qué casos ya existen para la historia y el artefacto separa nuevos de existentes. Re-correr el flujo no duplica.

## Etapa 4 — Sincronización de identificadores

Es el tramo que más se hace a mano y el que más silenciosamente rompe la trazabilidad.

**Con capacidad de creación**, no hay problema que resolver: el identificador llega en la respuesta y se escribe.

**Sin capacidad**, hay que emparejar contra lo ya cargado:

1. Consultar los casos vinculados a la historia con su identificador y su resumen.
2. Emparejar cada caso con un escenario. La llave es el **nombre del escenario normalizado** — lo que exige que el resumen del caso derive del nombre del escenario de forma determinista. Por eso cualquier prefijo de nomenclatura debe ser **regla del generador y no criterio humano**: si a veces lo pone la persona y a veces el escenario, el emparejamiento deja de ser posible.
3. Emitir la tabla escenario ↔ identificador ↔ confianza y **detenerse ante cualquier ambigüedad**: escenario sin pareja, dos escenarios que empatan con el mismo caso, o escenario que ya tiene un identificador distinto al que le tocaría. Nada se adivina.
4. Con la tabla aprobada por el usuario, escribir las etiquetas en los archivos de escenarios.

**Compuerta humana previa cuando la carga la hizo una persona:** antes de sincronizar, el usuario confirma que los casos están cargados, en la ubicación correcta y con el tipo correcto. Pero el agente **no se queda en la palabra**: verifica lo que puede alcanzar —conteo por consulta, tipo de cada caso, ubicación si la API lo expone— y reporta la diferencia si la hay. La confirmación humana desbloquea; la verificación del agente valida.

**Verificación inversa, que es la matriz de trazabilidad real:** todo escenario con exactamente un identificador, y todo caso de la historia con exactamente un escenario. Lo que sobre o falte de cualquier lado se reporta.

## Restricciones

- **NUNCA** publicar, sincronizar ni subir evidencias sin la ficha de `[[calidad-alm-write-authorization-gate]]`.
- **NUNCA** declarar una capacidad disponible sin haberla probado, ni declararla ausente sin haberlo intentado. "Creemos que no tenemos permisos" no es un diagnóstico.
- **NUNCA** escribir un identificador de trazabilidad por inferencia cuando el emparejamiento fue ambiguo.
- **NUNCA** dar el ciclo por cerrado con la verificación inversa en desequilibrio: casos huérfanos o escenarios sin identificador son deuda de trazabilidad, y se reportan aunque el resto haya salido bien.
- Cada etapa completada se registra en `[[calidad-pipeline-state-tracking]]`.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | la capacidad usada para publicar fue verificada con una operación real y registrada, no supuesta | Bloqueado: se asumió una capacidad de escritura sin verificarla. Suponer permisos produce lotes a medias y procesos manuales que nadie diseñó. |
| 2 | toda escritura del ciclo pasó por la ficha de autorización de calidad-alm-write-authorization-gate | Bloqueado: se publicó en el ALM del cliente sin autorización humana explícita. |
| 3 | la sincronización de identificadores hacia los features se hizo sobre una tabla de emparejamiento sin ambigüedades, aprobada antes de escribir | Bloqueado: se escribieron identificadores de trazabilidad por inferencia. Un identificador mal puesto rompe la trazabilidad y nadie lo nota hasta la auditoría. |

## Cross-links

`[[calidad-alm-write-authorization-gate]]`, `[[calidad-alm-mcp-integration]]`, `[[calidad-design-test-cases]]`, `[[calidad-funcional-test-design]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-cucumber-bdd-conventions]]`, `[[calidad-repo-capability-discovery]]`, `[[calidad-pipeline-state-tracking]]`.
