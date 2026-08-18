# Estrategia de actualización de selectores — serenity-wdio brownfield

## Regla central

Cuando la UI cambia (nuevo id, nuevo texto, reorganización de la jerarquía), se actualiza ÚNICAMENTE la asignación del selector dentro del UI Mapping. Todo lo demás permanece literal:

- Imports (`@serenity-js/web` para web; sin imports de PageElement en mobile).
- Nombre del elemento / constante y su descripción (`describedAs(...)`), a menos que el control haya cambiado de significado.
- Métodos auxiliares del UI Mapping, comentarios y orden de propiedades.
- **NO se tocan** Tasks, Questions ni Interactions que consumen ese UI Mapping. Si el contrato (nombre y tipo) se mantiene, los consumidores no requieren cambios.

## Web — patrón del arquetipo (PageElement + By)

```typescript
// features/web/UI/LoginUI.ts - antes
import { By, PageElement } from '@serenity-js/web';

export class LoginUI {
  static buttonLogin = () =>
    PageElement.located(By.xpath("//button[@id='btn-login']"))
               .describedAs('button for login');

  static userInput = () =>
    PageElement.located(By.xpath("//input[@id='input-username-login']"))
               .describedAs('input for user');
}
```

```typescript
// features/web/UI/LoginUI.ts - despues (la app renombro los ids)
import { By, PageElement } from '@serenity-js/web';

export class LoginUI {
  static buttonLogin = () =>
    PageElement.located(By.css("button#btnSignIn"))
               .describedAs('button for login');

  static userInput = () =>
    PageElement.located(By.css("input#inputUsername"))
               .describedAs('input for user');
}
```

Único cambio: el argumento de `By.xpath(...)` / `By.css(...)`. Imports, nombres, `describedAs` y orden permanecen idénticos. Las Tasks que invocan `LoginUI.buttonLogin()` no requieren cambios.

## Mobile — patrón del arquetipo (selectores string)

```typescript
// features/mobile/android/UI/LoginUI.ts - antes
export const LoginUI = {
  button_login: '~login-button',      // Accessibility ID (prioridad 1)
  input_user: '~username-input',
  input_password: '~password-input',
};
```

```typescript
// features/mobile/android/UI/LoginUI.ts - despues (nuevo accessibility id)
export const LoginUI = {
  button_login: '~btnLogin',
  input_user: '~username-input',
  input_password: '~password-input',
};
```

Solo cambia el string del selector. Las Interactions (`Tap.on(...)`, `Type.value(...).into(...)`) y las Tasks (`TapWhenVisible.on(...)`) no se tocan.

## Prioridad de selectores (arquetipo)

1. Accessibility ID (`~id`)
2. TestID (`~testId`)
3. Texto visible
4. CSS (web)
5. XPath (último recurso)

## Validación previa al cambio

- Confirmar que el nuevo selector existe en la nueva versión (Appium Inspector para mobile; DevTools para web).
- Preferir selectores estables; no migrar de `id`/`css` a `xpath` "porque es más corto".
- Si el control desaparece o cambia de tipo (button → link, input → dropdown), ya **no** es un selector update: escalar a `refactor` o `new-page`.

## Anti-patrones

- Renombrar la constante/método del UI Mapping durante un selector update: rompe todos los consumidores sin razón.
- Introducir `Target` (API v2) al actualizar un selector web: usar `PageElement.located(By...)`.
- Tocar Tasks o Questions en el mismo cambio que el selector update: si hay que tocarlos, escalar a `refactor`.
- Migrar la estrategia de selector si la nueva versión sigue exponiendo la original.
