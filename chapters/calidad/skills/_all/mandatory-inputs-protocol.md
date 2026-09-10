---
id: calidad-mandatory-inputs-protocol
version: 2.2.0
scope: chapter
type: skill
chapter: calidad
description: Define los inputs obligatorios y opcionales que el usuario debe entregar antes de generar cualquier prueba automatizada.
tags: [inputs, protocol, spec, firma, user-story, enforcement, mandatory]
enforcement: mandatory
verification:
  - check: "los 4 inputs base (intent, project_name, output_path, spec/ui_source/apk_path) + modo de operación confirmados explícitamente por el usuario"
    failure_message: "Bloqueado: faltan inputs obligatorios o el modo de operación no fue confirmado. No se puede generar sin contrato de entrada completo."
  - check: "project_name matchea ^[a-z][a-z0-9-]*[a-z0-9]$ y output_path es ruta absoluta verificada"
    failure_message: "Bloqueado: project_name u output_path no cumplen las reglas formales del protocolo."
  - check: "spec entregado como contenido completo, no como ruta de archivo"
    failure_message: "Bloqueado: se requiere el contenido completo del spec, no la ruta del archivo."
  - check: "risk_map confirmado por usuario o default HIGH reportado explícitamente para revisión"
    failure_message: "Bloqueado: no se puede priorizar sin risk_map confirmado o default HIGH declarado al usuario."
  - check: "sut_available, data_available y (front/mobile) locator_map resueltos vía SUT readiness gate antes de validar spec"
    failure_message: "Bloqueado: no se resolvió si el desarrollo/datos/mapeo de locators están disponibles. Aplicar el SUT readiness gate."
  - check: "checkpoint de datos de prueba emitido y confirmado por el usuario antes del STRATEGY.md, derivado de los escenarios planificados (entidad + estado exigido), con validación cruzada contra el catálogo y con lo faltante comunicado al QA con dueño y fecha"
    failure_message: "Bloqueado: no se confirmaron los datos de prueba concretos. Generar con datos sin confirmar produce una suite que falla por dato y no por defecto."
  - check: "la matriz de cobertura de todas las plataformas del alcance quedó escrita en .evidence/coverage-declared.json y aprobada antes de generar código"
    failure_message: "Bloqueado: se empezó a generar sin congelar la cobertura. Diseñar escenarios sobre la marcha deja criterios sin cubrir y los diseña con los insumos lejos."
  - check: "se emitió .evidence/input-sufficiency.json evaluando suficiencia y no solo presencia, con el hueco concreto por entrada incompleta"
    failure_message: "Bloqueado: se dio un insumo por cubierto porque llegó. La historia llega casi siempre y casi nunca basta; sin dictamen por entrada, el agente descubre lo que falta ejecutando."
  - check: "cada criterio de aceptación es verificable: condición observable, plataformas donde aplica, estado de entrada exigido y resultado observable con su copy exacto"
    failure_message: "Bloqueado: hay criterios que no se pueden convertir en aserción sin consultar a una persona. Eso no es un criterio, es una intención, y se resuelve antes de generar."
---

# Mandatory Inputs Protocol — Contrato de Entrada Antes de Generar

## Cuándo aplicar

Aplica este skill **al inicio** de cualquier solicitud (paso 1 de `[[calidad-route-test-generation]]`). Su objetivo es asegurar que todos los insumos necesarios están presentes y bien formados antes de invocar `[[calidad-spec-validation]]` o cualquier workflow de generación.

## Inputs comunes y su semántica

