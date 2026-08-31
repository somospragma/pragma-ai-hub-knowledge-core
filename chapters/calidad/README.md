# Chapter Calidad — Knowledge Core

## Overview

El Chapter Calidad de Pragma agrupa el conocimiento accionable para **QA automation para cualquier sistema bajo prueba — APIs, web, mobile, performance — sin presunción de sector o región**. Capacidades específicas (compliance, anonimización, mobile clouds) se activan según el contexto del cliente, no por defecto. Los assets de este chapter están diseñados para alimentar agentes que generan, extienden y operan suites de pruebas reales en producción.

Cubre siete stacks de automatización:

- **Karate** — API testing (REST/SOAP) sobre OpenAPI/Swagger/WSDL.
- **Playwright** — E2E web testing y accesibilidad.
- **K6** — Performance testing.
- **Appium Serenity** (`appium-serenity`) — Mobile sobre JVM: Serenity + Cucumber sobre Gradle, en patrón Screenplay o Page Object Model.
- **Appium WebdriverIO** (`appium-wdio`) — Mobile multi-plataforma en TypeScript con cucumber-js: Android, iOS, tablets y navegador móvil, en local y en device farm.
- **Appium Core** (`appium-core`) — El conocimiento mobile que **no depende del lenguaje**: resolución de locators, comportamiento de apps Flutter bajo Appium, catálogo de interacciones y auto-discovery de locators desde el binario.
- **serenity-wdio** — Web, web_movil, mobile nativo (Android e iOS), desktop y API sobre un único arquetipo multiplataforma (TypeScript + WebdriverIO v9 + Serenity/JS + Cucumber 11).

`appium-core` no es un stack que se elija: **acompaña** a cualquiera de los dos de producto y se instala aparte. Entre `appium-serenity` y `appium-wdio` decide el ecosistema del equipo, nunca la preferencia del agente: ver la desambiguación en `[[calidad-intent-detection]]`.

Y los ejes cross-cutting que aplican a todos los stacks:

- **Funcional** — el trabajo funcional del proceso de pruebas: análisis y refinamiento de historias de usuario (INVEST, criterios de aceptación, ambigüedades), diseño de casos de alto nivel con técnicas formales, estrategias y planes de prueba (ISO/IEC/IEEE 29119-3), con integración a Azure DevOps y Jira vía MCP. Sus entregables son documentos y artefactos ALM, no código; sus casos diseñados alimentan a los stacks de automatización. **Es transversal, no un stack**: no tiene artefacto detectable en un repositorio y el router bifurca a él desde cualquier stack, por lo que viaja en todos los bundles.
- **Convenciones Cucumber** — arquetipos multi-plataforma donde Cucumber orquesta web y mobile con un vocabulario Gherkin compartido: catálogo de steps, sufijo de plataforma, tagging y propiedades verificables por análisis estático.

- **Seguridad** (OWASP API Top 10, DAST con ZAP).
- **Datos de prueba** y trazabilidad requisito → test → resultado.
- **CI/CD** (Azure DevOps, GitHub Actions, GitLab CI).
- **Contract testing** y validación de specs.
- **Shift-left y mocking**: construir y validar pruebas antes de que el desarrollo exista — service virtualization con Mockoon, datos sintéticos deterministas, contrato de mapeo de locators UI, y prototipos opt-in de front (HTML) y de app mobile (en la misma tecnología de la app real, ej. Flutter con Semantics identifiers) para ejecutar la suite en browser/emulador pre-desarrollo. Los mocks validan la construcción del test; la certificación formal siempre corre contra integraciones reales vía switchover solo-configuración.

## Mapa de assets

### Estructura de carpetas y archivos

