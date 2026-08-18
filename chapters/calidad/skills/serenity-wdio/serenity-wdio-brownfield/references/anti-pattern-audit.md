# Auditoría de anti-patrones — serenity-wdio brownfield

## Regla central

Al extender un proyecto existente se escanea el código en busca de anti-patrones prohibidos y se **marca cada ocurrencia**, pero **no se aplican correcciones automáticas sobre código preexistente**. El objetivo es dar visibilidad al usuario, no reescribir su código sin permiso. El código **nuevo** que se genere sí debe estar libre de estos anti-patrones.

## Anti-patrones prohibidos

| Anti-patrón | Por qué está prohibido | Dónde buscar |
|---|---|---|
| `Target` | API legacy de Serenity/JS v2; en v3 se usa `PageElement.located(By...)` | Cualquier `.ts` de UI Mapping, Tasks, Questions |
| `resolveFor(actor)` | Anti-patrón de resolución manual; rompe la abstracción de Screenplay | Tasks, Questions, Interactions |
| `browser.$` directo en Tasks o Steps | Expone WebdriverIO fuera de las Interactions; solo se permite encapsulado dentro de una `Interaction` | `features/**/Tasks/`, `features/step-definitions/**` |

Anti-patrones complementarios a reportar cuando aparezcan: hard waits (`browser.pause()`, `setTimeout`) y callbacks en `Task.where` (deben usar `async/await`).

## Procedimiento de auditoría

1. Delimitar el alcance del escaneo a las capas Screenplay y a los step definitions:
   - Tasks: `features/**/Tasks/**/*.ts`
   - Steps: `features/step-definitions/**/*.ts`
   - Questions e Interactions cuando el `change_type` los toque.
2. Buscar cada patrón por texto. Ejemplos de señales:

```text
Target            -> import ... Target ... | Target.the( | Target.located(
resolveFor        -> .resolveFor(
browser.$ en Task -> browser.$(  o  browser.$$(  dentro de un archivo bajo Tasks/ o step-definitions/
```

3. Para `browser.$`, distinguir el contexto:
   - **Permitido**: dentro de una clase que extiende `Interaction` (mobile encapsula WebdriverIO ahí).
   - **Prohibido**: en un archivo bajo `Tasks/` o `step-definitions/`.
4. Registrar cada ocurrencia en el reporte con ruta relativa y número de línea.

## Formato del reporte

```json
{
  "anti_patterns_found": [
    {
      "pattern": "Target",
      "file": "features/web/Tasks/LoginTask.ts",
      "line": 12,
      "snippet": "Target.the('login button').located(...)",
      "action": "reportado; NO corregido automaticamente"
    },
    {
      "pattern": "browser.$ in Task",
      "file": "features/step-definitions/web/login.steps.ts",
      "line": 34,
      "snippet": "const el = await browser.$('#login');",
      "action": "reportado; NO corregido automaticamente"
    }
  ],
  "note": "Las correcciones sobre codigo preexistente requieren decision explicita del usuario."
}
```

## Qué hacer con las ocurrencias

- **Reportar** al usuario la lista completa con su ubicación.
- **No** editar el código preexistente para corregir el anti-patrón salvo que el usuario lo apruebe explícitamente como un `refactor` con su propio alcance.
- Al generar código nuevo, aplicar el patrón correcto:
  - En vez de `Target`: `PageElement.located(By.xpath(...) | By.css(...))` (web).
  - En vez de `resolveFor`: componer con `Task.where(...)` y dejar que el actor resuelva.
  - En vez de `browser.$` en Task/Step: encapsularlo en una `Interaction` (mobile) o usar `Click`/`Enter`/`Wait` de `@serenity-js/web` (web).
