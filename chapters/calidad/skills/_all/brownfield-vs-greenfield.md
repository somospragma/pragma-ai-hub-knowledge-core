---
id: calidad-brownfield-vs-greenfield
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: Distingue proyectos brownfield (existentes) de greenfield (nuevos) y define qué se genera y qué no en cada modo, por framework.
tags: [brownfield, greenfield, karate, playwright, k6, conventions]
---

# Brownfield vs Greenfield — Reglas de Generación por Modo

## Cuándo aplicar

Aplica este skill después de `[[calidad-intent-detection]]` y antes de invocar el workflow específico de generación (paso 4 de `[[calidad-route-test-generation]]`).

## Criterios de clasificación

Es **brownfield** si **cualquiera** de las siguientes condiciones es verdadera:

- El usuario provee archivos del proyecto existente (features, tests, page objects, configuraciones).
- El `output_path` ya contiene código de pruebas (existe `pom.xml`, `karate-config.js`, `package.json` con `@playwright/test`, `playwright.config.ts`, carpetas `features/`, `tests/`, `pages/`, etc.).
- El usuario describe explícitamente "queremos agregar tests al proyecto X", "actualizar selectores", "extender la suite existente".

Es **greenfield** si **todas** las siguientes son verdaderas:

- No hay archivos previos en el `output_path` (o existe pero está vacío).
- El usuario no menciona un proyecto preexistente.
- No hay convenciones del cliente que respetar más allá de las del Chapter.

**Regla de oro:** si tienes duda, **inspecciona el `output_path` antes de decidir**. Si después de inspeccionar sigues con duda, pregunta al usuario.

## Inventario del arquetipo — BLOCKER antes del primer archivo

En brownfield, **no se genera ningún archivo hasta emitir `.evidence/archetype-inventory.md` y mostrarlo al usuario**. Es la puerta que evita el fallo más caro y más repetido del modo brownfield: generar antes de conocer el proyecto.

Verificado en campo, tres fallos con la misma causa en una sola entrega: se redefinieron steps que ya existían en otra épica, se generó un step que colisionaba con otra historia, y se escribieron credenciales literales en el código mientras el proyecto ya tenía su mecanismo de carga de datos. El workflow decía "inventariar", pero no exigía **emitir** el inventario ni bloqueaba si faltaba.

El inventario contiene, como mínimo:

| Sección | Contenido | Fuente |
|---|---|---|
| Recursos y comandos | qué scripts y ejecutores existen y cuál se usa | `[[calidad-repo-capability-discovery]]` |
| Catálogo de steps | vocabulario existente y **tabla de clasificación** de cada step candidato en reutilizar/extender/crear, con el archivo donde vive el existente | `[[calidad-cucumber-bdd-conventions]]`, `references/step-catalog.md` |
| Patrón de carga de datos | cómo cargan los datos de prueba los steps existentes | reference de detección de convenciones del stack |
| Taxonomía de tags | etiquetas en uso y su significado real | reference de detección de convenciones del stack |
| Selectores | dónde viven, con qué sintaxis y cómo se resuelven | reference de detección de convenciones del stack |
| Alcance del ejecutor | qué carga y, sobre todo, **qué queda fuera** | `[[calidad-repo-capability-discovery]]` |
| Estructura | convención de directorios y de nombres por plataforma | reference de detección de convenciones del stack |
| Deuda observada | señales de deuda del arquetipo, **para reportar, no para corregir** | reference de detección de convenciones del stack |

Reglas asociadas:

- **La tabla de clasificación de steps es blocker.** Un step clasificado `reuse` no se redefine.
- **Búsqueda por similitud, no solo exacta**: los steps que verifican elementos comunes (fechas, montos, estados, títulos) colisionan entre épicas; los nuevos llevan su contexto en el nombre.
- **Validación anti-duplicación después de generar**: definiciones repetidas es blocker, no advertencia.
- **Nunca credenciales ni datos literales** en el código generado: se usa el mecanismo del proyecto.
- El inventario se registra como fase en `[[calidad-pipeline-state-tracking]]` y se relee al retomar sesión.

## Reglas duras por framework

### Karate

| Modo        | Qué SE genera                                                    | Qué NO se genera                                                     |
|-------------|------------------------------------------------------------------|----------------------------------------------------------------------|
| greenfield  | Proyecto completo: `.feature`, bodies JSON, `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, `README.md` | —                                                                    |
| brownfield  | Solo `.feature` nuevos/actualizados y bodies JSON                | `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, ningún archivo de build o configuración |

