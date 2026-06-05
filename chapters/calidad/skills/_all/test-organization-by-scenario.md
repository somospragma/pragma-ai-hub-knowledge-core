# Test Organization by Scenario — Cuándo carpetas, cuándo flat

## Principio

Organizar tests por carpetas (una por HU/escenario/recurso) **cuando hay ≥3 HUs o escenarios distintos**. Para proyectos chicos (<3 HUs), mantener estructura flat. La regla equilibra trazabilidad (más fácil saber qué prueba cada test) contra overhead de navegación (carpetas vacías o casi vacías molestan).

## Tabla por stack

| Stack | Estructura ≥3 HUs | Estructura <3 HUs |
|---|---|---|
| Karate | `features/{resource}/{HU}.feature` | `features/{resource}.feature` (flat) |
| Playwright | `tests/{HU}/{flow}.spec.ts` | `tests/{flow}.spec.ts` (flat) |
| K6 | `tests/{scenario}/main.js` (ya canónico en K3 por escenario de performance) | mismo (K6 siempre usa carpetas porque cada escenario es distinto) |
| Appium | `features/{capability}/{HU}.feature` | `features/{HU}.feature` (flat) |

## Reglas

- **Umbral 3**: la regla numérica `<3 = flat / ≥3 = carpetas` evita debates. Si dudas, usar carpetas (favorece trazabilidad).
- **Una HU, una carpeta**: cuando se usa estructura jerárquica, el primer nivel agrupa por HU/feature/capability del negocio, NO por capa técnica.
- **Sin carpetas espurias**: una carpeta con un solo archivo se debe colapsar (mover el archivo al padre y borrar la carpeta).
- **K6 es excepción**: siempre usa `tests/{scenario}/main.js` porque cada escenario (`linea-base`, `carga`, `estres`, opcional `spike`/`soak`) tiene config y workload distintos. Aplicar el umbral 3 no tiene sentido aquí.
- **Naming**: `kebab-case` para nombres de carpeta. El nombre coincide con el identificador de HU del backlog (ej. `HU-101-transactions`).

## Trade-off

- **A favor de carpetas (trazabilidad)**: navegación clara desde el backlog al test; fácil agregar mocks/data específicos por HU; reportes naturalmente agrupados por HU; menos colisiones de nombres.
- **A favor de flat (overhead)**: menos clicks para abrir un archivo; estructura más simple para juniors; menos boilerplate cuando hay sólo 1-2 HUs.

La regla del 3 es un compromiso pragmático: el costo de carpetas se justifica cuando el inventario es mediano o grande.

## Cuándo migrar de flat a carpetas

Cuando una HU adicional llevaría el conteo a 3, refactorizar:

1. Crear carpetas por HU existentes.
2. Mover los archivos al subdirectorio correspondiente.
3. Ajustar imports / paths en runners y configs.
4. Verificar que `effective_minimum` no cambia (el conteo de tests es el mismo, sólo cambia la organización).

## Cross-links

`[results-structure-universal](./results-structure-universal.md)`, `[[karate-greenfield]]`, `[[playwright-greenfield]]`, `[[k6-greenfield]]`, `[[appium-screenplay-android]]`.