```
chapters/calidad/
├── README.md
│
├── steering/
│   └── _all/
│       └── chapter-calidad-perspective.md
│
├── skills/
│   ├── _all/
│   │   ├── alm-mcp-integration.md
│   │   ├── brownfield-vs-greenfield.md
│   │   ├── business-driven-prioritization.md
│   │   ├── environment-blocker-evidence.md
│   │   ├── execution-metadata-schema.md
│   │   ├── figma-mcp-integration.md
│   │   ├── intent-detection.md
│   │   ├── mandatory-inputs-protocol.md
│   │   ├── pipeline-state-tracking.md
│   │   ├── post-generation-execution-prompt.md
│   │   ├── pre-design-strategy-document.md
│   │   ├── results-structure-universal.md
│   │   ├── smoke-gate-policy.md
│   │   ├── spec-validation.md
│   │   ├── step-isolation-pattern.md
│   │   ├── streaming-files-protocol.md
│   │   ├── sut-readiness-gate.md
│   │   ├── test-evidence-and-traceability.md
│   │   ├── test-organization-by-scenario.md
│   │   ├── transversal-capabilities.md
│   │   ├── ui-locator-map-contract.md
│   │   ├── visual-regression.md
│   │   ├── accessibility/
│   │   │   ├── SKILL.md
│   │   │   └── references/{audit-report-structure, design-review, disability-types-and-barriers, regulatory-framework, severity-and-findings, wcag-pour}.md
│   │   ├── cicd-integration/
│   │   │   ├── SKILL.md
│   │   │   └── references/{allure-aggregation, azure-devops-pipeline-templates, github-actions-workflows, gitlab-ci-jobs, mobile-cloud-providers, quality-gates, rp-integration, secrets-in-pipelines, sharding-and-parallelization}.md
│   │   ├── context-determined-defaults/
│   │   │   ├── SKILL.md
│   │   │   └── references/{data-class-public-internal-confidential-restricted, operational-criticality-tiers, regulatory-exposure-mapping, traffic-class-and-peak-analysis, user-impact-and-blast-radius}.md
│   │   ├── contract-testing/
│   │   │   ├── SKILL.md
│   │   │   └── references/{asyncapi-event-contracts, cdc-vs-schema-first, contract-testing-vs-karate-match, openapi-diff-breaking-changes, pact-broker-pactflow, pact-consumer-tests, pact-provider-verification, schema-registry-confluent, spring-cloud-contract}.md
│   │   ├── delivery-gate-contract/
│   │   │   └── SKILL.md
│   │   ├── executive-report-generator/
│   │   │   ├── SKILL.md
│   │   │   └── references/{appium-report-template, failure-classification-rules, k6-report-template, karate-report-template, playwright-report-template, report-structure, templates}.md
│   │   ├── failure-triage-and-classification/
│   │   │   ├── SKILL.md
│   │   │   └── references/{bug-vs-test-design-decision-tree, failure-pattern-catalog, quarantine-pattern, re-run-protocol-for-determinism, stability-score-metric}.md
│   │   ├── security-testing/
│   │   │   ├── SKILL.md
│   │   │   └── references/{api-fuzzing-schemathesis-restler, auth-testing-patterns, compliance-regulatory-mapping, dast-with-owasp-zap, owasp-api-top-10-2023, sast-sca-dast-pipeline, secrets-management}.md
│   │   ├── seo/
│   │   │   ├── SKILL.md
│   │   │   └── references/{accessibility, hreflang, images, on-page, performance, schema, sitemap, technical}.md
│   │   ├── service-virtualization-mockoon/
│   │   │   ├── SKILL.md
│   │   │   └── references/{cli-docker-and-ci, dynamic-templating-and-faker-seed, mock-vs-real-switchover, mockoon-environment-file, openapi-to-mock, soap-xml-mocking, stateful-crud-and-data-buckets}.md
│   │   ├── sut-types-and-adaptations/
│   │   │   ├── SKILL.md
│   │   │   └── references/{data-pipeline-batch-streaming, event-driven-messaging, graphql-api, grpc-service, legacy-soap-ejb, ml-inference-service, rest-microservice, serverless-functions}.md
│   │   ├── test-data-management/
│   │   │   ├── SKILL.md
│   │   │   └── references/{anonymization-pii, builder-factory-objectmother-patterns, data-for-perf-testing, datasets-versioning, seeding-cleanup-transactional, synthetic-data-faker, test-data-strategies}.md
│   │   ├── test-execution-orchestration/
│   │   │   ├── SKILL.md
│   │   │   └── references/{evidence-archival, execute-and-capture-by-framework, executor-as-skill-vs-as-pipeline, output-parsers, result-schema-common}.md
│   │   ├── test-self-correction-loop/
│   │   │   ├── SKILL.md
│   │   │   └── references/{anti-cheating-guardrails, correction-audit-log, correction-loop-state-machine, diff-aware-repair-rules, iteration-limits-and-escalation, regulated-client-overrides}.md
│   │   └── test-self-healing/
│   │       ├── SKILL.md
│   │       └── references/{commercial-vs-oss-healing-tools, healing-aware-page-object, healing-strategies-by-framework, llm-driven-selector-repair, multi-locator-fallback-pattern, over-healing-guardrails, visual-ai-healing}.md
│   │   ├── cucumber-bdd-conventions/
│   │   │   ├── SKILL.md
│   │   │   └── references/{file-structure-conventions, gherkin-tagging-and-naming, hooks-and-world-contract, platform-suffix-and-ambiguity, static-correctness-properties, step-catalog}.md
│   │   ├── funcional-story-analysis/
│   │   │   ├── SKILL.md
│   │   │   └── references/{acceptance-criteria-quality, ambiguity-taxonomy, analysis-report-format, invest-scoring}.md
│   │   ├── funcional-story-refinement/
│   │   │   ├── SKILL.md
│   │   │   └── references/{example-mapping-three-amigos, refinement-proposal-format, story-splitting-patterns}.md
│   │   ├── funcional-test-design/
│   │   │   ├── SKILL.md
│   │   │   └── references/{bdd-atdd-alignment, combinatorial-pairwise, decision-tables-state-transition, equivalence-partitioning-bva, exploratory-charters-error-guessing, technique-selection-guide, test-case-format}.md
│   │   ├── funcional-test-strategy/
│   │   │   ├── SKILL.md
│   │   │   └── references/{automation-stack-mapping, levels-types-quadrants, risk-based-approach}.md
│   │   └── funcional-test-plan/
│   │       ├── SKILL.md
│   │       └── references/{entry-exit-criteria, progress-and-closure-reports, risk-analysis-matrix, test-plan-structure, traceability-rtm}.md
│   │
│   ├── appium-serenity/
│   │   ├── appium-run-and-tags.md
│   │   ├── appium-apk-auto-discovery/
│   │   │   ├── SKILL.md
│   │   │   └── references/{adb-and-emulator-bootstrap, appium-inspector-rest-api, crawler-strategy, locator-confidence-scoring, safety-and-cleanup, selector-extraction-rules}.md
│   │   ├── appium-brownfield/
│   │   │   ├── SKILL.md
│   │   │   └── references/{convention-detection, selector-update-strategy}.md
│   │   └── appium-screenplay-android/
│   │       ├── SKILL.md
│   │       └── references/{android-only-scope-rationale, contractual-questions, deferred-locators-strategy, flutter-apps-and-prototype, gherkin-syntax-rules, gradle-version-matrix, health-check-pipeline, locator-resolution-protocol, mandatory-inputs-validation, metadata-emitter-appium, mobile-accessibility, mobile-evidence-and-triage, mobile-interactions-catalog, mobile-visual-regression, no-aggregate-collision, preflight, project-structure, screenplay-layers, smoke-gate-gradle, smoke-vs-proposed-scenarios, step-isolation-appium, templates}.md
│   │
│   ├── k6/
│   │   ├── k6-run-and-suite.md
│   │   ├── k6-brownfield/
│   │   │   ├── SKILL.md
│   │   │   └── references/{convention-detection, extension-patterns}.md
│   │   └── k6-greenfield/
│   │       ├── SKILL.md
│   │       └── references/{auth-strategy-setup-vs-per-vu, availability-metric-from-rnf, config-and-utils-modules, contractual-checks-from-user-story, coverage-formula, crud-dynamic-id-correlation, enums-headers-security-extraction, execution-status-and-blockers, five-script-types, handle-summary-evidence, k6-discovery-checklist, modular-architecture, options-scenarios-executors, preflight, project-structure, realistic-sleep-policy, results-structure-and-metadata, smoke-1-1-gate, tag-policy-and-metrics-isolation, templates, threshold-tier-justification, thresholds-three-tiers, vocabulary-and-scenario-mapping}.md
│   │
│   ├── karate/
│   │   ├── karate-run-and-tags.md
│   │   ├── karate-brownfield/
│   │   │   ├── SKILL.md
│   │   │   └── references/{client-specific-conventions, convention-detection, mandatory-inputs-brownfield}.md
│   │   └── karate-greenfield/
│   │       ├── SKILL.md
│   │       └── references/{cobertura-comment-enforcement, contract-testing-match-patterns, encrypted-payloads, feature-design-dsl, file-location-constraint, metadata-emitter-karate, negative-coverage-formula, preflight, project-structure, smoke-gate-mvn, step-isolation-karate, templates}.md
│   │
│   ├── playwright/
│   │   ├── playwright-run-and-modes.md
│   │   ├── playwright-brownfield/
│   │   │   ├── SKILL.md
│   │   │   └── references/{convention-detection, selector-update-strategy}.md
│   │   ├── playwright-from-live-app/
│   │   │   └── SKILL.md
│   │   └── playwright-greenfield/
│   │       ├── SKILL.md
│   │       └── references/{accessibility-axe-wcag, auth-detection-rules, auth-storage-state, coherence-checks, contractual-checks-from-ui, coverage-formula, execution-modes-live-mocked-hybrid, fixtures-composition, front-prototype-recipe, interactive-design-prototype-source, metadata-emitter-playwright, mocks-page-route, page-object-model, playwright-config-strict-ts, playwright-native-tags-v142, preflight, project-structure, selector-priority, smoke-gate-playwright, step-isolation-playwright, templates, ui-source-priority, visual-regression, waits-policy}.md
│   │
│   └── serenity-wdio/
│       ├── serenity-wdio-run-and-tags.md
│       ├── references/serenity-wdio-test-data-management.md
│       ├── serenity-wdio-greenfield/
│       │   ├── SKILL.md
│       │   └── references/{cucumber-tags, gates-and-evidence, mandatory-inputs,
│       │                   metadata-emitter-serenity-wdio, platforms-and-scope,
│       │                   preflight, project-structure, run-and-modes,
│       │                   screenplay-conventions, smoke-gate-wdio,
│       │                   step-isolation-serenity-wdio, templates/,
│       │                   wdio-configs}.md
│       ├── serenity-wdio-brownfield/
│       │   ├── SKILL.md
│       │   └── references/{anti-pattern-audit, convention-detection,
│       │                   native-app-window-handles, prior-analysis,
│       │                   selector-update-strategy}.md
│       ├── serenity-wdio-screenplay-pattern/
│       │   ├── SKILL.md
│       │   └── references/{screenplay-api, screenplay-mobile, screenplay-web}.md
│       ├── serenity-wdio-cucumber-gherkin/
│       │   ├── SKILL.md
│       │   └── references/{gherkin-features, step-definitions}.md
│       ├── serenity-wdio-api-testing-rest/
│       │   ├── SKILL.md
│       │   └── references/{api-auth-y-estructura, api-questions-assertions,
│       │                   api-requests}.md
│       ├── serenity-wdio-webdriverio-handling/
│       │   ├── SKILL.md
│       │   └── references/{wdio-directo, wdio-encapsulado,
│       │                   wdio-referencia-rapida}.md
│       ├── serenity-wdio-test-execution-runner/
│       │   ├── SKILL.md
│       │   └── references/{diagnostico-ejecucion, env-variables,
│       │                   orquestador-y-modos}.md
│       ├── serenity-wdio-reporting/
│       │   ├── SKILL.md
│       │   └── references/{configuracion-reporters, lectura-de-fallos,
│       │                   troubleshooting-reportes}.md
│       └── serenity-wdio-troubleshooting/
│           ├── SKILL.md
│           └── references/{problemas-generales, problemas-mobile}.md
│
├── workflows/
│   ├── _all/
│   │   ├── analyze-and-refine-stories.workflow.md
│   │   ├── build-test-strategy-and-plan.workflow.md
│   │   ├── design-test-cases.workflow.md
│   │   ├── generate-executive-report.workflow.md
│   │   ├── route-test-generation.workflow.md
│   │   ├── seo-audit.workflow.md
│   │   └── test-self-correction-loop.workflow.md
│   ├── appium-wdio/
│   │   ├── extend-appium-wdio-brownfield.workflow.md
│   │   ├── generate-appium-wdio-greenfield.workflow.md
│   │   └── migrate-selectors-to-testdata.workflow.md
│   ├── appium-serenity/
│   │   ├── complete-deferred-locators.workflow.md
│   │   ├── extend-appium-brownfield.workflow.md
│   │   └── generate-appium-screenplay-android.workflow.md
│   ├── k6/
│   │   ├── calibrate-k6-thresholds.workflow.md
│   │   ├── extend-k6-brownfield.workflow.md
│   │   └── generate-k6-suite.workflow.md
│   ├── karate/
│   │   ├── extend-karate-brownfield.workflow.md
│   │   └── generate-karate-greenfield.workflow.md
│   ├── playwright/
│   │   ├── generate-playwright-greenfield.workflow.md
│   │   └── update-playwright-brownfield.workflow.md
│   └── serenity-wdio/
│       ├── complete-deferred-locators.workflow.md
│       ├── extend-serenity-wdio-brownfield.workflow.md
│       └── generate-serenity-wdio-greenfield.workflow.md
│
└── prompts/
    ├── _all/
    │   ├── analyze-user-story.prompt.md
    │   ├── generate-high-level-test-cases.prompt.md
    │   ├── generate-mockoon-environment.prompt.md
    │   └── generate-test-plan-document.prompt.md
    ├── appium-wdio/
    │   └── validate-appium-wdio-inputs.prompt.md
    ├── appium-serenity/
    │   ├── generate-cucumber-feature-android.prompt.md
    │   ├── generate-screenplay-task.prompt.md
    │   └── validate-appium-inputs.prompt.md
    ├── k6/
    │   ├── extract-config-from-openapi.prompt.md
    │   ├── generate-k6-script.prompt.md
    │   └── generate-utils-and-payloads.prompt.md
    ├── karate/
    │   ├── analyze-openapi-for-karate.prompt.md
    │   ├── generate-karate-feature.prompt.md
    │   └── generate-karate-match-schema.prompt.md
    ├── playwright/
    │   ├── detect-pages-from-ui-source.prompt.md
    │   ├── extract-pages-from-live-app.prompt.md
    │   ├── generate-accessibility-suite.prompt.md
    │   ├── generate-mock-handlers.prompt.md
    │   └── generate-page-object.prompt.md
    └── serenity-wdio/
        ├── generate-cucumber-feature.prompt.md
        ├── generate-screenplay-task.prompt.md
        └── validate-serenity-wdio-inputs.prompt.md
```

