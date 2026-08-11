---
id: calidad-appium-wdio-greenfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium-wdio]
description: Genera un arquetipo Appium multi-plataforma en TypeScript con WebdriverIO y cucumber-js, cubriendo Android, iOS, tablets y navegador móvil en local y en device farm.
tags: [appium, webdriverio, wdio, typescript, cucumber, mobile, android, ios, ipad, tablet]
---

# Appium WebdriverIO — Arquetipo multi-plataforma en TypeScript

## Cuándo aplicar

Cuando se solicita un proyecto **nuevo** de automatización mobile sobre stack Node/TypeScript: Appium como servidor, WebdriverIO como cliente del protocolo y cucumber-js como runner. Es el stack idiomático cuando el equipo ya vive en TypeScript, cuando la misma suite debe cubrir app nativa y navegador móvil, o cuando hay que soportar más de dos plataformas (teléfono, tablet, iPad, web móvil) sin multiplicar proyectos.

Para el stack Appium sobre JVM —Java, Screenplay, Serenity, Gradle— usar `[[calidad-appium-screenplay-android]]`. Son dos stacks distintos con el mismo servidor Appium debajo: no se mezclan en un mismo proyecto y la elección la determina el ecosistema del equipo, no la preferencia del agente. La desambiguación está en `[[calidad-intent-detection]]`.

Para extender un arquetipo TypeScript/WebdriverIO que ya existe, usar `[[calidad-appium-wdio-brownfield]]`.

