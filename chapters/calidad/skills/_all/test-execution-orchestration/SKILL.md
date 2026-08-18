---
id: calidad-test-execution-orchestration
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Ejecutar las pruebas generadas como capacidad del chapter: invocar comandos, capturar output, parsear resultados a un esquema común, gestionar modos de operación (full / scaffold-only / execute-only / dry-run)."
tags: [execution, orchestration, runtime, result-parsing, modes, evidence, enforcement, mandatory]
enforcement: mandatory
verification:
  - check: "ejecutado al menos smoke en modo full con exit_code capturado, stdout persistido y artefactos archivados"
    failure_message: "Bloqueado: en modo full no se ejecutó nada o no se capturó evidencia de la corrida. La entrega no puede declarar success."
  - check: "modo confirmado explícitamente al inicio (no asumir full) y degradación a scaffold-only documentada cuando aplica"
    failure_message: "Bloqueado: el modo de operación no fue confirmado o la degradación automática no quedó documentada."
  - check: "resultados parseados a esquema común consumible por triage (calidad-failure-triage-and-classification)"
    failure_message: "Bloqueado: el output de ejecución no fue parseado al esquema común; triage no puede operar sobre datos crudos."
---

# Test Execution Orchestration — Ejecución y Parseo de Resultados como Capacidad del Chapter

## Cuándo aplicar

Aplica este skill **después de generar tests con cualquier workflow del chapter** (Karate, Playwright, K6, Appium, en greenfield o brownfield). La ejecución de las pruebas generadas es **parte del contrato de entrega del chapter**, no un opcional ni una responsabilidad delegable al cliente sin justificación.

El propósito es que el AI no solo entregue archivos de test, sino que **demuestre que esos tests corren y producen resultados parseables** dentro de un esquema común — habilitando triage automático (`[[calidad-failure-triage-and-classification]]`), auto-corrección (`[[calidad-test-self-correction-loop]]`) y self-healing (`[[calidad-test-self-healing]]`).

Activa este skill en paralelo con `[[calidad-test-evidence-and-traceability]]` para que los artefactos generados queden archivados como evidencia auditable, y con `[[calidad-cicd-integration]]` cuando la ejecución debe migrarse a pipeline después de la validación inicial.

## Modos de operación

| Modo | Comportamiento | Cuándo usar |
|---|---|---|
| `full` (default) | Generar + ejecutar + verificar + auto-corregir | Default cuando el agente tiene capacidad de shell y acceso al SUT |
| `scaffold-only` | Solo generar; reportar comandos para que humano ejecute | Sin acceso a shell, sin env, sin creds |
| `execute-only` | Sobre tests existentes; solo ejecutar y reportar (no modificar) | Smoke check, validación pre-deploy |
| `dry-run` | Generar + ejecutar + reportar diff propuesto; NO aplicar correcciones | Default para clientes regulados (requiere aprobación humana) |

Cómo elegir el modo: invocar `[[calidad-mandatory-inputs-protocol]]` para confirmar con el usuario qué modo aplica al engagement (perfil del cliente, ventanas de cambio, requerimientos regulatorios). Si la capacidad técnica del agente lo impide (sin shell, sin env vars, sin acceso de red al SUT), **degradar automáticamente a `scaffold-only`** y reportar estado `partial` con la razón explícita.

Política por defecto:
- Clientes no regulados con acceso técnico → `full`.
- Clientes regulados (financiero, salud, gobierno) → `dry-run` por defecto.
- Sin shell o sin acceso a env → `scaffold-only` automático.
- Validación sobre suite ya existente → `execute-only`.

## Cadencia y aislamiento (regla universal)

1. **Instrumentar ANTES de la primera corrida**: logfile del servidor de automatización, log de transacciones del mock si aplica, hook de evidencia por fallo (screenshot + DOM/page source) y screenshots por paso. Instrumentar después del primer fallo es diagnosticar a ciegas justo el caso que importaba.
2. **Gate 1:1 primero**: UN escenario end-to-end (`[[calidad-smoke-gate-policy]]`), con el conteo verificado contra el filtro pedido.
3. **Suite completa como inventario**, una vez, para conocer todos los fallos.
4. **Corrección aislada**: cada re-ejecución durante la corrección corre **solo el test que se está corrigiendo** (por nombre o tag). Relanzar la suite en cada iteración está prohibido (`[[calidad-test-self-correction-loop]]`).
5. **Regresión final**: suite completa una vez más, para confirmar.

**Salidas de comandos largos a archivo**, y nunca diagnosticar sobre output de terminal truncado, entremezclado o reusado de una corrida anterior.

## Instrucción

