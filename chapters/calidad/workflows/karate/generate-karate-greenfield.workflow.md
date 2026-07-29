---
id: calidad-generate-karate-greenfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [karate]
description: Flujo completo para generar un proyecto Karate desde cero a partir de un spec OpenAPI/Swagger/WSDL.
tags: [karate, greenfield, workflow, openapi]
---

# Workflow — Generar proyecto Karate greenfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` y `[[calidad-brownfield-vs-greenfield]]` identifican un escenario greenfield para Karate: el usuario provee spec, no provee archivos de un proyecto existente, y solicita pruebas funcionales/contract de APIs.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `spec` | Sí | OpenAPI 3.x, Swagger 2.0 o WSDL. |
| `project_name` | Sí | En kebab-case. |
| `output_path` | Sí | Carpeta destino. |
| `base_url` | No | Si se omite, se extrae del spec. |
| `user_story` | No | Tag `@user-story:HUT-XXX`. |
| `firma` | No | Documento técnico complementario. |

Recolectar inputs siguiendo `[[calidad-mandatory-inputs-protocol]]`, incluido el SUT readiness gate (`[[calidad-sut-readiness-gate]]`). Si `execution_target: mock | hybrid` (pruebas antes del desarrollo), el `spec` DEBE incluir response schemas completos y examples — sin eso el mock no es fiel y el gate detiene el flujo.

## Pasos

### 1. Pre-flight check del stack (OBLIGATORIO)

Antes de cualquier otra acción, ejecutar el pre-flight según [[calidad-karate-greenfield]] (consultar `references/preflight.md` en su subfolder):
- Si pasa: continuar al paso 2.
- Si falla: aplicar las degradaciones documentadas en `preflight.md` y reportar al usuario antes de proceder.
- Persistir el resultado en `.evidence/preflight-result.json`.

Este paso es enforcement obligatorio según `[[calidad-pre-generation-protocol]]`.

### 2. Análisis previo (STRATEGY.md)

Antes de generar cualquier código, generar `STRATEGY.md` en el `output_path` según ``references/templates.md` (sección `STRATEGY.md`)` y `[[calidad-pre-design-strategy-document]]`. Presentar al usuario y esperar:
- "aprobado" → continuar al siguiente paso.
- "modificar X" → iterar el documento; volver a presentar.

NUNCA generar código sin STRATEGY.md aprobado explícitamente.

### 3. Validar el spec
Aplica `[[calidad-spec-validation]]`. OpenAPI > 200 chars, WSDL > 100 chars, debe parsear sin errores. Si falla, detente y reporta error específico.

### 4. Extraer service info
Service name kebab-case desde `info.title` (fallback: filename). `base_url` desde `servers[0].url` / `schemes+host+basePath` / `soap:address`. Variable de URL: camelCase + `Url`.

### 5. Inventario de endpoints y schemas
Para cada path×method: required headers, body fields, response codes, enums, formatos. Convierte `components.schemas` o `definitions` a la notación match (`[[calidad-karate-greenfield]] (consultar `references/contract-testing-match-patterns.md` en su subfolder)`).

### 6. Decidir cobertura por endpoint
Aplica `[[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)`. Declara el número objetivo de escenarios por endpoint ANTES de generar.

### 7. Generar features
Invoca `[[calidad-karate-greenfield]]` paso 5. Usa los tipos y tags de `references/feature-design-dsl.md`. Si hay señales de cifrado, añade los escenarios de `references/encrypted-payloads.md`. Aplica `[[calidad-route-test-generation]]` para mapear endpoint → archivos.

### 8. Generar schemas `-match.json`
Uno por schema utilizado en respuestas. Respeta `#type` vs `##type`.

### 9. Generar infraestructura
`pom.xml`, `karate-config.js`, `logback-test.xml`, `TestRunner.java` según `references/project-structure.md`. Versiones exactas: `karate-junit5` 1.4.1, `maven-surefire-plugin` 3.2.2. Bloque `<testResources>` obligatorio (`[[calidad-karate-greenfield]] (consultar `references/file-location-constraint.md` en su subfolder)`).

