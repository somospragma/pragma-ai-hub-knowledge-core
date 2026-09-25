---
id: calidad-smoke-gate-policy
version: 1.2.0
scope: chapter
type: skill
chapter: calidad
description: "Política universal de smoke gate 1:1 obligatorio antes de declarar success. Comando por stack, criterios de aceptación, comportamiento ante fallo. Incluye serenity-wdio."
tags: [smoke-gate, universal, mandatory, post-generation, serenity-wdio]
enforcement: mandatory
verification:
  - check: "el filtro del gate matchea exactamente 1 escenario, verificado con el conteo ANTES de ejecutar"
    failure_message: "Bloqueado: el gate matchea un número de escenarios distinto de 1. Un tag compartido por varios deja de ser gate y pasa a ser suite parcial."
  - check: "en brownfield el gate reutiliza la taxonomía de etiquetas del proyecto; no se introdujo ningún tag nuevo sin confirmación explícita del usuario"
    failure_message: "Bloqueado: se introdujo una etiqueta de compuerta en un repositorio que ya tiene taxonomía propia. Verificado en campo: rompe la convención del equipo, rompe la trazabilidad hasta el ALM y el ejecutor puede componer el filtro de forma que el tag nuevo nunca encaje."
  - check: "el preflight de esa misma corrida está verde antes de ejecutar el gate"
    failure_message: "Bloqueado: un gate rojo contra un SUT que nunca se tocó no informa nada y arranca el diagnóstico sobre la causa equivocada."
---

# Smoke Gate Policy — Universal cross-stack

## Principio

Antes de declarar `status: success` en el contrato `[[calidad-delivery-gate-contract]]`, el agente DEBE ejecutar al menos un smoke test mínimo end-to-end por framework. El objetivo NO es validar cobertura ni regresion completa, sino confirmar que el scaffold compila, arranca y ejecuta un happy path básico contra el SUT. Es una puerta de calidad obligatoria — sin smoke verde no hay success.

Aplica a los 5 frameworks del chapter (Karate, Playwright, K6, Appium, serenity-wdio) tanto en greenfield como en brownfield, y a los 5 IDEs soportados.

## 1:1 significa UN escenario, no un tag que matchea varios

El gate ejecuta **exactamente un** escenario: el flujo crítico end-to-end más representativo de la entrega. No "los escenarios `@smoke`", no "la suite mínima". Razones:

- Un caso crítico completo destapa los problemas **transversales** (locators, esperas, datos, instrumentación) con un solo diagnóstico. Lanzar N escenarios que fallan por la misma causa multiplica el ruido y el tiempo — verificado en campo, con el usuario pidiendo tres veces "no ejecutes tantos test hasta no confirmar el primero".
- Un tag compartido por varios escenarios deja de ser un gate y pasa a ser una suite parcial.

**El principio del gate es "un escenario", no un tag concreto.** Cómo se selecciona ese escenario depende de si el repositorio ya tiene taxonomía propia:

| Situación | Cómo se selecciona el escenario del gate |
|---|---|
| **Brownfield con taxonomía de humo existente** | Se **reutiliza** la etiqueta del proyecto y se acota a un solo escenario combinándola con filtro por nombre. **Prohibido introducir un tag nuevo.** |
| **Greenfield, o repositorio sin taxonomía** | Se crea el tag dedicado **`@smoke-gate`** sobre un solo escenario (que además puede llevar `@smoke`) |
| **Se necesita un tag nuevo en un repo con convención propia** | Solo con confirmación explícita del usuario, registrada en la evidencia |

La taxonomía real del repositorio sale del mapa de `[[calidad-repo-capability-discovery]]` y **manda sobre el default de este asset**. Verificado en campo: el agente creó `@smoke-gate` en un proyecto cuya etiqueta de humo estandarizada aparecía en los ejemplos de uso de sus propios ejecutores y viajaba hasta el ALM como etiqueta del caso; el tag nuevo rompió la convención y la trazabilidad, y además el ejecutor componía el filtro de forma que el tag nuevo nunca encajaba.

En cualquiera de los tres casos, antes de ejecutar se **verifica el conteo**: si el filtro del gate matchea ≠ 1 escenario, el gate está mal construido y se corrige antes de correr. El resto de la etiqueta de humo es suite, no gate.

**Regla de orden ante fallos**: mientras el gate no esté verde, se re-ejecuta **solo ese escenario**. Está prohibido lanzar la suite completa para "ver qué más falla": primero un caso verde end-to-end, después cobertura.

**Después del gate sí va la suite completa** — el gate no reemplaza la cobertura. La cadencia completa (gate 1:1 → suite de inventario → corrección aislada test por test → suite de regresión) está en `[[calidad-test-self-correction-loop]]`. Lo que nunca se hace es relanzar la suite entera en cada iteración de corrección: durante la corrección se ejecuta **solo el test que se está corrigiendo**.

## Comando por stack

**En brownfield, el comando sale del mapa de `[[calidad-repo-capability-discovery]]`, no de esta tabla.** Los comandos de abajo son el default para greenfield o para cuando el repositorio no provee ejecutor propio; en un repo real casi nunca son los correctos. Igualmente, el nombre del tag en los comandos se sustituye por la etiqueta real del proyecto cuando aplica la fila 1 de la tabla anterior.

