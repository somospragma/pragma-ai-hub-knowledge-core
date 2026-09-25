---
id: calidad-pre-design-strategy-document
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "STRATEGY.md design-doc obligatorio aprobado por el usuario ANTES de generar código de tests. Aplica a los 5 stacks en greenfield; delta-strategy en brownfield."
tags: [pre-design, strategy, mandatory, universal, gate]
enforcement: mandatory
---

# Pre-design — STRATEGY.md universal antes de generar código

Principio universal del chapter calidad: **NUNCA se genera código de tests sin un `STRATEGY.md` aprobado explícitamente por el usuario**. El `STRATEGY.md` es el design doc que precede a templates, scaffolds y prompts. El agente lo redacta a partir de los inputs mandatorios y del análisis del SUT, lo presenta al usuario, e itera hasta que el usuario emite la palabra "aprobado" (o equivalente).

Aplica a los 5 stacks (Karate, Playwright, K6, Appium, serenity-wdio) en greenfield. En brownfield, el documento puede simplificarse a un "delta-strategy" focalizado en lo nuevo.

## Reglas de operación

1. El `STRATEGY.md` se genera y se presenta al usuario **antes de emitir el primer archivo de código**.
2. El usuario aprueba con frase explícita (`aprobado`, `procede`, `ok continuar`) o pide cambios (`modificar X`, `cambiar Y`).
3. Si pide cambios, el agente itera el documento y lo vuelve a presentar. No avanza a templates hasta aprobación explícita.
4. El `STRATEGY.md` se persiste en `output_path/STRATEGY.md` y se referencia en `delivery_gate.inputs_confirmed.ui_source_or_spec` (campo strategy) y luego en el reporte ejecutivo (sección 2 — Cumplimiento de SLAs).
5. Si el IDE corre en modo batch sin posibilidad de pregunta interactiva, el agente emite el `STRATEGY.md` propuesto, marca el delivery gate como `partial` y bloquea generación de código hasta aprobación humana asíncrona documentada en `.evidence/strategy-approval.md`.

## Estructura genérica del STRATEGY.md

Las secciones 1 a 7 son comunes a todos los stacks. La sección 8 ("Estrategia por stack") se rellena con el bloque específico cuyo detalle está en el `STRATEGY.md` de la skill del stack correspondiente.

### 1. Contexto

- SUT: nombre, descripción funcional en 1 párrafo.
- Tipo de SUT: API pública / API privada / Frontend web / Mobile Android / Híbrido.
- Equipo y stakeholders: roles consultables (Dev, Infra, QA lead, PO).
- Stack tecnológico del SUT: lenguaje, framework, runtime, cloud provider si aplica.
- Tipo de relación: greenfield (proyecto nuevo) o brownfield (extender proyecto existente).

### 2. Volumen y SLAs

- Usuarios concurrentes esperados (peak vs sostenido).
- Peak QPS o throughput objetivo (por endpoint si aplica).
- SLA de latencia: p50, p95, p99 por endpoint / página crítica.
- SLA de disponibilidad (% uptime objetivo).
- SLA de error rate máximo tolerable.
- Ventanas de mantenimiento / horarios pico.

Si un SLA no se conoce, declararlo explícitamente como "a determinar" — NUNCA inventar. La sección 2 del reporte ejecutivo se construye desde esta sección.

### 3. Alcance funcional

- HUs / endpoints / páginas / features en scope (lista enumerada).
- HUs / endpoints / páginas / features explícitamente fuera de scope (lista enumerada con justificación).
- Criterios de aceptación por unidad funcional (mínimo 1 línea por HU).
- Prioridad por unidad: CRITICAL / HIGH / MEDIUM / LOW (proviene del `risk_map`).

### 4. Dependencias externas

- Auth: tipo (Bearer / OAuth2 / SAML / Cookie), provider (Cognito / Auth0 / propio), endpoint para obtener token, refresh policy.
- Bases de datos: lectura o escritura desde tests, instancia compartida o aislada, política de cleanup.
- Servicios de terceros consumidos: con o sin mock, gestión de cuotas y rate limits.
- Sistemas mensajería: Kafka / SQS / RabbitMQ — se prueban o se mockean.

