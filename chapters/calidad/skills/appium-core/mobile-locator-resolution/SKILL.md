---
id: calidad-mobile-locator-resolution
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium-core]
description: Resuelve locators mobile contra la jerarquía real — identidad no es capacidad, conteo de nodos, validación por efecto externo y comportamiento de apps Flutter bajo Appium.
tags: [appium, mobile, locators, flutter, semantics, android, ios, agnostico]
---

# Resolución de locators mobile

## Cuándo aplicar

Siempre que haya que **escribir o reparar un locator** en una suite Appium, en cualquier plataforma y con cualquier cliente: Java, TypeScript, Python o C#. El problema que resuelve no es del lenguaje sino del árbol de accesibilidad que expone el dispositivo, así que aplica igual desde `AppiumBy` en Java que desde `driver.$()` en WebdriverIO.

Este bundle pertenece al stack `appium-core`, que se instala junto al stack de producto (`appium-serenity` o `appium-wdio`). Los stacks de producto aportan la sintaxis; este aporta el método. El stack `serenity-wdio` también cubre mobile Android e iOS, pero no consume este bundle: resuelve locators con su propio conocimiento encapsulado en sus references (Screenplay TypeScript/WebdriverIO); no instalar `appium-core` junto a un proyecto `serenity-wdio`.

## Lectura obligatoria

| Reference | Para qué |
|---|---|
| `references/locator-resolution-protocol.md` | El protocolo completo: identidad contra capacidad, conteo de nodos, validación por efecto externo, prohibiciones |
| `references/flutter-under-appium.md` | Qué ve Appium en una app Flutter y por qué casi todo lo anterior se vuelve obligatorio ahí |

## Las tres reglas que evitan el noventa por ciento de los fallos

1. **El identificador da identidad, no capacidad.** Que un nodo lleve el identificador del contrato no significa que reciba clics ni texto. En Flutter y en varios frameworks híbridos ese nodo es un contenedor no interactuable, y el elemento capaz es un descendiente con los mismos límites.
2. **El único conteo aceptable es uno.** Cero significa que el locator no resuelve; dos o más es ambigüedad, y el driver elegirá cualquiera: el fallo será intermitente y se atribuirá a la app. Queda prohibido resolver la ambigüedad con índice posicional o con unión de expresiones.
3. **La prueba de que un locator funciona es un efecto externo**, no que el valor se vea en la jerarquía: una navegación efectiva, un payload que llega al backend, un estado que persiste.

## Instrucción

1. **Volcar la jerarquía real** de la pantalla y parsearla **como árbol**. Nunca deducir la topología de la indentación de un volcado impreso: la indentación no es el árbol.
2. **Partir siempre del identificador del contrato** cuando exista. Es la única ancla; el texto visible y la posición no lo son.
3. **Enumerar los ejes candidatos** desde ese nodo: él mismo, sus descendientes capaces, sus hermanos con los mismos límites.
4. **Contar nodos por candidato** y quedarse con el que resuelve exactamente uno.
5. **Validar por efecto externo** ejecutando la interacción.
6. **Fijar la resolución** en la capa de locators del proyecto y protegerla con una prueba, para que nadie la "simplifique" de vuelta sin que el build avise.

## Sintaxis por stack

El método es el mismo; cambia cómo se expresa. Equivalencias de las estrategias que importan:

| Estrategia | Java (`appium-serenity`) | TypeScript (`appium-wdio`) |
|---|---|---|
| Identificador de accesibilidad | `AppiumBy.accessibilityId("id")` | `driver.$('~id')` |
| Identificador de recurso Android | `AppiumBy.androidUIAutomator("new UiSelector().resourceId(\"id\")")` | `driver.$('android=new UiSelector().resourceId("id")')` |
| XPath | `AppiumBy.xpath("//*[@resource-id='id']")` | `driver.$('//*[@resource-id="id"]')` |
| Cadena de clases iOS | `AppiumBy.iOSClassChain("**/XCUIElementTypeButton[\`label == \"X\"\`]")` | `driver.$('-ios class chain:**/XCUIElementTypeButton[\`label == "X"\`]')` |
| Predicado iOS | `AppiumBy.iOSNsPredicateString("label == 'X'")` | `driver.$('-ios predicate string:label == "X"')` |
| Conteo de coincidencias | `driver.findElements(...).size()` | `(await driver.$$(sel)).length` |

En `appium-wdio` los locators no se escriben en el código: viven en archivos de test-data. Ese es el destino de la expresión resuelta, no una excepción al protocolo. Ver `[[calidad-appium-wdio-greenfield]]`.

## Restricciones

- **No fijar en un asset del chapter la expresión que funcionó en una app concreta.** Lo que se fija es el protocolo; la expresión se resuelve contra cada app.
- **No relajar el discriminante hasta que "algo" haga match.** Es la forma más rápida de producir un verde falso, y es lo que el guardrail anti-cheating del chapter prohíbe. Aplica también al self-healing: puede re-resolver la capacidad cuando cambie la topología, nunca aflojar el ancla. Ver `[[calidad-test-self-healing]]`.
- **No resolver el mismo elemento en dos capas** (una en el objeto de página y otra en línea dentro del paso). Una sola capa de resolución.
- **En brownfield, la resolución que el proyecto ya usa es la convención detectada** y se reutiliza; no se introduce una segunda estrategia en paralelo.

## Relación con otros assets

- El mapa de identificadores (`[[calidad-ui-locator-map-contract]]`) declara la convención de **identidad**; este bundle resuelve la **capacidad** pantalla por pantalla.
- Cuando no hay mapa y sí hay binario, `[[calidad-appium-apk-auto-discovery]]` descubre los locators recorriendo la app, y cada hallazgo se verifica con este protocolo antes de fijarlo.
- Las interacciones que usan el locator resuelto están en `[[calidad-mobile-interactions]]`.