### Steering

| Path                                                | Propósito                                                                |
|-----------------------------------------------------|--------------------------------------------------------------------------|
| `steering/_all/chapter-calidad-perspective.md`      | Perspectiva rectora del Chapter para cualquier sistema bajo prueba con disciplina de QA automation. |

### Skills cross-cutting (`skills/_all/`)

#### Pre-generación (contratos de entrada y diseño)

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `mandatory-inputs-protocol.md`         | Inputs obligatorios y opcionales antes de generar pruebas (intent, project_name, spec, firma, user_story).   |
| `intent-detection.md`                  | Decide qué framework aplicar a partir del intent del usuario.                                                |
| `spec-validation.md`                   | Valida OpenAPI 3.x, Swagger 2.0 y WSDL antes de generar; extrae endpoints, base URL, security schemes, enums. |
| `brownfield-vs-greenfield.md`          | Distingue proyectos existentes vs nuevos y define qué se genera y qué no en cada modo.                       |
| `business-driven-prioritization.md`    | Asignación de prioridad CRITICAL/HIGH/MEDIUM/LOW por valor de negocio, nunca por keywords del path.          |
| `pre-design-strategy-document.md`      | `STRATEGY.md` como design-doc obligatorio aprobado por humano antes de generar código (los 4 stacks en greenfield). |
| `pipeline-state-tracking.md`           | Traza viva del pipeline en `.evidence/pipeline-state.json`: qué fase está hecha, cuál falta y con qué evidencia. Se lee al abrir cualquier sesión y se escribe tras cada fase, para que el proceso sobreviva a los cortes de contexto y ninguna entrega se cierre con fases pendientes. |
| `sut-readiness-gate.md`                | Gate del paso 1.5 del router: ¿desarrollo desplegado o pruebas antes del desarrollo? Resuelve `execution_target` (real/mock/hybrid), `data_strategy` (real/synthetic) y `locator_map`, y endurece los inputs obligatorios por stack en modo pre-desarrollo. Regla maestra: mock valida construcción, nunca certifica. |

#### Generación (cómo se emite el scaffold)

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `streaming-files-protocol.md`          | Orden de scaffold por valor entregado: tests → utilities → infraestructura.                                  |
| `test-organization-by-scenario.md`     | Regla universal: organizar por carpetas (una por HU) cuando hay ≥3 HUs; flat para proyectos chicos.          |
| `step-isolation-pattern.md`            | Aislamiento de métricas y criterios por step (setup/auth/main/cleanup) usando tags.                           |

#### Post-generación (gates obligatorios antes de declarar success)

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `post-generation-execution-prompt.md`  | Prompt universal post-scaffold para resolver modo (`full` / `dry-run` / `scaffold-only` / `execute-only`) antes del smoke gate. |
| `smoke-gate-policy.md`                 | Smoke gate 1:1 obligatorio antes de declarar success; comando por stack y comportamiento ante fallo.         |
| `delivery-gate-contract.md`            | Bloque YAML universal de cierre con `status`, `blockers[]`, `evidence_persisted{}` y `audit_log`.            |

#### Evidencia y trazabilidad

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `test-evidence-and-traceability.md`    | Configuración de reportes, traces, summaries y trazabilidad requisito → test → resultado.                    |
| `results-structure-universal.md`       | Convención universal `results/{categoría}/{fecha}/` para los 4 frameworks (diffabilidad y compatibilidad CI). |
| `execution-metadata-schema.md`         | Schema universal `{ISO}-metadata.json` (13 keys) emitido por cada corrida en los 4 frameworks.               |
| `environment-blocker-evidence.md`      | Schema `.evidence/execution-status.json` para reportar bloqueos (WAF, network, auth, rate-limit, device, etc.) sin auto-corregir. |

#### Operación (ejecución, triage, auto-corrección)

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `test-execution-orchestration/SKILL.md`| Ejecutar las suites generadas: invocar comandos, capturar output, parsear resultados, gestionar modos.       |
| `failure-triage-and-classification/SKILL.md` | Clasifica fallos como deterministic vs flaky y diagnostica causa raíz antes de proponer corrección.    |
| `test-self-correction-loop/SKILL.md`   | Loop iterativo de auto-corrección con anti-cheating guardrails (max 3 iteraciones por default).              |
| `test-self-healing/SKILL.md`           | Self-healing en runtime: multi-locator fallback, LLM-driven selector repair, visual AI healing.              |

#### Transversales (seguridad, contratos, datos, CI)

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `cicd-integration/SKILL.md`            | Integración de las cuatro suites en pipelines Azure DevOps / GitHub Actions / GitLab CI.                     |
| `security-testing/SKILL.md`            | Estrategia de seguridad: OWASP Top 10 API, fuzzing, SAST/DAST/SCA, autenticación.                            |
| `contract-testing/SKILL.md`            | CDC con Pact, OpenAPI diff, AsyncAPI, Spring Cloud Contract, Schema Registry.                                |
| `context-determined-defaults/SKILL.md` | Defaults inferidos del contexto del cliente (data class, criticality tiers, regulatory exposure, peak).      |
| `sut-types-and-adaptations/SKILL.md`   | Adaptaciones por tipo de SUT (REST, GraphQL, gRPC, eventos, ML inference, serverless, SOAP/EJB, batch).      |
| `test-data-management/SKILL.md`        | Builder/Factory/ObjectMother, datasets versionados, anonimización PII, data para perf, sintética. Ante ausencia de datos reales, sintéticos deterministas (Faker + seed) coherentes con los data buckets del mock. |
| `service-virtualization-mockoon/SKILL.md` | Service virtualization con Mockoon para construir/validar pruebas sin backend desplegado: environment JSON versionable, mock desde OpenAPI, CRUD stateful con data buckets, SOAP/XML, proxy hybrid, CLI/Docker en CI y switchover mock → real solo-configuración. Bundle con 7 references. |
| `ui-locator-map-contract.md`           | Contrato QA+dev de identificadores UI (`data-testid` / accessibility ids) versionado en `locator-map.json`, para que las pruebas front/mobile construidas antes del desarrollo no fallen por drift de selectores; incluye validación de drift al llegar la app real y enforcement explícito (sin mapa no se generan page objects salvo waiver del usuario). |
| `figma-mcp-integration.md`             | Consumo de Figma como fuente UI vía MCP (server oficial remoto con OAuth o Framelink con PAT) con setup guiado por IDE y fallback REST API; un link público de Figma no es consumible sin conexión autenticada. |
| `alm-mcp-integration.md`               | Integración con Azure DevOps (`@azure-devops/mcp`) y Jira (Atlassian Remote MCP) vía MCP: traer HUs/work items/test plans y llevar test cases, estados, defectos y documentos, con setup guiado, gates de escritura, idempotencia y trazabilidad. Puerta ALM de todo el chapter. |

#### Capacidades transversales complementarias (accesibilidad, SEO, visual)

