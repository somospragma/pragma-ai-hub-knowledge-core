---
id: calidad-cicd-integration
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Integración de las suites Karate, Playwright, K6, Appium y serenity-wdio en pipelines Azure DevOps / GitHub Actions / GitLab CI con paralelización, gates de calidad y agregación de reportes."
tags: [cicd, azure-devops, github-actions, gitlab-ci, sharding, gates, allure, reportportal, serenity-wdio]
---

# CI/CD Integration — Integración de Suites de Pruebas en Pipelines

## Cuándo aplicar

Aplica este skill **cada vez que una suite generada debe correr en pipeline**, ya sea:

- como **PR check** (validación obligatoria antes de merge),
- como **nightly build** (regresión completa fuera de horario de trabajo),
- como **release gate** (bloqueo de despliegue a producción si los gates de calidad no se cumplen),
- o como **trigger manual** (smoke tests por demanda, validación post-deploy).

Pragma trabaja predominantemente con **Azure DevOps Pipelines** como plataforma CI/CD primaria, pero los clientes pueden requerir **GitHub Actions** o **GitLab CI** según su stack interno. Este skill cubre las tres plataformas con paridad funcional.

Activa este skill después de generar suites con `[[calidad-karate-greenfield]]`, `[[calidad-karate-brownfield]]`, `[[calidad-playwright-greenfield]]`, `[[calidad-playwright-brownfield]]`, `[[calidad-k6-greenfield]]`, `[[calidad-appium-screenplay-android]]`, `[[calidad-serenity-wdio-greenfield]]` o `[[calidad-serenity-wdio-brownfield]]`, y siempre en paralelo con `[[calidad-test-evidence-and-traceability]]` para asegurar que los reportes generados queden archivados como evidencia auditable.

## Instrucción

1. **Definir el trigger** — Decide si la suite corre en `pr` (validación de PRs hacia `main`/`develop`), `push` (después de merge), `schedule` (nightly/cron), `release` (gate de despliegue) o `manual`/`workflow_dispatch`. Las suites de carga (K6) NUNCA deben correr en cada PR — solo nightly o manual. Snippets de triggers por plataforma en `references/azure-devops-pipeline-templates.md`, `references/github-actions-workflows.md`, `references/gitlab-ci-jobs.md`.
2. **Seleccionar agente** — Linux para Karate/Playwright/K6/serenity-wdio (más rápido y barato); Windows si la suite usa Edge legacy o componentes específicos de IIS; macOS para Appium iOS (obligatorio por Xcode) y para serenity-wdio en modo `movil` iOS. Pool self-hosted si el SUT está en red privada. Consideraciones en `references/azure-devops-pipeline-templates.md`.
3. **Instalar tooling** — Cachear dependencias para reducir tiempos: JDK 17 + Maven (`~/.m2`) para Karate; Node 20 + `npm ci` (`~/.npm`) para Playwright y serenity-wdio; binario `k6` (descarga directa o imagen Docker `grafana/k6`); Appium Server + Android SDK / Xcode para mobile. Para serenity-wdio en modo `movil`, añadir Appium Server + drivers (`uiautomator2` / `xcuitest`) al paso de instalación. Patrones de cache por plataforma documentados en cada template.
4. **Ejecutar con paralelización** — Elige la estrategia de sharding apropiada por framework. Playwright soporta `--shard=i/n` nativo. Karate usa `karate.parallel` con threads. K6 NO se shardea (es la herramienta de carga; se distribuye VUs entre runners). Appium se paraleliza por device en grids cloud. Detalle en `references/sharding-and-parallelization.md`.
5. **Publicar resultados como artifacts** — JUnit XML, HTML reports, screenshots, videos, traces, summaries K6. Usa `PublishTestResults@2` en Azure, `actions/upload-artifact@v4` en GitHub, `artifacts:` en GitLab. Retención mínima 30 días en PR, 90 días en nightly.
6. **Agregar reportes** — Allure como dashboard por defecto (simple, ampliamente adoptado en Pragma). ReportPortal para clientes que requieren ML-based failure clustering e integración con Jira/ALM. Setup por tecnología en `references/allure-aggregation.md` y `references/rp-integration.md`.
7. **Aplicar gates de calidad** — Cobertura mínima por endpoint (Karate), thresholds K6 (p95/p99/error_rate), pixel diff Playwright visual, accessibility violations, vulnerabilidades High/Critical de security. Cada gate debe **fallar el build** automáticamente; los overrides requieren justificación obligatoria en el commit message. Detalle en `references/quality-gates.md`.

8. **Diagnosticar los fallos del pipeline como entorno distinto, no como "lo mismo pero más lento"** — El runner no tiene aceleración gráfica, su red no es la de la máquina de desarrollo y arranca siempre en frío. Antes de tocar el YAML: descartar la red del propio puesto, mirar las capturas de la corrida y separar petición rechazada de petición sin respuesta. Detalle en `references/runner-is-not-your-machine.md`.

## Restricciones

- **NUNCA** commit de tokens, secrets, credenciales reales, claves privadas o certificados en archivos YAML del pipeline. Usa secret stores (Azure Key Vault, GitHub Secrets, GitLab masked variables, HashiCorp Vault) según `references/secrets-in-pipelines.md`.
- **NUNCA** ejecutar suites de carga (K6) en agentes shared sin coordinación previa con el equipo de plataforma del cliente. Las pruebas de carga consumen recursos del runner y pueden degradar otros pipelines concurrentes. Reservar agentes dedicados o pools self-hosted.
- **NUNCA** correr suites mobile contra el cloud real (BrowserStack/SauceLabs) en cada PR — coste prohibitivo. Usar emuladores locales en PR; reservar device cloud para nightly y release gates. Detalle en `references/mobile-cloud-providers.md`.
- **NUNCA** desactivar un gate de calidad sin justificación documentada en el commit message (`SKIP_GATE: <razón>`). El override debe ser visible en el historial.
- **NUNCA** publicar reportes con datos sensibles (PII, tokens, payloads de producción) sin enmascarar. Coordina con `[[calidad-test-evidence-and-traceability]]`.
- Si la suite incluye cobertura de seguridad (`[[calidad-security-testing]]`), los gates SAST/SCA/DAST son **obligatorios** además de los gates funcionales.
- Sigue `[[calidad-mandatory-inputs-protocol]]` para confirmar la plataforma CI/CD del cliente antes de generar el pipeline (Azure DevOps vs GitHub Actions vs GitLab CI no es intercambiable).

## Cross-links

- `references/azure-devops-pipeline-templates.md`
- `references/github-actions-workflows.md`
- `references/gitlab-ci-jobs.md`
- `references/sharding-and-parallelization.md`
- `references/quality-gates.md`
- `references/runner-is-not-your-machine.md`
- `references/allure-aggregation.md`
- `references/rp-integration.md`
- `references/secrets-in-pipelines.md`
- `references/mobile-cloud-providers.md`
