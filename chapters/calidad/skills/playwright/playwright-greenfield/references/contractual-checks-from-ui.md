# Contractual checks from UI — Validación no superficial (Playwright)

## Principio

`await expect(locator).toBeVisible()` no es una validación contractual: confirma que el elemento existe en el DOM, pero no que el dato que el SUT debía pintar coincide con el contrato funcional. Un test que sólo verifica visibilidad pasa en verde aunque la API devuelva la lista vacía, aunque la paginación esté rota, o aunque el formato de un monto haya cambiado de `$1,234.56` a `1234.56` (regresión típica de localización).

**Regla obligatoria**: cada `.spec.ts` que valide datos del dominio debe expresar el contrato funcional con aserciones específicas — cantidad esperada, formato esperado, texto del dominio, navegación post-acción — además de la visibilidad estructural.

Aplica al workflow `[[calidad-generate-playwright-greenfield]]` paso 7 ("Planificar tests") y se audita como parte del DoD (`[[calidad-delivery-gate-contract]]`).

## Anti-pattern frecuente

```typescript
// MAL — pasa en verde aunque la API devuelva []
await expect(page.getByRole('region', { name: 'Transactions' })).toBeVisible();
```

El test no falla si:
- El endpoint responde `200 OK` con `[]`.
- La paginación está rota (sólo se ven los primeros 5 de 100 esperados).
- Los amounts vienen sin formato.
- El primer row corresponde a otro usuario por bug de tenancy.

## Patrón correcto

```typescript
// BIEN — codifica el contrato funcional
const rows = page.getByRole('row');
await expect(rows).toHaveCount(20);                                    // página típica
await expect(rows.first().getByText(/^\$[\d,]+\.\d{2}$/)).toBeVisible(); // formato monetario
await expect(page.getByText(/Página \d+ de \d+/)).toBeVisible();        // paginación viva
```

Cada aserción es independiente y declara una propiedad del contrato. El test ahora falla cuando:
- La cantidad de rows cambia (regresión de paginación o de filtro).
- El formato monetario se rompe.
- La paginación desaparece.

## Tabla — tipo de pantalla → checks contractuales mínimos

| Tipo de pantalla        | Checks contractuales mínimos                                                                                                  |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Listado paginado        | `toHaveCount(expected)`, paginación visible con texto `Página X de Y`, primer y último item con formato esperado del dominio.  |
| Detalle                 | Campos clave con valores del dominio (`toHaveText`, regex de formato), no sólo `toBeVisible`. Incluir IDs/labels del registro. |
| Formulario              | Mensaje de éxito específico (texto exacto del SUT) tras submit válido; mensajes de error específicos por campo en submit inválido. |
| CRUD completo           | Persistencia: refresh (`page.reload()`) + re-verificar que el dato creado/editado sigue presente; eliminar + verificar ausencia.  |
| Login                   | Redirect a la ruta post-login esperada (`expect(page).toHaveURL(/dashboard/)`) y user info visible (nombre, avatar, rol).      |
| Filtros                 | `toHaveCount` del resultado filtrado (no "al menos un row visible"); validar que filtros inválidos producen empty state explícito. |
| Tabla con ordenamiento  | Orden visible verificado leyendo el primer y último valor, no sólo "la columna existe".                                       |
| Modal / dialog          | Foco trapped en el modal; cierre por ESC y por botón; data del modal contiene los campos del registro abierto.                |
| Wizard / multi-step     | Estado del paso actual visible; navegación adelante/atrás preserva data previa.                                               |
| Empty state             | Mensaje exacto cuando el endpoint responde `[]`; CTA correcto (no "crear" cuando es read-only).                               |
| Error state             | Mensaje del backend renderizado tal cual; retry visible si aplica; el layout no colapsa.                                       |

## Ejemplos por tipo

### Listado paginado

