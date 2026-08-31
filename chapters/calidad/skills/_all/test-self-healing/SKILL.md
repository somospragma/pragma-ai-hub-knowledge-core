---
id: calidad-test-self-healing
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Estrategias de self-healing aplicadas en runtime a los tests generados por el chapter: multi-locator fallback, LLM-driven selector repair, visual AI healing, schema-drift tolerance. Incluye guardrails contra over-healing que esconde bugs reales."
tags: [self-healing, auto-healing, multi-locator, llm-repair, visual-ai, schema-drift, resilience, enforcement, mandatory]
enforcement: mandatory
verification:
  - check: "self-healing aplica solo a selectores/locators/schema-drift no críticos; nunca a assertions de negocio"
    failure_message: "Bloqueado: over-healing detectado; se intentó sanar una assertion de contrato/negocio en lugar de un locator."
  - check: "cada healing en runtime queda registrado con before/after y razón en evidencia"
    failure_message: "Bloqueado: el healing se aplicó sin dejar registro auditable en .evidence/."
  - check: "estrategia de healing diseñada antes de entregar (multi-locator, fallback, schema-drift) y no improvisada en runtime"
    failure_message: "Bloqueado: el suite se entregó sin estrategia de healing — viola la disciplina del chapter para suites en CI/CD recurrente."
---

# Test Self-Healing — Estrategias de Resiliencia en Runtime con Guardrails Anti-Cheating

## Cuándo aplicar

Aplica este skill **antes de entregar un suite** al cliente: el healing no es una idea-de-último-momento, se diseña durante la construcción del Page Object / API Object / payload baseline y se observa en runtime. Cualquier suite del chapter que se ejecute en CI/CD recurrente — y especialmente las que corren contra entornos compartidos (dev, staging) donde el SUT muta — necesita estrategia de healing.

Frameworks dentro del alcance del chapter para healing:

- **Playwright** (web): multi-locator fallback, soft-locators, visual AI opcional.
- **Appium** (mobile native/híbrido Android/iOS): chain de `AppiumBy` con accessibility-id como primary, OSS Healenium para selectors legacy.
- **Karate** (REST/GraphQL): schema-drift tolerance con `##type` y matchers permisivos controlados.
- **K6** (perf): schema drift de response shape detectado vía `check()` con telemetría.
- **serenity-wdio** (web + mobile + api): dos superficies de fragilidad distintas — web usa `PageElement` + `By` con fallback por estrategia de selector; mobile nativo usa selectores `string` con Accessibility ID como primary. El mecanismo canónico de resolución de locators diferidos está en `[[complete-deferred-locators]]`.

**Fuera de scope** del chapter (y por tanto fuera de este skill): aplicaciones desktop nativas, sistemas embedded e IoT. Ver `[[calidad-sut-types-and-adaptations]]` para el alcance completo. Tampoco aplica a Pact ni a pruebas de contract, donde el healing es explícitamente anti-patrón (ver `references/over-healing-guardrails.md`).

Combinar siempre con `[[calidad-chapter-perspective]]` (perspectiva del chapter), `[[calidad-mandatory-inputs-protocol]]` (no curar sin baseline confirmado), `[[calidad-test-evidence-and-traceability]]` (los logs de healing son evidencia) y `[[calidad-business-driven-prioritization]]` (qué suites merecen healing vs deterministicas).

## Instrucción

1. **Identificar la superficie de fragilidad por SUT.** Para web: selectors DOM, timings de render, modales asíncronos. Para mobile: cambios de OS, accessibility-id no garantizados por dev, popups de permisos. Para API REST/GraphQL: response shape, campos opcionales del proveedor, paginación. Para K6: drift de schema en endpoints bajo carga. Documentar la superficie en un `healing-surface.md` dentro del suite y cruzar con `[[calidad-sut-types-and-adaptations]]`.

2. **Antes de "sanar", verificar que el locator apuntaba al nodo correcto.** El identificador da **identidad, no capacidad**: el nodo del contrato puede ser un contenedor no clickeable/no editable cuyo elemento capaz es un descendiente. Aplicar el protocolo de resolución (`[[calidad-appium-screenplay-android]]`, consultar [[calidad-mobile-locator-resolution]]; equivalente web en `selector-priority.md` de `[[calidad-playwright-greenfield]]`): volcar la jerarquía, enumerar ejes, **contar nodos (único válido = 1)** y validar por efecto externo. Un "healing" que cambia de estrategia sin este paso puede estar tapando un locator mal resuelto.

   **Prohibido relajar el discriminante** hasta que "algo" haga match (quitar el ancla, pasar a `contains` genérico, tomar el primero de N): eso reintroduce ambigüedad y produce verdes falsos. El identificador del contrato sigue siendo el ancla; lo que se re-resuelve es el eje hacia el nodo capaz.

