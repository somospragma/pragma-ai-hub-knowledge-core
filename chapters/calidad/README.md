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
- **Workflows brownfield K6 y Appium** — declarados en el router como placeholders (`extend-k6-brownfield`, `extend-appium-brownfield`); en construcción por agentes paralelos del chapter.
- **Skill formal de contract testing** consumer-driven con Pact, complementario a `match` patterns de Karate.

## Maintainers

Chapter Calidad — Pragma. Para cambios, propuestas de nuevos assets o reportes de inconsistencias, abrir un PR siguiendo las convenciones internas listadas arriba.
