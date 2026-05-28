# Chapter Calidad — Knowledge Core

## Overview

El Chapter Calidad de Pragma agrupa el conocimiento accionable para **QA automation para cualquier sistema bajo prueba — APIs, web, mobile, performance — sin presunción de sector o región**. Capacidades específicas (compliance, anonimización, mobile clouds) se activan según el contexto del cliente, no por defecto. Los assets de este chapter están diseñados para alimentar agentes que generan, extienden y operan suites de pruebas reales en producción.

Cubre cuatro frameworks de automatización:

- **Karate** — API testing (REST/SOAP) sobre OpenAPI/Swagger/WSDL.
- **Playwright** — E2E web testing y accesibilidad.
- **K6** — Performance testing.
- **Appium** — Mobile testing (Android V2 con Screenplay + Serenity + Cucumber).

Y cuatro ejes cross-cutting que aplican a los cuatro frameworks:

- **Seguridad** (OWASP API Top 10, DAST con ZAP).
- **Datos de prueba** y trazabilidad requisito → test → resultado.
- **CI/CD** (Azure DevOps, GitHub Actions, GitLab CI).
- **Contract testing** y validación de specs.

## Mapa de assets

### Steering

| Path                                                | Propósito                                                                |
|-----------------------------------------------------|--------------------------------------------------------------------------|
| `steering/_all/chapter-calidad-perspective.md`      | Perspectiva rectora del Chapter para cualquier sistema bajo prueba con disciplina de QA automation. |

### Skills cross-cutting (`skills/_all/`)

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `mandatory-inputs-protocol.md`         | Inputs obligatorios y opcionales antes de generar pruebas (intent, project_name, spec, firma, user_story).   |
| `intent-detection.md`                  | Decide qué framework aplicar a partir del intent del usuario.                                                |
| `spec-validation.md`                   | Valida OpenAPI 3.x, Swagger 2.0 y WSDL antes de generar; extrae endpoints, base URL, security schemes, enums. |
| `brownfield-vs-greenfield.md`          | Distingue proyectos existentes vs nuevos y define qué se genera y qué no en cada modo.                       |
| `streaming-files-protocol.md`          | Orden de scaffold por valor entregado: tests → utilities → infraestructura.                                  |
| `business-driven-prioritization.md`    | Asignación de prioridad CRITICAL/HIGH/MEDIUM/LOW por valor de negocio, nunca por keywords del path.          |
| `test-evidence-and-traceability.md`    | Configuración de reportes, traces, summaries y trazabilidad requisito → test → resultado.                    |
| `cicd-integration/SKILL.md`            | Integración de las cuatro suites en pipelines Azure DevOps / GitHub Actions / GitLab CI.                     |
| `security-testing/SKILL.md`            | Estrategia de seguridad: OWASP Top 10 API, fuzzing, SAST/DAST/SCA, autenticación.                            |
| `test-execution-orchestration/SKILL.md`| Ejecutar las suites generadas: invocar comandos, capturar output, parsear resultados, gestionar modos `full` / `dry-run` / `scaffold-only` / `execute-only`. |
| `failure-triage-and-classification/SKILL.md` | Clasifica fallos como deterministic vs flaky y diagnostica causa raíz antes de proponer corrección.    |
| `test-self-correction-loop/SKILL.md`   | Loop iterativo de auto-corrección con anti-cheating guardrails (max 3 iteraciones por default).             |
| `test-self-healing/SKILL.md`           | Self-healing en runtime: multi-locator fallback, LLM-driven selector repair, visual AI healing.              |

### Skills per-framework

#### Karate (`skills/automation/karate/`)

| Asset                            | Capacidad                                                                                       |
|----------------------------------|-------------------------------------------------------------------------------------------------|
| `karate-greenfield/SKILL.md`     | Genera proyecto Karate completo desde un spec OpenAPI/Swagger/WSDL.                             |
| `karate-brownfield/SKILL.md`     | Extiende un proyecto Karate existente respetando convenciones, sin regenerar infraestructura.   |
| `karate-run-and-tags.md`         | Comandos Maven, ejecución por tag o environment, semántica de tags estándar.                    |

Incluye references específicas como `negative-coverage-formula.md` (con `risk_factor` modulado por negocio), `contract-testing-match-patterns.md`, `encrypted-payloads.md` y reglas de cliente Mercantil aisladas.

#### Playwright (`skills/automation/playwright/`)

| Asset                              | Capacidad                                                                                              |
|------------------------------------|--------------------------------------------------------------------------------------------------------|
| `playwright-greenfield/SKILL.md`   | Genera proyecto Playwright E2E web completo desde fuentes UI reales (URL viva, Figma, Storybook).      |
| `playwright-brownfield/SKILL.md`   | Extiende o ajusta un proyecto Playwright existente respetando convenciones.                            |
| `playwright-run-and-modes.md`      | Modos de ejecución (headless, headed, UI, debug, visual, a11y) y override de BASE_URL.                 |

