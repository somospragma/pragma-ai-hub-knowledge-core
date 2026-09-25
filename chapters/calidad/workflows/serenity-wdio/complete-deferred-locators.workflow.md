---
id: complete-deferred-locators
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [serenity-wdio]
description: Resuelve los localizadores diferidos pendientes en el arquetipo WebdriverIO + Serenity/JS, reemplazando marcadores TODO/DEFERRED por selectores reales tanto en contexto web (PageElement + By) como en mobile nativo (selectores string con Accessibility ID).
tags: [serenity-wdio, locators, deferred, pageobject, accessibility-id, technical-debt, completion]
---

# Workflow — Completar localizadores diferidos

## Cuando usar

Despues de generar el scaffold con `[[generate-serenity-wdio-greenfield]]` o de extender un proyecto con `[[extend-serenity-wdio-brownfield]]`, cuando el equipo ya tiene acceso a la aplicacion real (navegador levantado o dispositivo/emulador con la app instalada) y va a reemplazar los placeholders `// TODO: completar selector` por selectores reales para que los escenarios validen contra el DOM real en vez de lanzar errores de localizador no resuelto.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| Proyecto generado o extendido | Si | Output de `[[generate-serenity-wdio-greenfield]]` o `[[extend-serenity-wdio-brownfield]]`. |
| Aplicacion web o URL base | Segun contexto | Requerido para localizadores web. |
| APK o `.app` funcional | Segun contexto | Requerido para localizadores mobile nativo. |
| Dispositivo o emulador | Segun contexto | Conectado y visible en `adb devices` (Android) o `xcrun simctl list` (iOS). |
| Appium Server | Segun contexto | Corriendo en la URL configurada en `.env.movil.*` (default `http://127.0.0.1:4723`). |

## Pasos

### 1. Identificar los localizadores diferidos pendientes en el proyecto

Buscar en todos los archivos `UI/` del proyecto los marcadores de localizador pendiente:

```bash
# Buscar marcadores en archivos UI de web y mobile
grep -rn "TODO\|DEFERRED\|PENDIENTE\|placeholder" \
  features/web/**/UI/ \
  features/mobile/**/UI/ \
  --include="*.ts"
```

Tambien buscar `PageElement` sin selector resuelto en web (patron tipico: `By.xpath('')` o `By.css('')` vacios) y selectores string vacios o ficticios en mobile (patron tipico: `''` o `'~placeholder'`):

```bash
# Selectores vacios en web
grep -rn "By\.xpath('')\|By\.css('')\|By\.id('')" features/web/**/UI/ --include="*.ts"

# Selectores placeholder en mobile
grep -rn "'~placeholder'\|'TODO'\|'DEFERRED'" features/mobile/**/UI/ --include="*.ts"
```

Documentar la lista completa de archivos y lineas afectados antes de continuar.

### 2. Determinar el contexto de cada localizador diferido

Para cada localizador identificado, clasificarlo segun su ubicacion en el proyecto:

- Si esta en `features/web/**/UI/` → contexto **web**: usar `PageElement.located(By.xpath(...))` o `By.css(...)`.
- Si esta en `features/mobile/**/UI/` → contexto **mobile nativo**: usar selector `string` plano.

No mezclar patrones. Un localizador web nunca usa selector `string` plano y un localizador mobile nunca usa `PageElement`.

### 3. Resolver localizadores en contexto web

Para cada localizador diferido en `features/web/**/UI/`:

**3a. Inspeccionar el elemento en el navegador**

Abrir la aplicacion en el navegador, navegar hasta la pantalla que contiene el elemento y usar las herramientas de desarrollo del navegador (DevTools → Elements) para identificar el selector real.

Orden de preferencia de selectores web:

1. `By.css('[data-testid="..."]')` — atributo de prueba dedicado (mas estable).
2. `By.css('#id-unico')` — ID unico en el DOM.
3. `By.css('.clase-especifica')` — clase semantica unica.
4. `By.xpath("//button[@aria-label='...']")` — atributo accesible.
5. `By.xpath("//tag[@atributo='valor']")` — XPath simple (ultimo recurso).

**3b. Reemplazar el placeholder en el archivo UI**

```typescript
// Antes (placeholder)
static buttonSubmit = () =>
  PageElement.located(By.xpath('')) // TODO: completar selector
             .describedAs('boton de envio');

// Despues (selector real)
static buttonSubmit = () =>
  PageElement.located(By.css('[data-testid="btn-submit"]'))
             .describedAs('boton de envio');
```

**3c. Verificar que el selector funciona**

Ejecutar el escenario asociado o validar el selector directamente en la consola de DevTools:

```javascript
// En consola de DevTools del navegador
document.querySelector('[data-testid="btn-submit"]')
```

**3d. Eliminar el marcador de diferido**

Quitar el comentario `// TODO: completar selector`, `// DEFERRED`, `// PENDIENTE` o equivalente una vez verificado el selector.

### 4. Resolver localizadores en contexto mobile nativo

Para cada localizador diferido en `features/mobile/**/UI/`:

**4a. Inspeccionar el elemento con Appium Inspector**

Iniciar Appium Inspector apuntando al dispositivo/emulador con la app instalada. Configurar las capabilities desde el archivo `.env.movil.android` o `.env.movil.ios` correspondiente. Navegar hasta la pantalla que contiene el elemento.

**4b. Extraer el selector real**

Orden de preferencia de selectores mobile nativo:

1. Accessibility ID (`~id`) — el atributo `accessibility-id` / `content-desc` del elemento. **Prioridad maxima.**
2. TestID (`~testId`) — cuando el equipo de desarrollo expone un atributo de prueba dedicado.
3. Texto visible — cuando el texto es unico y estable en la pantalla.
4. XPath — unico como ultimo recurso; evitar indices posicionales.

**4c. Reemplazar el placeholder en el archivo UI**

```typescript
// Antes (placeholder)
export const LoginUI = {
  button_login: 'TODO',         // DEFERRED: actualizar con selector real
  input_user: 'PENDIENTE',
  input_password: '~placeholder',
};

// Despues (selectores reales)
export const LoginUI = {
  button_login: '~login-button',       // Accessibility ID
  input_user: '~username-input',       // Accessibility ID
  input_password: '~password-input',   // Accessibility ID
};
```

**4d. Verificar que el selector funciona**

Ejecutar el escenario asociado en el dispositivo/emulador para confirmar que el elemento es localizable y que las Interactions lo manipulan correctamente:

```bash
node ./scripts/run.mjs --mode=movil --platform=android --tags="@smoke and @login"
```

**4e. Eliminar el marcador de diferido**

Quitar el comentario `// DEFERRED`, `// TODO`, `// PENDIENTE` o el valor placeholder del selector una vez verificado.

### 5. Actualizar referencias en Tasks y Steps

Si algun Task o Step hacia referencia al localizador diferido por nombre o importaba el objeto UI, verificar que las importaciones y los usos siguen siendo correctos despues del cambio:

```bash
# Verificar importaciones del archivo UI modificado
grep -rn "import.*LoginUI\|import.*FormUI" \
  features/web/**/Tasks/ \
  features/web/**/Steps/ \
  features/mobile/**/Tasks/ \
  --include="*.ts"
```

Si el nombre del objeto UI o de alguna propiedad cambio durante la resolucion, actualizar todas las referencias de forma consistente.

### 6. Ejecutar los escenarios asociados para verificar los localizadores resueltos

Ejecutar la suite completa de los escenarios que dependen de los localizadores recien resueltos:

```bash
# Verificar escenarios web asociados
node ./scripts/run.mjs --mode=web --tags="@smoke"

# Verificar escenarios mobile asociados (Android)
node ./scripts/run.mjs --mode=movil --platform=android --tags="@smoke"

# Verificar escenarios mobile asociados (iOS)
node ./scripts/run.mjs --mode=movil --platform=ios --tags="@smoke"
```

Revisar los reportes generados en `allure-results/` y el reporte serenity-bdd. Si algun escenario falla, volver al paso 3 o 4 segun el contexto e identificar la causa (selector incorrecto, elemento no visible, timeout insuficiente).

### 7. Agregar guardrail de CI para detectar localizadores diferidos residuales

Agregar un paso al pipeline de CI que impida promover codigo con marcadores de localizador diferido pendientes:

```bash
# Script de verificacion — agregar como step en el pipeline CI
if grep -rn "TODO\|DEFERRED\|PENDIENTE" features/**/UI/ --include="*.ts" | grep -v "//.*justificacion"; then
  echo "Localizadores diferidos pendientes detectados — bloqueando build."
  exit 1
fi
```

Este guardrail solo aplica a archivos `UI/`; no escanear Tasks, Interactions ni Questions para evitar falsos positivos.

### 8. Registrar localizadores no resolubles con justificacion tecnica

Si algun localizador no puede resolverse en esta iteracion (elemento aun no implementado en la app, pantalla inaccesible sin datos de prueba especificos, atributo de accesibilidad pendiente de agregar por el equipo de desarrollo), documentarlo como comentario en el archivo UI con la justificacion tecnica:

```typescript
// Web — elemento pendiente de implementar en sprint N+1
static panelResultados = () =>
  PageElement.located(By.css('[data-testid="results-panel"]'))
             .describedAs('panel de resultados');
// DEFERRED: el equipo de desarrollo agrega data-testid en sprint 42 (ticket PROJ-1234). No eliminar hasta confirmar.

// Mobile — atributo de accesibilidad pendiente
export const DashboardUI = {
  card_resumen: 'DEFERRED', // DEFERRED: el equipo mobile agrega accessibility-id en v2.3.0 (ticket MOB-567).
};
```

Estos marcadores con justificacion son la unica excepcion al guardrail de CI del paso 7. Ajustar el script de CI para ignorar lineas que contengan la cadena `justificacion:` o el ticket asociado.

## Criterios de finalizacion

1. Cero marcadores `TODO`, `DEFERRED` o `PENDIENTE` sin justificacion tecnica documentada en archivos `UI/`.
2. Todos los `PageElement.located(By.xpath/css(...))` en `features/web/**/UI/` tienen un selector no vacio y verificado contra la aplicacion real.
3. Todos los selectores `string` en `features/mobile/**/UI/` son Accessibility ID (`~id`), TestID, texto visible o XPath justificado; ningun valor es un placeholder.
4. Los escenarios `@smoke` asociados a los localizadores resueltos pasan en su modo correspondiente (web y/o mobile).
5. Las referencias en Tasks y Steps que usaban los localizadores diferidos siguen compilando y ejecutandose sin errores.
6. El guardrail de CI esta configurado en el pipeline.
7. Los localizadores no resolubles estan documentados con justificacion tecnica y ticket de referencia.
8. Si hubo fallos durante la verificacion del paso 6: cada fallo esta clasificado (localizador incorrecto, elemento no visible, timeout, drift del DOM) y la causa raiz esta documentada.
