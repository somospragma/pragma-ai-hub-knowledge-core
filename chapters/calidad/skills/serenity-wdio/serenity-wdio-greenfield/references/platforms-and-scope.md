# Plataformas y alcance (Serenity WDIO Greenfield)

## Plataformas soportadas

El stack `serenity-wdio` soporta exactamente cinco plataformas:

| Plataforma | Modo (`--mode`) | Motor / tecnologia | Notas |
|---|---|---|---|
| Web desktop | `web` | WebdriverIO v9 + `@serenity-js/web` | Chrome/Firefox con WebDriver Classic forzado |
| Web movil (WebView) | `web_movil` | WebdriverIO v9 + WebView | Contexto hibrido, requiere control de contexto |
| Movil nativo | `movil` (`--platform=android` / `--platform=ios`) | Appium (UiAutomator2 / XCUITest) | Selectores como string, sin `@serenity-js/web` |
| Desktop | `desktop` | Appium Windows | No usa `enforceWebDriverClassic` |
| API | `api` | `@serenity-js/rest` | Pruebas REST sin navegador |

## Diferenciacion con el stack `appium`

El stack `appium` del chapter `calidad` es Java 21 + Gradle + Serenity BDD (Java) y su auto-generador solo cubre Android. El stack `serenity-wdio` es diferente y complementario:

- **Lenguaje**: TypeScript (`target: es2022`, `strict: true`), no Java.
- **Runner**: WebdriverIO v9 + Cucumber-JS 11, no Gradle + JUnit.
- **Alcance**: multiplataforma (web, web_movil, movil, desktop, api), no solo Android.
- **Serenity**: Serenity/JS v3.31, no Serenity BDD Java.

Por esta razon `serenity-wdio` se registra como stack nuevo y usa `appium` unicamente como patron estructural de referencia (misma disposicion greenfield/brownfield/run-and-tags), no como base tecnica a extender.

## Regla critica de contexto

Antes de generar codigo, confirmar siempre si el escenario es Web, Movil nativo (Appium) o Hibrido (WebView). Nunca asumir el contexto. Mobile y Web no son intercambiables y no comparten APIs.