Incluye references para Page Object Model, fixtures, selectores, auth storage state, mocks `page.route`, visual regression y accesibilidad axe/WCAG.

#### K6 (`skills/automation/k6/`)

| Asset                         | Capacidad                                                                                      |
|-------------------------------|------------------------------------------------------------------------------------------------|
| `k6-greenfield/SKILL.md`      | Genera proyecto K6 completo de performance testing desde un spec OpenAPI/Swagger.              |
| `k6-run-and-suite.md`         | Instalación y ejecución de scripts K6 individuales y la suite completa con `run-all.sh`.        |

Incluye references para los cinco tipos de scripts (load, stress, spike, soak, smoke), thresholds en tres niveles, correlación dinámica de IDs y módulos de config/utils.

#### Appium (`skills/automation/appium/`)

| Asset                                          | Capacidad                                                                                  |
|------------------------------------------------|--------------------------------------------------------------------------------------------|
| `appium-screenplay-android/SKILL.md`           | Genera proyecto Appium V2 Android con Screenplay + Serenity + Cucumber listo para correr.  |
| `appium-run-and-tags.md`                       | Comandos Gradle, filtros por tags y override de env.                                       |

Incluye references para capas Screenplay, locators diferidos, smoke vs proposed scenarios, matriz de versiones Gradle y health-check pipeline.

### Workflows

| Tipo               | Asset                                                                                  |
|--------------------|----------------------------------------------------------------------------------------|
| Router rector      | `workflows/_all/route-test-generation.workflow.md`                                     |
| Karate greenfield  | `workflows/automation/karate/generate-karate-greenfield.workflow.md`                   |
| Karate brownfield  | `workflows/automation/karate/extend-karate-brownfield.workflow.md`                     |
| Playwright greenfield | `workflows/automation/playwright/generate-playwright-greenfield.workflow.md`        |
| Playwright brownfield | `workflows/automation/playwright/update-playwright-brownfield.workflow.md`          |
| K6 greenfield      | `workflows/automation/k6/generate-k6-suite.workflow.md`                                |
| K6 calibración     | `workflows/automation/k6/calibrate-k6-thresholds.workflow.md`                          |
| Appium greenfield  | `workflows/automation/appium/generate-appium-screenplay-android.workflow.md`           |
| Appium locators    | `workflows/automation/appium/complete-deferred-locators.workflow.md`                   |
| K6 brownfield      | `workflows/automation/k6/extend-k6-brownfield.workflow.md`                             |
| Appium brownfield  | `workflows/automation/appium/extend-appium-brownfield.workflow.md`                     |
| Self-correction loop (cross-framework) | invocado como fase final por todos los workflows anteriores (ver `[[calidad-test-self-correction-loop]]`). |

### Prompts (`prompts/automation/`)

| Framework  | Prompts disponibles                                                                                                        |
|------------|----------------------------------------------------------------------------------------------------------------------------|
| Karate     | `analyze-openapi-for-karate`, `generate-karate-feature`, `generate-karate-match-schema`                                    |
| Playwright | `detect-pages-from-ui-source`, `generate-page-object`, `generate-accessibility-suite`, `generate-mock-handlers`            |
| K6         | `extract-config-from-openapi`, `generate-k6-script`, `generate-utils-and-payloads`                                         |
| Appium     | `validate-appium-inputs`, `generate-cucumber-feature-android`, `generate-screenplay-task`                                  |

## Cómo empezar

Un developer o un agente que necesite generar pruebas en este chapter debe entrar por el **workflow router**:

```
workflows/_all/route-test-generation.workflow.md
```

Ese workflow se encarga de:

1. Recolectar inputs obligatorios (`mandatory-inputs-protocol`).
2. Identificar framework (`intent-detection`).
3. Validar el spec si aplica (`spec-validation`).
4. Decidir greenfield vs brownfield (`brownfield-vs-greenfield`).
5. Delegar al workflow específico del framework + modo correspondiente.
6. Emitir archivos con disciplina de scaffold por valor (`streaming-files-protocol`).
7. Configurar evidencia y trazabilidad (`test-evidence-and-traceability`).

No saltar pasos: el router protege contra la generación con inputs incompletos o framework equivocado.

**El contrato de entrega del Chapter incluye ejecución + verificación + auto-corrección.** Generar tests sin ejecutarlos es entrega incompleta. Cada workflow del chapter termina con una fase obligatoria que invoca `[[calidad-test-execution-orchestration]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-test-self-correction-loop]]` y `[[calidad-test-self-healing]]` cuando aplica. Ver principio 9 en `[[calidad-chapter-perspective]]`.

## Convenciones internas