### 5. Riesgos conocidos

- WAF en el ambiente de prueba: sí / no — proveedor, riesgo de bloqueo por carga, allowlist coordinada con Infra.
- Rate limits explícitos: ¿documentados? ¿se respetan o se prueban?
- Ambiente compartido vs dedicado: riesgo de interferencia entre runs.
- Datos sensibles: PII, PCI, PHI — política de masking y retención.
- Restricciones regulatorias (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultean modo a `dry-run`.

### 6. Execution target y plan de switchover (mock vs real)

Sale del `[[calidad-sut-readiness-gate]]` (paso 1.5 del router). Obligatoria aunque el target sea `real` (en ese caso, una línea que lo declare):

- `execution_target`: `real` / `hybrid` / `mock` — ¿contra qué corre la fase de ejecución de esta entrega?
- Si `mock` o `hybrid`: herramienta y ubicación del mock (`[[calidad-service-virtualization-mockoon]]`, data file en `mocks/mockoon/environment.json`), rutas mockeadas vs passthrough (hybrid), seed Faker compartido con la suite.
- `data_strategy`: `real` / `synthetic` — y si es sintética, locale + seed (`[[calidad-test-data-management]]`).
- Front/mobile: estado del locator map (`[[calidad-ui-locator-map-contract]]`) — versión acordada y con quién.
- **Plan de switchover**: punto de configuración por el que se cambia mock → real (env/profile, cero cambios en tests), checklist de certificación y responsable de la re-ejecución contra integraciones reales. Detalle en `[[calidad-service-virtualization-mockoon]]` (consultar `references/mock-vs-real-switchover.md` en su subfolder).
- Declaración explícita: la corrida contra mock valida construcción; la certificación queda `pending_real_integration` hasta la corrida real.

### 7. Próximos pasos y entregables

- Lista de archivos que el agente va a generar (alto nivel — no path-a-path).
- Comando de ejecución que se entregará al usuario.
- Reporte ejecutivo que se generará al cierre (formato pactado).
- Hitos de revisión: post-scaffold, post-smoke, post-suite completa.

### 8. Estrategia por stack

Esta sección la rellena el `STRATEGY.md` del stack específico:

- Karate: cobertura por endpoint con `effective_minimum`, risk_map, conventions cliente (si brownfield), Body_Mode, Scenario_Prefix.
- Playwright: pages identificadas, `mock_mode`, priorities por página, mock_endpoints, auth strategy.
- K6: 3 escenarios obligatorios (baseline / load / stress) + opt-in spike/soak, executor por escenario, workload, auth strategy.
- Appium: capabilities, device matrix, screens identificadas, locator strategy (auto-discovery vs deferred), app_package / app_activity.
- serenity-wdio: plataformas en scope (`web`, `web_movil`, `movil`, `desktop`, `api`), modos y configs correspondientes, capabilities (para mobile: Bundle ID / app_package verificado), locator strategy (`PageElement`+`By` para web, selectores string para mobile), Screenplay conventions (Tasks/Interactions/Questions), datos de prueba por módulo. En brownfield: delta-strategy enfocado en lo nuevo; no rediseñar infraestructura existente (`configs/`, `scripts/run.mjs`, `.env.*`).

## Regla anti-cheating

No se permite "tomar atajos saltando STRATEGY.md" bajo el argumento de "el caso es simple" o "es solo un endpoint". Cada proyecto pasa por `STRATEGY.md` aprobado, sin excepciones. Saltarlo invalida la entrega y el `delivery_gate.status` se reporta como `failed` con `blocker: "strategy_not_approved"`.

## Cross-links

- `[[calidad-pre-generation-protocol]]` — paso obligatorio donde se ancla la generación de `STRATEGY.md`.
- `[[calidad-mandatory-inputs-protocol]]` — proviene los inputs que alimentan el documento.
- `[[calidad-executive-report-generator]]` — consume el `STRATEGY.md` para construir la sección 2 del reporte.
- `[[calidad-delivery-gate-contract]]` — el path al `STRATEGY.md` se referencia en el bloque YAML de cierre.
