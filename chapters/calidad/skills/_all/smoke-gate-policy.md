---
id: calidad-smoke-gate-policy
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "Política universal de smoke gate 1:1 obligatorio antes de declarar success. Comando por stack, criterios de aceptación, comportamiento ante fallo."
tags: [smoke-gate, universal, mandatory, post-generation]
enforcement: mandatory
---

# Smoke Gate Policy — Universal cross-stack

## Principio

Antes de declarar `status: success` en el contrato `[[calidad-delivery-gate-contract]]`, el agente DEBE ejecutar al menos un smoke test mínimo end-to-end por framework. El objetivo NO es validar cobertura ni regresion completa, sino confirmar que el scaffold compila, arranca y ejecuta un happy path básico contra el SUT. Es una puerta de calidad obligatoria — sin smoke verde no hay success.

Aplica a los 4 frameworks del chapter (Karate, Playwright, K6, Appium) tanto en greenfield como en brownfield, y a los 5 IDEs soportados.

## Comando por stack

| Stack | Comando smoke gate |
|---|---|
| Karate | `mvn test -f pom.xml -Dkarate.options="--tags @smoke"` (con al menos 1 happy path etiquetado `@smoke`) |
| Playwright | `npx playwright test --grep @smoke --project=chromium-live --workers=1 --max-failures=1` |
| K6 | `k6 run tests/linea-base/main.js --vus 1 --iterations 1` (ver `[k6 smoke-1-1-gate](../k6/k6-greenfield/references/smoke-1-1-gate.md)`) |
| Appium | `./gradlew test -Dcucumber.filter.tags=@smoke` (con al menos 1 escenario `@smoke`) |

## Reglas

- **Exit 0** → smoke gate verde, continuar el flujo y permitir `status: success`.
- **Exit ≠ 0** → status `partial` con `blocker: "smoke_gate_failed_<framework>"` (ej. `smoke_gate_failed_karate`, `smoke_gate_failed_playwright`, `smoke_gate_failed_k6`, `smoke_gate_failed_appium`). Escalar al usuario con stderr completo del comando.
- El smoke gate NO ejecuta suite completa; solo valida que el scaffold corre end-to-end. La suite completa se ejecuta como parte del paso de ejecución del `[[calidad-post-generation-protocol]]`.
- El agente DEBE garantizar que existe al menos un test/feature/escenario etiquetado o nombrado de modo que el comando smoke lo encuentre. Si no existe, el smoke gate se considera "no provisto" y bloquea con `blocker: "smoke_gate_missing_scenario_<framework>"`.
- Si el smoke gate falla por causa ambiental (WAF, DNS, device caído), el blocker se reclasifica como `environment_blocked_*` según `[ver schema](./environment-blocker-evidence.md)`.

## Smoke gate contra mock (`execution_target: mock | hybrid`)

Cuando `[[calidad-sut-readiness-gate]]` resolvió que las pruebas se construyen antes del desarrollo, el smoke gate corre contra el mock (`[[calidad-service-virtualization-mockoon]]`), que debe estar levantado ANTES de ejecutar el comando:

- El smoke verde contra mock es un **gate de construcción válido**: demuestra que el scaffold compila, corre end-to-end y es determinista. Habilita `status: success` de la entrega de construcción.
- NO sustituye el gate contra el SUT real: el bloque `smoke_gate` registra `executed_against` y el delivery gate cierra con `certification: pending_real_integration`. Al momento del switchover, el smoke gate se re-ejecuta contra el ambiente real (checklist en `[[calidad-service-virtualization-mockoon]]`, consultar `references/mock-vs-real-switchover.md` en su subfolder).
- Si el mock no levanta o el health-probe no responde, el blocker es `mock_unavailable` (no `environment_blocked_*`, que se reserva para ambientes reales).
- K6: contra mock SOLO se ejecuta el smoke 1:1; jamás `load/stress/spike/soak` (las métricas del mock no representan al SUT).

## Wiring con el contrato

El campo `smoke_gate` se agrega al bloque `delivery_gate` (ver `[[calidad-delivery-gate-contract]]`):

```yaml
smoke_gate:
  framework: karate | playwright | k6 | appium
  command: "..."
  executed: true | false | skipped
  executed_against: real | mock | hybrid
  exit_code: <int>
  duration_seconds: <int>
```

## Detalle por stack

Cada framework documenta el detalle del comando, dónde colocar el `@smoke`, parseo de exit code y reporters:

- Karate: `[smoke-gate-mvn](../karate/karate-greenfield/references/smoke-gate-mvn.md)`
- Playwright: `[smoke-gate-playwright](../playwright/playwright-greenfield/references/smoke-gate-playwright.md)`
- K6: `[smoke-1-1-gate](../k6/k6-greenfield/references/smoke-1-1-gate.md)` (cubierto en oleada K6 paralela)
- Appium: `[smoke-gate-gradle](../appium/appium-screenplay-android/references/smoke-gate-gradle.md)`

## Cross-links

`[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-failure-triage-and-classification]]`.
