---
id: calidad-ui-locator-map-contract
version: 1.3.0
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

Un archivo `locator-map.json` versionado en el proyecto de tests (y referenciado desde el repo del frontend/app), acordado en sesión conjunta QA + dev + diseño a partir del Figma (consumido vía `[[calidad-figma-mcp-integration]]` — los nombres de capas/componentes del diseño son la semilla de los identificadores):

```json
{
  "version": "1.0.0",
  "source": "figma:https://figma.com/file/XXXX (page: Checkout v3)",
  "agreed_with": "equipo frontend, 2026-07-20",
  "convention": { "web": "data-testid", "mobile": "semantics_identifier | semantics_label | resource-id | accessibilityId (declarar cuál)" },
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

1. `name` es el identificador lógico que usan Page Objects y Tasks; `web`/`mobile` son los valores literales que desarrollo se compromete a implementar (`data-testid` en web; en Android nativo `resource-id`/`contentDescription` según convención acordada).
1b. **Apps Flutter**: la convención `mobile` la declara el equipo dev — `semantics_identifier` (se expone como `resource-id` en Android con Flutter 3.19+ y `accessibilityIdentifier` en iOS; estable ante i18n, preferida cuando dev la adopta) o `semantics_label` (→ `content-desc`/`@name`; muy común en campo — su costo: el catálogo de textos pasa a ser parte del contrato, paridad carácter a carácter en todos los idiomas). **Ambas son de primera clase**: el mapa registra cuál rige. OJO en la resolución Android: `AppiumBy.id` NO resuelve el identifier de Flutter — la estrategia verificada está en [[calidad-appium-screenplay-android]] (consultar `references/locator-resolution-protocol.md` en su subfolder).
1c. **El mapa garantiza identidad, no capacidad**: el nodo del identificador puede ser un contenedor sin capacidad de click/escritura; el eje hacia el nodo capaz se resuelve en runtime por pantalla (protocolo de resolución) y se registra como `resolution_verified_<fecha>` en el mapa. El contrato con dev incluye además las prácticas que hacen automatizable cada elemento (`ExcludeSemantics` en compuestos, `explicitChildNodes` en campos editables — un componente = UN nodo).
1d. **Flutter Web**: la columna `web` no usa `data-testid` (no hay DOM de la UI) — usa la proyección del árbol de semántica (`aria-label` / rol / texto del catálogo), con el paso de activación de accesibilidad al arranque. Ver [[calidad-playwright-greenfield]] (consultar `references/front-prototype-recipe.md`).
2. Naming kebab-case (web) / snake_case (mobile), prefijado por pantalla, sin valores derivados de texto visible (el texto cambia con i18n; el testid no).
3. `role` opcional documenta el rol ARIA esperado — habilita fallback `getByRole` y validación de accesibilidad.
4. Todo elemento con el que el robot interactúe o aserte DEBE estar en el mapa. Elementos decorativos no.

## Compromisos de cada parte

- **Desarrollo** implementa exactamente los identificadores del mapa (es un criterio de aceptación de sus HUs — idealmente verificado en su propio CI).
- **QA** genera los selectores SOLO desde el mapa: Playwright `getByTestId('login-username')` (consistente con `selector-priority` de [[calidad-playwright-greenfield]]); Appium `AppiumBy.accessibilityId("login_username")` — los placeholders de `deferred-locators-strategy` de [[calidad-appium-screenplay-android]] salen del mapa, no se inventan.
- **Cambios** al mapa (renombrar, agregar pantalla) se hacen por PR sobre el archivo, con ambos equipos como reviewers. El mapa es la fuente de verdad; ni el test ni el DOM la redefinen unilateralmente.
- **Los prototipos como especificación ejecutable**: cuando existe front prototype (web) o app prototype (Flutter), estos implementan exactamente los identificadores del mapa — el equipo dev tiene el ejemplo corriendo de lo que se comprometió a implementar. Recetas: [[calidad-playwright-greenfield]] (consultar `references/front-prototype-recipe.md`) y [[calidad-appium-screenplay-android]] (consultar `references/flutter-apps-and-prototype.md`).

## Validación de drift cuando llega el desarrollo

Antes de correr la suite contra la app real por primera vez (paso 4 del checklist de certificación en `[[calidad-service-virtualization-mockoon]]`, `references/mock-vs-real-switchover.md`):

1. **Web**: navegar las rutas del mapa y verificar que cada `web` id existe en el DOM (`page.getByTestId(id).count() > 0`). Emitir reporte `.evidence/locator-map-drift-{ISO}.json` con `expected / found / missing`.
2. **Mobile**: volcar la jerarquía (Appium `getPageSource` o `[[calidad-appium-apk-auto-discovery]]`) y diffear contra los `mobile` ids del mapa.
3. **Drift detectado** → el fallo se reporta como **incumplimiento de contrato de identificadores** al equipo de desarrollo (con la lista exacta de faltantes), NO como N tests rojos a auto-corregir. La auto-corrección de selectores (`[[calidad-test-self-healing]]`) aplica después de que el drift de contrato esté resuelto o formalmente aceptado (y entonces el mapa se actualiza primero).

## Enforcement ante ausencia del mapa

Preguntar por el mapa **no es un trámite**: la respuesta cambia el flujo. Si `execution_target != real` y el mapa no existe:

1. **Default: DETENER.** No se generan page objects, tasks ni tests de UI. Blocker `locator_map_missing`, status `partial`. Se ofrece al usuario la plantilla del mapa y la sesión de acuerdo con desarrollo como siguiente paso.
2. **Override explícito (única excepción):** si el usuario, informado del riesgo, decide continuar sin mapa, debe confirmarlo con frase explícita. El flujo continúa con selectores inferidos y registra en el delivery gate `locator_map: waived` + el riesgo aceptado ("suite puede fallar íntegramente por drift de identificadores al llegar el desarrollo") en `blockers` o `next_steps`. El mensaje de cierre lo repite.
3. **PROHIBIDO el camino intermedio observado en pruebas**: preguntar, no recibir mapa, y continuar en silencio generando reporte completo como si nada faltara. Eso invalida la entrega.

## Restricciones

- **NUNCA** completar el mapa con valores adivinados por el QA sin acuerdo de desarrollo: un mapa unilateral es una lista de deseos, no un contrato.
- **NUNCA** usar selectores fuera del mapa en tests construidos pre-desarrollo (CSS visual, XPath posicional): anula la garantía del contrato.
- El mapa no sustituye la validación real: `locator_map: provided` habilita construir; la certificación sigue exigiendo la validación de drift + suite contra la app real.
- En brownfield, el mapa aplica a pantallas nuevas; selectores de tests preexistentes no se migran al mapa sin pedido explícito.

## Cross-links

`[[calidad-sut-readiness-gate]]`, `[[calidad-playwright-greenfield]]` (references `selector-priority.md`, `ui-source-priority.md`), `[[calidad-appium-screenplay-android]]` (reference `deferred-locators-strategy.md`), `[[calidad-complete-deferred-locators]]`, `[[calidad-test-self-healing]]`, `[[calidad-delivery-gate-contract]]`.
