---
id: calidad-deterministic-work-to-tooling
version: 1.4.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Todo trabajo determinista y repetido de una certificación se resuelve con una herramienta del proyecto, no con el razonamiento del agente. Antes de hacerlo a mano se comprueba si el proyecto ya la tiene; si no la tiene, se construye una vez, se documenta en el proyecto y se registra en el mapa de capacidades para que la siguiente sesión la encuentre."
tags: [herramientas, automatizacion-del-proceso, costo, determinismo, brownfield, capacidades, universal, mandatory]
enforcement: mandatory
verification:
  - check: "antes de resolver cualquier tarea determinista y repetida se consultó el mapa de capacidades del proyecto, y la respuesta (existe / no existe) quedó registrada"
    failure_message: "Bloqueado: se hizo a mano trabajo determinista sin comprobar si el proyecto ya lo resolvía. Ya ocurrió en campo estabilizar una certificación entera de a un escenario teniendo el ejecutor por lotes en el mismo repositorio."
  - check: "toda herramienta construida quedó dentro del proyecto, documentada y registrada con su invocación, y .evidence/tooling-gaps.md declara qué resuelve el proyecto y qué hueco queda"
    failure_message: "Bloqueado: hay una herramienta construida que la siguiente sesión no va a encontrar. Un script suelto que nadie registra se vuelve a escribir en la siguiente historia."
  - check: "la salida de cada herramienta es acotada y legible por máquina; ninguna vuelca su registro completo al razonamiento del agente"
    failure_message: "Bloqueado: una herramienta devuelve la salida cruda. El coste no es ejecutar: es que la salida entre al contexto y se reenvíe en cada paso posterior."
  - check: "todo artefacto que un asset obligatorio exige es entrada de alguna herramienta o está cubierto por una puerta que bloquea; ninguno depende sólo de que el agente lo recuerde"
    failure_message: "Bloqueado: hay una obligación sostenida sólo por texto. Ya se midió que seis de cada diez artefactos obligatorios no se creaban y nadie lo notaba. Se convierte en entrada de herramienta o en puerta con código de salida."
---

# Lo Determinista se Convierte en Herramienta del Proyecto

## Problema que resuelve

En una certificación, la mayor parte del gasto no está en decidir: está en **hacer a mano, una y otra vez, cosas que no requieren criterio**. Lanzar una corrida y leer su salida, clasificar por qué falló, comprobar si el escenario compila y enlaza, contar qué criterios quedan sin cubrir, buscar si ya existe un mecanismo verde para esa pantalla, comprobar que los artefactos obligatorios están.

Todo eso es determinista: la misma entrada produce la misma salida, y no hay juicio de por medio. Cuando lo resuelve el razonamiento del agente, se paga **cada vez**, y se paga dos veces: por resolverlo y porque la salida cruda se queda en el contexto y se reenvía en cada paso posterior de la sesión.

Verificado en campo, midiendo partida por partida una certificación de cincuenta casos: **la mitad del presupuesto se fue en ejecutar y leer salidas**, y generar todo el código de los cincuenta casos costó menos de una novena parte. El trabajo caro no era el que exigía criterio.

Lo que corrige este asset no es quién hace el trabajo determinista, sino **qué lo hace**. Pasárselo a una persona lo mueve; convertirlo en herramienta lo elimina.

## Cuándo aplicar

En cuanto una tarea determinista se vaya a hacer por **segunda** vez en la misma entrega, y siempre en la fase de descubrimiento de capacidades, antes de la primera corrida.

## Instrucción

### 1. Reconocer qué es candidato a herramienta

Una tarea se convierte en herramienta cuando cumple las cuatro:

1. **Determinista** — la misma entrada produce la misma salida. Si hay juicio, no lo es.
2. **Repetida** — ocurre más de dos veces en una entrega, o en todas las entregas.
3. **De salida acotable** — se puede resumir en un veredicto pequeño y estructurado, aunque el insumo sea enorme.
4. **Sin criterio de calidad de por medio** — decidir *si un fallo es defecto del producto* exige juicio; *extraer qué step falló y con qué clase de error* no.

La cuarta es la frontera importante. La herramienta **prepara la decisión**; no la toma. Clasificar un fallo por patrón es herramienta; declarar un defecto del sistema bajo prueba sigue siendo del agente y de la persona, con la cadena de evidencia de `[[calidad-failure-triage-and-classification]]`.

### 2. Preguntar primero si el proyecto ya la tiene

**Nunca se construye lo que ya existe.** El mapa de `[[calidad-repo-capability-discovery]]` es la fuente, y la consulta se registra con su respuesta.

