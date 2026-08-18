---
id: calidad-route-test-generation
version: 1.0.0
scope: chapter
type: workflow
chapter: calidad
description: Workflow rector del Chapter Calidad para enrutar cualquier solicitud de generación de pruebas al framework correcto.
tags: [workflow, routing, orchestration, karate, k6, playwright, appium, appium-wdio]
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
- **Condicionales**: `base_url` (si no está en spec), `user_story` (obligatorio en Karate brownfield cuando el cliente impone convenciones cliente-específicas), y los que el SUT readiness gate endurece cuando se prueba antes del desarrollo (`spec` con response schemas, `locator_map` — ver paso 1.5).
- **Opcionales**: `firma`, `extra_params`.

## Pasos

### Paso 0 — Leer la traza del pipeline (SIEMPRE, sesión nueva o continuación)

Aplica `[[calidad-pipeline-state-tracking]]` **antes de cualquier otra cosa**:

- Si `output_path` ya existe y tiene `.evidence/pipeline-state.json`, leerlo **junto con `.evidence/session-log.md`** y **abrir el turno reportando**: fase actual, fases pendientes, bloqueos y `open_corrections` reafirmadas. Continuar por `next_action`, no por lo que parezca urgente.
- Si no existen, crearlos: la traza con todas las fases de la ruta en `pending`, la bitácora con su entrada de apertura.
- **Actualizar la traza al cerrar cada fase**, en el mismo turno. Una fase sin evidencia no se marca `done`.
- **Anotar en la bitácora** cada evento significativo —comando y su código de salida, decisión con su motivo, instrucción del usuario citada textualmente, bloqueo con evidencia, escritura en el ALM con quién autorizó— en el turno en que ocurre. La bitácora es **append-only**: nunca se reescribe ni se resume.

Este paso existe porque una generación real no cabe en una sesión: sin traza en disco, cada corte de contexto pierde el proceso (verificado en campo: seis sesiones, fases saltadas, correcciones del usuario olvidadas y dos contratos de cierre emitidos sin haber ejecutado la suite).

### Paso 1 — Recolectar inputs

Aplica `[[calidad-mandatory-inputs-protocol]]`:

- **Lee COMPLETO cada insumo entregado y emite la tabla de extracción** (qué se extrajo de cada uno y dónde se usará). Un insumo sin fila es un insumo ignorado → blocker.
- Verifica que `intent`, `project_name`, `output_path` y (cuando aplique) `spec` estén presentes y bien formados.
- Pregunta por `user_story` y `firma`; recomiéndalos explícitamente.
- Si falta algún obligatorio, **detente**, solicita exactamente lo que falta y espera.

### Paso 1.5 — SUT readiness gate (¿desarrollo listo o pruebas antes del desarrollo?)

Aplica `[[calidad-sut-readiness-gate]]` inmediatamente después de los inputs base, porque su resultado muta la obligatoriedad de los demás inputs:

- Pregunta explícitamente: (1) ¿el desarrollo está desplegado y accesible? → `execution_target: real | hybrid | mock`; (2) ¿existen datos de prueba? → `data_strategy: real | synthetic`; (3) si el intent es front/mobile: ¿existe mapeo acordado de identificadores UI? → `locator_map: provided | missing` (`[[calidad-ui-locator-map-contract]]`).
- Si `execution_target: mock | hybrid`, aplica la matriz de obligatoriedad por stack del gate: `spec` con response schemas completos (API), fuente UI + locator map (Playwright), locator map con accessibility ids (Appium). Si falta un insumo marcado STOP, **detente** y solicítalo.
- Si `execution_target: mock | hybrid`, los mocks se gestionan con `[[calidad-service-virtualization-mockoon]]` y la data sintética con `[[calidad-test-data-management]]` (Faker + seed fijo compartido con el mock).
- Registra los tres valores para el `STRATEGY.md` (paso de pre-diseño) y para el bloque final del delivery gate. **Regla maestra**: mock valida construcción, nunca certifica — la corrida contra mock cierra con `certification: pending_real_integration`.

### Paso 2 — Identificar framework

Aplica `[[calidad-intent-detection]]`:

- Determina si la solicitud es Karate, K6, Playwright, Appium JVM, Appium TypeScript — o **funcional** (análisis/refinamiento de HUs, diseño de casos de alto nivel, estrategia o plan de pruebas). Ver la desambiguación de "pruebas funcionales" en el skill.
- Si el intent es ambiguo, **pregunta**; no asumas Playwright por defecto.
- Si el intent es mobile, resuelve **cuál de los dos stacks Appium** aplica con la tabla de desambiguación de `[[calidad-intent-detection]]`. En greenfield sin señales del ecosistema, pregunta; no elijas por ti.
- Si el usuario pide mobile iOS, no abortes: iOS está soportado. La única limitación es la del scaffolder greenfield JVM, que se resuelve con scaffold manual.
- Si el repositorio es híbrido (web y mobile en el mismo proyecto), enruta **las dos** rutas y declara que se entregan dos stacks.