| Input          | Obligatoriedad                                  | Qué es                                                                                            | Cómo se usa                                                                                                  |
|----------------|-------------------------------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `intent`       | Obligatorio                                     | Texto en lenguaje natural que describe qué quiere el usuario                                      | Insumo de `[[calidad-intent-detection]]` para elegir framework                                               |
| `project_name` | Obligatorio                                     | Nombre del proyecto en **kebab-case**                                                             | Nombre de carpetas, artefactos Maven/npm, identificadores en reportes                                        |
| `output_path`  | Obligatorio                                     | Ruta **absoluta** del directorio donde se escriben los archivos                                   | Destino del streaming de archivos (`[[calidad-streaming-files-protocol]]`)                                   |
| `spec`         | Obligatorio (Karate/K6)                         | **Contenido COMPLETO** del OpenAPI/Swagger/WSDL (no la ruta del archivo)                          | Input de `[[calidad-spec-validation]]`; fuente única para endpoints, schemas y auth                          |
| `base_url`     | A veces obligatorio                             | Base URL del servicio                                                                             | Necesario si el spec **no** lo declara (algunos Swagger 2.0 sin `host`, WSDL sin `<soap:address>` accesible) |
| `user_story`   | Opcional (recomendado · obligatorio en Karate brownfield cuando el cliente impone convenciones cliente-específicas) | Historia de usuario (formato Gherkin libre o As-a/I-want/So-that) con criterios de aceptación   | Naming de escenarios, prioridad de endpoints, criterios negativos                                            |
| `firma`        | Opcional (altamente recomendado)                | Documento técnico del servicio: reglas de negocio, ejemplos de datos reales, terminología, SLAs   | Enriquecimiento de payloads, escenarios `@negative`, vocabulario en nombres de escenarios                    |
| `extra_params` | Opcional                                        | JSON con parámetros framework-specific                                                            | Ej.: `{"include_login_case": true}` para Appium, `{"thresholds": {"http_req_duration": "p(95)<500"}}` para K6 |
| `sut_available` | Obligatorio (pregunta sí/parcial/no)           | ¿El desarrollo está desplegado y accesible?                                                       | Resuelve `execution_target: real | hybrid | mock` vía `[[calidad-sut-readiness-gate]]` (paso 1.5 del router)  |
| `data_available` | Obligatorio (**no es sí/no**: matriz de suficiencia) | ¿Existen los datos **en el estado que exige cada escenario planificado**? | Resuelve `data_strategy: real \| synthetic` (`[[calidad-test-data-management]]`) y produce la lista de lo que el QA debe gestionar, con dueño y fecha |
| `locator_map`  | Condicional (front/mobile; **obligatorio** si `execution_target != real`) | Mapeo acordado QA+dev de identificadores UI (`data-testid` / accessibility ids)  | Fuente única de selectores pre-desarrollo; formato y contrato en `[[calidad-ui-locator-map-contract]]`        |
| `test_credentials` | Obligatorio cuando el flujo requiere autenticación | Usuario de prueba vigente y su contraseña                                    | Se cargan por el mecanismo del proyecto; **jamás literales en el código** ni escritas en evidencia            |
| `test_data_entities` | Obligatorio cuando el escenario opera sobre entidades concretas | Los identificadores reales bajo prueba (cuenta, tarjeta, producto, contrato)  | Se validan contra el catálogo de datos del proyecto antes de generar                                          |

## Presencia no es suficiencia

La tabla de arriba dice **qué debe llegar**. No dice **qué debe contener**, y ahí está el hueco que más caro sale: en campo llegó la historia, se dio el insumo por cubierto, y el agente terminó descubriendo el recorrido ejecutando.

> **La historia de usuario es obligatoria siempre, y casi nunca es suficiente por sí sola.**

Por eso el gate no evalúa presencia sino **suficiencia, entrada por entrada**, y cuando algo falta **nombra la pieza, no el documento**. "El criterio 7 no es verificable: dice que el sistema responde correctamente y no dice qué ve la persona" es accionable en un mensaje. "Falta la historia" devuelve la pelota sin información.

### Qué se espera de los criterios de aceptación

Obligatorios para los tres frentes —web, móvil y backend—, y con contrato de verificabilidad. Cada criterio declara:

| Campo | Por qué |
|---|---|
| **Condición observable**, no una cualidad | "Responde correctamente" no se convierte en aserción sin preguntarle a alguien |
| **En qué plataformas aplica** | O "todas", pero dicho. Es lo que decide si hay uno o tres escenarios |
| **El estado de entrada que exige** | El dato en qué condición; alimenta el checkpoint de datos de abajo |
| **El resultado observable, con el copy exacto** si es texto | Sin copy exacto, la aserción se escribe de memoria y falla por formato |
| **Qué queda fuera de alcance** | Un criterio sin frontera se interpreta ancho y se paga en escenarios que nadie pidió |

Un criterio que no se puede convertir en aserción sin consultar a una persona no es un criterio: es una intención, y el gate lo reporta **por su número**.

### Dos insumos propios del front

Cuando la entrega es web o móvil, dos entradas más, cada una con su asset y su contrato:

- **El recorrido funcional detallado** — `[[calidad-functional-flow-input]]`. Secuencia de pantallas, bifurcaciones **con la condición que las dispara**, pantallas intermitentes, desenlaces con su copy y su duración, y precondiciones. Puede vivir en la historia o aparte; lo que no puede es no existir.
- **Las fuentes de interfaz** — `[[calidad-ui-source-contract]]`. `ui_source` no es una fuente sino una familia, y cada miembro responde una pregunta distinta: el diseño estático da el flujo y los copys pero no el árbol; el design system da el árbol pero no el flujo. Se declara **cuál cubre el eje de flujo y cuál el de estructura**.

### Lo que valida la máquina no lo razona el agente

Buena parte de este contrato es **forma, no criterio**: que el nombre de proyecto cumpla su patrón, que la ruta de salida sea absoluta, que el spec llegue como contenido y no como ruta, que cada entrada del dictamen traiga sus campos. Eso lo comprueba la puerta —que valida estructura además de existencia— y **no debe gastarse en razonamiento**, igual que le exigimos al agente con las corridas.

Lo que sí exige juicio y no puede validarse por esquema es una lista corta: si un criterio de aceptación se puede convertir en aserción, si una fuente responde el eje que se le pide, y si lo que falta bloquea o se acepta con precio. Eso va al verificador con contexto limpio (`[[calidad-fresh-context-verification]]`), no a la autoevaluación de quien acaba de escribirlo.

### El dictamen de suficiencia

El resultado de esta fase es un artefacto, no una impresión: `.evidence/input-sufficiency.json`, con una fila por entrada y cuatro campos.

| Campo | Contenido |
|---|---|
| **Qué se espera** | El contrato de esa entrada |
| **Qué llegó** | Presente, parcial o ausente — y de qué fuente |
| **Qué falta exactamente** | La pieza, no el documento |
| **Qué pasa si no llega** | Detener · degradar con precio · pedir, y **de dónde puede venir** |

Ese último campo es el que vuelve accionable el dictamen: no dice "falta el mapa de identificadores", dice "falta, y puede salir del repositorio de front, del design system o de un acuerdo con desarrollo". Y el precio de degradar no es retórico: sale del histórico de la cuenta. Ver `[[calidad-sut-readiness-gate]]`, que es quien emite el dictamen y quien registra el riesgo aceptado.

## Checkpoint de datos de prueba (antes del STRATEGY.md)

Los datos concretos con los que se va a ejecutar **son un insumo obligatorio**, no un detalle a resolver durante la generación. Verificado en campo: el usuario tuvo que adelantarse a darlos, y aun así uno de los identificadores no existía en el catálogo del proyecto sin que el agente lo detectara — la suite habría fallado por dato, no por defecto.

Antes de emitir el `STRATEGY.md`, emitir esta tabla y **esperar confirmación explícita**:

| Dato | Valor detectado en el proyecto | Valor indicado por el usuario | Estado |
|---|---|---|---|
| Usuario de prueba | `<el que usan los tests existentes>` | `<el que indicó el usuario>` | pendiente |
| Contraseña | recibida (no se muestra) | recibida | pendiente |
| Entidad bajo prueba | `<las disponibles en el catálogo>` | `<la indicada>` | pendiente |