Este paso no es una formalidad. Verificado en campo, y es el caso más caro del catálogo: una certificación se estabilizó escenario por escenario durante cinco días, con 214 corridas, **teniendo en el propio repositorio un ejecutor por etiquetas y multiplataforma**, documentado, con una sección del mapa de capacidades titulada literalmente "existe, úsalo".

Un repositorio maduro ya suele traer: el ejecutor por etiquetas, el archivado de reportes, el preflight, la publicación al gestor de pruebas, la restauración de datos de prueba y el enganche de pre-commit. Se comprueba antes de escribir una línea.

### 3. Si no existe, se construye una vez y queda

Cuando hay hueco, **el hueco se cierra en el proyecto**, no en el turno:

| Requisito | Por qué |
|---|---|
| Vive **dentro del repositorio del proyecto**, junto a sus otras utilidades | Un script en un directorio temporal se pierde y se vuelve a escribir en la siguiente historia |
| Tiene **su documentación en el proyecto**: qué hace, cómo se invoca, qué devuelve, cuándo usarla | Sin eso, la siguiente sesión no la encuentra aunque exista |
| Queda **registrada en el mapa de capacidades con su invocación exacta** | Es lo que hace que la próxima consulta del paso 2 devuelva "existe" |
| Su **salida es acotada y estructurada** | Ver el paso 4 |
| **No reimplementa** lo que el arquetipo ya resuelve; lo envuelve | Reimplementar duplica la fuente de verdad |
| Se **entrega con el commit de la historia**, como parte del trabajo | Una herramienta sin commitear no existe |

Un error de campo que esto evita: ante la necesidad de sembrar una precondición, se armó un script suelto que además importaba piezas fuera de su tiempo de ejecución y falló; la vía correcta era un artefacto permanente del proyecto, que después se creó y se reutilizó durante el resto de la entrega.

### 4. El contrato de salida es lo que produce el ahorro

Construir la herramienta y luego volcar su salida cruda al razonamiento **no ahorra nada**. El contrato mínimo:

- **Un veredicto pequeño y estructurado** — del orden de un par de kilobytes: qué se ejecutó, cuál fue el resultado, dónde falló, de qué clase es el fallo, y las rutas de los artefactos completos.
- **Los artefactos grandes quedan en disco**, referenciados por ruta. Se abren de forma excepcional, acotada y con hipótesis declarada.
- **Un resumen legible por una persona**, separado del veredicto estructurado, para quien tenga que mirarlo.
- **Código de salida distinto de cero cuando bloquea**, para que pueda encadenarse en una puerta.

### 5. La aritmética que decide

Construir cuesta una vez; no construir cuesta cada vez.

```
usos previstos × ahorro por uso  >  coste de construirla   ->  se construye
```

Con los números medidos en la certificación de referencia: una herramienta de ejecución y veredicto costaría del orden de treinta unidades de presupuesto construirla, y ahorra unas diez por corrida. Con 214 corridas, se amortiza en las tres primeras. La conclusión práctica es que **casi siempre se construye**, y que la duda sólo aparece en tareas que ocurren una o dos veces por historia.

El ahorro además **no se queda en la historia**: la siguiente entrega del mismo proyecto la hereda ya construida.

### 6. El catálogo mínimo de una certificación

El chapter fija **qué debe existir y qué debe devolver**; cada proyecto lo implementa con su stack y sus convenciones.

| Capacidad | Qué reemplaza | Veredicto que devuelve |
|---|---|---|
| **Ejecutar y resumir** | leer el registro completo de la corrida | escenario, resultado, step que falló, clase de fallo, rutas |
| **Triar el fallo** | clasificar leyendo el registro | clase de fallo por patrón, evidencia asociada, y si es candidato a defecto |
| **Empaquetar la evidencia visual** | intentar interpretar una captura | texto reconocido, árbol o capa semántica del instante, geometría y firma de pantalla (ver `[[calidad-test-evidence-and-traceability]]`) |
| **Auditar en frío** | recorrer mentalmente la cadena de steps | secuencia de interacciones en orden, con estrategia y espera de cada paso (ver `[[calidad-cold-audit-before-execution]]`) |
| **Buscar el hermano estable** | recordar si ya existe un mecanismo verde | escenarios verdes que tocan esa pantalla o componente, con archivo y línea (ver `[[calidad-cross-platform-learning-propagation]]`) |
| **Medir cobertura** | recordar qué falta por cubrir | matriz declarada contra entregada y la diferencia |
| **Comprobar precondiciones y datos** | descubrir por corrida fallida que el dato no servía | estado real de cada dato exigido, antes de ejecutar |
| **Preflight** | sondear a mano y leer cinco salidas | verde o rojo con la sonda que falló |
| **Puerta de entrega y presencia de artefactos** | comprobar a mano artefactos, estático y cobertura | lo que falta, con código de salida que bloquea. **Es la de mayor apalancamiento del catálogo**: sin ella, toda regla obligatoria del chapter depende de que el agente se acuerde |

