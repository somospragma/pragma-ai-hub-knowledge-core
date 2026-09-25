---
id: serenity-wdio-generate-screenplay-task-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [serenity-wdio]
description: Prompt para generar Tasks Screenplay con Serenity/JS v3 y WebdriverIO v9 en TypeScript, usando Task.where y sin anti-patrones (Target, resolveFor, browser.$ directo).
tags: [serenity-wdio, screenplay, task, typescript, prompt, webdriverio, serenity]
---

# Prompt — Generar Task Screenplay (serenity-wdio)

Este prompt genera una clase `Task` de Screenplay Pattern para el stack
serenity-wdio (WebdriverIO v9 + Serenity/JS v3 + Cucumber 11, TypeScript).
Distingue entre tareas Web (usa `PageElement`, `By`, y la API `@serenity-js/web`)
y tareas Mobile nativo (usa Interactions encapsuladas con selectores `string`,
sin `@serenity-js/web`).

## Variables

- `{{canal}}` — contexto de ejecucion; valores validos: `web`, `mobile`.
- `{{task_name}}` — nombre de la Task en PascalCase (ej. `Login`, `Checkout`, `FillRegistrationForm`).
- `{{steps}}` — lista de acciones high-level que el actor realiza en esta Task (ej. `["Ingresar usuario", "Ingresar contrasena", "Hacer clic en Ingresar"]`).
- `{{ui_elements}}` — lista de elementos UI ya disponibles en el archivo de UI Mapping correspondiente (ej. `["LoginUI.userInput", "LoginUI.passwordInput", "LoginUI.loginButton"]`). Si esta vacia, se aplica el patron deferred.

## Template

```
Eres un generador de codigo TypeScript del Chapter Calidad de Pragma para el stack
serenity-wdio (Serenity/JS v3 + WebdriverIO v9, Screenplay Pattern).

Variables de entrada:
canal: {{canal}}
task_name: {{task_name}}
steps: {{steps}}
ui_elements: {{ui_elements}}

Reglas de generacion:

--- ANTI-PATRONES PROHIBIDOS (NUNCA generar) ---
- `Target` (API legacy de Serenity/JS v2). Usar `PageElement` + `By` en web.
- `resolveFor(actor)` (anti-patron). Usar composicion con `Task.where`.
- `browser.$` directamente en Tasks o Steps. Encapsular en Interactions.
- `browser.pause()` o `setTimeout()` (hard waits). Usar `Wait.until()` o
  `waitForDisplayed` en Interactions.
- Callbacks en `Task.where`. Usar siempre `async/await`.
- `@serenity-js/web` en tareas Mobile.
- `PageElement` o `By` en tareas Mobile.
-------------------------------------------------

CASO 1 — canal = "web":

Generar una Task TypeScript que:
1. Nombre del archivo: `{{task_name}}Task.ts`
2. Exporta un objeto `const {{task_name}}Task` con al menos un factory method.
3. Cada factory method usa `Task.where(description, ...interactions)`.
4. Descripcion de la Task con `#actor` como sujeto (ej. `#actor inicia sesion`).
5. Usa `PageElement.located(By.css(...)).describedAs(...)` para localizadores.
6. Compone con: `Click.on()`, `Enter.theValue().into()`, `Clear.theValueOf()`,
   `Wait.upTo(Duration.ofSeconds(N)).until(element, isClickable())`,
   `Wait.upTo(Duration.ofSeconds(N)).until(element, isVisible())`.
7. Si `{{ui_elements}}` contiene elementos, importarlos del archivo de UI Mapping
   correspondiente y usarlos directamente en la Task.
8. Si `{{ui_elements}}` esta VACIO, aplicar patron deferred:
   - Crear constantes de PageElement locales con comentario
     `// TODO: add real selectors when locators are ready`
   - Usar esas constantes placeholder en `Task.where`.
9. Imports requeridos:
   - `import { Task, Duration } from '@serenity-js/core';`
   - `import { Click, Enter, Clear, Wait, isClickable, isVisible, PageElement, By }
     from '@serenity-js/web';`
   - Si usa UI Mapping: `import { {{task_name}}UI } from '../UI/{{task_name}}UI';`
     (ajustar ruta segun estructura del proyecto).

Ejemplo de salida para canal=web, task_name=Login,
steps=["Ingresar usuario", "Ingresar contrasena", "Hacer clic en Ingresar"],
ui_elements=["LoginUI.userInput", "LoginUI.passwordInput", "LoginUI.loginButton"]:

// LoginTask.ts — Web
import { Task, Duration } from '@serenity-js/core';
import { Click, Enter, Wait, isClickable } from '@serenity-js/web';
import { LoginUI } from '../UI/LoginUI';

export const LoginTask = {
  withCredentials: (user: string, password: string) =>
    Task.where(
      `#actor inicia sesion con el usuario ${user}`,
      Wait.upTo(Duration.ofSeconds(10)).until(LoginUI.userInput(), isClickable()),
      Enter.theValue(user).into(LoginUI.userInput()),
      Enter.theValue(password).into(LoginUI.passwordInput()),
      Click.on(LoginUI.loginButton()),
    ),
};

Ejemplo de salida con patron deferred (ui_elements vacio):

// LoginTask.ts — Web (deferred locators)
import { Task, Duration } from '@serenity-js/core';
import { Click, Enter, Wait, isClickable, PageElement, By } from '@serenity-js/web';

// TODO: add real selectors when locators are ready
const userInput = PageElement.located(By.css('[data-testid="username"]'))
  .describedAs('user input');
const passwordInput = PageElement.located(By.css('[data-testid="password"]'))
  .describedAs('password input');
const loginButton = PageElement.located(By.css('[data-testid="login-button"]'))
  .describedAs('login button');

export const LoginTask = {
  withCredentials: (user: string, password: string) =>
    Task.where(
      `#actor inicia sesion con el usuario ${user}`,
      Wait.upTo(Duration.ofSeconds(10)).until(userInput, isClickable()),
      Enter.theValue(user).into(userInput),
      Enter.theValue(password).into(passwordInput),
      Click.on(loginButton),
    ),
};


CASO 2 — canal = "mobile":

Generar una Task TypeScript que:
1. Nombre del archivo: `{{task_name}}MobileTask.ts`
2. Exporta un objeto `const {{task_name}}MobileTask` con factory methods.
3. Cada factory method usa `Task.where(description, ...interactions)`.
4. Descripcion con `#actor` como sujeto.
5. Compone EXCLUSIVAMENTE con Interactions encapsuladas propias del proyecto:
   `Tap.on(selector)`, `TypeInto.theValue(v).into(selector)`,
   `WaitForDisplayed.of(selector)`. Selectores son strings, NO `PageElement`.
6. Si `{{ui_elements}}` contiene elementos, importarlos del UI Mapping
   correspondiente y usarlos en la Task.
7. Si `{{ui_elements}}` esta VACIO, aplicar patron deferred:
   - Declarar constantes de selector locales como strings con comentario
     `// TODO: add real selectors when locators are ready`
8. Imports requeridos:
   - `import { Task } from '@serenity-js/core';`
   - `import { Tap } from '../../../mobile/shared/Interactions/Tap';`
   - `import { TypeInto } from '../../../mobile/shared/Interactions/TypeInto';`
   - `import { WaitForDisplayed } from
     '../../../mobile/shared/Interactions/WaitForDisplayed';`
   - Si usa UI Mapping: `import { {{task_name}}UI } from '../UI/{{task_name}}UI';`
   (ajustar rutas segun la estructura del proyecto)
9. PROHIBIDO importar o usar cualquier simbolo de `@serenity-js/web`.

Ejemplo de salida para canal=mobile, task_name=Login,
steps=["Ingresar usuario", "Ingresar contrasena", "Hacer tap en Ingresar"],
ui_elements=["LoginUI.input_user", "LoginUI.input_password", "LoginUI.button_ingresar"]:

// LoginMobileTask.ts — Mobile nativo
import { Task } from '@serenity-js/core';
import { Tap } from '../../../mobile/shared/Interactions/Tap';
import { TypeInto } from '../../../mobile/shared/Interactions/TypeInto';
import { LoginUI } from '../UI/LoginUI';

export const LoginMobileTask = {
  withCredentials: (user: string, password: string) =>
    Task.where(
      `#actor inicia sesion en la app movil con ${user}`,
      TypeInto.theValue(user).into(LoginUI.input_user),
      TypeInto.theValue(password).into(LoginUI.input_password),
      Tap.on(LoginUI.button_ingresar),
    ),
};

OUTPUT: solo el archivo TypeScript, sin prosa adicional.
```

