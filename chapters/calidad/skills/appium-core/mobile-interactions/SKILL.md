---
id: calidad-mobile-interactions
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium-core]
description: Repertorio de interacción mobile bajo Appium — escritura, campos OTP, gestos W3C, política de esperas, pantallas condicionales y aserciones que verifican el contrato.
tags: [appium, mobile, interacciones, gestos, esperas, aserciones, agnostico]
---

# Interacciones y aserciones mobile

## Cuándo aplicar

Cuando haya que **interactuar con la app o aseverar sobre ella** en una suite Appium, con cualquier cliente y en cualquier plataforma. Los comandos que hay debajo son del servidor Appium: el lenguaje solo cambia cómo se invocan.

Pertenece al stack `appium-core`, que se instala junto al stack de producto (`appium-serenity` o `appium-wdio`); `serenity-wdio` no lo requiere, tiene su propio catálogo de interacciones mobile encapsulado en sus references. Antes de interactuar hay que tener el locator resuelto: ver `[[calidad-mobile-locator-resolution]]`.

## Lectura obligatoria

| Reference | Para qué |
|---|---|
| `references/mobile-interactions-catalog.md` | Canon de escritura, campos OTP, gestos, esperas en tres capas, pantallas condicionales, estado entre escenarios |
| `references/contractual-assertions.md` | Aserciones que verifican el contrato y no la mera presencia de algo en pantalla |
| `references/system-dialogs-and-scenario-contamination.md` | Diálogos del sistema que quedan sobre la app y rompen el escenario siguiente; verificación de descargas |

## Las reglas que más caro salen cuando se ignoran

1. **Escribir en un campo no es una sola llamada.** El canon es tocar el campo, escribir, ocultar el teclado y verificar el valor resultante. El teclado tapa el elemento siguiente y el clic termina golpeando una tecla.
2. **Los campos de tipo PIN u OTP no aceptan escritura directa** en muchos widgets: se resuelven dígito a dígito o con el evento de teclado del dispositivo.
3. **Gestos con acciones W3C, nunca con la API táctil obsoleta.** Está retirada en los drivers actuales y su uso produce fallos que parecen del dispositivo.
4. **Esperas en tres capas**: espera implícita cero, espera explícita por condición, y espera de disponibilidad del árbol tras abrir una pantalla. Una espera fija es lenta cuando sobra e insuficiente cuando falta.
5. **La pantalla que esperas no siempre es la que llega.** Un flujo real desemboca en varias pantallas legítimas — cambio de contraseña obligatorio, sesión en otro dispositivo, aviso de mantenimiento. Esperar solo el camino feliz produce un timeout que se reporta como fallo de la app.
6. **Una aserción debe verificar el contrato**, no que "algo se ve". Que un elemento exista no prueba que el dato sea correcto, ni que la operación haya ocurrido.

## Instrucción

1. **Resolver el locator** con `[[calidad-mobile-locator-resolution]]` antes de escribir la interacción.
2. **Elegir el patrón del catálogo** que corresponda a la interacción, en vez de improvisar una secuencia de llamadas.
3. **Encapsular la interacción en la capa del proyecto** — Interaction en Screenplay, método del objeto de pantalla en un modelo de página — nunca suelta en la definición del paso.
4. **Aseverar contra el contrato**: valor esperado, estado esperado, efecto esperado. Aplicar la tabla de aserciones mínimas por tipo de pantalla de `references/contractual-assertions.md`.
5. **Instrumentar la evidencia antes de la primera corrida**, no cuando algo falla.

## Sintaxis por stack

| Operación | Java (`appium-serenity`) | TypeScript (`appium-wdio`) |
|---|---|---|
| Escribir | `element.sendKeys(texto)` | `await el.setValue(texto)` |
| Ocultar teclado | `driver.hideKeyboard()` | `await driver.hideKeyboard()` |
| Tap por coordenadas | `driver.executeScript("mobile: clickGesture", args)` | `await driver.execute('mobile: clickGesture', args)` |
| Scroll hasta elemento | `AppiumBy.androidUIAutomator("new UiScrollable(...)")` | `await driver.$('android=new UiScrollable(...)')` |
| Espera por condición | `WebDriverWait` / `Wait.until` | `await driver.waitUntil(fn, { timeout, timeoutMsg })` |
| Estado de la app | `driver.queryAppState(id)` | `await driver.queryAppState(id)` |

El comando `mobile:` es del servidor y es idéntico en ambos; lo que cambia es el método que lo invoca.

## Restricciones

- **No usar esperas fijas** como mecanismo de sincronización. Se aceptan solo para animaciones de duración conocida, con un comentario que lo justifique.
- **No usar el tap por coordenadas como método por defecto**: pasa aunque el elemento esté deshabilitado, con lo que puede ocultar un defecto real. Es un recurso de recuperación y se documenta por qué se usó.
- **No compartir estado entre escenarios** por variables de módulo: con ejecución en paralelo produce fallos que no se reproducen.
- **No aseverar sobre la mera existencia** de un elemento cuando lo que importa es su valor o su efecto.
