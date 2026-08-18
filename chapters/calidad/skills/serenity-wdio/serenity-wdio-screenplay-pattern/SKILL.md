---
id: serenity-wdio-screenplay-pattern
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Implementar Screenplay Pattern con Serenity/JS v3 y WebdriverIO v9 en Web, Mobile (Appium) y API REST. Cubre Tasks, Interactions, Questions, UI Mapping, composición con Task.where y las reglas obligatorias por plataforma.
tags: [serenity-wdio, screenplay, serenity-js, webdriverio, tasks, interactions, questions, ui-mapping, web, mobile, api]
---

## Instrucción

Antes de generar cualquier componente Screenplay, confirmar el contexto de plataforma:

```
¿Este componente es para:
1. Web (desktop browser)
2. Mobile nativo (Android/iOS via Appium)
3. API REST
4. Híbrido (WebView)?
```

No asumir el contexto. Cada plataforma tiene reglas distintas de imports, selectores y componentes permitidos.

### Componentes y responsabilidades

| Componente | Responsabilidad | Ejemplo |
|---|---|---|
| **Actor** | Quién ejecuta | `actorCalled('Pepito')` |
| **Ability** | Capacidad técnica del actor | `BrowseTheWeb.using(browser)`, `CallAnApi.at(url)` |
| **Task** | Qué hace (negocio) | `LlenarFormulario.conDataset('x')` |
| **Interaction** | Cómo lo hace (técnico) | `Click.on(...)`, `Tap.on(...)` |
| **Question** | Qué observa | `Text.of(...)`, `TextOf(selector)` |
| **UI Mapping** | Dónde está | `LoginUI.buttonLogin()` |

Regla de oro: Tasks describen negocio. Interactions describen mecánica. Nunca mezclar.

### Composición con Task.where

```typescript
Task.where(
  '#actor hace algo coherente de negocio',
  PrimeraSubTask,
  SegundaSubTask,
  TerceraInteraction,
);
```

- El primer argumento es una descripción legible (`#actor` se reemplaza por el nombre del actor en el reporte).
- Los siguientes son Tasks/Interactions a ejecutar en orden secuencial.
- No usar callbacks asíncronos como argumento.
- Una Task = una responsabilidad de negocio coherente.

### Errores arquitectónicos prohibidos

- Tasks que hacen más de una responsabilidad de negocio.
- Lógica condicional en Tasks — separar en Tasks distintas.
- Questions con efectos secundarios.
- Mezclar `browser.$` + Screenplay en el mismo nivel (Web).
- Reescribir desde cero cuando se puede refactorizar.
- Crear nuevas Interactions cuando ya existen las de `@serenity-js/web` (en web).

### Estándares transversales

- TypeScript con `strict: true`.
- `async/await` siempre, nunca `.then()`.
- `describedAs(...)` en PageElements (web) y descripciones legibles en Tasks/Interactions (mobile).
- Datos de prueba en JSON dentro de `features/[web|api]/Data/`.
- DRY: shared Tasks/Interactions reutilizables en `shared/`.

Para el detalle completo por plataforma (Web, Mobile nativo y API REST) con ejemplos de código, plantillas y checklists de calidad, ver las referencias:

- `references/screenplay-web.md` — implementación completa para Web.
- `references/screenplay-mobile.md` — implementación completa para Mobile nativo (Appium).
- `references/screenplay-api.md` — implementación completa para API REST.
