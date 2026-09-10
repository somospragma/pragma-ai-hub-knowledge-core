---
id: calidad-sut-readiness-gate
version: 2.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Gate que emite el dictamen de preparación del sistema antes de gastar la primera corrida: si está listo para que un agente lo automatice de forma determinista, qué falta exactamente, de dónde puede venir y qué cuesta seguir sin ello. Resuelve execution_target, data_strategy y qué inputs pasan a obligatorios por stack en modo pre-desarrollo."
tags: [sut-readiness, shift-left, mock, mockoon, execution-target, gate, mandatory, determinism]
enforcement: mandatory
verification:
  - check: "execution_target (real/mock/hybrid), data_strategy (real/synthetic) y, para front/mobile, locator_map resueltos explícitamente con el usuario antes de validar spec o generar código"
    failure_message: "Bloqueado: no se resolvió la disponibilidad del SUT, de los datos de prueba y del mapeo de locators. Sin este gate no se puede garantizar que los tests sean ejecutables ni deterministas."
  - check: "si execution_target es mock o hybrid, los inputs que la matriz por stack marca como obligatorios están presentes (spec con response schemas para API, locator map + fuente UI para front/mobile); ante locator_map ausente NO se generó código de UI salvo override explícito registrado como waived"
    failure_message: "Bloqueado: el modo pre-desarrollo exige insumos adicionales que no fueron entregados. Sin locator map no se generan page objects salvo waiver explícito del usuario. Consultar la matriz de obligatoriedad por stack."
  - check: "si execution_target es mock o hybrid, el delivery gate declara certification: pending_real_integration"
    failure_message: "Bloqueado: resultados contra mock no pueden presentarse como certificación del SUT."
  - check: "se emitió el dictamen de preparación en .evidence/input-sufficiency.json antes de generar, con veredicto por dimensión y, en cada ausencia, de dónde puede venir y qué cuesta seguir sin ella"
    failure_message: "Bloqueado: se iba a construir sin decir si el sistema está en condiciones. Tres variables repartidas entre la estrategia y el cierre no son un dictamen: nadie las lee antes de gastar la primera corrida."
---

# SUT Readiness Gate — Probar Antes de que el Desarrollo Exista

## Principio

El Chapter Calidad permite construir y validar pruebas **antes de que la funcionalidad esté terminada o desplegada** (shift-left). Para eso, la ausencia del SUT, de los datos de prueba o de los identificadores de UI no detiene la construcción: se sustituyen con mocks de servicios (`[[calidad-service-virtualization-mockoon]]`), datos sintéticos deterministas (`[[calidad-test-data-management]]`) y un contrato de mapeo de locators (`[[calidad-ui-locator-map-contract]]`).

La regla maestra que gobierna todo lo anterior: **los mocks validan la construcción del test, nunca certifican el SUT**. Un test que pasa contra mock demuestra que está bien diseñado, es determinista y ejecuta end-to-end; no demuestra nada sobre la integración real. La certificación formal exige re-ejecutar contra las integraciones reales, y ese reemplazo debe ser **solo configuración, cero cambios en el código de los tests**.

## Cuándo aplicar

Paso 1.5 del router `[[calidad-route-test-generation]]`: inmediatamente después de recolectar los inputs base (`[[calidad-mandatory-inputs-protocol]]`) y **antes** de validar el spec, porque el resultado de este gate muta la obligatoriedad de los demás inputs.

También aplica cuando se invoca un skill de stack directamente (sin router): el skill debe resolver estas preguntas antes de generar.

## Las tres preguntas del gate

Preguntar explícitamente al usuario; nunca asumir:

1. **¿El desarrollo está desplegado y accesible desde donde correrán los tests?**
   - `sí` → `execution_target: real`
   - `parcialmente` (algunos servicios/pantallas listos, otros no) → `execution_target: hybrid`
   - `no` (los tests deben estar listos antes del desarrollo) → `execution_target: mock`