| Asset                                  | Descripción                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `transversal-capabilities.md`          | Detecta qué capas complementarias (accesibilidad, SEO, seguridad, visual, contract, performance) teje el diseño según intent + tipo de SUT + contexto regulatorio. La invoca el Paso 2.5 del router. |
| `accessibility/SKILL.md`               | Accesibilidad WCAG/POUR: revisión desde diseño (Product Designer) + pruebas automatizadas, con marco normativo (foco banca/financiero), severidad, formato de hallazgo y estructura de reporte. Bundle con 6 references. |
| `seo/SKILL.md`                         | Auditoría SEO técnica agnóstica de stack para pruebas web; 8 dimensiones (técnico, on-page, performance, schema, imágenes, sitemap, hreflang, accesibilidad) como references. |
| `visual-regression.md`                 | Política transversal de regresión visual (web/móvil): baselines, dinamismo, match levels, anti-patrones.    |

#### Funcional — análisis, diseño, estrategia y plan (`skills/_all/`)

| Asset | Capacidad |
|---|---|
| `funcional-story-analysis/SKILL.md` | Análisis de HUs: scoring INVEST con evidencia, calidad de criterios de aceptación, taxonomía de ambigüedades/vacíos como preguntas al PO, veredicto Definition of Ready. |
| `funcional-story-refinement/SKILL.md` | Refinamiento propuesto (nunca impuesto): reescritura antes/después, splitting SPIDR, Example Mapping / Tres Amigos; aplica al ALM solo lo aprobado por el PO. |
| `funcional-test-design/SKILL.md` | Casos de alto nivel con técnicas ISTQB declaradas (particiones, BVA, tablas de decisión, estados, pairwise, error guessing, exploratorio), Gherkin español data-driven, trazabilidad CA→caso al 100%. |
| `funcional-test-strategy/SKILL.md` | Estrategia: niveles/cuadrantes, enfoque risk-based, frontera con lo unitario, mapeo a los stacks de automatización y al camino shift-left (mocks, locator map). |
| `funcional-test-plan/SKILL.md` | Plan ISO/IEC/IEEE 29119-3 (equivalencia IEEE 829): riesgos con análisis, criterios entrada/salida/suspensión medibles, RTM, informes de avance y reporte de cierre. |

El trabajo funcional produce documentos y artefactos ALM (no código): sus casos alimentan a los stacks de automatización, y sus insumos/resultados viajan a Azure DevOps / Jira vía `[[calidad-alm-mcp-integration]]`.

**Por qué es cross-cutting y no un stack**: no tiene artefacto detectable en un repositorio (los stacks se detectan por `karate-config.js`, `playwright.config.ts`, `webdriverio` en el `package.json`), el router bifurca a él en el paso 2 —antes de elegir framework— y sus assets los referencian skills transversales. Vive en `skills/_all/`, `workflows/_all/` y `prompts/_all/`, y por tanto viaja en todos los bundles.

#### Convenciones Cucumber (`skills/_all/cucumber-bdd-conventions/`)

| Asset | Capacidad |
|---|---|
| `cucumber-bdd-conventions/SKILL.md` | Arquetipos donde Cucumber orquesta varias plataformas o drivers a la vez: catálogo de steps y protocolo de reutilización, sufijo de plataforma contra ambigüedad del registro global, tagging y naming, estructura de archivos, contrato de hooks y World, y 12 propiedades verificables por análisis estático con sus comandos. |

Aplica a cualquier stack con Gherkin —Appium WebdriverIO, Playwright usado como librería, Karate— y es la capa que hace mantenible un repositorio híbrido web y mobile.

### Skills per-framework

#### Karate (`skills/karate/`)

| Asset                            | Capacidad                                                                                       |
|----------------------------------|-------------------------------------------------------------------------------------------------|
| `karate-greenfield/SKILL.md`     | Genera proyecto Karate completo desde un spec OpenAPI/Swagger/WSDL.                             |
| `karate-brownfield/SKILL.md`     | Extiende un proyecto Karate existente respetando convenciones, sin regenerar infraestructura.   |
| `karate-run-and-tags.md`         | Comandos Maven, ejecución por tag o environment, semántica de tags estándar.                    |

Incluye references específicas como `negative-coverage-formula.md` (con `risk_factor` modulado por negocio), `contract-testing-match-patterns.md`, `encrypted-payloads.md` y `client-specific-conventions.md` (patrones genéricos para proyectos brownfield donde el cliente impone convenciones propias).

#### Playwright (`skills/playwright/`)

| Asset                              | Capacidad                                                                                              |
|------------------------------------|--------------------------------------------------------------------------------------------------------|
| `playwright-greenfield/SKILL.md`   | Genera proyecto Playwright E2E web completo desde fuentes UI reales (URL viva, Figma, Storybook).      |
| `playwright-brownfield/SKILL.md`   | Extiende o ajusta un proyecto Playwright existente respetando convenciones.                            |
| `playwright-run-and-modes.md`      | Modos de ejecución (headless, headed, UI, debug, visual, a11y) y override de BASE_URL.                 |

Incluye references para Page Object Model, fixtures, selectores, auth storage state, mocks `page.route`, visual regression y accesibilidad axe/WCAG.

#### K6 (`skills/k6/`)

| Asset                         | Capacidad                                                                                      |
|-------------------------------|------------------------------------------------------------------------------------------------|
| `k6-greenfield/SKILL.md`      | Genera proyecto K6 completo de performance testing desde un spec OpenAPI/Swagger.              |
| `k6-brownfield/SKILL.md`      | Extiende un proyecto K6 existente sin tocar scripts preexistentes.                              |
| `k6-run-and-suite.md`         | Instalación y ejecución de scripts K6 individuales y la suite completa con `run-all.sh`.        |

Arquitectura modular: `scenarios/ + workloads/ + tests/{escenario}/main.js + shared/`. Cinco tipos de script (smoke, load, stress, spike, soak) con `options.scenarios` y executors (`ramping-vus`, `constant-vus`, `ramping-arrival-rate`). Includes references para thresholds en tres tiers con justificación, smoke 1:1 gate, contractual checks desde user story, auth strategy (setup-vs-per-vu), métricas de disponibilidad desde RNF, tag policy + step isolation, sleep policy realista, correlación dinámica de IDs en CRUD, extracción de enums/headers/security, vocabulary mapping (línea-base/carga/estrés vs smoke/load/stress), discovery checklist, preflight, templates y schema de results/metadata.

#### Appium Serenity (`skills/appium-serenity/`)

| Asset                                          | Capacidad                                                                                  |
|------------------------------------------------|--------------------------------------------------------------------------------------------|
| `appium-screenplay-android/SKILL.md`           | Genera proyecto Appium V2 Android con Screenplay + Serenity + Cucumber listo para correr.  |
| `appium-apk-auto-discovery/SKILL.md`           | Recorrido automatizado del APK (crawler + Appium Inspector REST API) que extrae locators reales con score de confianza; alternativa a locators diferidos. |
| `appium-brownfield/SKILL.md`                   | Extiende un proyecto Appium Android/iOS existente respetando convenciones; plataforma detectada del proyecto. |
| `appium-run-and-tags.md`                       | Comandos Gradle, filtros por tags y override de env.                                       |

Incluye references para capas Screenplay, locators diferidos vs auto-discovery (score de confianza por selector), smoke vs proposed scenarios, smoke gate Gradle, matriz de versiones Gradle inmutable, health-check pipeline, accesibilidad móvil, visual regression móvil, reglas anti-colisión de tasks Gradle, y el paquete de robustez mobile endurecido con feedback de campo: protocolo de resolución de locators (identidad ≠ capacidad, con la matriz Flutter verificada), catálogo de interacciones de experto (escritura, OTP, scroll W3C, esperas, recuperación), y protocolo de evidencia y triage (screenshot → page source como árbol → log del mock antes de hipotetizar; checklist anti falsos-verdes de reportería).

#### Appium Core (`skills/appium-core/`)

| Asset | Capacidad |
|---|---|
| `mobile-locator-resolution/SKILL.md` | Protocolo de resolución de locators: identidad no es capacidad, conteo de nodos igual a uno, validación por efecto externo. Incluye qué ve Appium en una app Flutter y el race del árbol de semántica. |
| `mobile-interactions/SKILL.md` | Canon de escritura, campos OTP, gestos W3C, esperas en tres capas, pantallas condicionales y aserciones que verifican el contrato en vez de la mera presencia. |
| `appium-apk-auto-discovery/SKILL.md` | Descubre locators reales recorriendo el binario: bootstrap de emulador, view hierarchy vía la API REST del inspector, extracción con score de confianza y cleanup. Alternativa a los locators diferidos cuando no hay mapa de identificadores. |

