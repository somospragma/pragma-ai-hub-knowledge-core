---
id: calidad-asset-resolver
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO al encontrar una referencia entre dobles corchetes que no exista con ese nombre. Traduce cada id del chapter al titulo y a la carpeta con que la CLI lo instala en el IDE. Sin esta tabla las referencias cruzadas del chapter no resuelven y el conocimiento obligatorio no se abre."
tags: [resolver, referencias, navegacion, enforcement, mandatory, generado]
enforcement: mandatory
generated_by: scripts/build-asset-resolver.py
---

# Asset Resolver — Traducir una Referencia al Nombre Instalado

## Cuándo aplicar

En cuanto encuentres una referencia entre dobles corchetes y no exista ningún
archivo ni carpeta con ese nombre. No es un enlace roto del documento: es que la
referencia es el **identificador en la fuente del chapter**, y la CLI instala
cada asset con un nombre derivado de su título, no de su id.

Ejemplo real: `[[calidad-failure-triage-and-classification]]` vive instalado en
`failure-triage-and-classification-clasificacion-de-fallos-y-analisis-de-causa-ra`.

## Instrucción

1. **Nunca des por inexistente un asset porque su identificador no aparezca.** Búscalo
   en la tabla de abajo y abre la carpeta de la columna *Instalado como*.
2. Si la carpeta no existe con ese nombre exacto, **busca por título**: el nombre
   instalado siempre empieza por las primeras palabras del título, en minúsculas
   y con guiones.
3. Si aun así no aparece, el asset no se instaló en este workspace. Dilo
   explícitamente: *"`X` está referenciado pero no instalado aquí"*. No lo
   sustituyas por tu criterio ni sigas adelante en silencio, sobre todo si el
   asset es una compuerta obligatoria.

### Dónde buscar según el IDE

| IDE | Skills | Steering / instrucciones | Workflows |
|---|---|---|---|
| Kiro | `.kiro/skills/<carpeta>/SKILL.md` | `.kiro/steering/<carpeta>.md` | `.kiro/workflows/<carpeta>.workflow.md` |
| GitHub Copilot | `.github/skills/<carpeta>/SKILL.md` | `.github/instructions/<carpeta>-instruction.md` | `.github/workflows/<carpeta>.workflow.md` |
| Claude Code | `.claude/skills/<carpeta>/SKILL.md` | `.claude/rules/<carpeta>.md` | `.claude/workflows/<carpeta>.workflow.md` |
| Amazon Q | `.amazonq/rules/<carpeta>.md` | `.amazonq/rules/<carpeta>.md` | `.amazonq/rules/<carpeta>.md` |

Un asset con `references/` cuelga de su propia carpeta:
`<ruta-del-skill>/references/<archivo>.md`.

## Lo que nunca debes hacer

- **Nunca concluyas que un recurso no existe a partir de una búsqueda que no
  comprobaste que corrió.** Una salida vacía puede ser "no hay resultados" o
  puede ser "el comando falló". Comprueba el código de salida antes de afirmar
  ausencia, y busca por dos caminos distintos antes de declarar que falta algo
  que un documento afirma que existe.
- **Nunca reemplaces un skill obligatorio que no encontraste por tu propio
  criterio.** Que no lo halles no reduce lo que exige.

## Tabla de traducción


### Steering / instrucciones

| Referencia | Instalado como |
|---|---|
| `[[calidad-alm-write-guard]]` | `alm-write-guard-nada-se-escribe-en-el-sistema-del-cliente-sin-permiso` |
| `[[calidad-chapter-entry-point]]` | `punto-de-entrada-del-chapter-calidad` |
| `[[calidad-chapter-perspective]]` | `perspectiva-del-chapter-calidad-de-pragma` |
| `[[calidad-execution-discipline-protocol]]` | `execution-discipline-protocol-no-se-ejecuta-a-ciegas` |
| `[[calidad-post-generation-protocol]]` | `post-generation-protocol-disciplina-obligatoria-despues-del-ultimo-archivo` |
| `[[calidad-pre-generation-protocol]]` | `pre-generation-protocol-disciplina-obligatoria-antes-del-primer-archivo` |
| `[[calidad-session-continuity-protocol]]` | `session-continuity-protocol-antes-de-responder-saber-donde-quedaste` |

### Workflows