3. **Aplicar multi-locator fallback en Page Objects** siguiendo orden de prioridad estricto:
   - Playwright: `getByTestId` → `getByRole` → `getByLabel` → `getByText` → CSS (último recurso).
   - Appium: `AppiumBy.accessibilityId` → `AppiumBy.id` → `AppiumBy.xpath` (xpath solo como último fallback, nunca primario).
   - serenity-wdio web: `By.css('[data-testid]')` → `By.css('#id')` → `By.css('.clase')` → `By.xpath("//[@aria-label]")` → `By.xpath` simple (último recurso). Encapsular en `PageElement.located(By...).describedAs(...)`.
   - serenity-wdio mobile: `'~accessibility-id'` → `'~testId'` → texto visible → XPath (nunca índices posicionales). Selector como `string` plano dentro de la Interaction; nunca `PageElement` en mobile.
   - Ver `references/multi-locator-fallback-pattern.md` para snippets y `references/healing-aware-page-object.md` para el patrón de inyección.

3. **Aplicar schema-drift tolerance en assertions** con reglas estrictas: los campos opcionales del contrato deben permitirse ausentes (`##type` en Karate; `optional()` o `check()` permisivos en K6), pero **los campos requeridos jamás se relajan**. Ver `references/healing-strategies-by-framework.md` para la matriz por framework.

4. **Configurar healing telemetry obligatoria.** Cada vez que un locator alternativo se activa o un campo opcional cambia, emitir un **structured log** JSON con: `test_id`, `framework`, `locator_original`, `locator_resolved`, `strategy_idx`, `timestamp`, `suite`, `tags`. El log alimenta el dashboard de healing y dispara alertas cuando se cruza el threshold (ver Restricciones). Sin telemetría, el healing está prohibido — curar en silencio es esconder bugs.

5. **Si el healing requiere LLM-driven repair** (todas las estrategias del fallback agotadas), invocar `[[calidad-playwright-extract-pages-from-live-app-prompt]]` con: DOM snapshot, screenshot del estado actual, último selector válido conocido y mensaje de error. Validar el selector propuesto contra el live app (smoke local) **antes** de hacer commit; nunca aceptar la salida del LLM directo a `main`. Ver `references/llm-driven-selector-repair.md` para el prompt completo, costos y latencia.

6. **Verificar que el healing no enmascara bugs reales** ejecutando `[[calidad-test-self-correction-loop]]` sobre el suite reparado y cruzando los resultados con `[[calidad-failure-triage-and-classification]]`. Si el triage indica que la fragilidad es un cambio de contrato del SUT, el healing se revierte y se abre ticket de bug. Las reglas duras están en `references/over-healing-guardrails.md`.

## Restricciones

- **NUNCA curar silenciosamente.** Todo healing genera log estructurado (paso 4) y, si supera el threshold (>3 healings/semana en un mismo test), abre ticket automático en el board del chapter.
- **NUNCA reintentar una operación que muta el estado del sistema bajo prueba.** El healing existe para resolver **identificación de elementos**, no para repetir operaciones de negocio. Un reintento que consume un intento de un contador, genera una transacción, gasta un cupo, envía un código o quema una vigencia **altera el sujeto de la prueba**. Reintentar la **lectura** de un dato es inocuo; reintentar el **envío** cambia el criterio bajo prueba.

  Caso medido: se añadió un mecanismo que reintentaba hasta 3 veces ante una pantalla de error. Esa pantalla era en realidad el rechazo del token, así que cada reintento consumía un intento real del contador de la aplicación. El escenario que verifica "se agotan los 3 intentos" habría gastado **nueve**, bloqueando la cuenta y contaminando todo lo que viniera detrás — incluidos los escenarios de tope de intentos y de reinicio del contador, que existen precisamente para verificar ese conteo.

  Si un reintento sobre una operación mutante es inevitable, se **declara explícitamente** en el log de healing, se **acota el número**, y se comprueba que ningún escenario del feature dependa del conteo que ese reintento altera. Los guardrails clásicos están escritos sobre *no ocultar fallos*; este cubre el caso distinto de un mecanismo de resiliencia que corrompe el estado.

