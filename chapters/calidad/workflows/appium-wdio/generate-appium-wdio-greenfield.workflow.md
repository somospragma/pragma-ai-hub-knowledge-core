---
id: calidad-generate-appium-wdio-greenfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [appium-wdio]
description: Genera desde cero un arquetipo Appium multi-plataforma en TypeScript con WebdriverIO y cucumber-js, ejecutable de primera.
tags: [appium, webdriverio, typescript, cucumber, greenfield, mobile]
---

# Generar arquetipo Appium WebdriverIO

## Cuándo usar este workflow

Cuando el router `[[calidad-route-test-generation]]` resolvió intent mobile-only sobre stack Node/TypeScript en modo greenfield. Para el stack Appium sobre JVM, usar `[[calidad-generate-appium-screenplay-android]]`. Si el intent requiere además cubrir web, web_movil, desktop o api con el mismo vocabulario Gherkin (no solo mobile), usar `[[serenity-wdio-greenfield]]` en su lugar — comparten runtime Node/WebdriverIO pero son arquetipos distintos.

## Pasos

### Paso 0 — Verificar que `appium-core` está instalado

Este stack **depende de `appium-core`**, que se instala aparte. Antes de cualquier otra cosa, comprueba que el workspace tiene los tres bundles del core: `[[calidad-mobile-locator-resolution]]`, `[[calidad-mobile-interactions]]` y `[[calidad-appium-apk-auto-discovery]]`.

Si faltan, **detente y díselo al usuario** con el comando exacto:

```
pragma-ai init --ide <ide> --chapter calidad --stack appium-core
```

No es una recomendación: sin el protocolo de resolución de locators se generan selectores plausibles en vez de verificados, y eso produce una suite verde que no prueba nada. Si el usuario decide continuar sin el core, déjalo declarado en la traza del pipeline y en el delivery gate como una carencia asumida.

### Paso 1 — Validar inputs

Aplica `[[calidad-appium-wdio-validate-inputs-prompt]]`. Obligatorios: `project_name`, `output_path`, `platforms`, `app_source`, `execution_mode`. Si falta uno, detente y solicítalo con `[[calidad-mandatory-inputs-protocol]]`.

Si `platforms` incluye iOS, verifica el entorno: macOS con Xcode, driver XCUITest instalado y, para dispositivo físico, credenciales de firma. Sin eso, el perfil iOS se genera y se documenta pero no se ejecuta, y el resultado final es `partial`.

### Paso 2 — Resolver el estado del SUT

Aplica `[[calidad-sut-readiness-gate]]` y `[[calidad-ui-locator-map-contract]]`. Sin mapa de identificadores de interfaz, los selectores se generan diferidos y marcados como pendientes. **Un selector inventado produce una suite verde que no prueba nada**: es la forma más cara de fallar en este stack, porque el falso verde se descubre en producción.

### Paso 3 — Leer las references obligatorias

Abre las references de `[[calidad-appium-wdio-greenfield]]` y declara en el turno cuáles se leyeron. Como mínimo: estructura del proyecto, perfiles como datos, matriz de capabilities de cada plataforma solicitada, ciclo de vida del servidor Appium y selectores en test-data.

Las convenciones de la capa Cucumber vienen de `[[calidad-cucumber-bdd-conventions]]`.

### Paso 4 — Emitir la infraestructura

En este orden, persistiendo cada archivo con `[[calidad-streaming-files-protocol]]`:

1. `package.json` con un script por perfil y las variantes de modo y dispositivo.
2. `tsconfig.json` estricto.
3. `cucumber.config.js` con un perfil por plataforma solicitada, cada uno cargando hooks, carpetas compartidas y su propia carpeta de plataforma.
4. `.env.example` con todas las variables y ningún valor real.
5. Linter y formateador.

### Paso 5 — Emitir la capa de configuración y runtime

Constructores de capabilities por plataforma, gestor del servidor Appium, perfiles de plataforma como datos, motor genérico de conexión, servicios de evidencia y teardown.

Toda capability que varíe entre máquinas se lee de variable de entorno. Ningún identificador de dispositivo, equipo de firma ni credencial se escribe literal.

### Paso 6 — Emitir la capa de prueba

1. Clase base de objetos de pantalla con el repertorio de interacción.
2. Un objeto de pantalla por pantalla que la historia cubra.
3. Test-data por épica y plataforma base, con grupos de selectores en camelCase.
4. Catálogo de steps inicial.
5. Features con al menos dos escenarios ejecutables por plataforma solicitada, más los escenarios propuestos que se deriven de la historia, marcados como tales.
6. Definiciones de steps con sufijo de plataforma.
7. Hooks generados desde la lista de perfiles.

### Paso 7 — Health-check

En orden, deteniéndose en el primer fallo:

- [ ] `npx tsc --noEmit` sin errores.
- [ ] Linter sin errores ni advertencias.
- [ ] `npx cucumber-js --profile <principal> --dry-run` sin steps `undefined` ni `ambiguous`.
- [ ] Las 12 propiedades de `[[calidad-cucumber-bdd-conventions]]`.
- [ ] Verificación de entorno: servidor Appium alcanzable, dispositivo visible, drivers de Appium instalados.

Un fallo de entorno se reporta como blocker con su comando de remediación según `[[calidad-environment-blocker-evidence]]`, no como fallo de la suite.

### Paso 8 — Ejecutar el smoke

Aplica `[[calidad-test-execution-orchestration]]` con el perfil de la plataforma principal y el filtro de camino crítico. Si falla, `[[calidad-failure-triage-and-classification]]` y luego `[[calidad-test-self-correction-loop]]`, respetando `max_iterations` y los guardrails anti-cheating del chapter.

Un smoke verde **no es el final**: siguen la suite completa, la verificación del reporte y el reporte ejecutivo.

### Paso 9 — Cerrar

- Reporte ejecutivo con `[[calidad-generate-executive-report]]`.
- Bloque de cierre con `[[calidad-delivery-gate-contract]]`.
- README con prerequisitos por plataforma, comando por perfil, filtros por tag, ruta del reporte y variables pendientes de completar.

## Criterios de finalización

- [ ] Todos los perfiles solicitados existen en la configuración, con sus scripts y su directorio de reporte propio.
- [ ] Cada plataforma solicitada tiene al menos dos escenarios ejecutables.
- [ ] Cero selectores en código: todos en test-data.
- [ ] Cero credenciales, identificadores de dispositivo o equipos de firma literales en cualquier archivo generado.
- [ ] El health-check del paso 7 pasó completo.
- [ ] El smoke se ejecutó al menos una vez y su resultado está reportado como `success`, `partial` o `failed`.
- [ ] Si alguna plataforma no se pudo ejecutar, está declarado explícitamente con el motivo y el comando para que lo corra el cliente.
- [ ] El catálogo de steps existe y refleja los steps compartidos generados.
- [ ] La traza del pipeline se actualizó al cerrar cada fase y el delivery gate se emitió con cero fases obligatorias pendientes.