**Validación cruzada obligatoria.** Si el valor que da el usuario no aparece en el catálogo de datos del proyecto, se **detiene** y se pregunta, listando los disponibles: *"no encontré la entidad X para el usuario Y; las disponibles son [...]. ¿Usamos una de estas o actualizamos el catálogo?"*. Aceptar el valor sin cruzarlo es la vía directa a una suite roja por dato.

**La tabla de arriba es el mínimo, no el checkpoint completo.** Confirmar quién es el usuario y qué entidad se usa no dice si esa entidad está **en el estado que el escenario necesita**: una tarjeta que existe pero sin movimientos en tránsito no sirve para el escenario que valida movimientos en tránsito. Por eso el checkpoint se emite derivado de los escenarios planificados, con una fila por dato requerido y su estado exigido, y **lo que falte se le comunica al QA en el chat con dueño y fecha** — porque conseguir un dato en el ambiente de un cliente puede tardar días. Procedimiento, plantilla del mensaje y la diferencia entre mock (se sintetiza y se declara) y software ya desarrollado (bloqueo con fecha) en `[[calidad-test-data-management]]` (consultar `references/data-sufficiency-gate.md` en su subfolder).

Las contraseñas se marcan como recibidas y **nunca** se muestran, se transcriben a un asset, al `STRATEGY.md` ni a `.evidence/`.

## Todo insumo entregado se lee COMPLETO y se declara qué se extrajo

Un insumo que el usuario entrega es una instrucción, no un adorno. Antes de generar nada, emitir una **tabla de extracción** —una fila por insumo— con: qué es, qué se extrajo de él y dónde se usará.

| Insumo | Qué se extrajo | Dónde se usa |
|---|---|---|
| `locator-map.json` | 13 pantallas, 173 identificadores, convención `semantics_identifier`, bloque `resolution_verified` con la estrategia Android | Targets, prototipo, gate de paridad |
| Prototipo interactivo (HTML) | 82 textos exactos, modelo de datos, formato de moneda, grafo de navegación | Catálogo de textos, datos del prototipo, orden de pantallas |
| … | … | … |

Reglas duras:

- **Leer el archivo entero**, no su primera pantalla. Los bloques que resuelven el trabajo suelen estar al final (verificado en campo: el `locator-map.json` traía el bloque con la estrategia de locators correcta y el agente pasó cinco turnos redescubriéndola por ensayo y error).
- **Un insumo sin fila en la tabla es un insumo ignorado** → blocker. Si de verdad no aporta, se declara explícitamente por qué.
- **Volver a los insumos durante el trabajo**, no solo al inicio: ante un fallo de datos, textos, montos o navegación, el insumo original manda sobre la inferencia. En campo, un prototipo interactivo entregado como insumo se abrió una sola vez, antes de escribir la estrategia, y nunca más — contenía la respuesta a cinco de los diecinueve problemas que costaron la sesión.
- Los valores del insumo **se copian, no se recuerdan**: montos, textos y rutas se transcriben del archivo, no de memoria.

## Reglas de uso

1. **Lee la `firma` ANTES de analizar el spec.** La firma te da el dominio, las reglas de negocio y los valores reales para construir payloads creíbles. Sin ese contexto, las pruebas terminan siendo "happy-path inventado".
2. **Si `user_story` está presente, los escenarios deben nombrarse con su lenguaje de negocio.** Ejemplo: si la historia habla de "cliente Pyme", el escenario es `"Cliente Pyme consulta su saldo disponible"`, no `"GET /accounts/{id} returns 200"`.
3. **Si la `firma` define reglas no presentes en el spec** (ej.: "un cliente no puede tener más de 3 direcciones activas") → **genera escenarios `@negative` aunque el spec no las indique**. La firma es fuente de verdad de negocio incluso cuando el contrato técnico no la refleja.
4. **NUNCA inventes** reglas, headers, valores enum, mensajes de error o flujos que no estén ni en el spec ni en la firma. Si falta información crítica, **pregunta**; no rellenes.
5. **Validación de `project_name`**: debe matchear `^[a-z][a-z0-9-]*[a-z0-9]$`. Si trae espacios, mayúsculas o snake_case, rechaza y solicita corrección.
6. **Validación de `output_path`**: debe ser absoluta. Si es relativa, rechaza. Antes de escribir, verifica que el directorio padre existe.
7. **Validación de `spec`**: si el usuario pasa una ruta de archivo en lugar de contenido, rechaza con: *"se requiere el contenido completo del spec, no la ruta del archivo."*

