---
id: calidad-delivery-gate-contract
version: 1.8.0
scope: chapter
type: skill
chapter: calidad
enforcement: mandatory
description: "OBLIGATORIO. Contrato YAML que el agente DEBE emitir literalmente al final de toda generación, antes del mensaje de cierre. Sin este bloque, la entrega se considera incompleta. Universal a los 5 IDEs."
tags: [delivery-gate, contract, mandatory, universal, all-ides]
verification:
  - check: "bloque delivery_gate emitido literalmente como último contenido antes del mensaje de cierre"
    failure_message: "Bloqueado: la entrega no incluye el bloque YAML delivery_gate. Sin este contrato la entrega es inválida."
  - check: "todos los campos obligatorios del schema rellenados (schema_version, framework, mode, status, inputs_confirmed, coverage, files_emitted, evidence_persisted)"
    failure_message: "Bloqueado: el bloque delivery_gate tiene campos obligatorios vacíos o ausentes."
  - check: "consistencia status vs execution.exit_code (success requiere exit_code 0 en modo full)"
    failure_message: "Bloqueado: contradicción entre status declarado y exit_code reportado."
  - check: "modo full sin ejecución real reporta status: partial con blocker execution_skipped"
    failure_message: "Bloqueado: no se puede declarar success en modo full sin evidencia de ejecución."
  - check: "bloque transversal_capabilities presente (detected/omitted); capas tejidas solo si confirmed_by_user"
    failure_message: "Bloqueado: faltó evaluar/registrar las capacidades transversales complementarias (accesibilidad, SEO, seguridad, visual, contract, performance)."
  - check: "execution_target declarado; si es mock o hybrid, certification: pending_real_integration + mock_evidence completo + switchover en next_steps"
    failure_message: "Bloqueado: la corrida contra mock no declara la certificación pendiente o carece de evidencia del mock y plan de switchover."
  - check: "si execution_target es mock o hybrid, el mensaje de cierre posterior al bloque YAML repite la advertencia de certificación pendiente"
    failure_message: "Bloqueado: el cierre no advierte que los resultados contra mock no certifican el SUT. La advertencia al inicio del flujo no sustituye la del cierre."
  - check: "pipeline-state.json leído y sin fases obligatorias pendientes; phases_pending vacío"
    failure_message: "Bloqueado: hay fases del pipeline sin completar. Emitir el gate ahora sería declarar terminada una entrega incompleta."
  - check: "cada blocker declarado incluye la evidencia del sondeo (comando ejecutado + salida) que lo comprueba"
    failure_message: "Bloqueado: hay blockers afirmados sin sondear. Un bloqueo de ambiente supuesto ya cerró una entrega en falso."
  - check: "si execution_target es mock/hybrid, mock_evidence.traffic_verified es true con evidencia del log del mock"
    failure_message: "Bloqueado: no se demostró que el SUT consumiera el mock. Una suite verde contra un SUT que ignora el mock no valida el contrato."
  - check: "el análisis estático del cliente corrió en local y pasó antes de cualquier commit, con su salida adjunta"
    failure_message: "Bloqueado: se iba a commitear sin pasar la puerta de calidad del cliente. Descubrirlo en el pipeline cuesta un ciclo entero."
  - check: "la cobertura declarada en la matriz de insumos se comparó contra la entregada, y la diferencia está reportada"
    failure_message: "Bloqueado: no se comparó lo prometido contra lo entregado. Una entrega que se declara completa sin ese cruce ya cerró historias con criterios sin cubrir."
  - check: "los artefactos obligatorios que los assets de la ruta prescriben existen en la evidencia, o su ausencia está justificada"
    failure_message: "Bloqueado: faltan artefactos obligatorios. Un asset marcado obligatorio cuyo artefacto nunca se creó es una regla que no se cumplió y que nadie notó."
---

# Delivery Gate Contract — Bloque YAML de Cierre Obligatorio

## Cuándo aplicar

Siempre, al final de todo workflow de generación (greenfield o brownfield, los 4 frameworks). Es lo último que el agente emite antes del mensaje "listo".

Aplica universalmente a los 5 IDEs soportados (Kiro, Claude Code, GitHub Copilot, Amazon Q IDE, Amazon Q CLI). Sin este bloque, la entrega se considera incompleta.

## Precondición: la traza manda

**Antes de emitir el bloque, leer `.evidence/pipeline-state.json` (`[[calidad-pipeline-state-tracking]]`) y verificar que ninguna fase obligatoria está en `pending` o `in_progress`.** Si las hay:

- NO se emite el gate como cierre. Se emite un **reporte de estado** que enumera las fases pendientes y la siguiente acción, y el trabajo continúa.
- Un gate emitido sobre fases pendientes es una entrega falsa, aunque todos sus campos estén rellenos. Verificado en campo: dos gates emitidos en la misma corrida, el primero sin ninguna ejecución y el segundo con `status: success` mientras 3 de 4 escenarios estaban `SKIPPED`.

Reglas de coherencia que el propio agente debe verificar antes de emitir:

| Si… | Entonces… |
|---|---|
| `mode: full` | `suite_executed` y `report_verified` en `done`; `execution.*` con datos reales |
| `status: success` | cero fases obligatorias pendientes, cero `blockers`, y `execution.skipped` coherente con lo realmente ejecutado |
| hay escenarios `SKIPPED` por filtro | NO pueden contarse como `coverage.delivered` |
| `blockers[]` no vacío | cada blocker con **evidencia del sondeo** que lo comprobó (comando + salida), no una afirmación |
| `execution_target: mock` | tráfico verificado contra el mock (ver `mock_evidence.traffic_verified`) |

## Instrucción

Emite literalmente este bloque YAML (rellenando los slots) antes de cualquier despedida:

```yaml
delivery_gate:
  schema_version: "1.1"
  pipeline_state: ".evidence/pipeline-state.json"   # traza leída; cero fases obligatorias pendientes
  phases_pending: []                                # si no está vacío, esto NO es un cierre
  framework: karate | playwright | k6 | appium
  mode: full | dry-run | scaffold-only | execute-only
  execution_target: real | mock | hybrid    # contra qué corrió la fase de ejecución (SUT readiness gate)
  certification: certified | pending_real_integration   # certified SOLO si execution_target: real
  mock_evidence:                            # null si execution_target: real
    tool: mockoon
    data_file: "mocks/mockoon/environment.json"
    faker_seed: 12345
    locator_map: "locator-map.json" | null  # solo front/mobile pre-desarrollo
    front_prototype: true | false           # opt-in: prototipo HTML del front (mocks/front-prototype/)
    app_prototype: true | false             # opt-in: prototipo de app en la tecnología real (mocks/app-prototype/)
    prototype_acceptance: ".evidence/prototype-acceptance.json"  # paridad + fidelidad + CA recorribles
    traffic_verified: true | false          # el SUT (app/front) consumió REALMENTE el mock: peticiones en su log
    switchover_plan: "STRATEGY.md#6"        # dónde quedó documentado el plan mock -> real
  preflight:
    tool_version: "11.0.21"           # Java/Node/k6/Gradle según stack
    verdict: pass | fail | skipped
    notes: "..."
  inputs_confirmed:
    project_name: "..."
    output_path: "..."
    ui_source_or_spec: "..."
    user_story: "HUT-001" | null
    firma: "..." | null
    risk_map: { addPet: HIGH, findPetsByStatus: MEDIUM, ... }
  transversal_capabilities:               # capas complementarias evaluadas (paso 2.5 del router)
    detected:
      - capability: accessibility | seo | security | visual | contract | performance
        skill: calidad-accessibility-testing
        tag: "@accessibility"
        rationale: "..."                  # por qué aplica (risk-first / SUT / sector)
        confirmed_by_user: true | false
    omitted:
      - capability: seo
        reason: "..."                     # por qué no aplica / fuera de alcance / descartada
  coverage:
    declared:
      addPet: 10        # effective_minimum por endpoint/HU/script
      findPetsByStatus: 8
    delivered:
      addPet: 10
      findPetsByStatus: 8
    diff_ok: true
  files_emitted:
    total: 28
    paths:
      - "src/test/java/com/testing/features/pet/addPet.feature  [ok]"
      - "..."
  coherence_checks:
    structure_canonical: pass | fail
    no_dead_code: pass | fail
    compile_dry_run: pass | fail | skipped
    notes: "..."
  execution:
    run_command: "mvn test -f pom.xml"
    exit_code: 0
    total: 28
    passed: 28
    failed: 0
    skipped: 0
    rerun_N3_applied: true | false | not_applicable
    deterministic_failures: 0
    flaky_failures: 0
    smoke_1_1:                          # SOLO K6 — gate obligatorio en modo full
      executed: true | false | skipped
      exit_code: 0                      # int (0 = ok); null si executed=false|skipped
  corrections_applied:
    count: 0
    audit_log: ".evidence/audit-log-20260604.md"
    anti_cheating_violations: 0
  evidence_persisted:
    session_config: ".evidence/session-config.json"
    generation_manifest: ".evidence/generation-manifest.json"
    execution_log: ".evidence/execution-log-20260604.json" | null
    audit_log: ".evidence/audit-log-20260604.md" | null
    coverage_audit: ".evidence/coverage-declared-vs-delivered.json"
    executive_report: ".evidence/report-{ISO}.html" | null   # null si modo scaffold-only/dry-run
  status: success | partial | failed
  blockers: []                          # lista de razones si status != success
  next_steps: []                        # acciones recomendadas al usuario
```