- **NUNCA fijar a mano un umbral que depende de cuánto tarda una operación.** Un umbral temporal escrito a mano es una suposición sobre la velocidad del dispositivo, y en una granja el dispositivo cambia en cada corrida. Se **mide** la operación y se deriva el umbral de la medida. Caso medido: un lector exigía "al menos 20 segundos de vigencia restante" para leer 8 dígitos; en la granja esa lectura tardaba más, así que cada intento empezaba con margen aparente y terminaba pasada la rotación. Medir sale más barato que adivinar dos veces.

- **NUNCA curar cambios de contrato del SUT.** Si un campo requerido fue eliminado, un endpoint movido, un status code cambió de `200` a `4xx`, o una pantalla mobile cambió de flujo, **es bug, no healing**. Reportar vía `[[calidad-failure-triage-and-classification]]`.
- **NUNCA curar tests en producción sin auditoría.** El log de healings es parte de la evidencia del entregable (ver `[[calidad-test-evidence-and-traceability]]`); ocultarlo invalida la entrega.
- **En Karate:** NUNCA convertir un `#string` requerido a `##string` para que pase. Esconde bug de contrato.
- **En K6:** NUNCA aflojar threshold (latencia, error_rate, http_req_failed) sin justificación documentada y aprobada por el lead del chapter.
- **Healing bloqueado en suites etiquetadas `@security`, `@contract`, `@regression-strict`** — deben fallar deterministícamente si el SUT cambia. Ver `references/over-healing-guardrails.md`.
- **Healing requiere expiration.** Cada healing aplicado tiene 30 días de vigencia; pasado ese plazo si el primary locator sigue sin funcionar, se convierte en deuda técnica y se abre ticket auto-creado.
- **No usar comerciales por default.** OSS primero (Healenium, Resemble.js, multi-locator pattern). Solo licenciar Mabl/Testim/Functionize si el cliente ya los paga (ver `references/commercial-vs-oss-healing-tools.md`).
- **Cross-link obligatorio con `[[calidad-test-self-correction-loop]]`** (anti-cheating es regla maestra del chapter) y `[[calidad-failure-triage-and-classification]]` (triage decide si es healing válido o bug). Sin estos cruces, el healing está incompleto.
- Activar este skill después de haber confirmado los inputs vía `[[calidad-mandatory-inputs-protocol]]` y haber priorizado el suite vía `[[calidad-business-driven-prioritization]]`.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | self-healing aplica solo a selectores/locators/schema-drift no críticos; nunca a assertions de negocio | Bloqueado: over-healing detectado; se intentó sanar una assertion de contrato/negocio en lugar de un locator. |
| 2 | cada healing en runtime queda registrado con before/after y razón en evidencia | Bloqueado: el healing se aplicó sin dejar registro auditable en .evidence/. |
| 3 | estrategia de healing diseñada antes de entregar (multi-locator, fallback, schema-drift) y no improvisada en runtime | Bloqueado: el suite se entregó sin estrategia de healing — viola la disciplina del chapter para suites en CI/CD recurrente. |

## Cross-links

- `references/healing-strategies-by-framework.md` — matriz Playwright / Appium / Karate / K6 / serenity-wdio.
- `references/multi-locator-fallback-pattern.md` — snippet `ResilientLocator` y equivalentes Java/Karate.
- `references/llm-driven-selector-repair.md` — flujo de reparación con LLM y validación previa al commit.
- `references/visual-ai-healing.md` — Applitools, Percy, Resemble.js; cuándo aplicar y cuándo no.
- `references/commercial-vs-oss-healing-tools.md` — tabla comparativa y recomendación Pragma.
- `references/healing-aware-page-object.md` — POM con inyección de estrategia de healing.
- `references/over-healing-guardrails.md` — **crítico**. Reglas duras anti-cheating.

Cross-links con otros assets del chapter:

- `[[calidad-chapter-perspective]]`
- `[[calidad-mandatory-inputs-protocol]]`
- `[[calidad-test-evidence-and-traceability]]`
- `[[calidad-sut-types-and-adaptations]]`
- `[[calidad-business-driven-prioritization]]`
- `[[calidad-test-execution-orchestration]]`
- `[[calidad-failure-triage-and-classification]]`
- `[[calidad-test-self-correction-loop]]`
- `[[calidad-karate-greenfield]]`
- `[[calidad-playwright-greenfield]]`
- `[[calidad-k6-greenfield]]`
- `[[calidad-appium-screenplay-android]]`
- `[[serenity-wdio-greenfield]]`
- `[[serenity-wdio-brownfield]]`
- `[[calidad-playwright-extract-pages-from-live-app-prompt]]`