En **brownfield Karate** debes detectar y respetar **exactamente** las convenciones del proyecto:

| Convención                  | Cómo se detecta                                                                                | Ejemplo                                              |
|-----------------------------|------------------------------------------------------------------------------------------------|------------------------------------------------------|
| `features_dir`              | Carpeta que contiene archivos `.feature` existentes                                            | `src/test/java/features/`                            |
| `bodies_dir`                | Carpeta hermana que contiene JSON de request bodies                                            | `src/test/java/bodies/`                              |
| `package_name`              | Paquete Java declarado en `TestRunner.java`                                                    | `com.client.qa.api`                                  |
| `base_url_var`              | Nombre de la variable de base URL en `karate-config.js`                                        | `baseUrlApi`, `apiBaseUrl`                           |
| `header_style`              | Inline en feature vs. `karate-config.js` vs. helper feature                                    | inline / config / helper                             |
| `body_loading_style`        | `read('classpath:...')` vs. `read('bodies/...')` vs. inline                                    | classpath / relative                                 |
| `scenario_naming_pattern`   | Convención observada en los `Scenario:` existentes                                             | `"[POSITIVE] should ..."`, `"CP-001 Crear usuario"`  |

### Playwright

| Modo        | Qué SE genera                                                          | Qué NO se genera                                                     |
|-------------|------------------------------------------------------------------------|----------------------------------------------------------------------|
| greenfield  | Proyecto completo: tests, Page Objects, `playwright.config.ts`, `tsconfig.json`, `package.json`, fixtures, README | —                                                                    |
| brownfield  | Solo Page Objects y tests (nuevos o actualizados)                      | `package.json`, `playwright.config.ts`, `tsconfig.json`, fixtures base, scripts npm |

En **brownfield Playwright** detecta y respeta:

| Convención              | Cómo se detecta                                                       | Ejemplo                                  |
|-------------------------|-----------------------------------------------------------------------|------------------------------------------|
| `test_file_pattern`     | Naming de los `*.spec.ts` o `*.test.ts` existentes                    | `feature.spec.ts`, `*.e2e.ts`            |
| `page_object_style`     | Clase con métodos vs. función factory vs. POM con fixtures            | class / factory / fixture-based          |
| `selector_strategy`     | `getByRole`, `getByTestId`, CSS, XPath                                | getByTestId preferido                    |
| `import_style`          | Alias `@/pages/...` vs. rutas relativas                               | `@/pages/LoginPage`                      |
| `auth_pattern`          | `storageState`, `globalSetup`, login por test                         | storageState con `setup.ts`              |

### K6

| Modo        | Qué SE genera                                                                                  | Qué NO se genera                                                                                  |
|-------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| greenfield  | Proyecto completo: 5 scripts (`smoke`, `load`, `stress`, `spike`, `soak`), `config.js`, `utils.js`, `package.json`, `README.md`, `run-all.sh`, `.gitignore` | —                                                                                                 |
| brownfield  | Solo `tests/*-test.js` nuevos y patches incrementales a `config.js` / `utils.js`               | `package.json`, `README.md`, `run-all.sh`, `.gitignore`, ni regeneración completa de `config.js`/`utils.js` |

**Detección brownfield:** el `project_root` (= `output_path`) contiene mínimo `tests/config.js` + `tests/utils.js` + ≥1 `tests/*-test.js`. Si falta alguno, tratar como greenfield.

**Acción greenfield:** invocar `[[calidad-k6-greenfield]]` y el workflow `[[calidad-generate-k6-suite]]`.

**Acción brownfield:** invocar `[[calidad-k6-brownfield]]` y el workflow `[[calidad-extend-k6-brownfield]]`. NO regenerar infraestructura. Reusar `config.js` y `utils.js` (entregar patches incrementales, no archivos completos).

En **brownfield K6** detecta y respeta:

| Convención                       | Cómo se detecta                                                                              | Ejemplo                                  |
|----------------------------------|----------------------------------------------------------------------------------------------|------------------------------------------|
| `tests_dir`                      | Carpeta que contiene los `*-test.js` existentes                                              | `tests/` (default) o `perf/`, `k6/`       |
| `script_naming`                  | Estilo del filename del primer script                                                        | `smoke-test.js` (kebab) / `smoke_test.js` (snake) |
| `groups_naming`                  | Idioma y prefijos en `group()` / `check()`                                                   | Español (`'crear usuario'`) vs Inglés    |
| `auth_mode`                      | `authToken` en `config.js` + `Authorization` en `getDefaultHeaders()`                        | `spec` (default) o `external` (override) |
| `existing_thresholds`            | Valores de `options.thresholds` mapeados a Conservative/Moderate/Relaxed                     | Moderate                                 |
| `existing_payload_builders`      | Funciones `buildXxxBody()` ya presentes en `utils.js`                                        | `buildCreateUserBody`                    |
| `existing_id_correlation_pattern`| Cómo se extrae el id del response del POST y se reusa en GET/PUT/DELETE                      | `const id = res.json('id');` + guard     |
| `handle_summary_path`            | Destino dentro de `handleSummary()`: `results/` (default) vs `reports/`                       | `results/${timestamp}-summary.json`      |

Detalle del algoritmo en [[calidad-k6-brownfield]] (consultar `references/convention-detection.md` en su subfolder). Patrones de extensión en [[calidad-k6-brownfield]] (consultar `references/extension-patterns.md` en su subfolder).

### Appium

Pragma's Chapter Calidad soporta **tanto greenfield como brownfield** en Appium, y **tanto Android como iOS**. La separación es:

| Modo        | Plataforma soportada              | Asset destino                                                                                  |
|-------------|-----------------------------------|------------------------------------------------------------------------------------------------|
| greenfield  | Android (vía scaffolder V2)       | `[[calidad-appium-screenplay-android]]`                                                                |
| greenfield  | iOS (vía scaffold manual)         | Guidance manual en `references/android-only-scope-rationale.md` del skill greenfield           |
| brownfield  | Android **e** iOS                 | `[[calidad-appium-brownfield]]`                                                                        |

**Detección brownfield Appium:** `project_root` contiene `build.gradle` o `pom.xml`, **más** `src/test/resources/features/` (o equivalente), **más** ≥1 archivo `.feature`. Si además existen UserInterfaces bajo `src/main/java/.../userinterfaces/`, refuerza brownfield.

**Acción brownfield:** invocar `[[calidad-appium-brownfield]]`. Preservar infraestructura (`build.gradle`/`pom.xml`, `gradlew`, `serenity.conf`, runner Cucumber). Respetar convenciones detectadas (`base_package`, `gherkin_language`, tags, naming). Soporta Android y iOS — la plataforma se detecta leyendo `automationName` en las capabilities (`UiAutomator2` → android, `XCUITest` → ios).

**Acción greenfield Android:** invocar `[[calidad-appium-screenplay-android]]` (scaffolder V2 produce proyecto completo Gradle + Screenplay + Serenity + Cucumber). Solo Android — es una limitación del auto-generador, no del chapter.

**Acción greenfield iOS:** el scaffolder V2 NO genera proyectos iOS. Apuntar al usuario al workaround manual descrito en `references/android-only-scope-rationale.md` del skill `[[calidad-appium-screenplay-android]]`. V3 del scaffolder incluirá iOS.

## Restricciones

- En brownfield **jamás regenerar infraestructura existente**: no sobrescribir `pom.xml`, `playwright.config.ts`, `package.json`, runners ni configs.
- En brownfield **jamás cambiar convenciones detectadas**: si el proyecto usa `getByTestId`, el código nuevo usa `getByTestId`; si los scenarios se nombran `CP-001 ...`, los nuevos también.
- Si las convenciones del brownfield están en **conflicto interno** (p. ej. dos estilos de Page Object), **pregunta al usuario** cuál adoptar; no decidas tú.
- En greenfield aplica los estándares del Chapter; no inventes variantes.
- Encadena con `[[calidad-streaming-files-protocol]]` para el orden de emisión de archivos.

## Auto-corrección en brownfield

En brownfield, la auto-corrección aplica EXCLUSIVAMENTE a tests recién generados/modificados por el agente. NUNCA aplicar correcciones automáticas a tests preexistentes del cliente, aunque fallen. Si tests preexistentes fallan: reportar al humano, NO modificar (puede esconder bugs, romper convenciones del cliente, o violar el contrato implícito de no-modificación).

Esta regla aplica a las cuatro capacidades del loop final obligatorio (`[[calidad-test-execution-orchestration]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-test-self-correction-loop]]`, `[[calidad-test-self-healing]]`) y a sus invocaciones desde cualquier workflow brownfield del chapter (`[[calidad-extend-karate-brownfield]]`, `[[calidad-update-playwright-brownfield]]`, `[[calidad-extend-k6-brownfield]]`, `[[calidad-extend-appium-brownfield]]`). El alcance de la auto-corrección se delimita por el conjunto de archivos producidos o modificados en la corrida actual; cualquier fallo fuera de ese conjunto se reporta y escala, no se repara.

