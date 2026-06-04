# Coherence checks (Playwright)

Toda artefacto generado debe estar acoplado al grafo de tests. Archivos huérfanos (fixtures, data, mocks que no importa nadie) son ruido: inflan el repo, mienten sobre la cobertura, y degradan el code review.

## Regla obligatoria

**Cada fixture, mock o data file generado por el agente debe ser importado por al menos un `.spec.ts`.** Si al cierre de la generación un artefacto no tiene importadores, hay dos resoluciones válidas:

1. Refactorizar uno o más tests para consumir el artefacto (preferido cuando el artefacto representa un caso real).
2. Eliminar el artefacto huérfano antes de la entrega.

Nunca entregar artefactos huérfanos justificando "es para uso futuro".

## Verificación post-emisión

Ejecutar al final del workflow `[[generate-playwright-greenfield]]`, antes del delivery gate:

```bash
# Cada path bajo fixtures/ debe ser importado por ≥1 archivo bajo tests/.
grep -r --include="*.ts" "from.*fixtures/" tests/ | wc -l       # esperado > 0
grep -r --include="*.ts" "from.*data/" tests/     | wc -l       # esperado > 0
grep -r --include="*.ts" "from.*mocks/" tests/    | wc -l       # esperado > 0 si mock_mode != off

# Detectar huérfanos: archivos en fixtures/ que nadie importa.
for f in fixtures/*.ts; do
  base=$(basename "$f" .ts)
  imports=$(grep -r --include="*.ts" "from .*fixtures/${base}" tests/ pages/ | wc -l)
  if [ "$imports" -eq 0 ]; then
    echo "ORPHAN: $f"
  fi
done
```

Cualquier línea `ORPHAN:` invalida la entrega para ese archivo. Resolver según las dos vías de arriba.

## Patrón data-driven obligatorio

Los datos de búsqueda, payloads de formulario, IDs sintéticos, expectativas de tabla, etc., **se importan desde `data/` o `utils/`**. Está prohibido hardcodear strings de datos directamente en los `.spec.ts`.

### Antes (prohibido)

```typescript
test('buscar producto por nombre', async ({ catalogPage }) => {
  await catalogPage.search('Coca-Cola 350ml');
  await catalogPage.expectResultIncludes('Coca-Cola 350ml');
});
```

### Después (correcto)

```typescript
import { test, expect } from '@fixtures/base.fixture';
import { searchTerms } from '@data/catalog.data';

for (const term of searchTerms) {
  test(`buscar producto por nombre - ${term.query}`,
    { tag: ['@regression', '@HU-CAT-01'] },
    async ({ catalogPage }) => {
      await catalogPage.search(term.query);
      await catalogPage.expectResultIncludes(term.expected);
    }
  );
}
```

`data/catalog.data.ts` contiene la lista; los tests recorren por `for...of`. Añadir un nuevo caso es agregar una fila, no escribir un nuevo test.

## Por qué importa

- Romper el grafo (importadores vs artefactos) hace que el agente acumule deuda silenciosa generación tras generación.
- Hardcodear strings en specs niega el valor del patrón data-driven y bloquea el reuso.
- El delivery gate (ver `[[calidad-delivery-gate-contract]]`) consume este check como una de sus señales de coherencia.

## Cross-links

- Modo de ejecución y proyectos: `[[playwright-greenfield/references/execution-modes-live-mocked-hybrid.md]]`.
- Cobertura por HU: `[[playwright-greenfield/references/coverage-formula.md]]`.
- Tags nativos v1.42+: `[[playwright-greenfield/references/playwright-native-tags-v142.md]]`.
- Auditoría general post-emisión: `[[calidad-post-generation-protocol]]`.