1. **Resolver modo** según contexto del cliente y capacidad técnica del agente. Confirmar con `[[calidad-mandatory-inputs-protocol]]` si hay ambigüedad. Si se degrada a `scaffold-only`, registrar la razón.
2. **Construir comando** usando el skill de run del framework correspondiente: `[[calidad-karate-run-and-tags]]`, `[[calidad-playwright-run-and-modes]]`, `[[calidad-k6-run-and-suite]]`, `[[calidad-appium-run-and-tags]]`. Detalle por framework en `references/execute-and-capture-by-framework.md`.
3. **Ejecutar y capturar** stdout + stderr + exit code + artefactos (HTML reports, JSON summaries, screenshots, traces, videos). Usar `tee` para no perder log y a la vez tenerlo en archivo.
4. **Parsear output** a esquema común definido en `references/result-schema-common.md` según el framework usado. Parsers concretos por framework en `references/output-parsers.md`.
5. **Archivar evidencia** según política de cliente — naming, storage, retención — definida en `references/evidence-archival.md`. Enlazar el archivado con `[[calidad-test-evidence-and-traceability]]`.
6. **Decidir siguiente acción**: si todo pasa → entregar resumen y handover. Si hay fallos → invocar `[[calidad-failure-triage-and-classification]]` para clasificar la naturaleza del fallo y, según modo, escalar a `[[calidad-test-self-correction-loop]]`.
7. **Reportar estado final** explícito: `success` / `partial` / `failed`, con resumen de totales (passed/failed/skipped/errored), duración, links a evidencia y, si aplica, decisión recomendada para el siguiente paso (entregar, iterar, escalar a humano).

Para decidir si la ejecución la hace el AI o el pipeline CI ver `references/executor-as-skill-vs-as-pipeline.md`.

## Restricciones

- **NUNCA** ejecutar suites de carga (K6) sin coordinación previa con el equipo de plataforma del cliente — consumen recursos shared y pueden afectar a otros sistemas.
- **NUNCA** ejecutar contra producción salvo dentro de una ventana coordinada y con autorización escrita del responsable del cliente.
- En modo `dry-run` o `scaffold-only`, **NO modificar** archivos del test después de la ejecución; cualquier corrección propuesta debe quedar como diff sugerido para aprobación humana.
- Si la ejecución consume tokens, secrets o credenciales, **usar el secret store** del cliente (Azure Key Vault, GitHub Secrets, GitLab masked variables, HashiCorp Vault) — nunca hardcodear. Ver `references/secrets-in-pipelines.md` del skill `[[calidad-cicd-integration]]`.
- Si el SUT está caído o no responde, **NO confundir el outage con bug del test** — categorizar como `environment` y delegar a `[[calidad-failure-triage-and-classification]]`.
- Si el output del runner excede umbrales de tamaño (logs muy verbosos, traces gigantes), respetar `[[calidad-streaming-files-protocol]]` para no saturar el contexto del agente.
- Si el modo es `execute-only`, **no regenerar ni reescribir** archivos del test bajo ninguna circunstancia; reportar y delegar al humano.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | ejecutado al menos smoke en modo full con exit_code capturado, stdout persistido y artefactos archivados | Bloqueado: en modo full no se ejecutó nada o no se capturó evidencia de la corrida. La entrega no puede declarar success. |
| 2 | modo confirmado explícitamente al inicio (no asumir full) y degradación a scaffold-only documentada cuando aplica | Bloqueado: el modo de operación no fue confirmado o la degradación automática no quedó documentada. |
| 3 | resultados parseados a esquema común consumible por triage (calidad-failure-triage-and-classification) | Bloqueado: el output de ejecución no fue parseado al esquema común; triage no puede operar sobre datos crudos. |

## Cross-links

- `references/execute-and-capture-by-framework.md`
- `references/result-schema-common.md`
- `references/output-parsers.md`
- `references/evidence-archival.md`
- `references/executor-as-skill-vs-as-pipeline.md`
- `[[calidad-chapter-perspective]]`
- `[[calidad-mandatory-inputs-protocol]]`
- `[[calidad-test-evidence-and-traceability]]`
- `[[calidad-cicd-integration]]`
- `[[calidad-streaming-files-protocol]]`
- `[[calidad-test-self-healing]]`
- `[[calidad-failure-triage-and-classification]]`
- `[[calidad-test-self-correction-loop]]`
- `[[calidad-karate-run-and-tags]]`
- `[[calidad-playwright-run-and-modes]]`
- `[[calidad-k6-run-and-suite]]`
- `[[calidad-appium-run-and-tags]]`
- `[[serenity-wdio-run-and-tags]]`