## Un gate sin fixtures es una hipótesis

**Todo gate se entrega con un caso que DEBE fallar y otro que DEBE pasar.** Sin
eso no se sabe si el gate protege algo o solo estorba, y una regla que nadie ha
visto fallar es una hipótesis sobre el comportamiento del código, no una
verificación.

No es teórico. Al escribir el test que ejercitaba un gate de siete reglas
apareció un **falso positivo real**: el patrón que detecta identificadores sin
sustituir llevaba la bandera de ignorar mayúsculas, así que rechazaba una
etiqueta de servicio legítima. Nadie lo habría visto hasta que alguien creara esa
etiqueta — y entonces el gate habría bloqueado un cambio correcto, que es la
forma más rápida de que un equipo aprenda a saltárselo.

La misma exigencia aplica a las comprobaciones de este contrato de cierre: si una
condición no se puede violar a propósito en una prueba, no está verificando nada.

## Antes del commit: la puerta de calidad del cliente y los artefactos prometidos

Tres comprobaciones que no cuestan una corrida contra el sistema bajo prueba y que evitan un ciclo entero de reproceso.

**1. El análisis estático del cliente se pasa en local, antes de commitear.** Si el cliente tiene una puerta de calidad, se corre contra ella desde la máquina, con las credenciales que ya viven en la configuración del repositorio, y **se pasa antes** de proponer el commit. Descubrir en el pipeline lo que se podía saber en local cuesta el ciclo completo. Detalle en `[[calidad-static-analysis-on-the-test-repo]]`. Casi siempre el repositorio ya tiene el comando y el gancho de pre-commit: se comprueba antes de construir nada. Si no lo tiene, el hueco se cierra construyéndolo una vez según `[[calidad-deterministic-work-to-tooling]]`, no repitiendo la comprobación a mano en cada entrega.

**2. La cobertura declarada se compara contra la entregada.** La matriz congelada en la fase de insumos es el compromiso; la entrega es lo que hay. La diferencia se reporta explícitamente, aunque sea cero. Sin este cruce, "ejecuté todo lo que había" se confunde con "cubrí todo lo que había que cubrir", y ya cerró historias con criterios sin escenario.

**3. Los artefactos obligatorios existen, y lo comprueba un comando que viene con el chapter.** Cada asset marcado como obligatorio prescribe artefactos. La comprobación **no es una autoevaluación del agente**: es un comando que verifica presencia y devuelve código de salida distinto de cero, enganchado al pre-commit del repositorio. Una obligación sostenida sólo por texto ya demostró no cumplirse.

El comando **no hay que construirlo**: se instala con el chapter, en `scripts/` de este skill.

```bash
python3 <scripts-de-este-skill>/check-required-artifacts.py --evidence .evidence
```

Es autocontenido —un solo archivo, sin dependencias— y lleva dentro la lista de artefactos que los assets obligatorios exigen, con su condición de aplicación. Comprueba presencia, imprime qué falta, quién lo exige y para qué, y devuelve código de salida distinto de cero. Se engancha al `pre-commit` del repositorio, que es donde no se puede saltar.

La lista no se mantiene a mano: la auditoría de la fuente del chapter la lee del propio script y falla si un asset obligatorio prescribe un artefacto que no está en ella. Así, añadir una obligación nueva y olvidarse de hacerla comprobable deja de ser posible. Ver `[[calidad-deterministic-work-to-tooling]]`, capas de exigibilidad.

Esta última es la comprobación que más veces destapa el problema de fondo: en una certificación auditada, **seis de cada diez artefactos obligatorios prescritos por los assets no se habían creado**, y eran precisamente los que habrían evitado los gastos más caros de la entrega. Una regla obligatoria cuyo artefacto nadie verifica es una regla que no existe.

## Restricciones