### 10. Asegurar resource files y validar DoD
Detecta referencias a `classpath:resources/files/*` y crea archivos por defecto. Recorre el checklist de finalización antes de entregar. Entrega con `[[calidad-streaming-files-protocol]]` y registra trazabilidad por `[[calidad-test-evidence-and-traceability]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.**

**Si `execution_target: mock | hybrid`** (resuelto por `[[calidad-sut-readiness-gate]]`): antes del smoke gate, generar el environment con `[[calidad-generate-mockoon-environment-prompt]]`, levantarlo (`mockoon-cli start --data mocks/mockoon/environment.json --port 3010 --faker-seed $FAKER_SEED &`) y verificar el health-probe. `karate-config.js` incluye env `mock` con `baseUrl` al mock; la suite corre con `-Dkarate.env=mock`. Ver `[[calidad-service-virtualization-mockoon]]`. El delivery gate registra `execution_target` y `certification: pending_real_integration`; el switchover a real es solo configuración (consultar `references/mock-vs-real-switchover.md` en su subfolder).

0. **Smoke gate 1:1 (obligatorio)** — Antes de ejecutar la suite completa, validar que el scaffold corre end-to-end con un solo escenario `@smoke`. Aplicar [[calidad-smoke-gate-policy]] y [[calidad-karate-greenfield]] (consultar `references/smoke-gate-mvn.md`). Comando: `mvn test -Dkarate.options="--tags @smoke"` (con `-Dkarate.env=mock` si aplica). Si falla con exit ≠ 0 → status `partial` con `blocker: "smoke_gate_failed_karate"` (o `mock_unavailable` si el mock no levantó) y escalar al usuario; NO continuar a ejecución completa de la suite.

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin shell, sin `mvn`, sin red al SUT), degradar a `scaffold-only` y reportar `partial`. **Con `execution_target: mock`, el mock local ES el SUT alcanzable**: no degradar a scaffold-only por falta de ambiente real; el default sigue siendo `full` contra el mock.
2. **Ejecutar** `mvn test` (o el filtro por tag de la nueva historia) vía `[[calidad-test-execution-orchestration]]`. Capturar `target/karate-reports/karate-summary.json` como evidencia primaria y parsear a esquema común.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar cada uno como deterministic / flaky y diagnosticar causa raíz (bug del SUT, contrato mal asumido, payload inválido, environment, timing, infra).
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique (p. ej. schema-drift tolerable en `match`). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca relajar aserciones de negocio, status code o headers de seguridad para forzar verde.
5. Reportar estado final: `success` (todos los tests pasan determinísticamente) | `partial` (entregado scaffold, no se pudo ejecutar) | `failed` (escalado a humano con contexto completo: feature, scenario, assertion, response real, hipótesis).
6. Archivar evidencia + audit log de correcciones aplicadas según `[[calidad-test-evidence-and-traceability]]`.

### Paso final — Reporte ejecutivo

Invocar `[[calidad-generate-executive-report]]` con `results_path`, `strategy_md_path` y `output_format` (preguntar al usuario o usar default `html`). El reporte se persiste en `.evidence/report-{ISO}.{ext}` y se referencia en el `delivery_gate.evidence_persisted.executive_report`. Si modo es `scaffold-only` o `dry-run` → omitir este paso y registrar `null`.

## Criterios de finalización (DoD — 14 items)

1. Todos los archivos no-Java en `src/test/java/` (cero en `src/test/resources/`).
2. Fórmula real de cobertura mínima aplicada por endpoint (no piso fijo de 5 si el endpoint es complejo).
3. Happy path valida status AND significado de negocio (no sólo `status 200`).
4. Contract tests con notación correcta (`#type` requerido, `##type` opcional, sin `##[] #type`).
5. Cobertura exhaustiva de required fields: `absent + null + invalid-type` por campo.
6. Cobertura exhaustiva de headers: `missing` + `invalid-format` (si aplica) por header.
7. Escenarios de cifrado si aplica: `valid + invalid-key + plaintext-body + missing-encryption-header`.
8. `pom.xml` con `karate-junit5` 1.4.1, `maven-surefire-plugin` 3.2.2 y `<testResources>` excluyendo `**/*.java`.
9. `karate-config.js` retorna `config` con `baseUrl`, `ssl`, `connectTimeout`, `readTimeout`.
10. `TestRunner.java` usa `.relativeTo(getClass())` y package `com.testing`.
11. Sin auth inline si el spec no declara `security`.
12. Todos los paths relativos en `Given path` (sin protocolo/host).
13. Field names en bodies coinciden exactamente con el spec.
14. Sin lógica condicional (`if`) en aserciones; `Examples` sin celdas vacías. Comando `mvn test` provisto en la entrega.
15. Tests ejecutados al menos una vez. Estado: `success` / `partial` / `failed` reportado.
16. Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
17. Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados.
18. Si el modo es `dry-run` o `scaffold-only`: scaffold + comando `mvn test` + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
19. Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).