| Stack | Comando smoke gate (1 escenario) | Verificación de conteo previa |
|---|---|---|
| Karate | `mvn test -f pom.xml -Dkarate.options="--tags @smoke-gate"` | `grep -rc "@smoke-gate" src/test/java/**/*.feature` == 1 |
| Playwright | `npx playwright test --grep @smoke-gate --workers=1 --max-failures=1` | `npx playwright test --grep @smoke-gate --list` devuelve 1 |
| K6 | `k6 run tests/linea-base/main.js --vus 1 --iterations 1` (ver [[calidad-k6-greenfield]] (consultar `references/smoke-1-1-gate.md` en su subfolder)) | 1 VU / 1 iteración por construcción |
| Appium | `./gradlew test -Dcucumber.filter.tags=@smoke-gate` | `grep -rc "@smoke-gate" src/test/resources/features/` == 1 |
| serenity-wdio | `node scripts/run.mjs --mode=web --tags=@smoke-gate` (equiv. `npm run test:smoke`) | `grep -rc "@smoke-gate" features/**/*.feature` == 1 |

**El filtro debe llegar de verdad al runner**: si el runner lleva tags hardcodeados, el `-D...filter.tags` se ignora y corre lo que el runner diga (causa raíz verificada en campo). Un solo runner por proyecto, tags solo por CLI — ver el detalle por stack en sus references de ejecución.

## Reglas

- **Preflight verde primero.** El gate no se ejecuta sin `[[calidad-execution-preflight]]` en verde en esa misma corrida: un gate rojo contra un SUT que nunca se tocó no informa nada y arranca un diagnóstico sobre la causa equivocada.
- **Exit 0** → smoke gate verde, continuar el flujo y permitir `status: success`.
- **Exit ≠ 0** → status `partial` con `blocker: "smoke_gate_failed_<framework>"` (ej. `smoke_gate_failed_karate`, `smoke_gate_failed_playwright`, `smoke_gate_failed_k6`, `smoke_gate_failed_appium`, `smoke_gate_failed_serenity-wdio`). Escalar al usuario con stderr completo del comando.
- El smoke gate NO ejecuta suite completa; solo valida que el scaffold corre end-to-end. La suite completa se ejecuta como parte del paso de ejecución del `[[calidad-post-generation-protocol]]`.
- El agente DEBE garantizar que existe al menos un test/feature/escenario etiquetado o nombrado de modo que el comando smoke lo encuentre. Si no existe, el smoke gate se considera "no provisto" y bloquea con `blocker: "smoke_gate_missing_scenario_<framework>"`.
- Si el smoke gate falla por causa ambiental (WAF, DNS, device caído), el blocker se reclasifica como `environment_blocked_*` según `[ver schema](./environment-blocker-evidence.md)`.
- **Retirar escenarios puede llevarse el gate por delante.** Tras eliminar o mover cualquier escenario de un feature, **contar** los que quedan con la etiqueta que forma el gate. Caso medido: se retiraron por redundantes los escenarios de un criterio de aceptación, y con ellos se fueron los únicos `@smoke` del feature — que pasó a tener **cero**, mientras features comparables tenían dos o tres. Nadie lo detectó: apareció de casualidad, semanas después, construyendo las etiquetas del CSV de importación. Si el borrado deja el feature sin gate, se repone en el camino central de la historia antes de cerrar, en todas las plataformas.

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
  framework: karate | playwright | k6 | appium | serenity-wdio
  command: "..."
  selector_source: repo_taxonomy | dedicated_tag | user_confirmed_new_tag
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
- serenity-wdio: [[serenity-wdio-greenfield]] (consultar `references/smoke-gate-wdio.md` en su subfolder)

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | el filtro del gate matchea exactamente 1 escenario, verificado con el conteo ANTES de ejecutar | Bloqueado: el gate matchea un número de escenarios distinto de 1. Un tag compartido por varios deja de ser gate y pasa a ser suite parcial. |
| 2 | en brownfield el gate reutiliza la taxonomía de etiquetas del proyecto; no se introdujo ningún tag nuevo sin confirmación explícita del usuario | Bloqueado: se introdujo una etiqueta de compuerta en un repositorio que ya tiene taxonomía propia. Verificado en campo: rompe la convención del equipo, rompe la trazabilidad hasta el ALM y el ejecutor puede componer el filtro de forma que el tag nuevo nunca encaje. |
| 3 | el preflight de esa misma corrida está verde antes de ejecutar el gate | Bloqueado: un gate rojo contra un SUT que nunca se tocó no informa nada y arranca el diagnóstico sobre la causa equivocada. |
| 4 | si en esta sesión se retiraron escenarios de algún feature, se contó que sobrevive al menos uno con la etiqueta del gate | Bloqueado: el feature quedó sin gate de humo. La eliminación se llevó por delante los escenarios que lo formaban y nada más lo va a detectar. |

## Cross-links

`[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-execution-preflight]]`, `[[calidad-repo-capability-discovery]]`.