Antes de activar este skill confirma intent con `[[calidad-intent-detection]]` y recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`. Aplica la perspectiva del chapter en `[[calidad-chapter-perspective]]`.

## Lectura obligatoria antes de emitir el primer archivo

Este SKILL es el índice. El detalle que hace que el proyecto arranque de primera vive en `references/`. **Abrirlas antes de generar** y declarar en el turno cuáles se leyeron, para que quede en la traza de `[[calidad-pipeline-state-tracking]]`:

| Reference | Para qué |
|---|---|
| `references/project-structure.md` | Árbol del arquetipo, perfiles de cucumber-js, tsconfig, scripts |
| `references/platform-profile-as-data.md` | El patrón que evita un hook por plataforma; base de todo lo demás |
| `references/capabilities-matrix-android.md` | Capabilities Android: UDID dinámico, chromedriver, nativo contra web |
| `references/capabilities-matrix-ios.md` | Capabilities iOS: simulador contra físico y el bloque WebDriverAgent completo |
| `references/appium-server-lifecycle.md` | Arrancar y verificar Appium y emuladores desde el propio framework |
| `references/selectors-in-testdata-json.md` | Selectores fuera del código, mapeo de plataformas derivadas |
| `references/screen-object-layer.md` | Capa de objetos de pantalla y su repertorio de interacción |
| `references/local-vs-cloud-execution.md` | Misma suite en local y en device farm, con fallback de dispositivos |
| `references/hybrid-web-native-context.md` | Contextos nativo y webview, deep links, diálogos del sistema |
| `references/mobile-evidence-and-video.md` | Video, screenshots y adjuntos al reporte |
| `references/i18n-locale-injection.md` | Idioma y región como dimensión de prueba |
| `references/troubleshooting-mobile-wdio.md` | Fallos conocidos con causa y solución verificadas |

Las convenciones de la capa Cucumber —catálogo de steps, sufijo de plataforma, tagging, propiedades verificables— son transversales y viven en `[[calidad-cucumber-bdd-conventions]]`. Este skill no las duplica: las consume.

## Reglas duras

1. **El servidor Appium es responsabilidad del framework, no del operador.** El arquetipo verifica si está corriendo y lo levanta si no. Un README que dice "abre otra terminal y ejecuta appium" es una suite que falla en CI. Ver `references/appium-server-lifecycle.md`.
2. **Cero selectores en código.** Van a `test-data/{plataforma-base}/{epica}.json` y se cargan por un loader tipado. La propiedad 3 de `[[calidad-cucumber-bdd-conventions]]` lo verifica por grep.
3. **Una plataforma nueva es un objeto de datos, no una clase.** Si agregar tablet exige escribir un hook y una estrategia, el diseño está mal. Ver `references/platform-profile-as-data.md`.
4. **`noReset` y `autoLaunch` se declaran explícitamente por plataforma**, nunca se heredan por descuido: son la causa raíz de la mitad de los fallos de arranque, y su valor correcto depende de si la suite instala la app o la asume instalada.
5. **iOS físico exige el bloque WebDriverAgent completo.** Sin `wdaLaunchTimeout`, `wdaConnectionTimeout` y reintentos explícitos, la primera sesión falla por timeout en cualquier máquina que no sea la del que lo escribió.
6. **En híbrido, el contexto se declara antes de tocar un elemento nativo.** Appium queda en `WEBVIEW` tras navegar; buscar un botón del sistema sin `switchContext('NATIVE_APP')` falla con "elemento no encontrado" y manda el diagnóstico al lado equivocado.
7. **La evidencia se instrumenta antes de la primera corrida**, no cuando algo falla: screenshot en fallo, volcado del árbol de pantalla y video. Un fallo en device farm sin evidencia es irreproducible.
8. **Los timeouts de creación de driver van por perfil**, en minutos, separados del timeout de step. Provisionar un dispositivo real tarda más que cualquier interacción.

## Instrucción

1. **Validar inputs** — Exige `project_name`, `output_path`, `platforms` (subconjunto de `android`, `ios`, `ipad`, `tablet`, `android-web`, `ios-web`), `app_source` (ruta al binario, o identificador de app ya instalada) y `execution_mode` (`local`, `cloud` o ambos). Si el intent incluye iOS físico, exige además equipo macOS con Xcode y credenciales de firma. Aplica `[[calidad-appium-wdio-validate-inputs-prompt]]` y detente si falta un obligatorio.
2. **Resolver el SUT y los locators** — Aplica `[[calidad-sut-readiness-gate]]` y `[[calidad-ui-locator-map-contract]]`. Sin mapa de identificadores, los selectores se generan diferidos y marcados, nunca inventados. Un selector inventado produce una suite verde que no prueba nada.
3. **Generar la estructura base** — Según `references/project-structure.md`: `package.json` con los scripts por plataforma, `tsconfig.json` estricto, `cucumber.config.js` con un perfil por plataforma, `.env.example` con **todas** las variables y ningún valor real, linter y formateador.
4. **Generar la capa de configuración** — Constructores de capabilities por plataforma según `references/capabilities-matrix-android.md` y `references/capabilities-matrix-ios.md`. Toda capability que cambie entre máquinas se lee de variable de entorno con valor por defecto documentado. Ningún identificador de dispositivo, equipo de firma ni credencial se escribe literal en el código.
5. **Generar la capa de runtime** — Gestor del servidor Appium, perfiles de plataforma como datos, motor genérico de conexión, servicios de teardown y de evidencia. Es el corazón del arquetipo y lo que permite que las plataformas siguientes cuesten un objeto.
6. **Generar la capa de objetos de pantalla** — `BaseScreen` con el repertorio de `references/screen-object-layer.md` y un objeto por pantalla de la historia cubierta, cargando selectores del test-data.
7. **Generar test-data** — Un JSON por épica y plataforma base, con grupos de selectores en camelCase. Las plataformas derivadas no tienen archivo propio: se resuelven por el mapa de plataformas.
8. **Generar features y definiciones** — Aplica `[[calidad-cucumber-bdd-conventions]]` completo: catálogo de steps inicial, sufijo de plataforma, tagging, nombres autoexplicativos. Siempre al menos dos escenarios ejecutables por plataforma solicitada (arranque de la app y flujo de autenticación o equivalente). Los escenarios aspiracionales derivados de la historia se marcan como propuestos y se declaran como tales.
9. **Cablear hooks** — Un `Before` por perfil generado desde la lista de perfiles, `AfterStep` de evidencia y `After` de teardown por plataforma, según `references/hooks-and-world-contract.md` de `[[calidad-cucumber-bdd-conventions]]`.
10. **Health-check antes de entregar** — En este orden, deteniéndose en el primer fallo:
    - `npx tsc --noEmit` sin errores.
    - Linter sin errores ni advertencias.
    - Todos los `.feature` parsean y **cada step resuelve**: correr con el runner en modo dry para detectar `undefined` y `ambiguous` sin necesidad de dispositivo.
    - Las 12 propiedades de `[[calidad-cucumber-bdd-conventions]]`.
    - Verificación de entorno: servidor Appium alcanzable, dispositivo o emulador visible, drivers de Appium instalados para las plataformas pedidas.
11. **Ejecutar el smoke** — Aplica `[[calidad-test-execution-orchestration]]` con el perfil de la plataforma principal. Si falla, `[[calidad-failure-triage-and-classification]]` y luego `[[calidad-test-self-correction-loop]]`, respetando los guardrails anti-cheating del chapter.
12. **Entregar** — Con `[[calidad-streaming-files-protocol]]`, trazabilidad por `[[calidad-test-evidence-and-traceability]]` y el bloque de `[[calidad-delivery-gate-contract]]`. El README documenta: prerequisitos por plataforma, comando por perfil, filtros por tag, ruta del reporte y qué variables de entorno hay que completar.

## Restricciones

- **No generar iOS sin macOS.** Si el entorno no tiene Xcode, se entrega el proyecto con el perfil iOS configurado y documentado, se declara que no se pudo ejecutar y se reporta `partial`. Nunca se degrada a Android en silencio.
- **No inventar identificadores de app, dispositivo ni firma.** Van como variables de entorno con marca de pendiente en el README y el comando exacto para obtener cada valor.
- **No mezclar este stack con el de Screenplay sobre JVM** en un mismo `output_path`.
- **No incluir credenciales, tokens ni identificadores de dispositivo reales** en ningún archivo generado. `.env.example` lleva nombres de variable y descripción; nunca valores.
- **No declarar éxito con un smoke verde**: el pipeline sigue con suite completa, verificación del reporte, triage y reporte ejecutivo.