Es el conocimiento mobile **agnóstico del lenguaje**: opera contra el servidor Appium y el árbol de accesibilidad del dispositivo, no contra el cliente. Los stacks de producto aportan la sintaxis; cada SKILL trae su tabla de equivalencias Java y TypeScript. Vive aparte precisamente para que no se duplique entre `appium-serenity` y `appium-wdio` —el patrón que ya nos costó una divergencia— y para que un cliente de Karate no lo reciba sin necesitarlo.

#### Appium WebdriverIO (`skills/appium-wdio/`)

| Asset                                          | Capacidad                                                                                  |
|------------------------------------------------|--------------------------------------------------------------------------------------------|
| `appium-wdio-greenfield/SKILL.md`              | Genera un arquetipo mobile multi-plataforma en TypeScript (WebdriverIO + cucumber-js): Android, iOS, iPad, tablet y navegador móvil, en local y en device farm. |
| `appium-wdio-brownfield/SKILL.md`              | Extiende un arquetipo TypeScript existente respetando sus convenciones, con línea base de propiedades antes de tocar nada. |
| `appium-wdio-run-and-profiles.md`              | Perfiles de cucumber-js, filtros por tag y combinación de plataforma, modo de ejecución y tipo de dispositivo. |

Incluye references con la matriz de capabilities de cada plataforma —el bloque WebDriverAgent de iOS documentado capability por capability, que es donde falla la primera sesión en cualquier máquina nueva—, ciclo de vida del servidor Appium y de emuladores gestionado por el propio framework, el patrón de perfil-de-plataforma-como-dato que evita un hook por plataforma, ejecución local contra device farm con fallback de dispositivos y cancelación de sesión en cola, contextos nativo y webview con deep links y diálogos del sistema, selectores fuera del código en archivos de test-data, capa de objetos de pantalla, evidencia y video, idioma como dimensión de prueba, y una tabla de fallos conocidos con causa y solución verificadas.

La capa Cucumber de este stack —catálogo de steps, sufijo de plataforma, tagging, propiedades verificables— no se duplica aquí: viene de `[[calidad-cucumber-bdd-conventions]]`.

#### serenity-wdio (`skills/serenity-wdio/`)

| Asset                                          | Capacidad                                                                                  |
|------------------------------------------------|--------------------------------------------------------------------------------------------|
| `serenity-wdio-greenfield/SKILL.md`            | Genera proyecto TypeScript + WebdriverIO v9 + Serenity/JS v3 + Cucumber 11 multiplataforma (web, web_movil, movil Android/iOS, desktop, api) con Screenplay puro. |
| `serenity-wdio-brownfield/SKILL.md`            | Extiende un proyecto serenity-wdio existente respetando convenciones detectadas, sin regenerar infraestructura. |
| `serenity-wdio-screenplay-pattern/SKILL.md`    | Implementación Screenplay por canal: `PageElement`+`By` en web, selectores `string` encapsulados en mobile, `@serenity-js/rest` en api. |
| `serenity-wdio-cucumber-gherkin/SKILL.md`      | Convenciones de `.feature` y step-definitions: tags de canal/suite/tipo, aislamiento por archivo de steps. |
| `serenity-wdio-api-testing-rest/SKILL.md`      | Pruebas de API REST con `@serenity-js/rest`: `CallAnApi`, `Send`, `LastResponse`, `ChangeApiConfig`, autenticación. |
| `serenity-wdio-webdriverio-handling/SKILL.md`  | Cuándo usar WebdriverIO directo vs encapsulado en Interactions; referencia rápida de comandos `browser.*`. |
| `serenity-wdio-test-execution-runner/SKILL.md` | Diagnóstico de ejecución, variables de entorno y orquestador `scripts/run.mjs` por modo y plataforma. |
| `serenity-wdio-reporting/SKILL.md`             | Configuración de reporters (Allure, Serenity BDD, cucumber JSON, video), lectura de fallos y troubleshooting de reportes. |
| `serenity-wdio-troubleshooting/SKILL.md`       | Problemas generales y específicos de mobile nativo (window handles `NATIVE_APP`, contextos híbridos, selectores por plataforma). |
| `serenity-wdio-run-and-tags.md`                | Comandos del orquestador `scripts/run.mjs` por `--mode`/`--platform`, mapeo a `.env.<modo>` y filtros de tags de Cucumber. |

Incluye references para plataformas y alcance (diferenciación con el stack `appium`), inputs obligatorios, estructura de proyecto, configs WDIO por modo, convenciones Screenplay, tags de Cucumber, gates y evidencia, pre-flight por plataforma, `STRATEGY.md.tpl`, aislamiento de steps, smoke gate del orquestador y emisor de metadata.

### Workflows

| Tipo                                   | Asset                                                                                  |
|----------------------------------------|----------------------------------------------------------------------------------------|
| Router rector                          | `workflows/_all/route-test-generation.workflow.md`                                     |
| Executive report (cross-framework)     | `workflows/_all/generate-executive-report.workflow.md` — consolidado HTML/PPTX/DOC post-corrida. |
| Self-correction loop (cross-framework) | `workflows/_all/test-self-correction-loop.workflow.md` — invocado como fase final por todos los workflows de stack. |
| Karate greenfield                      | `workflows/karate/generate-karate-greenfield.workflow.md`                              |
| Karate brownfield                      | `workflows/karate/extend-karate-brownfield.workflow.md`                                |
| Playwright greenfield                  | `workflows/playwright/generate-playwright-greenfield.workflow.md`                      |
| Playwright brownfield                  | `workflows/playwright/update-playwright-brownfield.workflow.md`                        |
| K6 greenfield                          | `workflows/k6/generate-k6-suite.workflow.md`                                           |
| K6 brownfield                          | `workflows/k6/extend-k6-brownfield.workflow.md`                                        |
| K6 calibración                         | `workflows/k6/calibrate-k6-thresholds.workflow.md`                                     |
| Appium JVM greenfield                      | `workflows/appium-serenity/generate-appium-screenplay-android.workflow.md`                      |
| Appium JVM brownfield                      | `workflows/appium-serenity/extend-appium-brownfield.workflow.md`                                |
| Appium JVM locators                        | `workflows/appium-serenity/complete-deferred-locators.workflow.md`                              |
| Appium WebdriverIO greenfield          | `workflows/appium-wdio/generate-appium-wdio-greenfield.workflow.md`                    |
| Appium WebdriverIO brownfield          | `workflows/appium-wdio/extend-appium-wdio-brownfield.workflow.md`                      |
| Appium WebdriverIO — migrar selectores | `workflows/appium-wdio/migrate-selectors-to-testdata.workflow.md`                      |
| serenity-wdio greenfield               | `workflows/serenity-wdio/generate-serenity-wdio-greenfield.workflow.md`                |
| serenity-wdio brownfield                | `workflows/serenity-wdio/extend-serenity-wdio-brownfield.workflow.md`                 |
| serenity-wdio locators                  | `workflows/serenity-wdio/complete-deferred-locators.workflow.md`                      |
| Funcional — análisis/refinamiento      | `workflows/_all/analyze-and-refine-stories.workflow.md`                                |
| Funcional — diseño de casos + ALM      | `workflows/_all/design-test-cases.workflow.md`                                         |
| Funcional — estrategia y plan          | `workflows/_all/build-test-strategy-and-plan.workflow.md`                              |

### Prompts (`prompts/`)

| Framework  | Prompts disponibles                                                                                                        |
|------------|----------------------------------------------------------------------------------------------------------------------------|
| Transversal (`_all`) | `generate-mockoon-environment` (data file Mockoon desde spec; opt-in cuando `execution_target` es mock/hybrid)   |
| Funcional  | `analyze-user-story`, `generate-high-level-test-cases`, `generate-test-plan-document`                                      |
| Karate     | `analyze-openapi-for-karate`, `generate-karate-feature`, `generate-karate-match-schema`                                    |
| Playwright | `detect-pages-from-ui-source`, `generate-page-object`, `generate-accessibility-suite`, `generate-mock-handlers`            |
| K6         | `extract-config-from-openapi`, `generate-k6-script`, `generate-utils-and-payloads`                                         |
| Appium Serenity | `validate-appium-inputs`, `generate-cucumber-feature-android`, `generate-screenplay-task`                              |
| Appium WebdriverIO | `validate-appium-wdio-inputs`                                                                                        |
| serenity-wdio | `validate-serenity-wdio-inputs`, `generate-cucumber-feature`, `generate-screenplay-task`                                |

## Instalación y sync — cómo llegan los assets a tu IDE

Los assets del chapter no se copian a mano: los distribuye la CLI **`pragma-ai`** desde el Hub de SOPP hacia el IDE que uses. El flujo estándar es:

```bash
# 1. Una vez por máquina: autenticación con OAuth2 (token en llavero del sistema)
pragma-ai login

# 2. En la raíz del proyecto QA, inicializar el entorno (elegir el stack del proyecto)
cd mi-proyecto-tests
pragma-ai init --ide kiro --chapter calidad --stack karate        # API testing
# o:
pragma-ai init --ide kiro --chapter calidad --stack playwright   # E2E web
pragma-ai init --ide kiro --chapter calidad --stack k6            # performance
pragma-ai init --ide kiro --chapter calidad --stack appium-serenity # mobile Android/JVM (Java + Gradle + Serenity BDD)
pragma-ai init --ide kiro --chapter calidad --stack appium-wdio   # mobile TypeScript (WebdriverIO + cucumber-js)
pragma-ai init --ide kiro --chapter calidad --stack appium-core   # compañero obligatorio de cualquier stack mobile
pragma-ai init --ide kiro --chapter calidad --stack serenity-wdio # web + web_movil + mobile Android/iOS + desktop + API (TypeScript + WebdriverIO)

# 3. Verificar instalación
pragma-ai status

# 4. Mantener al día (correr periódicamente)
pragma-ai update --dry-run    # ver qué cambiaría
pragma-ai update              # aplicar
```

`init` crea `pragma.yaml` en la raíz del proyecto, descarga los assets del chapter Calidad para el stack indicado (más todos los skills cross-cutting de `_all/`) en el path nativo del IDE, agrega `.pragma/` al `.gitignore` e instala los hooks para telemetría. Detalle completo de la CLI en el manual de `pragma-ai`.

**Stacks soportados en el chapter:** `karate`, `playwright`, `k6`, `appium-serenity`, `appium-wdio`, `appium-core` y `serenity-wdio`. `appium-serenity` (Java + Gradle + Serenity BDD) y `appium-wdio` (TypeScript + WebdriverIO + cucumber-js) son los dos stacks mobile de producto, mutuamente excluyentes por proyecto; **`appium-core` acompaña a cualquiera de los dos y se instala aparte** (`init` una vez por stack). `serenity-wdio` (TypeScript + WebdriverIO v9 + Serenity/JS) es un stack independiente que cubre web, web_movil, mobile Android **e iOS**, desktop y API sobre un único arquetipo multiplataforma. El trabajo **funcional** (análisis/refinamiento de HUs, diseño de casos, estrategia, planes, integración ALM) y las **convenciones Cucumber** no son stacks: son cross-cutting y llegan con cualquier `init`, sin pedirlos. Si la suite combina varios frameworks (APIs + UI + mobile en el mismo repositorio), correr `init` una vez por stack — los assets `_all/` solo se descargan en la primera corrida y los específicos de cada stack se suman sin conflicto. Un repositorio híbrido web y mobile necesita los stacks correspondientes, no uno solo.

**Multi-IDE** en el mismo proyecto: repetir `--ide`:

```bash
pragma-ai init --ide kiro --ide claude-code --chapter calidad --stack karate
```

**Diagnóstico** cuando algo no funciona:

```bash
pragma-ai doctor          # checa Hub, token, hooks, observabilidad
pragma-ai rollback        # restaura bundle anterior si un update rompió algo
```

## Cobertura por IDE

Cada IDE soporta un subset de los tipos de asset. Esta es la matriz para el chapter Calidad:

| Asset del Chapter | Cantidad | Kiro | Claude Code | GitHub Copilot | Amazon Q (IDE) | Amazon Q (CLI) |
|---|---|---|---|---|---|---|
| `steering`     | 3   | ✓ | ✓ | ✓ | ✓ | ✓ |
| `skill`        | 52  | ✓ | ✓ | ✓ | ✓ | ✓ |
| `workflow`     | 16  | ✓ | ✓ | ✓ | ✓ | ✓ |
| `prompt`       | 18  | ✓ | — | ✓ | ✓ | — |

Implicaciones operativas:

- **Claude Code y Amazon Q (CLI)**: reciben steering + skills + workflows del chapter pero **no los prompts**. Quienes usan estos IDEs invocan la lógica del prompt desde el skill o workflow correspondiente (el prompt es un template, su lógica vive replicada en el skill que lo referencia).
- **GitHub Copilot y Amazon Q (IDE)**: cobertura completa salvo `agent` (no presente en este chapter).
- **Kiro**: cobertura completa de los 4 tipos del chapter; es el IDE de referencia para los ejemplos de uso más abajo.

Paths de destino por IDE (típicos, después de `pragma-ai init`):

| IDE | Path workspace |
|---|---|
| Kiro            | `.kiro/skills/<id>/SKILL.md`, `.kiro/steering/<id>.md` |
| Claude Code     | `.claude/rules/<id>.md`, `CLAUDE.md` (steering concatenado) |
| GitHub Copilot  | `.github/skills/<id>/SKILL.md`, `.github/prompts/<id>.prompt.md`, `.github/copilot-instructions.md` (steering concatenado) |
| Amazon Q (IDE)  | `.amazonq/rules/<id>.md` |
| Amazon Q (CLI)  | `.amazonq/rules/<id>.md` |

## Cómo empezar

Una vez los assets están instalados en tu IDE vía `pragma-ai init`, el punto de entrada para generar pruebas es el **workflow router**:

```
workflows/_all/route-test-generation.workflow.md
```

Ese workflow se encarga de:

1. Recolectar inputs obligatorios (`[[calidad-mandatory-inputs-protocol]]`).
2. **SUT readiness gate** (`[[calidad-sut-readiness-gate]]`, paso 1.5): ¿el desarrollo está desplegado, o las pruebas deben ser ejecutables antes del desarrollo? Resuelve `execution_target` (real/mock/hybrid), `data_strategy` (real/synthetic) y, para front/mobile, la existencia del `locator_map` (`[[calidad-ui-locator-map-contract]]`). En modo pre-desarrollo endurece los inputs (spec con response schemas para API; Figma + locator map para Playwright; locator map para Appium) y activa `[[calidad-service-virtualization-mockoon]]`.
3. Identificar framework (`[[calidad-intent-detection]]`) — incluida la **ruta funcional**: los intents de análisis/refinamiento de HUs, diseño de casos, estrategia y plan bifurcan aquí directo a los workflows funcionales cross-cutting (`[[calidad-analyze-and-refine-stories]]`, `[[calidad-design-test-cases]]`, `[[calidad-build-test-strategy-and-plan]]`), sin spec-validation ni gates de ejecución, con delivery gate documental y gates humanos propios (aprobación del PO, confirmación antes de escribir al ALM).
4. Validar el spec si aplica (`[[calidad-spec-validation]]`).
5. Decidir greenfield vs brownfield (`[[calidad-brownfield-vs-greenfield]]`).
6. **Pre-diseño**: redactar `STRATEGY.md` y esperar aprobación humana (`[[calidad-pre-design-strategy-document]]`). Incluye la sección "Execution target y plan de switchover" cuando se prueba antes del desarrollo. En greenfield es obligatorio; en brownfield grande se simplifica a un delta-strategy.
7. Delegar al workflow específico del framework + modo correspondiente.
8. Emitir archivos con disciplina de scaffold por valor (`[[calidad-streaming-files-protocol]]`).
9. Configurar evidencia y trazabilidad (`[[calidad-test-evidence-and-traceability]]` + `[[calidad-results-structure-universal]]` + `[[calidad-execution-metadata-schema]]`).
10. **Resolver modo de operación** con el usuario (`[[calidad-post-generation-execution-prompt]]`): `full` / `dry-run` / `scaffold-only` / `execute-only`. Si `execution_target` es mock/hybrid, el mock se levanta antes del smoke gate.
11. **Smoke gate 1:1 obligatorio** (`[[calidad-smoke-gate-policy]]`) antes de declarar success. Si falla → status `partial`, no continúa a suite completa. Contra mock es gate de construcción válido y registra `executed_against`; K6 contra mock ejecuta SOLO el smoke 1:1 (jamás load/stress).
12. **Ejecución + triage + auto-corrección** del ciclo: `[[calidad-test-execution-orchestration]]` → `[[calidad-failure-triage-and-classification]]` → `[[calidad-test-self-correction-loop]]` (con `[[calidad-test-self-healing]]` cuando aplica). Bloqueos de ambiente se reportan vía `[[calidad-environment-blocker-evidence]]` (no se intenta auto-corregir el ambiente).
13. **Executive report** consolidado HTML/PPTX/DOC (`[[calidad-generate-executive-report]]`) cuando el modo es `full` o `execute-only`.
14. **Delivery gate contract** YAML (`[[calidad-delivery-gate-contract]]`) emitido como bloque final con `status`, `blockers[]`, `evidence_persisted{}`, `audit_log`, `execution_target` y `certification` (`pending_real_integration` cuando se corrió contra mock; el switchover a integraciones reales es solo configuración). Sin ese bloque, la entrega se considera incompleta.

