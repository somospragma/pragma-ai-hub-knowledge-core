---
id: serenity-wdio-webdriverio-handling
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Usar WebdriverIO v9 en TypeScript tanto de forma directa como encapsulado dentro de Screenplay Pattern (Interactions y Questions). Cubre selectores, acciones, mobile commands, Action API, contextos NATIVE_APP/WEBVIEW, custom commands y la regla de cuándo usar cada enfoque.
tags: [serenity-wdio, webdriverio, wdio-v9, interactions, questions, mobile, appium, typescript]
---

## Instrucción

Regla del proyecto: determinar primero si el código vive dentro de `features/` o en un script/config independiente.

| Escenario | Enfoque recomendado |
|---|---|
| Test de regresión BDD del proyecto | Screenplay (encapsulado en Interactions) |
| Spike rápido / prototipo / debug local | WDIO directo (script standalone) |
| Hooks de configuración (`before`, `after` en wdio.*.conf.ts) | WDIO directo |
| Workarounds del framework (overwriteCommand) | WDIO directo en config |
| Acción reutilizable en múltiples Tasks | Interaction que encapsule WDIO |
| Question reutilizable | Question.about que encapsule WDIO |
| Mobile (Appium) — cualquier acción nativa | Interaction encapsulando `browser.$` |
| Web — el comando ya existe en `@serenity-js/web` | NO usar WDIO directo, usar Screenplay/web |

En Tasks y Steps **nunca** se usa `browser.$` directo. Se permite WDIO directo solo en:

1. Archivos `configs/wdio.*.conf.ts` (hooks `before`/`after`)
2. Clases que extienden `Interaction` o crean `Question.about`
3. Scripts standalone fuera de `features/` (debug, exploración)

### Imports correctos en v9

```typescript
import { browser, $, $$, expect, driver } from '@wdio/globals';
```

- `browser` y `driver` son alias del mismo objeto en mobile.
- TypeScript: usar siempre `await` (v9 es 100% async).

### Decisión rápida: directo o encapsulado

```
¿El código vive en features/ o se ejecutará dentro de un escenario Cucumber?
├── SÍ
│   ├── ¿Es web y existe en @serenity-js/web?
│   │   └── SÍ → usar Click/Enter/Wait/Text de Serenity (NO WDIO)
│   └── NO existe en @serenity-js/web (mobile, gesto custom, etc.)
│       └── → encapsular en Interaction o Question
└── NO (config, hook, script standalone)
    └── → WDIO directo permitido
```

Para el detalle completo de comandos, plantillas de Interactions/Questions, mobile commands, Action API, manejo de contextos WEBVIEW, custom commands y anti-patrones, ver las referencias:

- `references/wdio-directo.md` — uso de WebdriverIO directo (selectores, acciones, esperas, mobile commands, Action API, contextos, custom commands).
- `references/wdio-encapsulado.md` — plantillas de Interaction y Question encapsulando WDIO, reglas de encapsulación y anti-patrones.
- `references/wdio-referencia-rapida.md` — tablas de comandos clave (navegación, element queries, interacciones, esperas, mobile específicos, estado del browser).