Y cuando la entrega es pre-desarrollo, cuatro más — ver `[[calidad-pre-development-artifacts-continuity]]`:

| Capacidad | Qué reemplaza | Veredicto que devuelve |
|---|---|---|
| **Cosechar el árbol de la app desplegada** | inferir la estructura de una pantalla | identificadores reales por pantalla, con su componente y su posición |
| **Extraer del repositorio de front** | que el modelo lea el código para entenderlo | identificadores declarados, rutas y puntos de llamada a servicios, **como delta** contra la última extracción |
| **Generar prototipo y mock desde las fuentes** | escribir pantallas y respuestas a mano | los artefactos emitidos, reproducibles |
| **Verificar deriva y estado** | analizar en qué estado quedó el mock | qué anclajes cambiaron y qué unidades pasaron a desplegadas u obsoletas |

La segunda merece énfasis porque es la que más se hace mal: **leer un repositorio de front con el modelo cuesta más que todo lo que ahorra**, y lo leído se sigue pagando el resto de la sesión. El extractor recorre; el agente lee el delta.

Ninguna de las nueve requiere criterio. Las nueve se hacían a mano.

Y cuando la entrega **empieza por historias y todavía no hay código** —analizar un alcance,
decir qué datos hacen falta, pedirlos al cliente— hay cinco más. Ver
`[[calidad-analyze-stories-and-request-data]]`:

| Capacidad | Qué reemplaza | Veredicto que devuelve |
|---|---|---|
| **Normalizar las historias a disco** | transcribir cada historia a markdown, una por una | archivos escritos y dictamen de qué fuente falta en cuál |
| **Armar el dossier de análisis** | escribir a mano la cabecera y la leyenda idénticas en decenas de archivos | rutas creadas, índice del lote, y qué queda por escribir con criterio |
| **Inventariar criterios de aceptación** | releer cada historia para enumerarlos | una fila por criterio, con su historia y su origen |
| **Cruzar criterios contra datos** | comprobar de memoria si cada caso tiene con qué ejecutarse | criterios sin dato, datos huérfanos, derivables colados. **Bloquea** |
| **Renderizar la solicitud al cliente** | reescribir el documento entero por cada corrección de forma | el markdown emitido desde la fuente de datos |

La aritmética de esta fase, medida en una sesión real de trece historias y 133.66 créditos:
**el 37% se fue reescribiendo documentos que ya estaban en disco, sin consultar una sola
fuente**, y otro tanto en transcripción mecánica. La causa raíz no era falta de conocimiento
sino una decisión de formato — la solicitud se trataba como prosa, así que cada corrección
obligaba a reescribirla entera. Declararla como datos y renderizarla convierte esos turnos
en ediciones de una línea.

Las dos últimas son además el ejemplo canónico del punto 7: **el renderizador no emite si el
cruce no pasa**. La auditoría dejó de ser algo que una persona tenía que exigir —lo exigió
dos veces, la segunda después del fallo— y pasó a ser una dependencia de la salida.

### 7. La forma fuerte: el artefacto es entrada de la herramienta, no una obligación que se comprueba

Aquí está el mecanismo que decide si un asset obligatorio se cumple o se ignora, y no es escribir mejor la obligación.

Lo verificado en campo: seis de cada diez artefactos que los assets declaraban obligatorios **no se crearon**, y nadie lo notó hasta auditarlo meses después. Los assets estaban bien escritos, marcados obligatorios, con su comprobación redactada. No bastó, y no iba a bastar: **una comprobación que el propio agente se autoaplica al final es una intención, no una garantía**.

Hay cuatro capas de exigibilidad, y sólo las dos primeras garantizan algo:

| Capa | Mecanismo | Qué garantiza |
|---|---|---|
| **1. Entrada obligatoria** | La herramienta **no funciona sin el artefacto** porque lo necesita para operar | Que exista, y en el momento correcto |
| **2. Puerta que bloquea** | Un comando comprueba presencia y devuelve código de salida distinto de cero, enganchado donde no se puede saltar | Que exista antes de que el trabajo aterrice |
| 3. Telemetría de carga | Se registra qué assets se activaron en la entrega | Detecta el incumplimiento **después** |
| 4. Texto en el asset | Descripción, etiqueta y sección de verificación | Sólo hace probable el cumplimiento |

**La capa 1 es la única que no se puede eludir, y es más barata que las otras.** En vez de pedir un artefacto y comprobar después si está, se diseña la herramienta para que **lo consuma**:

- El ejecutor resuelve qué correr **leyendo la matriz de cobertura**: sin matriz no sabe qué escenarios existen, luego no corre.
- El ejecutor exige la **firma de la auditoría en frío** del escenario: sin auditoría, se niega.
- El flujo de corrección parte de la **ficha**: sin ficha no hay entrada que procesar.
- La puerta de entrega lee el **manifiesto** y el **libro de aprendizajes**: sin ellos no puede emitir su veredicto.

Nadie olvida escribir la matriz de cobertura si es de donde el ejecutor saca qué correr. La obligación deja de ser papeleo y pasa a ser **una dependencia**, que es lo que la gente y los agentes sí respetan.

La capa 2 cubre lo que la 1 no alcanza: comprobar que el conjunto de artefactos obligatorios existe, con código de salida que bloquea, enganchado al pre-commit y a la puerta de entrega. Es la verificación determinista más trivial que hay —¿existen estos archivos?— y **es la que vuelve reales todas las demás reglas del chapter**.

Ésta **no hay que construirla en cada proyecto: viene con el chapter**, en `scripts/` de `[[calidad-delivery-gate-contract]]`, autocontenida y con la lista de artefactos dentro. Y la lista no se mantiene a mano: la auditoría de la fuente del chapter falla si un asset obligatorio prescribe un artefacto ausente de ella, de modo que declarar una obligación nueva sin hacerla comprobable deja de ser posible.

La capa 3 aprovecha telemetría que muchos entornos ya emiten al activar un skill: permite responder "¿se cargó el asset obligatorio en esta entrega?" sin preguntarle al agente. Detecta tarde, pero detecta.

### 8. Registrar el hueco cuando no se puede construir

Si el proyecto no permite construirla —restricción del cliente, falta de permisos, tiempo—, **se registra como hueco de capacidad** con lo que costaría y lo que ahorraría, y se sigue a mano. Un hueco documentado se cierra en la siguiente entrega; uno no documentado se paga para siempre.

## Restricciones

- **NUNCA** construir una herramienta sin haber consultado el mapa de capacidades. Duplicar lo que el arquetipo ya resuelve es peor que no tenerlo: crea una segunda fuente de verdad.
- **NUNCA** dejar una herramienta en un directorio temporal, en un archivo de trabajo o sólo en la conversación. Si no está en el proyecto, documentada y registrada, no existe.
- **NUNCA** trasladar a una herramienta una decisión que exige criterio de calidad. Aflojar una aserción, decidir que un fallo es del producto o dar por buena una cobertura parcial no se automatizan; ver los guardarraíles de `[[calidad-test-self-healing]]`.
- **NUNCA** hacer que una herramienta devuelva la salida cruda. Si devuelve el registro entero, se construyó el gasto en vez de eliminarlo.
- **NUNCA** usar una herramienta propia para saltarse una puerta del chapter. Una herramienta que "arregla" el conteo de cobertura o silencia un artefacto faltante es una violación de anti-cheating.
- La construcción de herramientas **no se hace en medio de la estabilización de un escenario**: se hace en la fase de capacidades, o al detectar el hueco por segunda vez, como trabajo declarado.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | antes de resolver cualquier tarea determinista y repetida se consultó el mapa de capacidades del proyecto, y la respuesta (existe / no existe) quedó registrada | Bloqueado: se hizo a mano trabajo determinista sin comprobar si el proyecto ya lo resolvía. Ya ocurrió en campo estabilizar una certificación entera de a un escenario teniendo el ejecutor por lotes en el mismo repositorio. |
| 2 | toda herramienta construida quedó dentro del proyecto, documentada y registrada con su invocación, y .evidence/tooling-gaps.md declara qué resuelve el proyecto y qué hueco queda | Bloqueado: hay una herramienta construida que la siguiente sesión no va a encontrar. Un script suelto que nadie registra se vuelve a escribir en la siguiente historia. |
| 3 | la salida de cada herramienta es acotada y legible por máquina; ninguna vuelca su registro completo al razonamiento del agente | Bloqueado: una herramienta devuelve la salida cruda. El coste no es ejecutar: es que la salida entre al contexto y se reenvíe en cada paso posterior. |
| 4 | todo artefacto que un asset obligatorio exige es entrada de alguna herramienta o está cubierto por una puerta que bloquea; ninguno depende sólo de que el agente lo recuerde | Bloqueado: hay una obligación sostenida sólo por texto. Ya se midió que seis de cada diez artefactos obligatorios no se creaban y nadie lo notaba. Se convierte en entrada de herramienta o en puerta con código de salida. |

## Cross-links

`[[calidad-repo-capability-discovery]]`, `[[calidad-test-execution-orchestration]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-cold-audit-before-execution]]`, `[[calidad-cross-platform-learning-propagation]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-human-fix-request-protocol]]`, `[[calidad-test-self-healing]]`, `[[calidad-measure-before-proposing]]`, `[[calidad-pre-development-artifacts-continuity]]`.