### Ruta funcional (bifurcación temprana desde el paso 2)

Si el intent es **funcional**, el router bifurca aquí y delega directo — los pasos 2.5 a 7 y los gates de ejecución (smoke, modo de operación, mock) NO aplican a entregables documentales:

| Intent funcional | Workflow destino |
|---|---|
| Analizar / refinar HUs | `[[calidad-analyze-and-refine-stories]]` |
| Diseñar casos de prueba de alto nivel (y publicarlos al ALM) | `[[calidad-design-test-cases]]` |
| Estrategia y/o plan de pruebas | `[[calidad-build-test-strategy-and-plan]]` |

Reglas de la ruta:

- Los inputs los define cada workflow funcional (`stories_source`, `output_path`, etc.); no aplican `spec` ni el gate de mocks. Los insumos pueden venir de Azure DevOps / Jira vía `[[calidad-alm-mcp-integration]]`.
- El **delivery gate contract se emite igual** (`framework: funcional`, `execution.*: null`, cobertura documental) — la ruta funcional no exime del cierre.
- Los gates humanos de la ruta son propios: aprobación del PO en refinamiento, aprobación de estrategia/plan, confirmación de lotes antes de escribir al ALM.
- Conexión con la automatización: los casos diseñados en funcional son el insumo de los stacks — si el usuario continúa hacia automatización, se re-entra al router con el nuevo intent (los pasos 1.5, 3, 4 aplican entonces con normalidad).

### Paso 2.5 — Detectar capacidades transversales complementarias

Aplica `[[calidad-transversal-capabilities]]`:

- A partir del `intent`, el framework detectado, el tipo de SUT (`[[calidad-sut-types-and-adaptations]]`) y el contexto regulatorio, identifica qué capas complementarias hacen la prueba integral: **accesibilidad** (`[[calidad-accessibility-testing]]`), **SEO** (`[[calidad-seo]]`), **seguridad** (`[[calidad-security-testing]]`), **regresión visual** (`[[calidad-visual-regression]]`), **contract testing** (`[[calidad-contract-testing]]`) y **performance** como suite K6 aparte.
- Si el alcance incluye publicar casos, sincronizar identificadores o subir evidencias al ALM, incorporar `[[calidad-alm-test-publishing-cycle]]`, cuyas escrituras pasan todas por `[[calidad-alm-write-authorization-gate]]`.
- Si hay fuente de diseño o escenarios visuales, recordar que `@visual` obliga a comparación de imagen (`[[calidad-visual-regression]]`) y que los textos del diseño se clasifican antes de usarse (`[[calidad-data-volatility-and-assertion-anchoring]]`).
- Aplica *risk-first* (`[[calidad-chapter-perspective]]`): en flujos críticos (login, MFA/OTP, pagos, transferencias, firma, onboarding) y sectores regulados (banca, salud, gobierno), seguridad y accesibilidad pasan de sugeridas a recomendadas con fuerza.
- **Propón** las capas detectadas al usuario con su justificación; no las asumas. Confirma alcance.
- Pasa al workflow específico (paso 5) la lista de capacidades confirmadas: cada una se teje como tag/suite (`@accessibility`, `@seo`, `@security`, `@visual`, `@contract`) dentro del proyecto del framework, o como suite separada cuando requiere otro runtime (performance K6).
- Registra las capas detectadas, confirmadas y omitidas (con motivo) para el bloque `transversal_capabilities` del delivery-gate.

### Paso 2.6 — Barrer el repositorio (solo brownfield, BLOCKER)

Aplica `[[calidad-repo-capability-discovery]]` antes de generar o ejecutar nada:

- Emitir `.evidence/repo-capability-map.md`: scripts y ejecutores disponibles, runbook real, taxonomía de etiquetas viva, alcance del ejecutor (y qué queda fuera), integraciones ya resueltas con el ALM o la nube de dispositivos, y recursos frágiles marcados como no reutilizables.
- Emitir `.evidence/archetype-inventory.md` con la tabla de clasificación de steps (`[[calidad-brownfield-vs-greenfield]]`).
- **Prohibido inventar comandos** y **prohibido construir a mano lo que el repositorio ya resuelve**. La convención del repositorio manda sobre los defaults del chapter en etiquetas, rutas y nomenclatura.

### Paso 2.7 — Evaluar factibilidad de automatización y suficiencia de datos (BLOCKER)

Las dos preguntas que deciden si el alcance comprometido es ejecutable. Se responden **antes de escribir el primer archivo**, con los escenarios ya esbozados:

- **¿Cada escenario se puede automatizar?** Aplica `[[calidad-automation-feasibility-assessment]]`: descomponer en pasos, clasificar cada paso, y en brownfield **buscar en el repositorio si los pasos difíciles ya están resueltos** (obtención de token, segundo factor o clave dinámica, lectura o actualización en base de datos, siembra de estado) antes de declarar nada imposible. Emitir el veredicto por escenario y esperar confirmación del alcance. Lo no automatizable **no se descarta**: se entrega como caso manual trazable, con su feature escrito y su caso creado en el gestor de pruebas.
- **¿Los datos alcanzan?** Aplica `[[calidad-test-data-management]]` (consultar `references/data-sufficiency-gate.md` en su subfolder): derivar de los escenarios la matriz de datos con el **estado que cada uno exige**, cruzarla contra el catálogo del proyecto y **comunicar al QA en el chat lo que falte, con dueño y fecha**. Contra mocks el faltante se sintetiza y se declara como sintético; contra software ya desarrollado es un bloqueo con fecha.

Ambos resultados entran al `STRATEGY.md` y al bloque final del delivery gate. Un alcance confirmado sin estas dos respuestas se descubre imposible a mitad de la entrega.

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
| Appium JVM greenfield (Android)       | `[[calidad-generate-appium-screenplay-android]]`    |
| Appium JVM brownfield (Android / iOS) | `[[calidad-extend-appium-brownfield]]`              |
| Appium TypeScript greenfield          | `[[calidad-generate-appium-wdio-greenfield]]`       |
| Appium TypeScript brownfield          | `[[calidad-extend-appium-wdio-brownfield]]`         |
| Migrar selectores hardcodeados a test-data (TypeScript) | `[[calidad-migrate-selectors-to-testdata]]` |

> **Nota mobile — dos stacks de producto y un core compartido.** El chapter soporta Appium sobre JVM (`appium-serenity`: Serenity y Gradle, con Screenplay o POM) y sobre TypeScript (`appium-wdio`: WebdriverIO y cucumber-js). Ambos requieren **`appium-core`**, que aporta lo que no depende del lenguaje: resolución de locators, comportamiento de Flutter, catálogo de interacciones y auto-discovery de binario. `appium-core` no se elige: acompaña. Los dos stacks de producto difieren en todo lo demás. La elección la determina el ecosistema del equipo o el proyecto existente, nunca la preferencia del agente: ver la tabla de desambiguación en `[[calidad-intent-detection]]` y, ante greenfield sin señales, **preguntar**.
>
> **Nota iOS.** El único alcance Android es el del *scaffolder* greenfield JVM; para greenfield iOS en JVM se aplica el scaffold manual de `references/android-only-scope-rationale.md` del skill `[[calidad-appium-screenplay-android]]`. El stack TypeScript genera iOS de forma nativa y el brownfield de ambos stacks soporta Android e iOS. iOS exige entorno macOS: si no está disponible, se entrega lo generado y se reporta `partial`, nunca se degrada a Android en silencio.
>
> **Nota repos híbridos.** Un repositorio con navegador y app nativa orquestados por un único cucumber-js necesita **dos rutas**, no una: la web por su stack y la mobile por el suyo. Las convenciones comunes de la capa Cucumber —catálogo de steps, sufijo de plataforma, tagging, propiedades verificables— vienen de `[[calidad-cucumber-bdd-conventions]]` y aplican a las dos.

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