## Migración masiva de un patrón repetido

Caso distinto del anterior: no se agregan tests, se **reemplaza un patrón defectuoso repetido decenas de veces** en tests preexistentes —un bloque de login copiado en 35 lugares, una espera mal calibrada, un helper que debió existir desde el principio. Es una de las pocas intervenciones legítimas sobre código preexistente, y solo bajo autorización explícita del usuario sobre el alcance, porque toca archivos que la regla anterior protege.

La disciplina que la hace segura:

1. **Inventariar y clasificar antes de tocar nada.** Cuántas ocurrencias hay y en cuántas formas distintas. Un inventario real: 35 bloques, de los cuales 14 no contemplaban un desenlace, 14 lo hacían en línea con una espera mal calibrada, 3 usaban un objeto de página y 4 no encajaban en ningún patrón. Ese último grupo es el que decide si la migración es viable.
2. **Whitelist de lo migrable, no blacklist de lo prohibido.** Se enumera exactamente qué puede haber entre el punto de entrada y el de salida del bloque para considerarlo equivalente. Todo lo que no esté en la lista **no se migra**: queda para revisión manual. Una blacklist deja pasar lo que nadie previó.
3. **Las exclusiones deliberadas se declaran y se justifican una por una.** El caso que siempre aparece: **el test que valida precisamente el comportamiento que el helper automatiza**. Migrarlo lo destruye — pasaría a aceptar automáticamente lo que su razón de ser es verificar. Igual el que ejerce a propósito el camino contrario. Detectarlos exige leer, no filtrar por patrón.
4. **Antes de atribuirse un fallo, establecer la línea base.** Si un escenario falla después de la migración, correrlo contra el código original (`git stash`) y comparar el error. Idéntico significa preexistente, y se reporta como tal sin tocarlo; distinto significa que lo produjo la migración. Sin esta comprobación, cada rojo preexistente se convierte en tiempo perdido persiguiendo un cambio propio.
5. **Declarar qué quedó verificado en ejecución y qué no.** Migrar 27 archivos y verificar uno end-to-end es un resultado legítimo; presentarlo como si los 27 estuvieran verificados no lo es. Lo demás está cubierto por typecheck y por la homogeneidad del patrón, y así se dice.

El cierre exige, además de la suite verde: verificación estática limpia, tests unitarios del helper nuevo, y el conteo de bloques migrados contra bloques inventariados. Si no cuadra, falta explicar la diferencia.

## Resolver conflictos al integrar la rama larga

Una rama de automatización que vivió varios días choca con la principal, y el conflicto casi siempre cae en los mismos dos sitios: **archivos de datos de prueba** (dos equipos agregaron claves distintas) y **archivos de steps** (dos personas resolvieron el mismo flujo de formas distintas).

**Las opciones de un clic pierden trabajo.** "Tomar el origen" y "conservar el destino" descartan en bloque el aporte del otro lado. En un caso medido, la rama principal traía tres claves de datos que la rama no tenía; aceptar la rama entera las habría borrado sin que nadie lo notara hasta que un escenario ajeno fallara semanas después.

El procedimiento que no pierde nada:

1. **Simular el merge en memoria**, sin tocar el árbol de trabajo ni dejar el repositorio a medias:

```bash
git merge-tree --write-tree --name-only origin/main HEAD
```

2. **Clasificar cada conflicto.** Los de datos suelen ser unión limpia, sin decisión real. Los de código exigen decidir, y pegar las dos versiones **no es una opción**: dos definiciones del mismo step producen `ambiguous`, que es peor que cualquiera de las dos.

3. **Medir qué sobrevive antes de elegir**, contando definiciones y usos de cada símbolo en disputa:

```
helperA:  definiciones=1  usos=3
helperB:  definiciones=1  usos=5   (4 fuera del bloque en conflicto)
```

Un símbolo con usos fuera del bloque no se puede eliminar aunque su versión pierda. Ese conteo convierte la decisión en un dato.

4. **La decisión de negocio es del usuario, no del agente.** Se presentan las opciones con sus consecuencias y se espera. Resolver por cuenta propia un conflicto entre dos implementaciones equivale a elegir por otro equipo.