| Referencia | Instalado como |
|---|---|
| `[[calidad-analyze-and-refine-stories]]` | `workflow-analizar-y-refinar-historias-de-usuario` |
| `[[calidad-build-test-strategy-and-plan]]` | `workflow-construir-estrategia-y-plan-de-pruebas` |
| `[[calidad-calibrate-k6-thresholds]]` | `calibrate-k6-thresholds-workflow` |
| `[[calidad-complete-deferred-locators]]` | `workflow-completar-locators-diferidos` |
| `[[calidad-design-test-cases]]` | `workflow-disenar-casos-de-prueba-y-publicarlos-al-alm` |
| `[[calidad-extend-appium-brownfield]]` | `workflow-extender-proyecto-appium-brownfield` |
| `[[calidad-extend-appium-wdio-brownfield]]` | `extender-arquetipo-appium-webdriverio` |
| `[[calidad-extend-k6-brownfield]]` | `extend-k6-brownfield-workflow` |
| `[[calidad-extend-karate-brownfield]]` | `workflow-extender-proyecto-karate-brownfield` |
| `[[calidad-generate-appium-screenplay-android]]` | `workflow-generar-proyecto-appium-screenplay-android` |
| `[[calidad-generate-appium-wdio-greenfield]]` | `generar-arquetipo-appium-webdriverio` |
| `[[calidad-generate-executive-report]]` | `workflow-generar-reporte-ejecutivo-post-corrida` |
| `[[calidad-generate-k6-suite]]` | `generate-k6-suite-workflow` |
| `[[calidad-generate-karate-greenfield]]` | `workflow-generar-proyecto-karate-greenfield` |
| `[[calidad-generate-playwright-greenfield]]` | `workflow-generar-proyecto-playwright-greenfield` |
| `[[calidad-migrate-selectors-to-testdata]]` | `migrar-selectores-hardcodeados-a-test-data` |
| `[[calidad-route-test-generation]]` | `route-test-generation-workflow-rector-del-chapter-calidad` |
| `[[calidad-seo-audit-workflow]]` | `workflow-seo-tecnico-auditoria-de-calidad-frontendbackend` |
| `[[calidad-test-self-correction-loop-workflow]]` | `test-self-correction-loop-workflow-estandar-de-ejecucion-triage-y-auto-correccio` |
| `[[calidad-update-playwright-brownfield]]` | `workflow-actualizar-proyecto-playwright-brownfield` |

### Skills