2. **¿Existen datos de prueba en ese ambiente (o un catálogo de datasets del cliente)?**
   - `sí` → `data_strategy: real` (respetando anonimización, ver `[[calidad-test-data-management]]`)
   - `no` → `data_strategy: synthetic` — datos generados con Faker + seed fijo; si hay mock de servicios, los mismos datos alimentan sus data buckets para coherencia end-to-end.
   - **Precedencia de fuentes de datos** (esta pregunta se hace PRIMERO, no al final): (1) data real/catálogo del cliente, (2) `examples` del spec y valores de la firma, (3) sintética Faker + seed determinista. **NUNCA inventar datos ad-hoc "con criterio del agente"**: un dato sin seed no es reproducible y rompe el determinismo de la suite.
3. **(Solo Playwright/Appium) ¿Existe un mapeo acordado de identificadores/localizadores de los elementos UI?**
   - `sí` → `locator_map: provided` — los selectores del proyecto salen del mapa, no se inventan.
   - `no` → `locator_map: missing` — si `execution_target != real`, es un insumo obligatorio: sin él los tests fallarán cuando llegue el desarrollo por drift de identificadores. **La pregunta no es decorativa: sin mapa NO se generan page objects ni se declara la corrida completa** — el flujo se detiene con blocker `locator_map_missing`. El usuario puede optar por continuar sin mapa SOLO con confirmación explícita, que se registra como `locator_map: waived` (riesgo aceptado) en el delivery gate. Ver `[[calidad-ui-locator-map-contract]]`.

Las tres respuestas se registran en el `STRATEGY.md` (`[[calidad-pre-design-strategy-document]]`, sección "Execution target y plan de switchover") y en el bloque final `[[calidad-delivery-gate-contract]]`.

## Matriz por stack — viabilidad y obligatoriedad en modo pre-desarrollo

Cuando `execution_target` es `mock` o `hybrid`, estos insumos **pasan de opcionales/ausentes a obligatorios**. Si falta alguno marcado STOP, detener y solicitarlo; la construcción pre-desarrollo no es viable sin él.

| Stack | ¿Viable antes del desarrollo? | Inputs que pasan a obligatorios | Ejecutable contra mock |
|---|---|---|---|
| Karate | Sí — mock Mockoon como SUT | `spec` OpenAPI/Swagger/WSDL con **response schemas completos y examples** (sin schemas de respuesta el mock no es fiel → STOP) | Suite completa + smoke gate |
| K6 | Sí, **solo para validar construcción** | `spec` con response schemas + RNF/SLAs para thresholds | Solo smoke 1:1. Métricas de `load/stress/spike/soak` contra mock son inválidas — ver restricción abajo |
| Playwright | Sí — depende del camino front/back (ver `references/execution-modes-live-mocked-hybrid.md` de [[calidad-playwright-greenfield]]): con front (desplegado o levantable desde su repo local) el back se mockea; sin front ni back, camino oficial = construcción completa con ejecución diferida | Fuente UI (Figma u otra de `ui-source-priority`) + **locator map** (`[[calidad-ui-locator-map-contract]]`); sin ambos → STOP (continuar solo con override explícito `locator_map: waived`) | Con front: suite `@mocked`/`@hybrid` + smoke. Sin front: ninguna por el camino oficial; existe la opción opt-in de prototipo de front (solo a elección explícita del usuario, ver la reference de caminos) |
| Appium | Sí — con APK real (backend mockeado si permite override de base URL) o, sin APK, vía la opción opt-in de **app prototype Flutter**; camino oficial sin APK: scaffold + deferred locators con ejecución diferida | **Locator map** con identifiers acordados desde diseño (para Flutter: `semantics_identifier`); `user_story`/`test_cases` | Con APK: suite contra backend mock. Sin APK: opt-in prototipo Flutter en emulador (solo a elección explícita del usuario, requiere Flutter SDK — ver [[calidad-appium-screenplay-android]], [[calidad-mobile-locator-resolution]] (`references/flutter-under-appium.md`)); si no, health-check estático + `[[calidad-complete-deferred-locators]]` |

En **brownfield** (cualquier stack), el gate aplica solo a los tests nuevos de la corrida: los mocks jamás justifican modificar tests preexistentes ni la infraestructura existente (regla anti-cheating maestra del chapter).