5. **Conservar el aporte que pierde, si es rescatable.** Cuando una versión gana, lo valioso de la otra puede sobrevivir en el mismo helper —por ejemplo, como último recurso de una cadena de localizadores— con un comentario que diga de dónde vino y por qué. Es preferible a duplicar la lógica en cada escenario.

6. **Medir el antes y el después.** El merge no debe empeorar el estado de la suite, y eso se comprueba con números, no con impresión:

| | escenarios | ambiguos |
|---|---|---|
| rama antes del merge | 619 | 32 |
| principal actual | 632 | **37** |
| resultado del merge | 636 | **37** |

Los cinco ambiguos nuevos vienen de la principal, no del merge. Sin esta tabla, el equipo los atribuye a la integración y se pierde una tarde.

7. **Verificar en ejecución al menos un escenario del archivo resuelto**, además de uno de control ajeno al conflicto.

## Paridad de garantías universales brownfield ↔ greenfield

Tras este chapter, todos los workflows brownfield reciben las mismas garantías universales que greenfield: smoke gate (universal), evidencia de bloqueo de ambiente, metadata por corrida, reporte ejecutivo, step isolation, validación contractual no superficial y STRATEGY.md condicional cuando el alcance es grande. La diferencia es de **scope de aplicación**: en brownfield estas mejoras se aplican **solo a archivos NUEVOS emitidos en la sesión**, nunca a tests preexistentes. Concretamente:

- **Smoke gate**: en brownfield ejecuta **un único escenario nuevo** (el más end-to-end), filtrado por el tag de la historia de la corrida o por el path del archivo emitido, con el conteo verificado antes de correr. **No inventar tags que el proyecto no usa** (`@new` no existe en el proyecto del cliente): las convenciones detectadas mandan. Los preexistentes no se ejecutan en el gate.
- **Traza del pipeline**: `.evidence/pipeline-state.json` (`[[calidad-pipeline-state-tracking]]`) aplica igual que en greenfield — se lee al abrir cada sesión y el delivery gate no se emite con fases pendientes. En brownfield importa más: las sesiones son largas sobre proyectos grandes.
- **Cadencia de corrección**: gate de un escenario → inventario de los nuevos → **corrección aislada test por test** → regresión de los nuevos (`[[calidad-test-self-correction-loop]]`). La suite preexistente nunca entra al ciclo.
- **Step isolation y validación contractual**: aplican solo a archivos nuevos. Los preexistentes mantienen su estructura aunque no cumplan los patrones.
- **Auto-corrección**: solo sobre archivos emitidos en la sesión; preexistentes son intocables.
- **Reporte ejecutivo**: debe segregar explícitamente "nuevos (en scope de esta sesión)" de "preexistentes (referencia)".
- **STRATEGY.md**: documenta lo NUEVO, no rediseña lo existente.

## Brownfield contra un SUT que aún no existe (shift-left)

Caso real y frecuente: el cliente tiene una suite viva y quiere agregar pruebas de un servicio o pantalla **que todavía no está desplegada**. Brownfield y shift-left no son excluyentes — el `[[calidad-sut-readiness-gate]]` se resuelve igual (paso 1.5 del router) y aplica **solo a los tests nuevos**:

| Capacidad | En brownfield |
|---|---|
| **Mock de servicios** (`[[calidad-service-virtualization-mockoon]]`) | **Sí**. El data file vive junto al proyecto (`mocks/mockoon/`) y los tests nuevos apuntan al mock **por configuración**, usando el mecanismo que el proyecto YA tenga para cambiar de ambiente (env, profile, config existente). Prohibido introducir un mecanismo nuevo de configuración ni reapuntar los tests preexistentes. |
| **Datos sintéticos** | Sí, con los builders/factories del proyecto si existen; no se introduce una segunda estrategia de datos. |
| **Locator map** (`[[calidad-ui-locator-map-contract]]`) | Sí para pantallas nuevas, **respetando la convención de identificadores del proyecto** (si el proyecto localiza por label, el mapa se expresa en labels). |
| **Prototipo de front/app** | **Normalmente NO**. Si la app ya existe y solo falta una pantalla, se difiere la ejecución de esos escenarios; un prototipo paralelo a una app real produce dos fuentes de verdad. Solo si el usuario lo pide explícitamente y se declara el riesgo. |

Cierre: la corrida cierra con `execution_target: mock` y `certification: pending_real_integration` **para los tests nuevos**, sin alterar el estado de certificación de la suite preexistente.