- Si falta cualquier campo obligatorio → entrega inválida.
- Si `status: success` pero `execution.exit_code != 0` → contradicción, reportar `failed`.
- Si modo es `dry-run` o `scaffold-only` → `execution.*` puede ser `null` pero documentar en `blockers` por qué.
- Si modo es `full` y no se ejecutó → `status: partial` con `blocker: "execution_skipped"`.
- `transversal_capabilities` debe estar presente: si no aplica ninguna capa, declarar `detected: []` y justificar en `omitted`. Una capa con `confirmed_by_user: false` no debe haberse tejido en la suite.
- Si `execution_target: mock | hybrid` → `certification: pending_real_integration` es obligatorio, `mock_evidence` completo, y `next_steps` DEBE incluir la re-ejecución contra integraciones reales (switchover). `certification: certified` con `execution_target != real` es contradicción → entrega inválida.
- Resultados contra mock JAMÁS se presentan como certificación de integración, performance o seguridad del SUT (regla maestra de `[[calidad-sut-readiness-gate]]`).
- **Advertencia de cierre obligatoria**: si `execution_target: mock | hybrid`, el mensaje final al usuario (el que sigue al bloque YAML) DEBE repetir en su primera línea: *"Resultados obtenidos contra mock: validan la construcción de la suite, NO certifican el SUT. Certificación pendiente de re-ejecución contra integraciones reales (ver plan de switchover)."* Decirlo solo al inicio del flujo no basta — el usuario que lee el cierre debe verla ahí (hallazgo de pruebas de campo).

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | bloque delivery_gate emitido literalmente como último contenido antes del mensaje de cierre | Bloqueado: la entrega no incluye el bloque YAML delivery_gate. Sin este contrato la entrega es inválida. |
| 2 | todos los campos obligatorios del schema rellenados (schema_version, framework, mode, status, inputs_confirmed, coverage, files_emitted, evidence_persisted) | Bloqueado: el bloque delivery_gate tiene campos obligatorios vacíos o ausentes. |
| 3 | consistencia status vs execution.exit_code (success requiere exit_code 0 en modo full) | Bloqueado: contradicción entre status declarado y exit_code reportado. |
| 4 | modo full sin ejecución real reporta status: partial con blocker execution_skipped | Bloqueado: no se puede declarar success en modo full sin evidencia de ejecución. |
| 5 | bloque transversal_capabilities presente (detected/omitted); capas tejidas solo si confirmed_by_user | Bloqueado: faltó evaluar/registrar las capacidades transversales complementarias (accesibilidad, SEO, seguridad, visual, contract, performance). |
| 6 | execution_target declarado; si es mock o hybrid, certification: pending_real_integration + mock_evidence completo + switchover en next_steps | Bloqueado: la corrida contra mock no declara la certificación pendiente o carece de evidencia del mock y plan de switchover. |
| 7 | si execution_target es mock o hybrid, el mensaje de cierre posterior al bloque YAML repite la advertencia de certificación pendiente | Bloqueado: el cierre no advierte que los resultados contra mock no certifican el SUT. La advertencia al inicio del flujo no sustituye la del cierre. |
| 8 | pipeline-state.json leído y sin fases obligatorias pendientes; phases_pending vacío | Bloqueado: hay fases del pipeline sin completar. Emitir el gate ahora sería declarar terminada una entrega incompleta. |
| 9 | cada blocker declarado incluye la evidencia del sondeo (comando ejecutado + salida) que lo comprueba | Bloqueado: hay blockers afirmados sin sondear. Un bloqueo de ambiente supuesto ya cerró una entrega en falso. |
| 10 | si execution_target es mock/hybrid, mock_evidence.traffic_verified es true con evidencia del log del mock | Bloqueado: no se demostró que el SUT consumiera el mock. Una suite verde contra un SUT que ignora el mock no valida el contrato. |
| 11 | el análisis estático del cliente corrió en local y pasó antes de cualquier commit, con su salida adjunta | Bloqueado: se iba a commitear sin pasar la puerta de calidad del cliente. Descubrirlo en el pipeline cuesta un ciclo entero. |
| 12 | la cobertura declarada en la matriz de insumos se comparó contra la entregada, y la diferencia está reportada | Bloqueado: no se comparó lo prometido contra lo entregado. Una entrega que se declara completa sin ese cruce ya cerró historias con criterios sin cubrir. |
| 13 | los artefactos obligatorios que los assets de la ruta prescriben existen en la evidencia, o su ausencia está justificada | Bloqueado: faltan artefactos obligatorios. Un asset marcado obligatorio cuyo artefacto nunca se creó es una regla que no se cumplió y que nadie notó. |

## Cross-links

`[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-test-execution-orchestration]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-executive-report-generator]]`, `[[calidad-generate-executive-report]]`, `[[calidad-static-analysis-on-the-test-repo]]` — pasar la puerta de calidad del cliente también es parte de la entrega, `[[calidad-execution-profile-and-config-provenance]]` — de qué depende que `execution_target` diga la verdad.
