
# Matriz de trazabilidad de requisitos (RTM)

La columna vertebral del proceso: demuestra que cada requisito tiene pruebas, cada prueba tiene razón de ser, y cada defecto tiene origen. Sin RTM, "probamos todo" es una opinión.

## La cadena

```
Épica/Feature → HU → CA → Caso de alto nivel → Test automatizado/manual → Ejecución → Defecto
```

Cada eslabón referencia al anterior. El chapter la implementa así:

| Eslabón | Mecanismo |
|---|---|
| HU → CA | Los CA viven en la HU (ALM o markdown) |
| CA → caso | Campo Trazabilidad del caso ([[calidad-funcional-test-design]], `references/test-case-format.md`) + matriz CA↔casos del entregable de diseño |
| Caso → test automatizado | Tag `@user-story:HU-123` en el código de los stacks ([[calidad-test-evidence-and-traceability]]) |
| Test → ejecución | Resultados y evidencia de los stacks (`results/`, delivery gate) o test runs del ALM |
| Ejecución → defecto | Defecto en ALM linkeado al caso y a la HU |

## Materialización

**Con ALM (preferida)** — la RTM son los links nativos, no un excel paralelo:
- Azure DevOps: HU —(Tests)— Test Case —(Test Runs)— resultados; defectos linkeados con "Bug". Queries de cobertura por Area/Iteration Path.
- Jira: issue links `tests`/`is tested by` (con Xray/Zephyr: requirement coverage nativo).
- La construye y mantiene [[calidad-alm-mcp-integration]] al crear/vincular casos y publicar resultados. El plan referencia las queries/vistas, no duplica la matriz a mano.

**Sin ALM** — archivo `rtm/{proyecto}-rtm.md` versionado:

```markdown
| HU | CA | Caso | Automatizado | Última ejecución | Estado | Defectos |
|---|---|---|---|---|---|---|
| HU-123 | CA-1 | TC-123-01 | karate @user-story:HU-123 | 2026-07-30 | pass | - |
| HU-123 | CA-2 | TC-123-03 | manual | 2026-07-29 | fail | BUG-88 |
```

## Verificaciones de salud de la RTM (se corren en cada informe de avance)

1. **CA sin caso** → hueco de diseño; vuelve a [[calidad-funcional-test-design]].
2. **Caso sin CA/regla** → alcance inventado; se elimina o se formaliza su regla.
3. **Caso sin ejecución** al corte → listado con motivo (pendiente/bloqueado/descartado).
4. **Defecto sin caso** → hueco de diseño descubierto en campo: se crea el caso que lo habría detectado (alimenta regresión).
5. **HU cerrada con casos en fail** → inconsistencia de proceso; se escala, no se archiva.

## Reglas

- La RTM se actualiza con el flujo (al diseñar, al ejecutar), no "al final para la entrega" — reconstruirla retroactivamente produce ficción.
- Cobertura se reporta en dos números que no se mezclan: **cobertura de diseño** (CA con caso) y **cobertura de ejecución** (CA con ejecución pass).