## Qué activa cada resultado

- `execution_target: mock` → generar/levantar el mock con `[[calidad-service-virtualization-mockoon]]` antes del smoke gate; los tests apuntan al mock **solo vía configuración** (env/profile). Prompt de generación: `[[calidad-generate-mockoon-environment-prompt]]`. **El mock levantado cuenta como SUT alcanzable: el modo de operación default sigue siendo `full` (contra mock)** — NO degradar a `scaffold-only` por "falta de ambiente real"; `scaffold-only` queda solo para cuando ni el mock es viable (spec sin response schemas, Playwright sin front alguno, Appium sin APK).
- `execution_target: hybrid` → mock en proxy mode: rutas no listas se mockean, el resto pasa al backend real (partial mocking). Documentar qué rutas están mockeadas en el STRATEGY.md.
- `data_strategy: synthetic` → Faker con locale de la jurisdicción y `FAKER_SEED` fijo (`[[calidad-test-data-management]]`, `references/synthetic-data-faker.md`); el mismo seed alimenta los data buckets del mock (`--faker-seed` de Mockoon) para que test y mock generen datos coherentes.
- `locator_map: provided` → Playwright genera selectores `getByTestId` desde el mapa; Appium genera `Target` desde los identifiers del mapa (Flutter: `semantics_identifier` → `AppiumBy.id`). Al llegar el desarrollo, validar drift mapa vs DOM/jerarquía real **antes** de correr la suite (`[[calidad-ui-locator-map-contract]]`).
- **Prototipos opt-in (front web / app mobile)**: cuando no existe el front o la app, el usuario puede elegir explícitamente que el agente genere un prototipo desde el mapa de locators y las fuentes de UI para ejecutar la suite antes del desarrollo. **Descartable es el compilado, no el proyecto que lo construye**: el generador y sus fuentes son activos del producto que se conservan y crecen entre historias — ver `[[calidad-pre-development-artifacts-continuity]]` (recetas en las references de cada stack). NUNCA por defecto; siempre con la advertencia de fidelidad, `front_prototype`/`app_prototype: true` en `mock_evidence` y `certification: pending_real_integration`. Para móvil, **preguntar SIEMPRE antes con qué tecnología se construirá la app real** (Flutter / nativa Android / React Native / sin definir): el prototipo se construye con la **misma tecnología declarada** — lo que Appium "ve" (jerarquía de semántica Flutter, widgets nativos, o views RN con testID) depende de la tecnología, y un prototipo en otra distinta valida en falso y está prohibido. Tecnología sin definir → sin prototipo fiel posible: camino oficial (ejecución diferida). Flutter es el caso documentado en detalle ([[calidad-appium-screenplay-android]], [[calidad-mobile-locator-resolution]] (`references/flutter-under-appium.md`)).
- **La misma pregunta aplica al front web**: framework DOM (React/Angular/Vue...) → prototipo HTML plano; **Flutter Web** → prototipo Flutter Web (renderiza a canvas: no hay DOM de la UI, solo el árbol `flt-semantics` que además se activa al arranque — un prototipo HTML validaría selectores que la app real jamás tendrá). Si el producto es Flutter multiplataforma, un solo prototipo Flutter sirve para mobile y web. Regla y receta en [[calidad-playwright-greenfield]] (consultar `references/front-prototype-recipe.md`).
- La continuidad entre historias de prototipos y mocks —qué se conserva, qué se regenera, el manifiesto de estado y el refresco desde lo ya desplegado— se rige por `[[calidad-pre-development-artifacts-continuity]]`. Antes de construir nada se lee su manifiesto: reconstruir lo que ya existía es el desperdicio más caro de este modo.
- Todo prototipo pasa su **gate de paridad** antes de usarse (cada selector del locator map → exactamente una coincidencia) y respeta el **contrato de fidelidad** (replica lo que la app real publicará; PROHIBIDO ajustar su semántica/estructura para que una prueba pase — anti-cheating extendido al prototipo).

## El dictamen: listo o no, qué falta y qué cuesta seguir sin ello

