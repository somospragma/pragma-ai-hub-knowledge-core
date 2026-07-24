---
id: calidad-ui-locator-map-contract
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Contrato de mapeo de identificadores/localizadores UI acordado entre QA y desarrollo, para construir pruebas front/mobile antes del desarrollo sin que fallen por drift de selectores cuando la app llegue."
tags: [locators, ui, contract, shift-left, playwright, appium, testid, accessibility-id, figma]
---

# UI Locator Map Contract — Identificadores Acordados Antes del Desarrollo

## Problema que resuelve

Cuando las pruebas de front (Playwright) o mobile (Appium) se construyen **antes** de que exista la interfaz, los selectores se infieren (de Figma, de la user story). Si el equipo de desarrollo luego implementa identificadores distintos, la suite entera falla el día del estreno — no por bugs, sino por drift de selectores. La solución no es adivinar mejor: es **convertir los identificadores en un contrato bidireccional** entre QA y desarrollo, versionado y verificable.

## Cuándo aplicar

- **Obligatorio** cuando `[[calidad-sut-readiness-gate]]` resolvió `execution_target: mock` (o construcción pre-desarrollo) para Playwright o Appium. Sin locator map en ese modo → STOP; la construcción no es viable.
- **Recomendado** en cualquier greenfield front/mobile, incluso con app viva: estabiliza la suite frente a refactors de UI.

## El contrato

Un archivo `locator-map.json` versionado en el proyecto de tests (y referenciado desde el repo del frontend/app), acordado en sesión conjunta QA + dev + diseño a partir del Figma:

```json
{
  "version": "1.0.0",
  "source": "figma:https://figma.com/file/XXXX (page: Checkout v3)",
  "agreed_with": "equipo frontend, 2026-07-20",
  "convention": { "web": "data-testid", "mobile": "android:contentDescription (accessibilityId)" },
  "screens": [
    {
      "screen": "login",
      "route": "/login",
      "elements": [
        { "name": "username_input",  "web": "login-username",  "mobile": "login_username",  "role": "textbox" },
        { "name": "password_input",  "web": "login-password",  "mobile": "login_password",  "role": "textbox" },
        { "name": "submit_button",   "web": "login-submit",    "mobile": "login_submit",    "role": "button" }
      ]
    }
  ]
}
```

Reglas del formato:

1. `name` es el identificador lógico que usan Page Objects y Tasks; `web`/`mobile` son los valores literales que desarrollo se compromete a implementar (`data-testid` en web, `contentDescription`/resource-id en Android según convención acordada).
2. Naming kebab-case (web) / snake_case (mobile), prefijado por pantalla, sin valores derivados de texto visible (el texto cambia con i18n; el testid no).
3. `role` opcional documenta el rol ARIA esperado — habilita fallback `getByRole` y validación de accesibilidad.
4. Todo elemento con el que el robot interactúe o aserte DEBE estar en el mapa. Elementos decorativos no.

## Compromisos de cada parte

- **Desarrollo** implementa exactamente los identificadores del mapa (es un criterio de aceptación de sus HUs — idealmente verificado en su propio CI).
- **QA** genera los selectores SOLO desde el mapa: Playwright `getByTestId('login-username')` (consistente con `selector-priority` de [[calidad-playwright-greenfield]]); Appium `AppiumBy.accessibilityId("login_username")` — los placeholders de `deferred-locators-strategy` de [[calidad-appium-screenplay-android]] salen del mapa, no se inventan.
- **Cambios** al mapa (renombrar, agregar pantalla) se hacen por PR sobre el archivo, con ambos equipos como reviewers. El mapa es la fuente de verdad; ni el test ni el DOM la redefinen unilateralmente.

## Validación de drift cuando llega el desarrollo

Antes de correr la suite contra la app real por primera vez (paso 4 del checklist de certificación en `[[calidad-service-virtualization-mockoon]]`, `references/mock-vs-real-switchover.md`):

1. **Web**: navegar las rutas del mapa y verificar que cada `web` id existe en el DOM (`page.getByTestId(id).count() > 0`). Emitir reporte `.evidence/locator-map-drift-{ISO}.json` con `expected / found / missing`.
2. **Mobile**: volcar la jerarquía (Appium `getPageSource` o `[[calidad-appium-apk-auto-discovery]]`) y diffear contra los `mobile` ids del mapa.
3. **Drift detectado** → el fallo se reporta como **incumplimiento de contrato de identificadores** al equipo de desarrollo (con la lista exacta de faltantes), NO como N tests rojos a auto-corregir. La auto-corrección de selectores (`[[calidad-test-self-healing]]`) aplica después de que el drift de contrato esté resuelto o formalmente aceptado (y entonces el mapa se actualiza primero).

## Restricciones

- **NUNCA** completar el mapa con valores adivinados por el QA sin acuerdo de desarrollo: un mapa unilateral es una lista de deseos, no un contrato.
- **NUNCA** usar selectores fuera del mapa en tests construidos pre-desarrollo (CSS visual, XPath posicional): anula la garantía del contrato.
- El mapa no sustituye la validación real: `locator_map: provided` habilita construir; la certificación sigue exigiendo la validación de drift + suite contra la app real.
- En brownfield, el mapa aplica a pantallas nuevas; selectores de tests preexistentes no se migran al mapa sin pedido explícito.

## Cross-links

`[[calidad-sut-readiness-gate]]`, `[[calidad-playwright-greenfield]]` (references `selector-priority.md`, `ui-source-priority.md`), `[[calidad-appium-screenplay-android]]` (reference `deferred-locators-strategy.md`), `[[calidad-complete-deferred-locators]]`, `[[calidad-test-self-healing]]`, `[[calidad-delivery-gate-contract]]`.