- **Frontmatter completo** sólo en assets accionables: `SKILL.md`, archivos `*.workflow.md`, archivos `*.prompt.md` y archivos de steering.
- **References** (todo lo que vive en `references/*.md` dentro de un skill) son **plain markdown sin frontmatter**: son material de apoyo del skill que las referencia.
- **Chapter README** (este archivo) es **plain markdown sin frontmatter**: no es un asset indexable.
- **Prose en español**; **código en inglés** (identificadores, comentarios técnicos, paths, comandos).
- **Sin emojis** en ningún asset.
- **Links entre assets**:
  - `[[asset-id]]` sólo para assets que tienen `id:` en su frontmatter.
  - References se enlazan por **path relativo** desde el documento que los cita, no por id.
- **Reglas específicas de cliente** se aíslan en su skill correspondiente. El caso vigente:
  - Cliente **Mercantil** tiene sus reglas en `skills/automation/karate/karate-brownfield/references/mercantil-*.md` (convenciones de naming, headers de seguridad).
  - El override de inputs obligatorios para Mercantil se documenta en `skills/_all/mandatory-inputs-protocol.md` con pointer al skill.

## Roadmap

Items conocidos pendientes en el chapter:

- **Appium iOS** — el auto-generador V3 con soporte iOS está pendiente; V2 cubre sólo Android.
- **Profundizar el catálogo de marcos regulatorios del alcance del Chapter** (LATAM + Estados Unidos): hoy se cubren PCI-DSS, OWASP API, ISO 27001, SOC 2, HIPAA, SOX, CCPA/CPRA, FedRAMP, Ley 1581, LGPD, LFPDPPP, Ley 19.628/21.719, Ley 25.326, Ley 29.733 y equivalentes locales LATAM. Marcos fuera de este alcance (UE, APAC, África) se escalan caso a caso, no se incorporan al chapter por defecto.
- **AsyncAPI testing** — el ecosistema Karate cubre REST y SOAP; queda pendiente un skill formal para eventos (Kafka, SNS/SQS, AMQP/RabbitMQ, Google Pub/Sub) basado en AsyncAPI 3.0.
- **Skill formal de contract testing** consumer-driven con Pact, complementario a `match` patterns de Karate.

## Maintainers

Chapter Calidad — Pragma. Para cambios, propuestas de nuevos assets o reportes de inconsistencias, abrir un PR siguiendo las convenciones internas listadas arriba.

---

## Ejemplos de uso desde Kiro

Esta sección muestra escenarios reales de un QA usando el Chapter Calidad desde **Kiro** (el chat integrado en el IDE, similar a Cursor / Cline / Amazon Q Developer). En todos los ejemplos el QA escribe en lenguaje natural y Kiro decide qué skill, workflow o prompt invocar.

El objetivo es ilustrar el **contrato completo** del chapter: no basta con generar archivos, hay que **ejecutarlos, triar fallos y aplicar auto-corrección** cuando aplica. Cada ejemplo declara explícitamente el modo de operación efectivo (`full` / `dry-run` / `scaffold-only` / `execute-only`).

### Cómo invocar los assets desde Kiro

Existen **tres modos de invocación**. Elegir uno u otro depende del nivel de control que el QA quiera tener sobre el routing.

1. **Workflow completo (recomendado por default)** — el QA describe la intención (qué quiere lograr, sobre qué SUT) y deja que el router `[[calidad-route-test-generation]]` clasifique el caso y delegue al workflow correcto. Es la entrada natural y aplica los guardrails de `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-intent-detection]]`, `[[calidad-spec-validation]]` y `[[calidad-brownfield-vs-greenfield]]` antes de generar nada.
2. **Skill directo** — cuando el QA ya sabe exactamente qué framework y modo aplica. Invoca el skill por id (ej. `@karate-greenfield`, `@playwright-brownfield`) y se salta el router. Kiro asume defaults de `[[calidad-context-determined-defaults]]` y solo pregunta lo crítico.
3. **Prompt directo** — cuando solo necesita un artefacto puntual (un `.feature` aislado, un `setupMocks(page)`, un script K6). Invoca el prompt por id (ej. `@karate-generate-feature-prompt`) y obtiene un fragmento listo para pegar, sin scaffold de proyecto.

### Ejemplos completos por tecnología

---

#### 1. Karate Greenfield — Servicio de pagos nuevo

**Setup**: workspace vacío en `tests/`. Spec OpenAPI 3.0 en `docs/api/pagos.yaml`. Historia de usuario en `docs/stories/pagos-v1.md`. Sin firma técnica del servicio. Modo efectivo: `full`.