1. **Resolver modo de operación universal** con el usuario si el workflow delegado no lo hizo (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin shell, sin entornos, sin credenciales), degradar a `scaffold-only` y reportar `partial`. Si `execution_target: mock | hybrid` (paso 1.5), levantar el mock (`[[calidad-service-virtualization-mockoon]]`) ANTES del smoke gate; la ejecución contra mock es válida como verificación de construcción y el delivery gate la registra como `certification: pending_real_integration`. **"Sin ambiente real" NO es motivo de `scaffold-only` cuando hay mock**: el mock levantado cuenta como SUT alcanzable y el default sigue siendo `full` contra mock. No sugerir scaffold-only de entrada para luego redirigir a mocks — el gate del paso 1.5 ya resolvió el camino.
1.5. **Preflight de ejecución (BLOCKER)**: aplicar `[[calidad-execution-preflight]]` y emitir `.evidence/preflight.json` con la salida real de cada sonda — SUT alcanzable, sesión apuntando al destino que se levantó, aplicación instalada y en primer plano con captura inicial. **Sin preflight verde no se ejecuta el smoke gate**, y nada de lo que ocurra después puede clasificarse como defecto del SUT.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` con el comando del mapa de recursos del repositorio en brownfield (`[[calidad-repo-capability-discovery]]`), o el idiomático del framework en greenfield. Si la entrega cubre varias plataformas, aplicar `[[calidad-cross-platform-learning-propagation]]`: usar el ejecutor multiplataforma del repositorio si existe, y si la ejecución es secuencial, aplicar los aprendizajes compartidos antes de arrancar cada plataforma siguiente.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar cada uno como deterministic / flaky y diagnosticar causa raíz. Declarar un defecto del SUT exige además la cadena de evidencia completa (`references/sut-defect-evidence-chain.md`), y publicarlo en el ALM exige la ficha de `[[calidad-alm-write-authorization-gate]]`.
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique. Respetar `max_iterations` (default 3) y los **anti-cheating guardrails maestros del chapter**.
5. Reportar estado final agregado: `success` (todos los tests pasan determinísticamente en el framework delegado) | `partial` (entregado scaffold, no se pudo ejecutar) | `failed` (escalado a humano con contexto completo del framework correspondiente).
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`. El router NO finaliza con éxito si esta fase quedó sin cerrar.
7. **Invocar `[[calidad-generate-executive-report]]`** para producir el reporte consolidado post-corrida en formato HTML/PPTX/DOC. Si modo es `scaffold-only` o `dry-run` → omitir y registrar `null` en el `delivery_gate.evidence_persisted.executive_report`.
8. **Emitir `[[calidad-delivery-gate-contract]]`** con el bloque YAML completo antes del mensaje final. Sin este bloque, la entrega se considera incompleta. **Precondición**: leer `.evidence/pipeline-state.json` y verificar cero fases obligatorias pendientes — con fases pendientes NO se emite el gate, se emite un reporte de estado y el trabajo continúa. Un smoke verde no es el final del pipeline: faltan suite completa, verificación del reporte, triage y reporte ejecutivo.

## Criterios de finalización

Este workflow se considera completo **solo cuando**:

- [ ] La **traza del pipeline** (`.evidence/pipeline-state.json`) fue leída al abrir la sesión y actualizada al cerrar cada fase; el delivery gate se emitió con cero fases obligatorias pendientes.
- [ ] Cada insumo entregado tiene su fila en la **tabla de extracción** (qué se extrajo, dónde se usó) o su justificación de no aplicabilidad.
- [ ] El framework destino y el modo (greenfield / brownfield) fueron resueltos correctamente para los **5 stacks soportados** (Karate, Playwright, K6, Appium JVM, Appium TypeScript) en cualquiera de sus dos modos — o la solicitud se bifurcó a la **ruta funcional** con su workflow correcto.
- [ ] Si el intent fue mobile: el stack Appium se resolvió por señales del ecosistema o preguntando, nunca por preferencia del agente.
- [ ] Si el repositorio era híbrido: se enrutaron ambos stacks y las convenciones Cucumber comunes se aplicaron con `[[calidad-cucumber-bdd-conventions]]`.
- [ ] Si la ruta fue funcional: el workflow delegado cerró con su delivery gate documental y sus gates humanos cumplidos (nada escrito al ALM sin aprobación/confirmación).
- [ ] El **SUT readiness gate** (paso 1.5) fue resuelto explícitamente: `execution_target`, `data_strategy` y (front/mobile) `locator_map` registrados en STRATEGY.md y delivery gate. Si `execution_target != real`, el delivery gate declara `certification: pending_real_integration` y `next_steps` incluye el switchover a integraciones reales.
- [ ] Las **capacidades transversales complementarias** (accesibilidad, SEO, seguridad, regresión visual, contract, performance) fueron evaluadas con `[[calidad-transversal-capabilities]]`, propuestas al usuario y registradas (aplicadas u omitidas con motivo) en el bloque `transversal_capabilities` del delivery-gate.
- [ ] Todos los archivos de prueba esperados están escritos en `output_path` y son consistentes con el spec/firma.
- [ ] En greenfield, la infraestructura completa (`pom.xml`/`package.json`/`build.gradle`, configs, runners, README) está presente.
- [ ] En brownfield (Karate, Playwright, K6 y Appium), **no** se sobrescribió infraestructura existente y las convenciones detectadas se respetaron.
- [ ] El comando de ejecución (`mvn test`, `npx playwright test`, `k6 run ...`, `./gradlew test`, `npx cucumber-js --profile <plataforma>`) está documentado en el `README.md` generado.
- [ ] La ruta del reporte de evidencia está documentada y el reporter está activo.
- [ ] El checklist de calidad propio del framework destino (ver el workflow específico) está aprobado.
- [ ] El usuario tiene un mensaje final que enumera (a) archivos generados, (b) comando de ejecución, (c) ruta del reporte, (d) tags de trazabilidad usados.
- [ ] Tests ejecutados al menos una vez por el workflow delegado. Estado agregado: `success` / `partial` / `failed` reportado por el router.
- [ ] Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
- [ ] Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados.
- [ ] Si el modo es `dry-run` o `scaffold-only`: scaffold + comandos de ejecución + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
- [ ] Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra del chapter).
