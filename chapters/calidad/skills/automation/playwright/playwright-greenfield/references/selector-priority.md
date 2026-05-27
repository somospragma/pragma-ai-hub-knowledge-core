
# Prioridad de selectores

## Orden (mejor → peor)

| Prioridad | API                              | Cuándo usar                                     | Ejemplo                                                          |
|-----------|----------------------------------|-------------------------------------------------|------------------------------------------------------------------|
| 1         | `page.getByTestId('id')`         | Solo si el HTML ya expone `data-testid`         | `page.getByTestId('users-table')`                                |
| 2         | `page.getByRole(role, options)`  | Default semántico para botones, links, headings | `page.getByRole('button', { name: 'Submit' })`                   |
| 3         | `page.getByLabel(text)`          | Inputs de formulario asociados a un `<label>`   | `page.getByLabel('Email')`                                       |
| 4         | `page.getByPlaceholder(text)`    | Inputs sin label visible                        | `page.getByPlaceholder('Search users')`                          |
| 5         | `page.getByText(text)`           | Texto visible no asociado a un rol claro        | `page.getByText('No results found')`                             |
| 6         | `page.locator(cssSelector)`      | Fallback CSS solo cuando lo anterior no aplica  | `page.locator('[name="fieldName"]')`                             |

## Reglas

- Nunca uses XPath salvo último recurso absoluto.
- No uses selectores por clase CSS visual (`.btn-primary`, `.mt-4`): se rompen al cambiar el tema.
- Para listas y filas, combina `getByRole('row', { name: /regex/ })` con búsquedas anidadas.
- Si tienes que recurrir a `locator(CSS)`, prefiere atributos estables (`[name="..."]`, `[type="..."]`) sobre clases visuales.

## Snippet

```typescript
// 1 — testid (si el HTML lo expone)
await page.getByTestId('login-form').isVisible();

// 2 — role
await page.getByRole('button', { name: 'Sign in' }).click();

// 3 — label
await page.getByLabel('Email').fill('user@example.com');

// 4 — placeholder
await page.getByPlaceholder('Search users').fill('alice');

// 5 — text
await expect(page.getByText('No results found')).toBeVisible();

// 6 — CSS fallback
await page.locator('[name="csrfToken"]').waitFor({ state: 'attached' });
```
