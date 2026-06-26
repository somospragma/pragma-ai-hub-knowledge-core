---
id: calidad-route-test-generation
version: 1.0.0
scope: chapter
type: workflow
chapter: calidad
description: Workflow rector del Chapter Calidad para enrutar cualquier solicitud de generación de pruebas al framework correcto.
tags: [workflow, routing, orchestration, karate, k6, playwright, appium]
---

# Route Test Generation — Workflow Rector del Chapter Calidad

## Cuándo usar este workflow

Usa este workflow **siempre** que un usuario solicite generar pruebas automatizadas, sin importar el framework. Es el punto de entrada único del Chapter Calidad para tareas de generación.

NO uses este workflow para:

- Revisión de tests existentes sin generar nuevos (usa workflows de code-review).
- Definición de estrategia de pruebas a alto nivel (usa workflows de planning).
- Configuración de CI/CD (usa workflows de DevOps).

## Inputs

Inputs obligatorios y opcionales gobernados por `[[calidad-mandatory-inputs-protocol]]`:

- **Obligatorios**: `intent`, `project_name`, `output_path`, `spec` (excepto algunos casos puntuales de Playwright greenfield sin contrato).
- **Condicionales**: `base_url` (si no está en spec), `user_story` (obligatorio en Karate brownfield cuando el cliente impone convenciones cliente-específicas).
- **Opcionales**: `firma`, `extra_params`.

## Pasos

### Paso 1 — Recolectar inputs

Aplica `[[calidad-mandatory-inputs-protocol]]`:

- Verifica que `intent`, `project_name`, `output_path` y (cuando aplique) `spec` estén presentes y bien formados.
- Pregunta por `user_story` y `firma`; recomiéndalos explícitamente.
- Si falta algún obligatorio, **detente**, solicita exactamente lo que falta y espera.

### Paso 2 — Identificar framework

Aplica `[[calidad-intent-detection]]`:

- Determina si la solicitud es Karate, K6, Playwright o Appium.
- Si el intent es ambiguo, **pregunta**; no asumas Playwright por defecto.
- Si el usuario pide mobile iOS greenfield, no abortes: el scaffolder V2 no lo genera automáticamente, pero el chapter sí soporta iOS via scaffold manual (apuntar a `references/android-only-scope-rationale.md` del skill `[[calidad-appium-screenplay-android]]`). Si es mobile iOS brownfield, enrutar a `[[calidad-appium-brownfield]]`.

### Paso 3 — Validar el spec

Aplica `[[calidad-spec-validation]]`:

- Para Karate/K6: valida el spec (OpenAPI/Swagger/WSDL) según reglas mínimas.
- Si la validación **falla**, reporta el error específico al usuario (ej. "spec vacío", "no es JSON ni YAML válido", "WSDL sin endpoint") y **detén** el workflow.
- Si pasa, extrae endpoints, base URL, security schemes y enums; pasa esa estructura al siguiente paso.

### Paso 4 — Decidir greenfield vs brownfield

Aplica `[[calidad-brownfield-vs-greenfield]]`:

- Inspecciona el `output_path` y los archivos que el usuario haya provisto.
- Aplica las reglas duras del framework correspondiente (qué se genera, qué no).
- En brownfield, detecta y registra las convenciones del proyecto (features dir, package, naming, selectores, etc.).

### Paso 5 — Invocar el workflow específico del framework

Transfiere el control al workflow concreto según el resultado de los pasos 2 y 4:

| Framework + modo            | Workflow destino                              |
|-----------------------------|-----------------------------------------------|
| Karate greenfield           | `[[calidad-generate-karate-greenfield]]`              |
| Karate brownfield           | `[[calidad-extend-karate-brownfield]]`                |
| Playwright greenfield       | `[[calidad-generate-playwright-greenfield]]`          |
| Playwright brownfield       | `[[calidad-update-playwright-brownfield]]`            |
| K6 greenfield               | `[[calidad-generate-k6-suite]]`                       |
| K6 brownfield               | `[[calidad-extend-k6-brownfield]]`                    |
| Appium greenfield (Android, V2)   | `[[calidad-generate-appium-screenplay-android]]`    |
| Appium brownfield (Android / iOS) | `[[calidad-extend-appium-brownfield]]`              |