| Referencia | Instalado como |
|---|---|
| `[[calidad-accessibility-testing]]` | `accesibilidad-politica-y-metodologia-transversal` |
| `[[calidad-alm-mcp-integration]]` | `alm-mcp-integration-azure-devops-y-jira-desde-el-agente` |
| `[[calidad-alm-test-publishing-cycle]]` | `alm-test-publishing-cycle-de-la-historia-al-caso-y-de-vuelta-al-feature` |
| `[[calidad-alm-write-authorization-gate]]` | `alm-write-authorization-gate-nada-se-escribe-sin-permiso` |
| `[[calidad-appium-apk-auto-discovery]]` | `skill-appium-apk-auto-discovery` |
| `[[calidad-appium-brownfield]]` | `appium-brownfield` |
| `[[calidad-appium-run-and-tags]]` | `ejecucion-y-filtros-de-tags-appium-screenplay-android` |
| `[[calidad-appium-screenplay-android]]` | `appium-screenplay-android` |
| `[[calidad-appium-wdio-brownfield]]` | `appium-webdriverio-extension-de-arquetipo-existente` |
| `[[calidad-appium-wdio-greenfield]]` | `appium-webdriverio-arquetipo-multi-plataforma-en-typescript` |
| `[[calidad-appium-wdio-run-and-profiles]]` | `ejecucion-por-perfiles-y-filtros-por-tag` |
| `[[calidad-asset-resolver]]` | `asset-resolver-traducir-una-referencia-al-nombre-instalado` |
| `[[calidad-automation-feasibility-assessment]]` | `automation-feasibility-assessment-que-se-puede-automatizar-y-que-se-hace-con-lo` |
| `[[calidad-brownfield-vs-greenfield]]` | `brownfield-vs-greenfield-reglas-de-generacion-por-modo` |
| `[[calidad-business-driven-prioritization]]` | `business-driven-prioritization-prioridad-por-valor-de-negocio` |
| `[[calidad-cicd-integration]]` | `cicd-integration-integracion-de-suites-de-pruebas-en-pipelines` |
| `[[calidad-context-determined-defaults]]` | `context-determined-defaults-defaults-derivados-del-contexto-no-del-sector` |
| `[[calidad-contract-testing]]` | `contract-testing-estrategia-de-contratos-entre-servicios` |
| `[[calidad-cross-platform-learning-propagation]]` | `cross-platform-learning-propagation-aprender-una-vez-aplicar-en-todas` |
| `[[calidad-cucumber-bdd-conventions]]` | `cucumber-bdd-convenciones-de-arquetipo-multi-plataforma` |
| `[[calidad-data-volatility-and-assertion-anchoring]]` | `data-volatility-and-assertion-anchoring-que-texto-sirve-de-ancla` |
| `[[calidad-delivery-gate-contract]]` | `delivery-gate-contract-bloque-yaml-de-cierre-obligatorio` |
| `[[calidad-environment-blocker-evidence]]` | `environment-blocker-evidence-schema-universal-evidenceexecution-statusjson` |
| `[[calidad-execution-metadata-schema]]` | `execution-metadata-schema-iso-metadatajson-universal` |
| `[[calidad-execution-preflight]]` | `execution-preflight-demostrar-que-la-corrida-toca-el-sut` |
| `[[calidad-executive-report-generator]]` | `executive-report-generator-reporte-ejecutivo-post-corrida-universal` |
| `[[calidad-failure-triage-and-classification]]` | `failure-triage-and-classification-clasificacion-de-fallos-y-analisis-de-causa-ra` |
| `[[calidad-figma-mcp-integration]]` | `figma-mcp-integration-consumir-disenos-de-figma-como-fuente-ui` |
| `[[calidad-flutter-locators-and-gestures]]` | `flutter-localizacion-y-gestos-en-movil-y-web` |
| `[[calidad-funcional-story-analysis]]` | `story-analysis-analisis-riguroso-de-historias-de-usuario` |
| `[[calidad-funcional-story-refinement]]` | `story-refinement-refinamiento-propuesto-decision-humana` |
| `[[calidad-funcional-test-design]]` | `test-design-casos-de-prueba-de-alto-nivel-con-tecnicas-formales` |
| `[[calidad-funcional-test-plan]]` | `test-plan-plan-de-pruebas-y-entregables-de-gestion` |
| `[[calidad-funcional-test-strategy]]` | `test-strategy-estrategia-de-pruebas` |
| `[[calidad-intent-detection]]` | `intent-detection-seleccion-de-framework-de-automatizacion` |
| `[[calidad-k6-brownfield]]` | `k6-brownfield` |
| `[[calidad-k6-greenfield]]` | `k6-greenfield` |
| `[[calidad-k6-run-and-suite]]` | `ejecucion-de-k6-comandos-y-suite` |
| `[[calidad-karate-brownfield]]` | `karate-brownfield` |
| `[[calidad-karate-greenfield]]` | `karate-greenfield` |
| `[[calidad-karate-run-and-tags]]` | `ejecucion-karate-y-semantica-de-tags` |
| `[[calidad-mandatory-inputs-protocol]]` | `mandatory-inputs-protocol-contrato-de-entrada-antes-de-generar` |
| `[[calidad-mobile-interactions]]` | `interacciones-y-aserciones-mobile` |
| `[[calidad-mobile-locator-resolution]]` | `resolucion-de-locators-mobile` |
| `[[calidad-pipeline-state-tracking]]` | `pipeline-state-tracking-la-traza-que-sobrevive-a-la-sesion` |
| `[[calidad-platform-parameterised-steps]]` | `steps-unificados-por-parametro-de-plataforma` |
| `[[calidad-playwright-brownfield]]` | `playwright-brownfield` |
| `[[calidad-playwright-from-live-app]]` | `playwright-desde-aplicacion-viva` |
| `[[calidad-playwright-greenfield]]` | `playwright-greenfield` |
| `[[calidad-playwright-run-and-modes]]` | `modos-de-ejecucion-de-playwright` |
| `[[calidad-post-generation-execution-prompt]]` | `post-generation-execution-prompt-confirmacion-universal-antes-de-smoke-gate` |
| `[[calidad-pre-design-strategy-document]]` | `pre-design-strategymd-universal-antes-de-generar-codigo` |
| `[[calidad-repo-capability-discovery]]` | `repo-capability-discovery-mirar-antes-de-construir` |
| `[[calidad-results-structure-universal]]` | `results-structure-convencion-universal-resultscategoriafecha` |
| `[[calidad-security-testing]]` | `security-testing-estrategia-de-pruebas-de-seguridad` |
| `[[calidad-seo]]` | `seo-auditoria-tecnica-para-pruebas-web` |
| `[[calidad-service-virtualization-mockoon]]` | `service-virtualization-con-mockoon-mock-de-servicios-para-construir-pruebas` |
| `[[calidad-session-reuse-and-isolation]]` | `session-reuse-and-isolation-compartir-sin-arrastrar-estado` |
| `[[calidad-smoke-gate-policy]]` | `smoke-gate-policy-universal-cross-stack` |
| `[[calidad-spec-validation]]` | `spec-validation-validacion-de-contratos-antes-de-generar` |
| `[[calidad-step-isolation-pattern]]` | `step-isolation-pattern-aislamiento-de-metricas-y-criterios-por-step` |
| `[[calidad-streaming-files-protocol]]` | `orden-de-scaffold-por-valor-entregado` |
| `[[calidad-sut-readiness-gate]]` | `sut-readiness-gate-probar-antes-de-que-el-desarrollo-exista` |
| `[[calidad-sut-types-and-adaptations]]` | `sut-types-and-adaptations-catalogo-y-adaptacion-de-frameworks-por-tipo-de-sistem` |
| `[[calidad-test-data-management]]` | `test-data-management-datos-de-prueba-reproducibles-y-conformes` |
| `[[calidad-test-evidence-and-traceability]]` | `test-evidence-and-traceability-reportes-y-tags-por-framework` |
| `[[calidad-test-execution-orchestration]]` | `test-execution-orchestration-ejecucion-y-parseo-de-resultados-como-capacidad-del` |
| `[[calidad-test-organization-by-scenario]]` | `test-organization-by-scenario-cuando-carpetas-cuando-flat` |
| `[[calidad-test-self-correction-loop]]` | `test-self-correction-loop-auto-correccion-controlada-con-guardrails-anti-cheatin` |
| `[[calidad-test-self-healing]]` | `test-self-healing-estrategias-de-resiliencia-en-runtime-con-guardrails-anti-chea` |
| `[[calidad-transversal-capabilities]]` | `deteccion-de-capacidades-transversales-complementarias` |
| `[[calidad-ui-locator-map-contract]]` | `ui-locator-map-contract-identificadores-acordados-antes-del-desarrollo` |
| `[[calidad-visual-regression]]` | `regresion-visual-politica-transversal-de-pruebas` |