## Flujo de recolección

```
1. Pedir al usuario los obligatorios faltantes, uno por uno o en bloque (preferir bloque para no fragmentar).
2. Si un input está incompleto → indicar exactamente QUÉ falta, no devolver "está incompleto".
3. Resolver el SUT readiness gate ([[calidad-sut-readiness-gate]]): sut_available, data_available y (front/mobile) locator_map. El resultado puede endurecer los inputs restantes.
3.5. En brownfield, ejecutar [[calidad-repo-capability-discovery]] y emitir el checkpoint de datos de prueba con validación cruzada contra el catálogo del proyecto.
4. Confirmar opcionales relevantes según framework detectado (firma, user_story, extra_params).
5. Para proyectos con convenciones cliente-específicas detectadas (ver `[[calidad-karate-brownfield]]` y su reference `client-specific-conventions.md`), aplicar reglas adicionales descritas allí.
6. Solo cuando TODOS los obligatorios están presentes → pasar el control a [[calidad-spec-validation]].
```

### Inputs para la ruta funcional

Los intents funcionales (análisis/refinamiento de HUs, diseño de casos, estrategia/plan) NO usan la tabla de arriba: su contrato de entrada lo define cada workflow funcional (`[[calidad-analyze-and-refine-stories]]`, `[[calidad-design-test-cases]]`, `[[calidad-build-test-strategy-and-plan]]`). Común a los tres: `stories_source`/`contexto_fuente` (IDs o queries del ALM vía `[[calidad-alm-mcp-integration]]`, o el contenido pegado) y `output_path`. `spec`, `sut_available` y `locator_map` no aplican salvo que el flujo derive en automatización (re-entrada al router).

**Que no usen la tabla de arriba no significa que no tengan contrato.** Durante mucho tiempo eso se leyó como que la ruta funcional no tenía compuerta de entrada, y el resultado fue que toda la maquinaria de suficiencia de este documento se quedó del lado de la automatización — mientras la fase que decide qué se va a poder probar arrancaba sin declarar nada.

El contrato de `[[calidad-analyze-stories-and-request-data]]` —la ruta que va de las historias a la solicitud de datos— añade cinco entradas propias. Las cinco son las que faltaron en la sesión medida, y cada una produjo su turno de reproceso:

| Input | Qué es | Lo que cuesta que falte |
|---|---|---|
| `fuentes_de_arquitectura` | Dónde vive la arquitectura de estos componentes **en esta cuenta**, o la declaración de que no existe | El agente la busca en la herramienta que suele funcionar en otros clientes. Un turno |
| `mapa_de_capas` | Qué repositorio prueba qué capa en esta cuenta | La estrategia reparte los criterios por dónde se ven, no por dónde viven. Un turno |
| `ambiente_objetivo` | A qué ambiente se refieren los datos | Una solicitud sin ambiente es una que alguien puede ejecutar en producción |
| `audiencia_de_la_solicitud` | Quién recibe el documento y qué conoce | Se escribe para quien conoce las historias, y lo recibe quien no. Reescritura completa |
| `capacidades_de_qa` | Qué puede provisionar el equipo por su cuenta en este producto | Se le piden al cliente datos que el equipo se crea solo. Dos turnos |

