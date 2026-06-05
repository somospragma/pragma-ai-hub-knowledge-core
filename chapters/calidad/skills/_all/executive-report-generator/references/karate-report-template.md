# Plantilla específica de Karate para el reporte ejecutivo

Esta plantilla guía las secciones del reporte ejecutivo cuando `framework = karate`. Complementa `report-structure.md` con el detalle propio del stack. Se invoca desde el Paso 6 del `SKILL.md`.

## Fuentes primarias

- `target/karate-reports/karate-summary.json` (o el path equivalente bajo `results/karate/<timestamp>/`).
- JUnit XML por feature en `target/karate-reports/*.xml`.
- `metadata.json` de la corrida (timestamp, commit, branch, environment, comando exacto).

## Sección 2 — Cumplimiento de SLAs (vista Karate)

Karate no produce SLAs de performance, pero sí cumplimiento de cobertura por endpoint y DoD por feature. Mapear los siguientes "SLAs funcionales" desde `STRATEGY.md`:

- Cobertura mínima por endpoint: `effective_minimum` declarado vs delivered (cantidad de escenarios efectivamente emitidos y ejecutados).
- Contract testing: todos los endpoints con su `-match.json` ejecutado.
- DoD por feature: los 14 ítems del checklist deben pasar.

## Sección 3 — Resultados por escenario / HU (vista Karate)

Agrupar por feature y luego por endpoint. Una fila por feature:

| Feature | Endpoint | Effective minimum declarado | Delivered | Pasados | Fallidos | % éxito | DoD |
|---|---|---|---|---|---|---|---|
| pet/addPet.feature | POST /pet | 10 | 10 | 9 | 1 | 90% | parcial |
| pet/findPetsByStatus.feature | GET /pet/findByStatus | 8 | 8 | 8 | 0 | 100% | OK |

Columna `DoD` resume si los 14 ítems del checklist de finalización del workflow pasan para ese feature.

### Sub-tabla: cobertura declarada vs delivered

Si `coverage.declared` y `coverage.delivered` del `delivery_gate.coverage` difieren, listar la diferencia:

| Endpoint | Declarado | Delivered | Diferencia |
|---|---|---|---|
| addPet | 10 | 10 | 0 |
| findPetsByStatus | 8 | 8 | 0 |
| getPetById | 6 | 5 | -1 |

Una diferencia negativa eleva el badge global a amarillo como mínimo.

## Sección 4 — Comparación entre corridas (vista Karate)

Por feature, comparar última vs penúltima corrida bajo `results/karate/`:

| Feature | Corrida anterior (pasados/totales) | Corrida actual (pasados/totales) | Delta | Recuperados | Regresiones |
|---|---|---|---|---|---|
| pet/addPet.feature | 8/10 | 9/10 | +1 | scenario_5 | (ninguna) |
| pet/findPetsByStatus.feature | 8/8 | 8/8 | 0 | (ninguno) | (ninguna) |

## Sección 7 — Anexos específicos Karate

- Comando exacto ejecutado (`mvn test -f pom.xml [tag filter]`).
- Path al reporte HTML nativo de Karate: `target/karate-reports/karate-summary.html`.
- Tag filters aplicados (`@regression`, `@user-story:HUT-XXX`, etc.).
- Versión de `karate-junit5` y `maven-surefire-plugin` declaradas en `pom.xml`.
- Listado de schemas `-match.json` usados, con path relativo.
