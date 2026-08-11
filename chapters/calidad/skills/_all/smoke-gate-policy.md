---
id: calidad-smoke-gate-policy
version: 1.2.0
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

## 1:1 significa UN escenario, no un tag que matchea varios

El gate ejecuta **exactamente un** escenario: el flujo crítico end-to-end más representativo de la entrega. No "los escenarios `@smoke`", no "la suite mínima". Razones:

- Un caso crítico completo destapa los problemas **transversales** (locators, esperas, datos, instrumentación) con un solo diagnóstico. Lanzar N escenarios que fallan por la misma causa multiplica el ruido y el tiempo — verificado en campo, con el usuario pidiendo tres veces "no ejecutes tantos test hasta no confirmar el primero".
- Un tag compartido por varios escenarios deja de ser un gate y pasa a ser una suite parcial.

**Convención**: tag dedicado **`@smoke-gate`** sobre **un solo** escenario (que además puede llevar `@smoke`). Antes de ejecutar, **verificar el conteo**: si `@smoke-gate` matchea ≠ 1 escenario, el gate está mal construido y se corrige antes de correr. El resto de `@smoke` es suite, no gate.

**Regla de orden ante fallos**: mientras el gate no esté verde, se re-ejecuta **solo ese escenario**. Está prohibido lanzar la suite completa para "ver qué más falla": primero un caso verde end-to-end, después cobertura.

**Después del gate sí va la suite completa** — el gate no reemplaza la cobertura. La cadencia completa (gate 1:1 → suite de inventario → corrección aislada test por test → suite de regresión) está en `[[calidad-test-self-correction-loop]]`. Lo que nunca se hace es relanzar la suite entera en cada iteración de corrección: durante la corrección se ejecuta **solo el test que se está corrigiendo**.

## Comando por stack

| Stack | Comando smoke gate (1 escenario) | Verificación de conteo previa |
|---|---|---|
| Karate | `mvn test -f pom.xml -Dkarate.options="--tags @smoke-gate"` | `grep -rc "@smoke-gate" src/test/java/**/*.feature` == 1 |
| Playwright | `npx playwright test --grep @smoke-gate --workers=1 --max-failures=1` | `npx playwright test --grep @smoke-gate --list` devuelve 1 |
| K6 | `k6 run tests/linea-base/main.js --vus 1 --iterations 1` (ver [[calidad-k6-greenfield]] (consultar `references/smoke-1-1-gate.md` en su subfolder)) | 1 VU / 1 iteración por construcción |
| Appium | `./gradlew test -Dcucumber.filter.tags=@smoke-gate` | `grep -rc "@smoke-gate" src/test/resources/features/` == 1 |

**El filtro debe llegar de verdad al runner**: si el runner lleva tags hardcodeados, el `-D...filter.tags` se ignora y corre lo que el runner diga (causa raíz verificada en campo). Un solo runner por proyecto, tags solo por CLI — ver el detalle por stack en sus references de ejecución.

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
  scenarios_matched: 1                # DEBE ser 1; distinto de 1 invalida el gate
  executed: true | false | skipped
  executed_against: real | mock | hybrid
  exit_code: <int>
  duration_seconds: <int>
```

## Detalle por stack

Cada framework documenta el detalle del comando, dónde colocar el `@smoke`, parseo de exit code y reporters:

- Karate: [[calidad-karate-greenfield]] (consultar `references/smoke-gate-mvn.md` en su subfolder)
- Playwright: [[calidad-playwright-greenfield]] (consultar `references/smoke-gate-playwright.md` en su subfolder)
- K6: [[calidad-k6-greenfield]] (consultar `references/smoke-1-1-gate.md` en su subfolder) (cubierto en oleada K6 paralela)
- Appium: [[calidad-appium-screenplay-android]] (consultar `references/smoke-gate-gradle.md` en su subfolder)

## Cross-links

`[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-failure-triage-and-classification]]`.
