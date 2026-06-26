
# Detección de convenciones en proyectos K6 brownfield

Antes de extender un proyecto K6 hay que inferir su contrato implícito: dónde viven los tests, cómo se nombran los scripts y los `group()` / `check()`, cuál es el modo de autenticación, qué tier de thresholds está vigente, cómo se construyen los payloads y dónde se persiste la evidencia.

## Qué detectar

| Convención | Cómo se infiere |
|---|---|
| `tests_dir` | Carpeta que contiene los `*-test.js` existentes. Suele ser `tests/` pero algunos proyectos usan `perf/`, `k6/`, `scripts/`. |
| `script_naming` | Estilo del nombre de archivo: `snake_case` (`smoke_test.js`), `kebab-case` (`smoke-test.js`), `camelCase` (`smokeTest.js`). Anota el patrón exacto del primer script. |
| `groups_naming` | Idioma y prefijos en `group('...')` y `check(..., {'...': ...})`. Ejemplos: español (`'crear usuario'`), inglés (`'Create user'`), con prefijo (`'[POST] /users'`). |
| `auth_mode` actual | Revisar `config.js` (¿está definida `authToken`?) y `utils.js` (¿`getDefaultHeaders()` emite `Authorization`?). Cruzar con el spec si está disponible: si el spec NO declaraba security pero Authorization se emite, el modo es `external`. |
| `existing_thresholds` | Comparar los valores de `options.thresholds` contra los tres tiers de `[[calidad-k6-greenfield]] (consultar `references/thresholds-three-tiers.md` en su subfolder)` (Conservative / Moderate / Relaxed). Anota el tier dominante. |
| `existing_payload_builders` | Funciones `buildXxxBody()` ya presentes en `utils.js`. Anota el sufijo / prefijo exacto (algunos proyectos usan `make...Payload`, `create...Body`, etc.). |
| `existing_id_correlation_pattern` | Cómo el proyecto extrae el ID del response del POST y lo reusa en GET/PUT/DELETE. Patrón canónico en `[[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder)`. Anota variaciones (clave del id: `id`, `uuid`, `transactionId`). |
| `handle_summary_path` | Path destino dentro de `handleSummary()`: `results/${timestamp}-summary.json` (default) vs `reports/...` vs estructura por test. Anota también el formato del timestamp y si exporta solo JSON o además HTML/JUnit. |
| `import_style` | ¿Imports relativos (`./utils.js`) o alias? ¿Se importa `textSummary` desde jslib remoto o desde un vendor local (`./vendor/k6-summary.js`)? |
| `env_vars_in_use` | Variables consumidas vía `__ENV.*` en `config.js` y scripts. Anota nombres exactos (BASE_URL, AUTH_TOKEN, RAMP_USERS, etc.) para no introducir variantes nuevas. |

## Algoritmo mínimo

Para inferir el patrón sin leer todo el proyecto, basta con:

1. Leer `tests/config.js` completo. Extraer claves (`baseUrl`, `authToken`, enums, headers constantes) y env vars referenciadas.
2. Leer `tests/utils.js` completo. Detectar `auth_mode` (¿`Authorization` está en `getDefaultHeaders()` activo o comentado?), inventario de `buildXxxBody()`, presencia de helpers (`uuidv4`, generadores).
3. Leer al menos **un** `tests/*-test.js` (preferentemente `smoke-test.js` por ser el más simple). Extraer:
   - Naming de archivo (define `script_naming`).
   - Idioma y formato de `group()` / `check()` (define `groups_naming`).
   - Valores de `options.thresholds` (clasifica tier).
   - Patrón de extracción de IDs en flujos CRUD (define `existing_id_correlation_pattern`).
   - Cuerpo de `handleSummary()` (define `handle_summary_path` e `import_style` de `textSummary`).
4. Si hay flujos CRUD, leer un script adicional que los ejercite (típicamente `load-test.js`) para confirmar consistencia del patrón.

## Regla de prioridad

Si las convenciones detectadas chocan con las reglas del Chapter (p. ej. el proyecto hardcodea IDs y el Chapter prohíbe IDs hardcodeados en CRUD), **el Chapter gana** sólo cuando se trate de una restricción de calidad explícita (ver `[[calidad-k6-greenfield]]` restricciones). Para convenciones de estilo (naming, idioma, formato), el proyecto existente gana siempre. Si la pugna no está clara, pregunta al usuario antes de decidir.