No saltar pasos: el router protege contra la generación con inputs incompletos, sin diseño aprobado o sin ejecución verificada.

**El contrato de entrega del Chapter incluye ejecución + verificación + auto-corrección.** Generar tests sin ejecutarlos es entrega incompleta. Anti-cheating maestro del chapter: tests en suites `@security`, `@contract`, `@compliance`, `@regulatory`, `@accessibility` NO se modifican por auto-corrección bajo ningún concepto. En brownfield, la auto-corrección NUNCA toca tests preexistentes.

## Mimir — dónde vive el conocimiento de verdad

**Mimir es la fuente de administración. Este repositorio es la fuente de autoría.**
Se escribe aquí, se sincroniza a Mimir, y la CLI de pragma-ai lo baja a los IDEs
desde Mimir. Nada llega a un IDE directamente desde este repo.

### `_config/` es legado y no se usa

`_config/ides.json`, `_config/asset-schemas.json`, `_config/taxonomy.json` y
`_config/templates/` **ya no gobiernan nada**. Mimir administra los tipos, los
scopes, la taxonomía y el mapeo a cada IDE.

**No los edites para "arreglar" nada.** Si un asset aterriza mal en un IDE, o si
un tipo o un campo no se acepta, es tema de Mimir o de la CLI: se reporta, no se
parchea aquí. Lo único que este repositorio produce son assets.

Se conservan como registro histórico de cómo estaba modelado el chapter antes de
Mimir, y porque algún script de tooling todavía los lee para validar la fuente
antes de sincronizar — nunca para decidir a dónde va nada.

### Los cuatro niveles

| Nivel | Dónde se escribe | A quién llega |
|---|---|---|
| **Chapter** | `chapters/calidad/` | Todas las cuentas |
| **Stack** | `chapters/calidad/skills/{stack}/` | Los proyectos que usan ese stack |
| **Cuenta** | `accounts/{cliente}/{chapter}/_cuenta/` | Todos los proyectos de esa cuenta |
| **Proyecto** | `accounts/{cliente}/{chapter}/{proyecto}/` | Un solo proyecto de la cuenta |

`accounts/` está **excluido del control de versiones** (`.git/info/exclude`): el
core no lleva nombres de cliente. Por eso `chapters/` tiene que ser agnóstico —
un nombre de cliente ahí viaja a todas las demás cuentas.

### Sincronizar

```bash
export MIMIR_BASE_URL=https://api-mimir.pragma.com.co
export MIMIR_TOKEN='Bearer …'        # Cognito, vida ~1h: pedir fresco cada sesión

# Chapter: incremental contra el baseline de sync-state.json
python3 migration/migrate_to_mimir.py --sync --dry-run
python3 migration/migrate_to_mimir.py --sync

# Cuenta: un destino por proyecto, cada uno con su propio estado
python3 migration/sync_account.py --client <cliente> --chapter calidad \
    --account <id> --frente <proyecto> --project <codigo> \
    --project-folder <proyecto> --audit
```

Reglas que cuestan caro aprender por las malas:

- **El `id` es la identidad.** Cambiarlo crea un documento nuevo y deja huérfano
  al viejo. Mover un archivo con `git mv` sin tocar el `id` es una actualización.
- **Ningún sync borra.** Lo que se retira de la fuente sigue en Mimir hasta que
  alguien lo elimine a mano.
- **`--only` nunca junto a `--prune`**: `--only` filtra la fuente, así que todo
  lo demás aparece como huérfano y `--prune` lo borraría.
- **Si un alta reporta error, el documento puede existir igualmente** sin quedar
  registrado en el estado. Verificar por el UUID del mensaje de error antes de
  reintentar, o se duplica.
- **El listado de documentos va rezagado** respecto de los documentos reales. No
  es la verdad: verificar por UUID.
- **Los archivos de un bundle se quedan en *staging*** hasta el siguiente PUT del
  documento. El script ya hace ese commit; si se sube algo a mano, hay que
  hacerlo.
- **El token es de super admin.** Nunca salir del alcance del chapter Calidad.

### `applies_to_stacks`

`_all/` significa «puede ir a todos los bundles», no «va a todos». Un asset de
`_all/` puede declarar a qué stacks aplica:

```yaml
applies_to_stacks: [playwright, appium-core, appium-wdio, appium-serenity]
```

Sin el campo se instala en todos, que es el comportamiento correcto para lo
verdaderamente transversal. Con él, deja de instalarse donde no aplica: un
contrato de locators no existe en una suite de carga, y la auditoría SEO no
tiene nada que hacer en un bundle de Appium.

El criterio sale del «cuándo aplicar» del propio documento, no de una intuición.
Si al escribirlo no puedes nombrar el stack donde **no** sirve, no lo acotes.

## Convenciones internas

- **Frontmatter completo** sólo en assets accionables: `SKILL.md`, archivos `*.workflow.md`, archivos `*.prompt.md` y archivos de steering.
- **References** (todo lo que vive en `references/*.md` dentro de un skill) son **plain markdown sin frontmatter**: son material de apoyo del skill que las referencia.
- **Chapter README** (este archivo) es **plain markdown sin frontmatter**: no es un asset indexable.
- **Prose en español**; **código en inglés** (identificadores, comentarios técnicos, paths, comandos).
- **Sin emojis** en ningún asset.
- **Links entre assets**:
  - `[[asset-id]]` para cualquier asset con `id:` en su frontmatter — es la forma portable porque sobrevive al sync de IDEs (Kiro, Cline, Claude Code, etc.) que aplanan workflows/prompts/steering a una sola carpeta.
  - References (archivos sin frontmatter dentro de `references/`) se enlazan por **path relativo** sólo cuando el documento que las cita vive en el **mismo skill folder** (ej. el `SKILL.md` apunta a sus propias references). Para references de **otro skill**, citar el skill por `[[skill-id]]` y mencionar el archivo en prosa (`consultar references/Y.md en su subfolder`); el path relativo cross-skill se rompe al sync.
- **Convenciones cliente-específicas detectadas en brownfield** se documentan como patrones genéricos en `skills/karate/karate-brownfield/references/client-specific-conventions.md`. El brownfield detecta y respeta esas convenciones (naming con prefix de ticket, headers transversales obligatorios, estilo step-by-step, etc.) sin nombrar clientes concretos.
  - El override de inputs obligatorios (cuando el cliente impone convenciones estrictas, `user_story` y `firma` pasan a obligatorios) se documenta en `skills/_all/mandatory-inputs-protocol.md` con pointer al skill.

### Dónde va cada asset (decidir esto mal es lo que más caro sale)

| Alcance | Carpeta | Criterio |
|---|---|---|
| Cross-cutting del chapter | `skills/_all/`, `workflows/_all/`, `prompts/_all/` | Aplica a **todos** los stacks. Viaja en todos los bundles. |
| Stack de producto | `skills/{stack}/` | Es de una tecnología concreta y los stacks son **mutuamente excluyentes por proyecto**. |
| Companion de familia | `skills/appium-core/` | Aplica a varios stacks de una misma familia pero **no a todos** los del chapter. Se instala aparte, junto al stack de producto. |
| Cuenta | `accounts/{cliente}/{chapter}/_cuenta/` | Es del cliente, no del chapter, y vale para **todos** sus proyectos. Fuera de git. |
| Proyecto | `accounts/{cliente}/{chapter}/{proyecto}/` | Vale para **un** repositorio del cliente. Su alcance va escrito en la primera línea del cuerpo, no en el frontmatter: el frontmatter no sobrevive a los IDEs que concatenan todo el steering en un archivo. |

Las tres preguntas, en orden:

1. ¿Sirve a un cliente que solo hace API o performance? → `_all`.
2. ¿Sirve a más de un stack de la misma familia, pero no a todos? → companion (`appium-core`).
3. ¿Es de una tecnología sola? → su stack.

**Lo que no se hace**: duplicar el mismo conocimiento en dos stacks. Diverge — ya ocurrió con el bloque de diagnóstico de los brownfield, que se copió a los cuatro stacks citando defectos de Serenity en Karate, K6 y Playwright.

Un companion **declara su dependencia en los workflows que lo requieren** (Paso 0 de verificación) porque no se instala solo.

### Regresión: correr antes de cada commit grande

