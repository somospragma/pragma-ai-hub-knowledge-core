# Fórmula de cobertura mínima (Playwright)

Análoga a la fórmula de Karate (ver `[[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)`), pero adaptada a UI E2E. La cobertura mínima por historia de usuario (HU) NO es un round number; se calcula y se declara antes de generar.

## Fórmula

```
effective_minimum = happy_paths(2-3)
                  + boundary(2)
                  + negative(2: missing-field, invalid-type)
                  + edge(1)
                  ≈ 8 tests mínimos por HU
```

| Componente      | Mínimo | Propósito                                                                        |
|-----------------|--------|----------------------------------------------------------------------------------|
| `happy_paths`   | 2-3    | Flujo principal end-to-end con datos válidos; variantes por dispositivo o rol.   |
| `boundary`      | 2      | Límites de input (max length, min length, fechas extremas, cantidades en borde). |
| `negative`      | 2      | Al menos `missing-field` y `invalid-type` para los inputs requeridos del flujo.  |
| `edge`          | 1      | Un caso específico de la HU (sesión expirada, doble click, navegación atrás).    |
| **TOTAL min**   | **8**  |                                                                                  |

## Modulación por riesgo

Para HUs `CRITICAL` o `HIGH` (según `priority_assignments` provistas por el PO; ver `[[playwright-greenfield/SKILL.md#asignación-de-prioridad-business-driven]]`), añadir:

- `visual_regression`: 1 test por página priorizada (Chromium-only).
- `accessibility`: 1 test por página priorizada (WCAG 2.0 A + AA con `@axe-core/playwright`).
- `security` (opcional, recomendado en CRITICAL): la suite de ``references/templates.md` (sección `xss-prevention.spec.ts`)`.

Para HUs `MEDIUM` o `LOW`, los 8 mínimos siguen siendo el piso. No bajar de 8 incluso en `LOW`.

## Declaración previa

Antes de generar la suite, el agente debe escribir en `.evidence/coverage-declared.json` (raíz del proyecto Playwright):

```json
{
  "version": 1,
  "generated_at": "ISO-8601",
  "hus": [
    {
      "id": "HU-01",
      "risk": "HIGH",
      "effective_minimum": 8,
      "breakdown": {
        "happy_paths": 2,
        "boundary": 2,
        "negative": 2,
        "edge": 1,
        "visual_regression": 1,
        "accessibility": 1
      },
      "spec_file": "tests/HU-01.spec.ts"
    }
  ]
}
```

Esta declaración alimenta `[[calidad-delivery-gate-contract]]` (`delivery_gate.coverage.declared`).

## Verificación

Tras generar `tests/HU-XX.spec.ts`, el conteo real de tests debe ser `>= effective_minimum`:

```bash
# Conteo simple: número de invocaciones a test( en el archivo.
grep -c "^\s*test(" tests/HU-01.spec.ts
# Debe ser >= effective_minimum declarado para HU-01.
```

Si el conteo real es menor, regenerar el archivo añadiendo los tests faltantes. No bajar el `effective_minimum` declarado para hacerlo "calzar".

## Anti-cheating

- No declarar `effective_minimum < 8` argumentando "HU simple".
- No contar `test.skip` ni `test.fixme` como parte del cumplimiento.
- No agrupar varias aserciones de casos distintos en un solo `test()` para inflar la sensación de cobertura por número de `expect()`.

## Cross-links

- Fórmula homóloga API: `[[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)`.
- Comentario de cobertura por archivo (equivalente en Karate): `[[calidad-karate-greenfield]] (consultar `references/cobertura-comment-enforcement.md` en su subfolder)`.
- Tags nativos v1.42+ obligatorios por HU: ``playwright-native-tags-v142.md``.
- Coherencia de artefactos: ``coherence-checks.md``.
- Gate de entrega: `[[calidad-delivery-gate-contract]]`.
