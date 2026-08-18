---
id: serenity-wdio-troubleshooting
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Diagnosticar y documentar errores, limitaciones e impedimentos de Serenity/JS v3 con WebdriverIO v9 en Web, Mobile (Appium) y API. Incluye el workaround de window handles para NATIVE_APP, alternativas cuando @serenity-js/web no aplica, problemas de timeouts, contextos híbridos WebView, resolución de rutas en cucumberOpts, duplicación de @cucumber/cucumber, setup de CallAnApi y cómo documentar cada workaround correctamente.
tags: [serenity-wdio, troubleshooting, workarounds, mobile, appium, native-app, window-handles, timeouts, webview, cucumber-opts, callAnApi]
---

## Instrucción

Mobile es distinto a Web. No asumir compatibilidad entre plataformas.

Serenity/JS está optimizado para web. En mobile nativo y contextos híbridos existen limitaciones reales del framework que requieren workarounds documentados.

**Reglas para todo workaround:**

1. Documentar por qué se aplica (contexto del problema).
2. Documentar dónde aplica (alcance: solo mobile, solo iOS, etc.).
3. Documentar dónde NO replicarlo (Tasks, Steps, etc.).
4. Citar la fuente o issue oficial cuando sea posible.
5. Aislarlo en una sola capa (config, helper, Interaction encapsulada).

### Flujo de diagnóstico

Cuando un test falla:

1. Leer el mensaje de error completo (no solo la primera línea).
2. Identificar el contexto — ¿web, mobile native, mobile webview, API?
3. Aislar la capa — ¿es el selector, la Task, el Wait, la config?
4. Reproducir mínimamente — un solo escenario, un solo step.
5. Buscar en docs oficiales: https://serenity-js.org/handbook/ y https://webdriver.io/docs/api/mobile.
6. No buscar en blogs antiguos (pre v3) ni Stack Overflow sin verificar versión.
7. Aplicar workaround en la capa correcta (config, helper, Interaction).
8. Documentar con la plantilla del proyecto.

### Errores prohibidos al "arreglar" problemas

- Replicar el workaround del config en cada Task.
- Bypassear Screenplay con `browser.$` directo en steps.
- Aumentar timeouts hasta esconder flakiness.
- Comentar tests que fallan en lugar de diagnosticar.
- Crear nuevas Interactions cuando ya existen las del proyecto.
- Mezclar `@serenity-js/web` en mobile.

Para el detalle completo de cada problema documentado (window handles, @serenity-js/web en mobile nativo, selectores lentos, contextos WEBVIEW, timeouts, APIs legacy de v2, hard waits, reportes incompletos) y la plantilla para documentar nuevos workarounds, ver las referencias:

- `references/problemas-mobile.md` — problemas específicos de mobile nativo (window handles, @serenity-js/web, selectores, WEBVIEW).
- `references/problemas-generales.md` — problemas transversales (timeouts, APIs legacy v2, hard waits, reportes vacíos, plantilla de documentación).

### Checklist al cerrar un diagnóstico

- [ ] El error está reproducido y entendido
- [ ] La causa raíz está identificada (no solo el síntoma)
- [ ] El fix está en la capa arquitectónica correcta
- [ ] El workaround está documentado con la plantilla
- [ ] Se verificó que no rompe otros perfiles (web/mobile/api)
- [ ] Se citaron fuentes oficiales (no blogs)
- [ ] El test pasa de forma estable (3 ejecuciones consecutivas)
