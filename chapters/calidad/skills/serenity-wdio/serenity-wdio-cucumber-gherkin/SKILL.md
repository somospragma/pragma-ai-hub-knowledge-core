---
id: serenity-wdio-cucumber-gherkin
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Crear, analizar y mantener archivos .feature de Cucumber con Gherkin en español, step definitions en TypeScript con Serenity/JS Screenplay Pattern, y parameter types personalizados ({actor} y {pronoun}). Aplica al escribir escenarios BDD, mapear steps a Tasks/Questions o diagnosticar problemas en features existentes.
tags: [serenity-wdio, cucumber, gherkin, bdd, step-definitions, screenplay, typescript, parameter-types]
---

## Instrucción

Este proyecto usa Cucumber v11 con Gherkin en español (web y API) e inglés (mobile, por convención del proyecto), Serenity/JS v3.31+ con Screenplay Pattern, WebdriverIO v9 y TypeScript con `strict: true`.

Parameter types personalizados definidos en `features/support/parameter.config.ts`:

| Parameter | Regex | Transformer | Uso |
|---|---|---|---|
| `{actor}` | `/[A-Z][a-z]+/` | `actorCalled(name)` | Nombre del actor (ej: `Pepito`) |
| `{pronoun}` | `/he\|she\|they\|his\|her\|their/` | `actorInTheSpotlight()` | Referencia al actor activo |

Usar `{actor}` en el primer step del escenario y `{pronoun}` en steps subsiguientes que referencian al mismo actor.

### Reglas obligatorias antes de generar

1. Preguntar el contexto si no está claro: ¿Es Web, Mobile nativo (Appium) o API REST?
2. Leer el `.feature` existente antes de crear steps.
3. Respetar la estructura de carpetas: Features en `features/[web|mobile/android|mobile/ios|api]/Features/*.feature`, Steps en `features/step-definitions/[web|mobile|api]/*.steps.ts`.
4. Nunca asumir selectores, Tasks ni Questions — leer los archivos existentes primero.

### Reglas de Gherkin

**Obligatorio:**
- Idioma: español para Web y API, inglés para Mobile (convención del proyecto).
- Un escenario = una responsabilidad de negocio.
- Usar `Scenario Outline` + `Examples` cuando hay múltiples datasets.
- Tags con `@` para filtrar ejecuciones.
- Nombres de actores con mayúscula inicial (`Pepito`, `Jorge`, `Ana`).

**Prohibido:**
- Detalles técnicos en Gherkin (selectores, XPath, IDs).
- Lógica condicional en steps (`if`, `switch`).
- Más de un `When` por escenario (usar `And`).
- Escenarios dependientes entre sí.
- Hard-coded waits en steps.

### Flujo para crear un nuevo escenario

1. Identificar el módulo → determinar carpeta en `features/[web|mobile|api]/`.
2. Escribir el `.feature` → lenguaje de negocio, sin detalles técnicos.
3. Verificar si ya existen Tasks/UI → leer archivos en `Tasks/` y `UI/`.
4. Crear o reutilizar Tasks → nunca duplicar lógica existente.
5. Crear el step definition → importar Tasks, usar `{actor}` / `{pronoun}`.
6. Registrar el step file en `cucumberOpts.import` del config correspondiente.

Para patrones completos de `.feature` y step definitions por contexto (Web, Mobile, API), mapeo Gherkin → Screenplay y checklist de calidad, ver las referencias:

- `references/gherkin-features.md` — patrones de `.feature` y reglas de Gherkin completas.
- `references/step-definitions.md` — plantillas de step definitions para Web, Mobile y API.