```typescript
import { test, expect } from '@fixtures/base.fixture';

test('listado de transacciones — primera página con 20 items', async ({ transactionsPage }) => {
  await transactionsPage.goto();

  const rows = transactionsPage.page.getByRole('row');
  await expect(rows).toHaveCount(20);

  // Formato monetario en cada fila
  await expect(rows.first().getByText(/^\$[\d,]+\.\d{2}$/)).toBeVisible();

  // Paginación viva
  await expect(transactionsPage.page.getByText(/^Página 1 de \d+$/)).toBeVisible();
});
```

### Detalle

```typescript
test('detalle de cuenta — balance con formato y currency', async ({ accountPage }) => {
  await accountPage.goto('acc-123');

  await expect(accountPage.balanceField).toHaveText(/^\$[\d,]+\.\d{2}\sUSD$/);
  await expect(accountPage.accountIdField).toHaveText('acc-123');
  await expect(accountPage.statusBadge).toHaveText('ACTIVE');
});
```

### Formulario — error específico por campo

```typescript
test('crear usuario — error específico por email inválido', async ({ userFormPage }) => {
  await userFormPage.goto();
  await userFormPage.fillEmail('not-an-email');
  await userFormPage.submit();

  // No "toBeVisible" sobre el contenedor de errores genérico.
  await expect(userFormPage.emailError).toHaveText('Ingrese un correo válido');
});
```

### CRUD — persistencia tras refresh

```typescript
test('crear producto persiste tras refresh', async ({ productsPage }) => {
  await productsPage.goto();
  await productsPage.createProduct({ name: 'Widget-42', price: 19.99 });

  await expect(productsPage.row('Widget-42')).toBeVisible();

  await productsPage.page.reload();
  await expect(productsPage.row('Widget-42')).toBeVisible();
  await expect(productsPage.row('Widget-42').getByText('$19.99')).toBeVisible();
});
```

### Filtros — count exacto

```typescript
test('filtro por status ACTIVE devuelve sólo activos', async ({ usersPage }) => {
  await usersPage.goto();
  await usersPage.filterByStatus('ACTIVE');

  const rows = usersPage.page.getByRole('row');
  await expect(rows).toHaveCount(7); // según fixture/data declarado

  // Todos los rows visibles deben tener la badge ACTIVE
  const badges = rows.locator('[data-status]');
  for (let i = 0; i < await badges.count(); i++) {
    await expect(badges.nth(i)).toHaveText('ACTIVE');
  }
});
```

## Cuándo `toBeVisible` solo basta

`toBeVisible()` aislado es legítimo cuando se valida exclusivamente la **estructura** de la página (existencia del layout, presencia del header, del nav, del footer) y no datos del dominio. Esos chequeos son útiles para detectar regresiones de routing/layout, pero **no cuentan como cobertura contractual** para el DoD.

```typescript
// Aceptable: estructura, no contrato.
test('shell de la app está montado', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('navigation')).toBeVisible();
  await expect(page.getByRole('main')).toBeVisible();
});
```

## Audit post-emisión

Antes de cerrar la entrega, contar la proporción de aserciones `toBeVisible` aisladas vs aserciones específicas en `tests/`:

```bash
total_visible=$(grep -r --include="*.spec.ts" -E "expect\([^)]+\)\.toBeVisible\(\)" tests/ | wc -l)
total_specific=$(grep -r --include="*.spec.ts" -E "\.(toHaveText|toHaveCount|toHaveURL|toContainText|toHaveValue|toHaveAttribute)\(" tests/ | wc -l)
echo "ratio toBeVisible/específicas: $total_visible / $total_specific"
```

Si `total_visible > total_specific` y los tests validan datos del dominio, **la suite está sub-validando el contrato**: refactorizar antes de declarar `status: success`.

## Cross-links

- Coherencia y data-driven: ``coherence-checks.md``.
- Cobertura por HU: ``coverage-formula.md``.
- Modo de ejecución: ``execution-modes-live-mocked-hybrid.md``.
- Auditoría post-emisión: `[[calidad-post-generation-protocol]]`.
- Gate de entrega: `[[calidad-delivery-gate-contract]]`.