Las tres preguntas resuelven variables. **El dictamen las convierte en algo que una persona lee y decide en un minuto**, que es lo que faltaba: hoy el resultado queda repartido entre la estrategia y el bloque de cierre, y nadie dice en voz alta si el sistema está en condiciones de ser automatizado.

Se emite **antes de escribir una línea** y se persiste en `.evidence/input-sufficiency.json`.

### Las cinco dimensiones que se dictaminan

| # | Dimensión | La pregunta |
|---|---|---|
| 1 | **Contrato de interfaz** | ¿Cómo nombra el robot lo que va a tocar? |
| 2 | **Alcanzabilidad y observabilidad** | ¿Puede llegar a ello y ver el resultado? |
| 3 | **Estado y datos** | ¿Puede poner al sistema en la condición que el caso exige? |
| 4 | **Determinismo del entorno** | ¿Dos corridas iguales dan lo mismo? |
| 5 | **Trazabilidad de salida** | ¿La corrida puede demostrar qué pasó? |

La segunda es la que ningún gate validaba y la que más caro sale: elementos sin identificador estable, texto que sólo existe en píxeles, listas navegables sólo a ciegas, desenlaces que desaparecen antes de poder leerlos.

### Qué significa cada dimensión por stack

| Stack | Contrato de interfaz | Alcanzabilidad | Estado y datos |
|---|---|---|---|
| **Karate** | Especificación con esquemas de respuesta **y ejemplos** | Endpoints del flujo expuestos, incluidos los de preparación | Datos, o endpoints para crearlos |
| **K6** | Lo anterior + umbrales derivados de requisitos no funcionales | Ambiente representativo y aislado | Volumen de datos suficiente |
| **Playwright** | Mapa de identificadores acordado y versionado | Texto de las aserciones expuesto en la capa de accesibilidad; en interfaz sobre lienzo, capa activable y controles con rol y nombre | Sesión y datos alcanzables por configuración |
| **Appium** (ambos) | Identificadores de accesibilidad declarados por elemento, **nunca derivados del texto visible** | Listas largas navegables con ancla de sección; desenlaces transitorios observables; pantallas protegidas contra captura declaradas | Precondiciones orquestables por API, no sólo a mano |
| **Funcional** | Criterios verificables | No aplica: no toca el sistema | No aplica |

### Qué bloquea y qué se puede aceptar con precio

| Dimensión | Karate | K6 | Playwright | Appium |
|---|---|---|---|---|
| Contrato de interfaz | **Detener** | **Detener** | Detener, con waiver explícito | Detener, con waiver explícito |
| Alcanzabilidad | Aviso | Aviso | **Aviso con precio** | **Aviso con precio** |
| Estado y datos | Detener si no hay dato ni forma de crearlo | ídem | ídem | ídem |
| Determinismo del entorno | Detener si no es alcanzable | **Detener** | Detener si no es alcanzable | ídem |
| Trazabilidad de salida | Aviso | Aviso | Aviso | **Aviso con precio** |

### El waiver lleva precio, y el precio sale del histórico

Aceptar seguir sin una entrada es legítimo y la decisión es de la persona. Lo que no es legítimo es **presentarlo como gratis**. El dictamen acompaña cada waiver con lo que costó la última vez que se aceptó en esta cuenta.

Medido: construir sin mapa de identificadores —el waiver más frecuente— produjo, en una certificación de cincuenta casos, del orden de **ochenta créditos sólo en reparaciones por selector adivinado**: tipo de nodo equivocado, un campo anidado que nadie sabía que existía, un copy con otro formato. Más las corridas que hicieron falta para descubrir cada uno.

Sin cifra, el riesgo se acepta en abstracto y se vuelve a aceptar igual de barato en la historia siguiente. **Por eso la puerta de entrega cierra el bucle**: reporta qué costó realmente cada waiver aceptado, y esa cifra alimenta el dictamen de la próxima. Ver `[[calidad-delivery-gate-contract]]`.

### La forma del dictamen

Cinco líneas, no un informe:

```
Preparación del sistema — <stack> · <modo> · <desplegado|mock|híbrido>
  Contrato de interfaz    LISTO       mapa cosechado de la app real (100% alta confianza)
  Alcanzabilidad          PARCIAL     3 desenlaces sin declarar duración -> del recorrido funcional
  Estado y datos          NO LISTO    estado 11 sin usuario ni forma de crearlo -> bloquea CA-2
  Entorno                 LISTO       build y driver fijados
  Trazabilidad            LISTO
Veredicto: NO LISTO para 1 de 24 criterios. Seguir sin resolverlo cuesta ~80 créditos (histórico).
```

Si la persona decide arrancar igual, **se arranca**: queda registrado como riesgo aceptado con su cifra, y el proceso continúa. El gate informa y registra; no veta.

## Mock ≠ certificación (contrato de cierre)

1. Smoke gate verde contra mock → `status: success` **de construcción**: el delivery gate registra `execution_target: mock | hybrid` y `certification: pending_real_integration`, con `next_steps` incluyendo la re-ejecución contra integraciones reales.
2. `certification: certified` solo es válido con `execution_target: real`.
3. El switchover mock → real se diseña desde el día uno: la URL objetivo vive en un único punto de configuración por stack (detalle en `[[calidad-service-virtualization-mockoon]]`, `references/mock-vs-real-switchover.md`). Si cambiar de mock a real requiere editar un test, el diseño está mal y se corrige antes de entregar.
4. **NUNCA** presentar reportes, métricas o evidencia obtenida contra mock como certificación de integración, performance o seguridad del SUT. Hacerlo es equivalente a un anti-cheating grave.

## Restricciones

- **NUNCA** inventar schemas de respuesta, payloads o identificadores UI para compensar insumos faltantes: si la matriz marca STOP, se detiene y se pide el insumo.
- **NUNCA** ejecutar `load/stress/spike/soak` de K6 contra un mock y reportar sus métricas: el mock no representa el comportamiento del SUT bajo carga.
- **NUNCA** completar el locator map con valores adivinados; el mapa es un acuerdo con el equipo de desarrollo, no una hipótesis del QA.
- El gate se resuelve una vez por corrida y queda registrado; si el usuario cambia de opinión a mitad de flujo (ej. "ya desplegaron"), re-ejecutar el gate y actualizar STRATEGY.md.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | execution_target (real/mock/hybrid), data_strategy (real/synthetic) y, para front/mobile, locator_map resueltos explícitamente con el usuario antes de validar spec o generar código | Bloqueado: no se resolvió la disponibilidad del SUT, de los datos de prueba y del mapeo de locators. Sin este gate no se puede garantizar que los tests sean ejecutables ni deterministas. |
| 2 | si execution_target es mock o hybrid, los inputs que la matriz por stack marca como obligatorios están presentes (spec con response schemas para API, locator map + fuente UI para front/mobile); ante locator_map ausente NO se generó código de UI salvo override explícito registrado como waived | Bloqueado: el modo pre-desarrollo exige insumos adicionales que no fueron entregados. Sin locator map no se generan page objects salvo waiver explícito del usuario. Consultar la matriz de obligatoriedad por stack. |
| 3 | si execution_target es mock o hybrid, el delivery gate declara certification: pending_real_integration | Bloqueado: resultados contra mock no pueden presentarse como certificación del SUT. |
| 4 | se emitió el dictamen de preparación en .evidence/input-sufficiency.json antes de generar, con veredicto por dimensión y, en cada ausencia, de dónde puede venir y qué cuesta seguir sin ella | Bloqueado: se iba a construir sin decir si el sistema está en condiciones. Tres variables repartidas entre la estrategia y el cierre no son un dictamen: nadie las lee antes de gastar la primera corrida. |

## Cross-links

`[[calidad-route-test-generation]]`, `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-service-virtualization-mockoon]]`, `[[calidad-ui-locator-map-contract]]`, `[[calidad-test-data-management]]`, `[[calidad-pre-design-strategy-document]]`, `[[calidad-smoke-gate-policy]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-execution-profile-and-config-provenance]]` — cómo se declara y se comprueba contra qué corrió de verdad.