```bash
python3 scripts/audit-chapter.py        # fuente: 7 checks, exit 1 si hay hallazgos
python3 scripts/build-kiro-bundles.py   # construye salida/{stack}/.kiro/
python3 scripts/audit-kiro-bundles.py   # bundles: cobertura, refs, paths rotos
```

`audit-chapter.py` verifica sobre la fuente:

| Check | Qué detecta |
|---|---|
| Frontmatter e ids únicos | Campos faltantes, semver inválido, `scope`/`stack` incoherentes, ids duplicados |
| Carpeta contra stack declarado | Un asset movido de carpeta al que se le olvidó actualizar `stack:` |
| Referencias `[[id]]` | Punteros a assets que no existen |
| Portabilidad | Paths relativos que **salen del bundle**: se rompen al aplanar en el IDE |
| References propias | Un bundle que cita una reference suya que ya no está ahí |
| Cadena de certificación | Que los eslabones del recorrido completo de una historia sigan existiendo |
| Workflows huérfanos | Un workflow que ningún asset invoca: camino inalcanzable |

Los tres últimos son los que fallan **después de mover archivos**, y son silenciosos: nada revienta, el agente simplemente se queda sin el conocimiento a mitad del recorrido.

### Al mover o renombrar assets

1. Usar `git mv`: preserva historial y el sync a Mimir lo ve como actualización, no como alta y baja.
2. **No cambiar los `id`.** El id es la identidad estable; la carpeta y el stack son metadata. Un id nuevo crea un documento nuevo en Mimir y deja huérfano al viejo.
3. Actualizar el campo `stack:` de todo lo movido.
4. Reconectar los punteros: buscar el nombre viejo del archivo y de la carpeta en todo el chapter.
5. Correr la regresión completa.
6. Tras sincronizar, **verificar archivos huérfanos en Mimir**: el migrador sube y actualiza, pero nunca borra. Un archivo de bundle que se movió a otro sitio permanece en el documento anterior hasta que se elimine a mano.


## Roadmap

Items conocidos pendientes en el chapter:

- **Appium iOS greenfield (V3)** — el scaffolder greenfield V2 solo genera proyectos Android (limitación de tooling). El brownfield Appium SÍ soporta Android e iOS (la plataforma se detecta del proyecto). El generador V3 con soporte iOS greenfield queda pendiente.
- **AsyncAPI testing formal** — hoy `[[calidad-contract-testing]]` documenta AsyncAPI/Schema Registry/Pact Messaging como referencia. Queda pendiente un skill greenfield específico para eventos (Kafka, SNS/SQS, AMQP/RabbitMQ, Google Pub/Sub) basado en AsyncAPI 3.0, con scaffold de tests de contract de payload + integración con el broker.
- **Profundizar el catálogo de marcos regulatorios del alcance del Chapter** (LATAM + Estados Unidos): hoy se cubren PCI-DSS, OWASP API, ISO 27001, SOC 2, HIPAA, SOX, CCPA/CPRA, FedRAMP, Ley 1581, LGPD, LFPDPPP, Ley 19.628/21.719, Ley 25.326, Ley 29.733 y equivalentes locales LATAM. Marcos fuera de este alcance (UE, APAC, África) se escalan caso a caso, no se incorporan al chapter por defecto.

## Maintainers

Chapter Calidad — Pragma. Para cambios, propuestas de nuevos assets o reportes de inconsistencias, abrir un PR siguiendo las convenciones internas listadas arriba.

---

## Ejemplos de uso desde Kiro

Esta sección muestra escenarios reales de un QA usando el Chapter Calidad desde **Kiro** (el chat integrado en el IDE, similar a Cursor / Cline / Amazon Q Developer). En todos los ejemplos el QA escribe en lenguaje natural y Kiro decide qué skill, workflow o prompt invocar.

> **Prerrequisito común a todos los ejemplos**: los assets ya están en `.kiro/` porque el QA corrió previamente:
> ```bash
> pragma-ai login   # una vez por máquina
> pragma-ai init --ide kiro --chapter calidad --stack <karate|playwright|k6|appium-serenity|appium-wdio|serenity-wdio>
> ```
> El stack se elige según el framework del proyecto. Sin este paso, Kiro no tiene visibilidad de `[[calidad-route-test-generation]]`, `@karate-greenfield`, ni el resto de assets. Si los ejemplos se ejecutan desde otro IDE, ajustar el `--ide` (`claude-code`, `cursor`, `github-copilot`, `amazon-q-ide`, `amazon-q-cli`) y considerar la **Cobertura por IDE** arriba — los `prompt`-type no llegan a Claude Code ni Amazon Q (CLI).

El objetivo es ilustrar el **contrato completo** del chapter: no basta con generar archivos, hay que **ejecutarlos, triar fallos y aplicar auto-corrección** cuando aplica. Cada ejemplo declara explícitamente el modo de operación efectivo (`full` / `dry-run` / `scaffold-only` / `execute-only`).

### Cómo invocar los assets desde Kiro

Existen **tres modos de invocación**. Elegir uno u otro depende del nivel de control que el QA quiera tener sobre el routing.

1. **Workflow completo (recomendado por default)** — el QA describe la intención (qué quiere lograr, sobre qué SUT) y deja que el router `[[calidad-route-test-generation]]` clasifique el caso y delegue al workflow correcto. Es la entrada natural y aplica los guardrails de `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-intent-detection]]`, `[[calidad-transversal-capabilities]]` (Paso 2.5: detecta y propone capas complementarias — accesibilidad, SEO, seguridad, visual, contract, performance — según intent, tipo de SUT y contexto regulatorio), `[[calidad-spec-validation]]` y `[[calidad-brownfield-vs-greenfield]]` antes de generar nada.
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

#### 2. Karate Brownfield — Cliente regulado agrega endpoint con convenciones propias

**Setup**: proyecto Karate existente en `pagos-cliente-tests/` con `karate-config.js`, features previos y convenciones consolidadas del cliente. Nuevo endpoint `POST /transferencia` agregado al spec. ticket_prefix = `TICKET-4521`. Body_Mode = A (JSON externo). Cliente regulado → modo `dry-run` automático.

```
> QA: Agrega el endpoint POST /transferencia al proyecto pagos-cliente-tests. Ticket TICKET-4521, body en JSON externo.

> Kiro: Detecto intent "karate brownfield" en proyecto con convenciones cliente-específicas estrictas. Activo el override de [[calidad-mandatory-inputs-protocol]] (user_story y firma son obligatorios cuando el cliente impone convenciones; ticket_prefix y Body_Mode ya los proporcionaste).
>
> Aplico [[calidad-brownfield-vs-greenfield]] para detectar convenciones del proyecto existente:
>   - headers strategy: `one-by-one` (detectado en features previos)
>   - body strategy: `external-json` (detectado en `resources/files/`)
>   - naming prefix: `TICKET-` (detectado en tags y nombres de scenario)
>   - headers transversales obligatorios detectados intactos: `Transaction-Id`, `Sid`, `Auth-Id`, `X-Channel` (NO se modifican, ver `references/client-specific-conventions.md`)
>
> Delego a `extend-karate-brownfield`. Como el cliente es regulado, [[calidad-test-execution-orchestration]] fuerza `mode: dry-run`. Genero:
>   1. `src/test/java/transferencia/transferencia.feature` (nuevo)
>   2. `src/test/resources/files/transferencia-valid.json` (nuevo)
>   3. NO toco `karate-config.js`, NO toco features previos.
>
> Ejecuto: `mvn test -Dkarate.options="--tags @TICKET-4521"`. Resultado: 4/5 pass, 1 fail por spec drift (el spec declara `metadata.channel` como required pero la API real lo trata como opcional).
>
> Triage [[calidad-failure-triage-and-classification]]: deterministic, causa = spec drift. [[calidad-test-self-correction-loop]] propone el diff (cambiar `#string` por `##string` en el campo opcional) pero NO aplica porque estamos en dry-run.

> QA: Entendido. ¿Qué pasa con el cambio?

> Kiro: Genero el reporte de cambios propuestos en `.evidence/dry-run-TICKET-4521.json` con el diff completo, justificación y trazabilidad al ticket. Creo ticket Jira de aprobación para el QA Lead del cliente. El cambio NO se aplica hasta que haya firma humana.
>
> Estado final: partial (dry-run). Modo efectivo: dry-run.
```

**Artefactos resultantes**:
- `src/test/java/transferencia/transferencia.feature`
- `src/test/resources/files/transferencia-valid.json`
- `.evidence/dry-run-TICKET-4521.json`
- Ticket Jira de aprobación (creado vía MCP)

**Cierre**: `partial`. Diff propuesto archivado bajo audit log del cliente. Espera aprobación humana.

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
