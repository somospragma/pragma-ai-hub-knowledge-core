# WebdriverIO v9 — Referencia rápida de comandos

## Navegación (web)

| Comando | Uso |
|---|---|
| `browser.url(path)` | Navegar a URL |
| `browser.back()` / `browser.forward()` | Historial |
| `browser.refresh()` | Recargar |
| `browser.getUrl()` | URL actual |
| `browser.getTitle()` | Título página |

## Element queries

| Comando | Uso |
|---|---|
| `$(selector)` / `browser.$(...)` | Un elemento |
| `$$(selector)` / `browser.$$(...)` | Lista de elementos |
| `el.$('child')` / `el.$$('child')` | Búsqueda anidada |
| `el.parentElement()` | Padre directo |

## Interacciones

| Comando | Uso |
|---|---|
| `el.click({ button, x, y })` | Click con opciones |
| `el.doubleClick()` | Doble click |
| `el.setValue(text)` | Escribir (reemplaza) |
| `el.addValue(text)` | Concatenar |
| `el.clearValue()` | Vaciar input |
| `el.scrollIntoView()` | Scroll hasta el elemento |
| `el.dragAndDrop(target)` | Drag and drop |

## Esperas

| Comando | Uso |
|---|---|
| `el.waitForExist({ timeout })` | Existe en DOM |
| `el.waitForDisplayed({ timeout, reverse })` | Visible (reverse=invisible) |
| `el.waitForClickable({ timeout })` | Clickable |
| `el.waitForEnabled({ timeout })` | Habilitado |
| `browser.waitUntil(fn, { timeout })` | Condición custom |

## Mobile específicos (v9)

| Comando | Uso |
|---|---|
| `el.longPress({ duration })` | Long press |
| `el.scrollIntoView({ direction, maxScrolls })` | Scroll hasta el elemento |
| `browser.swipe({ direction, percent })` | Swipe direccional |
| `browser.getContexts()` | Listar contextos disponibles |
| `browser.switchContext(name)` | Cambiar contexto |
| `browser.execute('mobile: <gesture>', params)` | Comando Appium crudo |
| `browser.hideKeyboard()` | Ocultar teclado (Android) |

## Estado del browser

| Comando | Uso |
|---|---|
| `browser.isMobile` | bool — sesión mobile |
| `browser.isAndroid` / `browser.isIOS` | bool — plataforma |
| `browser.capabilities` | Capabilities activas |
| `browser.getWindowRect()` | `{ x, y, width, height }` |