```
> QA: Necesito generar pruebas Karate para el spec OpenAPI en docs/api/pagos.yaml. Es un servicio nuevo de pagos, no tengo proyecto previo.

> Kiro: Entendido. Voy a entrar por el router [[calidad-route-test-generation]]. Detecto intent "karate greenfield" via [[calidad-intent-detection]]. Antes de generar necesito confirmar los inputs obligatorios ([[calidad-mandatory-inputs-protocol]]):
>   - project_name: sugiero `pagos-api-tests` (¿confirmas?)
>   - output_path: `tests/karate/pagos-api-tests/` (¿confirmas?)
>   - user_story: ¿tienes alguna historia para nombrar escenarios con lenguaje de negocio?
>   - firma técnica: ¿hay documento con SLAs, reglas de cifrado o headers especiales?

> QA: project_name y output_path OK. La historia está en docs/stories/pagos-v1.md. Sin firma por ahora.

> Kiro: Perfecto. Valido el spec con [[calidad-spec-validation]]... OpenAPI 3.0.3 válido, 7 endpoints, security scheme `bearerAuth`, 4 enums detectados. Aplico fórmula de cobertura (`negative-coverage-formula.md`) con risk_factor MEDIUM derivado de la historia: 28 escenarios totales (12 happy path, 11 negativos, 5 contract).
>
> Delego a `generate-karate-greenfield` y aplico [[calidad-streaming-files-protocol]] (tests primero, luego utilidades, luego infraestructura). Genero en este orden:
>   1. `tests/karate/pagos-api-tests/src/test/java/pagos/features/payments.feature`
>   2. `tests/karate/pagos-api-tests/src/test/java/pagos/features/refunds.feature`
>   3. `tests/karate/pagos-api-tests/src/test/resources/files/payment-valid.json`
>   4. `tests/karate/pagos-api-tests/karate-config.js`
>   5. `tests/karate/pagos-api-tests/src/test/java/pagos/TestRunner.java`
>   6. `tests/karate/pagos-api-tests/pom.xml`
>
> Ahora ejecuto la fase obligatoria de cierre ([[calidad-test-execution-orchestration]]) en modo smoke: `mvn test -Dtest=TestRunner -Dkarate.options="--tags @smoke"`.

> Kiro: Resultado: 27/28 pass, 1 fail. Triage con [[calidad-failure-triage-and-classification]]: el escenario `create payment with valid card` falló porque la API devolvió `transactionId: null` y el assertion era `#string`. Clasificación: deterministic (no es flaky, es producto que devuelve null sistemáticamente).
>
> Consulto la historia de usuario: dice "transactionId es opcional en respuesta async". Aplico [[calidad-test-self-correction-loop]] con diff-aware-repair: cambio `#string` por `##string` (opcional). Re-ejecuto: 28/28 pass.
>
> Estado final: success. Modo efectivo: full. Audit log persistido en `tests/karate/pagos-api-tests/.evidence/self-correction-2026-05-28.json`. Reporte HTML en `target/karate-reports/`.
```

**Artefactos resultantes**:
- `tests/karate/pagos-api-tests/pom.xml`
- `tests/karate/pagos-api-tests/karate-config.js`
- `tests/karate/pagos-api-tests/src/test/java/pagos/TestRunner.java`
- `tests/karate/pagos-api-tests/src/test/java/pagos/features/*.feature` (7 archivos, 28 escenarios)
- `tests/karate/pagos-api-tests/src/test/resources/files/*.json`
- `tests/karate/pagos-api-tests/.evidence/self-correction-2026-05-28.json`

**Cierre**: `success`. 28/28 escenarios pasando. 1 corrección aplicada bajo auditoría. Próximo paso sugerido: integrar a pipeline con `[[calidad-cicd-integration]]`.

---

#### 2. Karate Brownfield — Cliente Mercantil agrega endpoint

**Setup**: proyecto Karate existente en `pagos-mercantil-tests/` con `karate-config.js`, features previos y convenciones consolidadas. Nuevo endpoint `POST /transferencia` agregado al spec. HUT_ID = `PN-PR-BFF-4521`. Body_Mode = A (JSON externo). Cliente Mercantil → modo `dry-run` automático por regulación.

```
> QA: Agrega el endpoint POST /transferencia al proyecto pagos-mercantil-tests. HUT_ID PN-PR-BFF-4521, body en JSON externo.

> Kiro: Detecto intent "karate brownfield" en cliente Mercantil. Activo el override de [[calidad-mandatory-inputs-protocol]] para Mercantil (HUT_ID, Body_Mode son obligatorios, ya los proporcionaste).
>
> Aplico [[calidad-brownfield-vs-greenfield]] para detectar convenciones del proyecto existente:
>   - headers strategy: `one-by-one` (detectado en features previos)
>   - body strategy: `external-json` (detectado en `resources/files/`)
>   - naming prefix: `PN-PR-BFF-` (detectado en `@HUT_ID` tags)
>   - Mercantil security headers detectados intactos: `Transaction-Id`, `Sid`, `Auth-Id`, `X-Channel` (NO se modifican, según `references/mercantil-security-headers.md`)
>
> Delego a `extend-karate-brownfield`. Como el cliente es Mercantil (regulado), [[calidad-test-execution-orchestration]] fuerza `mode: dry-run`. Genero:
>   1. `src/test/java/transferencia/transferencia.feature` (nuevo)
>   2. `src/test/resources/files/transferencia-valid.json` (nuevo)
>   3. NO toco `karate-config.js`, NO toco features previos.
>
> Ejecuto: `mvn test -Dkarate.options="--tags @PN-PR-BFF-4521"`. Resultado: 4/5 pass, 1 fail por spec drift (el spec declara `metadata.channel` como required pero la API real lo trata como opcional).
>
> Triage [[calidad-failure-triage-and-classification]]: deterministic, causa = spec drift. [[calidad-test-self-correction-loop]] propone el diff (cambiar `#string` por `##string` en el campo opcional) pero NO aplica porque estamos en dry-run.

> QA: Entendido. ¿Qué pasa con el cambio?

> Kiro: Genero el reporte de cambios propuestos en `.evidence/dry-run-PN-PR-BFF-4521.json` con el diff completo, justificación y trazabilidad al HUT_ID. Creo ticket Jira de aprobación para el QA Lead de Mercantil. El cambio NO se aplica hasta que haya firma humana.
>
> Estado final: partial (dry-run). Modo efectivo: dry-run.
```

**Artefactos resultantes**:
- `src/test/java/transferencia/transferencia.feature`
- `src/test/resources/files/transferencia-valid.json`
- `.evidence/dry-run-PN-PR-BFF-4521.json`
- Ticket Jira de aprobación (creado vía MCP)

**Cierre**: `partial`. Diff propuesto archivado bajo audit log Mercantil. Espera aprobación humana.

---

#### 3. K6 Greenfield — API de catálogo de productos

**Setup**: spec OpenAPI de catálogo en `docs/api/catalog.yaml` (sin security en spec). Sin proyecto K6 previo. user_story dice "soportar 500 RPS en hora pico, P95 < 800ms". Modo efectivo: `full`.

```
> QA: Genera una suite K6 para la API de catálogo en docs/api/catalog.yaml. La historia menciona 500 RPS y P95 menor a 800ms.

> Kiro: Detecto intent "k6 greenfield". Aplico [[calidad-mandatory-inputs-protocol]]: project_name sugerido `catalog-perf-tests`, output_path `tests/k6/catalog-perf-tests/`. ¿Confirmas?

> QA: Sí.

> Kiro: Valido spec con [[calidad-spec-validation]]: OpenAPI 3.0.2, 5 endpoints GET, sin security scheme. Aplico [[calidad-context-determined-defaults]] sobre la user_story: 500 RPS + P95 < 800ms ubica al SUT en tier **Moderate** (no Light, no Heavy). Esto determina arrival_rate, stages y thresholds.
>
> Delego a `generate-k6-suite`. Sigo [[calidad-streaming-files-protocol]]:
>   1. `tests/k6/catalog-perf-tests/tests/smoke-test.js`
>   2. `tests/k6/catalog-perf-tests/tests/load-test.js`
>   3. `tests/k6/catalog-perf-tests/tests/stress-test.js`
>   4. `tests/k6/catalog-perf-tests/tests/spike-test.js`
>   5. `tests/k6/catalog-perf-tests/tests/soak-test.js`
>   6. `tests/k6/catalog-perf-tests/config.js`
>   7. `tests/k6/catalog-perf-tests/utils.js`
>   8. `tests/k6/catalog-perf-tests/run-all.sh`
>   9. `tests/k6/catalog-perf-tests/package.json`
>
> Fase de cierre [[calidad-test-execution-orchestration]]: ejecuto smoke con `k6 run tests/smoke-test.js`. Smoke pasa (5 VUs, 1 min, sin checks fallidos, P95=312ms).
>
> Estado final: success. Modo efectivo: full. La suite completa (load, stress, spike, soak) NO la ejecuto local porque consume tiempo y recursos; te dejo el comando `./run-all.sh` y te recomiendo delegar a CI con [[calidad-cicd-integration]].
```

**Artefactos resultantes**: 5 scripts en `tests/`, `config.js`, `utils.js`, `run-all.sh`, `package.json`. Reporte smoke en `.evidence/smoke-2026-05-28.json`.

**Cierre**: `success`. Smoke validado local. Suite completa diferida a CI.

---

#### 4. K6 Brownfield — Recalibrar thresholds tras migración de infra

**Setup**: proyecto K6 existente en `catalog-perf-tests/` con 5 scripts. El SUT migró de `m5.large` a `m5.xlarge`. Workflow esperado: `calibrate-k6-thresholds`. Modo efectivo: `execute-only`.

```
> QA: El SUT del catálogo migró a una instancia más grande. Quiero recalibrar los thresholds del proyecto K6 existente.

> Kiro: Detecto intent "k6 brownfield → recalibración". Esto cae naturalmente en `calibrate-k6-thresholds` (caso especial del self-correction-loop aplicado a performance).
>
> Aplico [[calidad-brownfield-vs-greenfield]]: detecto convenciones del proyecto (config.js con thresholds vigentes, utils.js intacto). NO regenero nada.
>
> Ejecuto smoke + load actuales para capturar métricas reales nuevas. Resultados:
>   - smoke: P95 = 180ms (antes 312ms) — mejora del 42%
>   - load: P95 = 540ms (antes 780ms) — mejora del 31%, error rate 0.1% (antes 0.4%)
>
> Comparo contra thresholds vigentes en `config.js`:
>   - http_req_duration p(95)<800 → propuesto p(95)<600
>   - http_req_failed rate<0.005 → propuesto rate<0.002
>
> Modo efectivo: execute-only. NO aplico el cambio, te propongo el diff y dejo el audit log en `.evidence/threshold-calibration-2026-05-28.json` con métricas antes/después y justificación. ¿Aplicas?
```

**Artefactos resultantes**: `.evidence/threshold-calibration-2026-05-28.json` (no se modificó `config.js`).

**Cierre**: nuevos thresholds propuestos. Espera aplicación manual del QA.

---

#### 5. Playwright Greenfield — App e-commerce desde live URL

**Setup**: sin spec OpenAPI, sin Figma. URL staging: `https://staging.shop.com`. Sin proyecto previo. Modo efectivo: `full`.

```
> QA: Necesito una suite Playwright para staging.shop.com. No tengo specs ni Figma, solo la URL.

> Kiro: Detecto intent "playwright greenfield desde live app". Aplico [[calidad-mandatory-inputs-protocol]]: project_name `shop-e2e-tests`, output_path `tests/playwright/shop-e2e-tests/`. ¿Confirmas?

> QA: Sí.

> Kiro: Como no hay spec, delego a `playwright-from-live-app`. Invoco `@playwright-extract-pages-from-live-app-prompt` con Playwright Codegen MCP. Crawling de 5 páginas top:
>   - Home, ProductDetail, Cart, Checkout, Login
>
> Aplico [[calidad-business-driven-prioritization]] sobre el crawl: Checkout y Login → CRITICAL; Cart, ProductDetail → HIGH; Home → MEDIUM.
>
> Genero POMs con `@playwright-generate-page-object-prompt`:
>   1. `tests/playwright/shop-e2e-tests/pages/HomePage.ts`
>   2. `tests/playwright/shop-e2e-tests/pages/ProductDetailPage.ts`
>   3. `tests/playwright/shop-e2e-tests/pages/CartPage.ts`
>   4. `tests/playwright/shop-e2e-tests/pages/CheckoutPage.ts`
>   5. `tests/playwright/shop-e2e-tests/pages/LoginPage.ts`
>
> Tests `@live` en `tests/e2e/*.spec.ts`, fixtures y `playwright.config.ts`. Ejecuto headed: `npx playwright test --headed --grep @live`.
>
> Resultado: 14/15 pass, 1 fail. Triage [[calidad-failure-triage-and-classification]]: el selector `getByRole('button', { name: 'Pay' })` no encontró el botón porque está dentro de un iframe del PSP. Clasificación: stale_locator deterministic.
>
> Invoco [[calidad-test-self-healing]] con multi-locator fallback: pruebo `frameLocator('iframe[name=psp]').getByRole('button', { name: 'Pay' })`. Encuentra. Aplico el cambio en `CheckoutPage.ts`, re-ejecuto: 15/15 pass.
>
> Estado final: success. Modo efectivo: full. Audit en `.evidence/self-healing-2026-05-28.json`.
```

**Artefactos resultantes**: 5 POMs, 5 spec files, `playwright.config.ts`, fixtures, `.evidence/`.

**Cierre**: `success`. Suite live + visual regression + a11y generada para CRITICAL/HIGH.

---

#### 6. Playwright Brownfield — Cambio de UI rompe selectores

**Setup**: proyecto Playwright existente. UI cambió labels a español. Modo efectivo: `full`.

```
> QA: La app cambió los labels a español y se me rompió la suite Playwright. ¿Puedes actualizar selectores?

> Kiro: Detecto intent "playwright brownfield → reparación selectores". Delego a `update-playwright-brownfield`.
>
> Aplico [[calidad-brownfield-vs-greenfield]]: detecto convenciones del proyecto:
>   - selector_strategy: `getByRole` (preferido)
>   - page_object_style: `class` (no `function-based`)
>   - path aliases: `@pages/*`, `@fixtures/*`
>
> Ejecuto suite completa para diagnóstico: `npx playwright test`. 22/30 pass, 8 fail.
>
> Triage [[calidad-failure-triage-and-classification]]: los 8 fallos son `stale_locator` deterministic (mismo patrón: labels en inglés ya no existen). Por ejemplo `getByRole('button', { name: 'Submit' })` debe ser `getByRole('button', { name: 'Enviar' })`.
>
> Aplico `references/playwright-selector-update-strategy.md` desde el skill `playwright-brownfield`. Importante: solo reemplazo nombres de selectores, NO toco firmas ni cuerpos de métodos del POM.
>
> Modo full → aplico los 8 cambios, re-ejecuto: 30/30 pass. Verifico que ningún test `@security` haya sido tocado (regla del skill brownfield).
>
> Estado final: success. Audit log con los 8 diffs en `.evidence/selector-update-2026-05-28.json`.
```

**Artefactos modificados**: 4 POMs con selectores actualizados. Tests `@security` intactos.

**Cierre**: `success`. 8 selectores reparados sin colateral.

---

#### 7. Appium Greenfield Android — App bancaria sin device

**Setup**: APK en `/Users/qa/builds/banco-app-2.5.0.apk`. include_login_case=true. user_story sobre login + consulta saldo. Sin device disponible. Modo efectivo: `scaffold-only`.

```
> QA: Genera proyecto Appium para esta APK: /Users/qa/builds/banco-app-2.5.0.apk. Quiero el flujo de login y consulta de saldo. No tengo device conectado ahora.

> Kiro: Detecto intent "appium screenplay android greenfield". Invoco `@appium-validate-inputs-prompt`: APK válida, platform=android, include_login_case=true. Como no hay device, [[calidad-test-execution-orchestration]] aplica `mode: scaffold-only` automáticamente.
>
> Delego a `generate-appium-screenplay-android`. Extraigo metadata de la APK (appPackage, appActivity, version). Genero:
>   1. `apps/qa-mobile/build.gradle` (Java 21, Serenity, Cucumber)
>   2. `apps/qa-mobile/src/test/java/co/com/banco/tests/tasks/LoginTask.java`
>   3. `apps/qa-mobile/src/test/java/co/com/banco/tests/tasks/CheckBalanceTask.java`
>   4. `apps/qa-mobile/src/test/java/co/com/banco/tests/questions/AppIsResponsive.java`
>   5. `apps/qa-mobile/src/test/java/co/com/banco/tests/interactions/TapOn.java`
>   6. `apps/qa-mobile/src/test/java/co/com/banco/tests/pages/LoginPage.java` (con `// TODO: update real locator` en locators diferidos)
>   7. `apps/qa-mobile/src/test/resources/features/login.feature` (@smoke, ejecutable)
>   8. `apps/qa-mobile/src/test/resources/features/check-balance.feature` (@proposed, basado en user_story)
>
> Fase de cierre: como modo=scaffold-only, ejecuto health-check estático: `./gradlew clean compileJava testClasses` con timeout 300s. Resultado: BUILD SUCCESSFUL.
>
> Estado final: partial. Scaffold completo entregado. Creo ticket para correr `complete-deferred-locators` cuando haya device disponible (Saucelabs o emulador local).
```

**Artefactos resultantes**: estructura Gradle + Screenplay completa. Features `@smoke` listos para ejecutar; `@proposed` con locators diferidos.

**Cierre**: `partial`. Scaffold validado por compilación. Pendiente: `complete-deferred-locators`.

---

#### 8. Appium Brownfield — Agregar escenarios a app existente

**Setup**: proyecto Appium Android existente en `apps/qa-mobile/`. Java 21 + Gradle. Device Android conectado. Modo efectivo: `full`.

```
> QA: Agrega estos test cases nuevos al proyecto apps/qa-mobile: TC-201 transferencia exitosa, TC-202 transferencia con saldo insuficiente, TC-203 cancelación. Tengo un emulador corriendo.

> Kiro: Detecto intent "appium brownfield". Delego a `extend-appium-brownfield`.
>
> Aplico [[calidad-brownfield-vs-greenfield]]: detecto convenciones del proyecto existente:
>   - base_package: `co.com.cliente.tests`
>   - gherkin_language: `es`
>   - tag conventions: `@smoke`, `@regression`, `@TC-NNN`
>   - screenplay_style: tasks separadas de interactions (no monolíticas)
>
> Invoco `@appium-generate-cucumber-feature-prompt` y `@appium-generate-screenplay-task-prompt`. Genero:
>   1. `src/test/resources/features/transferencia.feature` (3 escenarios @TC-201/202/203)
>   2. `src/test/java/co/com/cliente/tests/tasks/MakeTransfer.java`
>   3. `src/test/java/co/com/cliente/tests/tasks/CancelTransfer.java`
>   4. `src/test/java/co/com/cliente/tests/questions/TransferStatus.java`
>   5. NO toco tareas previas, NO toco build.gradle.
>
> Ejecuto: `./gradlew test --tests "*Transferencia*"`. Resultado: 2/3 pass, 1 fail.
>
> Triage [[calidad-failure-triage-and-classification]]: TC-202 falla por `NoSuchElementException` en el botón de confirmación. Stale locator deterministic.
>
> [[calidad-test-self-healing]] aplica multi-locator fallback en orden `accessibilityId → id → xpath`. El `accessibilityId` falla, el `id="btn_confirm_transfer"` encuentra. Aplico el cambio en `MakeTransfer.java`, re-ejecuto: 3/3 pass.
>
> Estado final: success. Modo efectivo: full. Verifico (regla brownfield) que ninguna feature previa ni tarea previa haya sido modificada: confirmado. Audit en `.evidence/self-healing-TC-202-2026-05-28.json`.
```

**Artefactos resultantes**: 1 feature nueva, 2 tasks, 1 question. Suite preexistente intacta.

**Cierre**: `success`. Nuevos TC pasan; 1 healing aplicado.

---

### Casos especiales

---

#### A. Skill directo — QA experto invoca `@karate-greenfield` sin router

Útil cuando el QA ya hizo decisiones de routing manualmente y quiere saltarse `[[calidad-intent-detection]]`.

```
> QA: @karate-greenfield genera tests para users-api.yaml con project_name users-api-tests.

> Kiro: Invoco directamente el skill `karate-greenfield`. Asumo defaults razonables ([[calidad-context-determined-defaults]]): output_path=`tests/karate/users-api-tests/`, risk_factor=MEDIUM (sin user_story que lo ajuste). Solo te pregunto lo crítico: ¿hay firma técnica o convenciones de cliente que deba respetar?

> QA: No, es un servicio interno estándar.

> Kiro: OK. Valido spec con [[calidad-spec-validation]], genero scaffold completo y ejecuto fase de cierre (orquestación + triage + self-correction loop). Resultado: 18/18 escenarios pass en smoke. Estado: success. Modo efectivo: full.
```

**Cuándo usarlo**: scripts repetitivos, QAs avanzados, contextos rutinarios donde el router agrega fricción innecesaria.

---

#### B. Prompt directo — QA necesita un único artefacto

Útil cuando el proyecto ya existe, la infraestructura ya está configurada y solo se necesita un feature adicional sin tocar nada más.

```
> QA: @karate-generate-feature-prompt para endpoint POST /products con required fields name, price, category, enum status [ACTIVE, INACTIVE].

> Kiro: Invoco solo el prompt `karate-generate-feature-prompt`. No genero pom.xml, no toco karate-config.js, no ejecuto nada. Te devuelvo un único `.feature` listo para pegar:

```gherkin
Feature: Create product

  Background:
    * url baseUrl
    * def validProduct = read('classpath:files/product-valid.json')

  @smoke @happy
  Scenario: Create product with valid payload
    Given path 'products'
    And request validProduct
    When method POST
    Then status 201
    And match response ==
      """
      {
        id: '#string',
        name: '#string',
        price: '#number',
        category: '#string',
        status: '#regex (ACTIVE|INACTIVE)'
      }
      """
  ...
```

> Pégalo en `src/test/java/products/products.feature`. No olvides crear `resources/files/product-valid.json`. Si quieres, invoco `@karate-generate-match-schema-prompt` para el match schema completo del recurso.
```

**Cuándo usarlo**: proyecto ya existe, QA tiene control fino, no quiere efectos colaterales.

---

#### C. Modo dry-run forzado por cliente regulado (HIPAA)

**Setup**: app de salud bajo HIPAA. El Compliance Officer del cliente exige aprobación humana para cualquier modificación de test. Modo efectivo: `dry-run` (forzado).

```
> QA: Corre la suite Playwright de la app de salud y arregla lo que falle.

> Kiro: Detecto `client_regulated: true` (HIPAA) en `tests/playwright/health-app/.config/compliance.json`. [[calidad-test-execution-orchestration]] fuerza `mode: dry-run` independiente de lo que pidas. NO voy a aplicar cambios automáticos.
>
> Ejecuto suite: `npx playwright test`. Resultado: 47/50 pass, 3 fail.
>
> Triage [[calidad-failure-triage-and-classification]]:
>   - Test 1: `stale_locator` deterministic en `PatientChartPage` (label cambió de "DOB" a "Date of Birth")
>   - Test 2: `assertion_drift` deterministic en `MedicationListPage` (API agregó campo `genericName` opcional)
>   - Test 3: `flaky` (timing en modal de consentimiento, falló 1/5 reintentos)
>
> Propongo diffs por cada uno pero NO los aplico. Genero `.evidence/dry-run-compliance-2026-05-28.json` con:
>   - los 3 diffs en formato unified
>   - justificación técnica de cada cambio
>   - evidencia de la ejecución (traces, screenshots, logs)
>   - clasificación del triage
>   - retention metadata (7 años, política HIPAA)
>
> Notifico al Compliance Officer del cliente vía el canal configurado en `compliance.json`. Espero aprobación firmada antes de aplicar.
>
> Estado final: partial. Modo efectivo: dry-run (forzado por client_regulated=true).
```

**Cuándo usarlo**: HIPAA, PCI Level 1, SOX, FedRAMP, o cualquier cliente cuyo `compliance.json` declare `client_regulated: true`.

---

Estos ejemplos cubren los 4 frameworks en sus dos modos (greenfield + brownfield), más 3 escenarios transversales que muestran las distintas formas de invocación y los modos de operación regulados. Para escenarios no cubiertos aquí, entrar siempre por `[[calidad-route-test-generation]]` y dejar que el router clasifique.