### Prompts

| Referencia | Instalado como |
|---|---|
| `[[calidad-appium-generate-cucumber-feature-prompt]]` | `prompt-generar-loginfeature-appium-android` |
| `[[calidad-appium-generate-screenplay-task-prompt]]` | `prompt-generar-task-screenplay-appium-android` |
| `[[calidad-appium-validate-inputs-prompt]]` | `prompt-validar-inputs-appium-screenplay-android` |
| `[[calidad-appium-wdio-validate-inputs-prompt]]` | `prompt-validar-inputs-appium-webdriverio` |
| `[[calidad-funcional-analyze-story-prompt]]` | `prompt-analizar-una-historia-de-usuario` |
| `[[calidad-funcional-generate-test-cases-prompt]]` | `prompt-generar-casos-de-prueba-de-alto-nivel` |
| `[[calidad-funcional-generate-test-plan-prompt]]` | `prompt-generar-documento-de-plan-de-pruebas` |
| `[[calidad-generate-mockoon-environment-prompt]]` | `prompt-generar-environment-mockoon-opt-in` |
| `[[calidad-k6-extract-config-prompt]]` | `prompt-extract-config-from-openapi` |
| `[[calidad-k6-generate-script-prompt]]` | `prompt-generate-k6-script` |
| `[[calidad-k6-generate-utils-prompt]]` | `prompt-generate-k6-utils-and-payloads` |
| `[[calidad-karate-analyze-openapi-prompt]]` | `prompt-analizar-spec-para-karate` |
| `[[calidad-karate-generate-feature-prompt]]` | `prompt-generar-feature-karate` |
| `[[calidad-karate-generate-match-schema-prompt]]` | `prompt-generar-matchjson` |
| `[[calidad-playwright-detect-pages-from-ui-source-prompt]]` | `prompt-detectar-paginas-desde-fuente-ui` |
| `[[calidad-playwright-extract-pages-from-live-app-prompt]]` | `prompt-extraer-paginas-desde-aplicacion-viva` |
| `[[calidad-playwright-generate-a11y-prompt]]` | `prompt-generar-suite-de-accesibilidad` |
| `[[calidad-playwright-generate-mock-handlers-prompt]]` | `prompt-generar-mock-handlers-opt-in` |
| `[[calidad-playwright-generate-page-object-prompt]]` | `prompt-generar-page-object` |


---

*Tabla generada por `scripts/build-asset-resolver.py` desde la fuente del
chapter. Si una fila no coincide con lo instalado, la fuente cambió y hay que
regenerarla: no la edites a mano.*