> Nota Appium: el scaffolder greenfield V2 solo genera proyectos Android (limitación de tooling). Para greenfield iOS, apuntar al usuario al workaround manual descrito en `references/android-only-scope-rationale.md` del skill `[[calidad-appium-screenplay-android]]`. El brownfield Appium sí soporta Android e iOS (la plataforma se detecta del proyecto), ver `[[calidad-appium-brownfield]]`.

### Paso 6 — Emitir archivos con disciplina

Aplica `[[calidad-streaming-files-protocol]]` durante toda la fase de generación:

- Primero archivos de prueba (`*.feature`, `*.spec.ts`, `tests/*.js`).
- Luego utilitarios compartidos (bodies, Page Objects, helpers, Tasks/Questions).
- Por último infraestructura (`pom.xml`, `package.json`, `playwright.config.ts`, `build.gradle`, README, runners).
- Cada archivo se persiste inmediatamente; nada se acumula en memoria.

### Paso 7 — Configurar evidencia y trazabilidad

Aplica `[[calidad-test-evidence-and-traceability]]`:

- Configura el reporter del framework (`karate-reports`, `playwright-report`, `handleSummary` K6, Serenity aggregate).
- Asegura que cada test tenga al menos un tag `@user-story:<ID>` o `@requirement:<ID>`.
- Documenta en el `README.md` la ruta del reporte y el comando para abrirlo.

### Fase final obligatoria — Ejecutar, triar y auto-corregir (invocación universal)

**Esta fase es parte del contrato de entrega del router**: independientemente del workflow específico al que se haya delegado en el paso 5, el router exige que el ciclo de ejecución + triage + auto-corrección se haya cerrado. Cada workflow específico ya integra esta fase con adaptaciones por framework; el router la audita y confirma su cumplimiento antes de finalizar.

1. **Resolver modo de operación universal** con el usuario si el workflow delegado no lo hizo (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin shell, sin entornos, sin credenciales), degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` con el comando idiomático del framework delegado.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar cada uno como deterministic / flaky y diagnosticar causa raíz.
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique. Respetar `max_iterations` (default 3) y los **anti-cheating guardrails maestros del chapter**.
5. Reportar estado final agregado: `success` (todos los tests pasan determinísticamente en el framework delegado) | `partial` (entregado scaffold, no se pudo ejecutar) | `failed` (escalado a humano con contexto completo del framework correspondiente).
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`. El router NO finaliza con éxito si esta fase quedó sin cerrar.
7. **Invocar `[[calidad-generate-executive-report]]`** para producir el reporte consolidado post-corrida en formato HTML/PPTX/DOC. Si modo es `scaffold-only` o `dry-run` → omitir y registrar `null` en el `delivery_gate.evidence_persisted.executive_report`.
8. **Emitir `[[calidad-delivery-gate-contract]]`** con el bloque YAML completo antes del mensaje final. Sin este bloque, la entrega se considera incompleta.

## Criterios de finalización

Este workflow se considera completo **solo cuando**:

- [ ] El framework destino y el modo (greenfield / brownfield) fueron resueltos correctamente para los **4 frameworks soportados** (Karate, Playwright, K6, Appium) en cualquiera de sus dos modos.
- [ ] Todos los archivos de prueba esperados están escritos en `output_path` y son consistentes con el spec/firma.
- [ ] En greenfield, la infraestructura completa (`pom.xml`/`package.json`/`build.gradle`, configs, runners, README) está presente.
- [ ] En brownfield (Karate, Playwright, K6 y Appium), **no** se sobrescribió infraestructura existente y las convenciones detectadas se respetaron.
- [ ] El comando de ejecución (`mvn test`, `npx playwright test`, `k6 run ...`, `./gradlew test`) está documentado en el `README.md` generado.
- [ ] La ruta del reporte de evidencia está documentada y el reporter está activo.
- [ ] El checklist de calidad propio del framework destino (ver el workflow específico) está aprobado.
- [ ] El usuario tiene un mensaje final que enumera (a) archivos generados, (b) comando de ejecución, (c) ruta del reporte, (d) tags de trazabilidad usados.
- [ ] Tests ejecutados al menos una vez por el workflow delegado. Estado agregado: `success` / `partial` / `failed` reportado por el router.
- [ ] Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
- [ ] Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados.
- [ ] Si el modo es `dry-run` o `scaffold-only`: scaffold + comandos de ejecución + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
- [ ] Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra del chapter).