Las cinco son **conocimiento de la cuenta**, no del chapter: se consultan antes de empezar. Si la cuenta no las tiene documentadas, preguntarlas una vez y registrarlas ahí es lo que hace que dejen de costar. Y aplica la misma regla que al resto del contrato: se evalúa **suficiencia**, y lo que falte se nombra por la pieza — "no sé qué repositorio prueba la capa de servicios" es accionable; "falta contexto" no.

Cruce con la `user_story` de esta tabla: si la HU entregada como input de automatización está visiblemente rota (sin CA, ambigua), ofrecer el análisis funcional (`[[calidad-funcional-story-analysis]]`) ANTES de generar código — mejora el insumo en vez de generar sobre él.

### K6-specific inputs

Para proyectos K6, además de los inputs base de la tabla anterior, el agente DEBE completar el checklist K6-específico (perfil de carga por escenario, dependencias externas, disponibilidad objetivo, data de prueba, endpoint objetivo vs auxiliares, volumen esperado, restricciones de ambiente). Ver [[calidad-k6-greenfield]] (consultar `references/k6-discovery-checklist.md`).

Sin este checklist, K6 no puede generar `options.stages` ni `options.thresholds` defendibles y debe degradar a `scaffold-only`.

## Overrides por convenciones cliente-específicas

Algunos clientes/proyectos imponen overrides sobre los inputs opcionales. Patrón típico: clientes con convenciones brownfield estrictas (ver `[[calidad-karate-brownfield]]` y su reference `client-specific-conventions.md`) elevan `user_story` y `firma` a obligatorios.

| Escenario                                                            | Skill / asset                      | Inputs que pasan a obligatorios                                                                                                                                       |
|----------------------------------------------------------------------|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Karate brownfield con convenciones cliente-específicas detectadas    | `[[calidad-karate-brownfield]]`            | `user_story` y `firma` son **obligatorios** (no opcionales). Convenciones genéricas detalladas en el reference `client-specific-conventions.md` dentro del skill `karate-brownfield`. |
| Pruebas antes del desarrollo (`execution_target: mock` o `hybrid`)   | `[[calidad-sut-readiness-gate]]`           | Karate/K6: `spec` con **response schemas completos y examples**. Playwright: fuente UI + `locator_map`. Appium: `locator_map` con accessibility ids. Matriz completa en el skill del gate. |

### Pattern para nuevos overrides

Cuando un cliente o proyecto necesite endurecer inputs:

1. Documentar la regla en el SKILL del framework correspondiente (por ejemplo `karate-brownfield/SKILL.md` o un reference de convenciones cliente-específicas).
2. Apuntar el override en la tabla de arriba con: escenario, skill o asset que lo define, lista de inputs que se vuelven obligatorios.
3. Si el override aplica también a la validación de spec o al flujo de generación, mencionarlo en el skill de framework, no acá: este documento sólo concentra el pointer.

## La cobertura se congela antes de generar, y para todas las plataformas

Diseñar los escenarios sobre la marcha —unos al principio, otros cuando toca la plataforma siguiente— tiene dos consecuencias, y las dos se pagan tarde.

La primera es de **cobertura**: en una entrega larga, con el contexto ya degradado por cientos de intercambios, el agente da por terminada la historia porque ejecutó todo lo que había creado, sin recordar que quedaron criterios sin escenario. Verificado en campo, exactamente así.

La segunda es de **calidad de diseño**: los escenarios que se diseñan al final se diseñan con los insumos lejos. La historia, el diseño y el contraste entre ambos están más frescos que nunca justo después de la fase de insumos; ese es el momento de decidir qué se prueba, no tres días después.

**Entregable obligatorio antes de escribir una línea de código: la matriz de cobertura completa, para todas las plataformas del alcance, aprobada por la persona.**

| Criterio | Plataformas | Escenario propuesto | Dato que exige | Reuso | Etiqueta |
|---|---|---|---|---|---|

Reglas de la matriz:

- **Cubre todas las plataformas del alcance desde el inicio**, aunque se estabilicen en serie. Que la ejecución sea secuencial no obliga a que el diseño lo sea, y diseñar todo junto es lo que revela qué escenarios son el mismo caso en tres canales.
- **Se vuelca al artefacto de pruebas como esqueletos** con etiqueta de pendiente. Un escenario que no existe como archivo no existe como compromiso.
- **La cobertura se mide contra la matriz, no contra la memoria.** Al cierre de cada sesión y en la entrega, se compara lo declarado contra lo entregado y la diferencia se reporta. La comparación es determinista y la hace una herramienta del proyecto (`[[calidad-deterministic-work-to-tooling]]`); confiarla al recuerdo del agente es exactamente lo que produce historias cerradas con criterios sin cubrir.
- **Todo cambio de alcance se refleja en la matriz** en el mismo turno en que se acuerda. Un criterio que sale del alcance sale de la matriz con su razón, no desaparece en silencio.

## Restricciones

- **NUNCA proceder** sin los inputs obligatorios resueltos.
- **NUNCA mezclar** convenciones cliente-específicas detectadas en un proyecto con proyectos genéricos de otros clientes.
- **NUNCA asumir** valores por defecto para `base_url`, headers de auth o entornos: si falta, se pregunta.
- **NUNCA dar por vigentes** los datos de prueba que encuentres en el proyecto sin confirmarlos: un catálogo puede estar desactualizado y el usuario es quien sabe qué sigue activo en el ambiente.
- **NUNCA escribir credenciales** en el código generado, en el `STRATEGY.md` ni en la evidencia.
- Encadena con `[[calidad-spec-validation]]` (paso siguiente) y con `[[calidad-intent-detection]]` (paso previo).

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | los 4 inputs base (intent, project_name, output_path, spec/ui_source/apk_path) + modo de operación confirmados explícitamente por el usuario | Bloqueado: faltan inputs obligatorios o el modo de operación no fue confirmado. No se puede generar sin contrato de entrada completo. |
| 2 | project_name matchea ^[a-z][a-z0-9-]*[a-z0-9]$ y output_path es ruta absoluta verificada | Bloqueado: project_name u output_path no cumplen las reglas formales del protocolo. |
| 3 | spec entregado como contenido completo, no como ruta de archivo | Bloqueado: se requiere el contenido completo del spec, no la ruta del archivo. |
| 4 | risk_map confirmado por usuario o default HIGH reportado explícitamente para revisión | Bloqueado: no se puede priorizar sin risk_map confirmado o default HIGH declarado al usuario. |
| 5 | sut_available, data_available y (front/mobile) locator_map resueltos vía SUT readiness gate antes de validar spec | Bloqueado: no se resolvió si el desarrollo/datos/mapeo de locators están disponibles. Aplicar el SUT readiness gate. |
| 6 | checkpoint de datos de prueba emitido y confirmado por el usuario antes del STRATEGY.md, derivado de los escenarios planificados (entidad + estado exigido), con validación cruzada contra el catálogo y con lo faltante comunicado al QA con dueño y fecha | Bloqueado: no se confirmaron los datos de prueba concretos. Generar con datos sin confirmar produce una suite que falla por dato y no por defecto. |
| 7 | la matriz de cobertura de todas las plataformas del alcance quedó escrita en .evidence/coverage-declared.json y aprobada antes de generar código | Bloqueado: se empezó a generar sin congelar la cobertura. Diseñar escenarios sobre la marcha deja criterios sin cubrir y los diseña con los insumos lejos. |
| 8 | se emitió .evidence/input-sufficiency.json evaluando suficiencia y no solo presencia, con el hueco concreto por entrada incompleta | Bloqueado: se dio un insumo por cubierto porque llegó. La historia llega casi siempre y casi nunca basta; sin dictamen por entrada, el agente descubre lo que falta ejecutando. |
| 9 | cada criterio de aceptación es verificable: condición observable, plataformas donde aplica, estado de entrada exigido y resultado observable con su copy exacto | Bloqueado: hay criterios que no se pueden convertir en aserción sin consultar a una persona. Eso no es un criterio, es una intención, y se resuelve antes de generar. |
