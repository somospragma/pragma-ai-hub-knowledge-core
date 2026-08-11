---
id: calidad-appium-wdio-brownfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium-wdio]
description: Extiende un arquetipo Appium multi-plataforma en TypeScript con WebdriverIO y cucumber-js respetando sus convenciones, sin tocar su infraestructura.
tags: [appium, webdriverio, typescript, cucumber, brownfield, mobile, convenciones]
---

# Appium WebdriverIO — Extensión de arquetipo existente

## Cuándo aplicar

Cuando el cliente entrega un proyecto **ya inicializado** sobre TypeScript, WebdriverIO y cucumber-js, y pide agregar cobertura o mantener la existente:

- Escenarios nuevos para una historia, en una o varias de las plataformas que el arquetipo ya soporta.
- Objetos de pantalla, definiciones de steps o grupos de selectores nuevos.
- Actualización de selectores tras un cambio de interfaz.
- Habilitar una plataforma nueva sobre la infraestructura existente (agregar tablet a un arquetipo que ya cubre teléfono).
- Refactor localizado, sin reescribir hooks, perfiles ni configuración.

Si el proyecto no existe todavía, usar `[[calidad-appium-wdio-greenfield]]`. Si el proyecto es Appium sobre JVM con Screenplay, usar `[[calidad-appium-brownfield]]`. La decisión entre modos está en `[[calidad-brownfield-vs-greenfield]]`.

Antes de activar este skill confirma intent con `[[calidad-intent-detection]]` y recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`. Aplica la perspectiva del chapter en `[[calidad-chapter-perspective]]`.

## Lectura obligatoria antes de tocar el proyecto

El conocimiento técnico del stack vive en el bundle **greenfield**; brownfield no lo duplica, lo consume. Abrir antes de generar y declarar cuáles se leyeron:

| Reference | Para qué |
|---|---|
| `[[calidad-appium-wdio-greenfield]]` (`references/capabilities-matrix-android.md`, `capabilities-matrix-ios.md`) | Entender las capabilities del proyecto antes de juzgarlas |
| `[[calidad-appium-wdio-greenfield]]` (`references/hybrid-web-native-context.md`) | Contextos y diálogos del sistema, si la historia toca webviews |
| `[[calidad-appium-wdio-greenfield]]` (`references/selectors-in-testdata-json.md`) | Dónde van los selectores y cómo se resuelven las plataformas derivadas |
| `[[calidad-appium-wdio-greenfield]]` (`references/troubleshooting-mobile-wdio.md`) | Fallos conocidos antes de diagnosticar desde cero |
| `[[calidad-mobile-locator-resolution]]` | Resolver locators antes de tocar uno (stack `appium-core`) |
| `[[calidad-mobile-interactions]]` | Repertorio de interacción y aserciones (stack `appium-core`) |
| `[[calidad-cucumber-bdd-conventions]]` | Catálogo de steps, sufijo de plataforma, tagging, propiedades verificables |
| `references/convention-detection.md` | Qué detectar del proyecto y en qué orden (propio de este skill) |
| `references/selector-update-strategy.md` | Cómo actualizar selectores sin tocar lógica (propio de este skill) |

**Las convenciones del cliente siempre mandan** sobre las del chapter: idioma de los steps, nomenclatura, estructura de carpetas, versiones, estilo. El chapter aporta el conocimiento técnico y los controles de calidad, nunca su estética.

## Instrucción

1. **Recolectar inputs** — Obligatorios: `project_root`, `change_type` (`new-scenario`, `new-screen`, `selector-update`, `new-platform`, `refactor`) y `change_description`. Condicionales según el tipo: `user_story` o `test_cases` para escenarios nuevos, `new_selectors` para actualización de selectores, `platform` para habilitar una plataforma. Si falta un obligatorio, detente y solicítalo.
2. **Inventariar el arquetipo antes de escribir una línea** — Aplica `references/convention-detection.md` completo. El resultado es un objeto de convenciones que gobierna todo lo que se genera después. Emitir código antes de este paso es la causa raíz del rechazo en revisión.
3. **Correr las verificaciones estáticas sobre el árbol completo, antes de tocar nada** — Las 12 propiedades de `[[calidad-cucumber-bdd-conventions]]`. Esto establece la **línea base**: separa lo que ya estaba roto de lo que uno rompa. Sin línea base, cualquier fallo posterior se atribuye al cambio.
4. **Construir o actualizar el catálogo de steps** — Si el proyecto no lo tiene, generarlo desde el código antes de agregar escenarios. Es la única forma de reutilizar en vez de duplicar, y de no provocar ambigüedades en épicas que no se están tocando.
5. **Clasificar cada step candidato** en `reuse`, `extend-platform`, `new-local` o `new-shared`, y **declarar la tabla en el turno** antes de generar. Es la traza de que el paso 4 se hizo de verdad.
6. **Generar solo lo solicitado**, según `change_type`:
   - `new-scenario`: feature nuevo o escenarios añadidos al existente respetando su estilo, definiciones solo de los steps clasificados como nuevos, y los grupos de selectores que falten.
   - `new-screen`: objeto de pantalla siguiendo el patrón de los existentes, su grupo de selectores en el test-data de cada plataforma base afectada, y los métodos que la historia necesita.
   - `selector-update`: aplica `references/selector-update-strategy.md`. Cambian valores en JSON; el código no se toca.
   - `new-platform`: perfil de plataforma, entrada en la configuración de perfiles, script de ejecución, y el mapeo de test-data si es una plataforma derivada. La infraestructura existente no se reescribe.
   - `refactor`: alcance literal de lo pedido, sin extender a archivos vecinos.
7. **Respetar la infraestructura** — No se tocan `cucumber.config.js` (salvo agregar un perfil, cuando ese es el pedido), `package.json`, `tsconfig.json`, hooks, gestor del servidor Appium ni motor de drivers. Si el cambio pedido exige tocar uno de ellos, **detente y explica por qué** antes de hacerlo.
8. **Verificar** — En este orden: compilación de tipos sin errores, linter limpio sobre los archivos tocados, todos los steps resuelven en modo dry (ni `undefined` ni `ambiguous`), y las 12 propiedades comparadas **contra la línea base del paso 3**. Cualquier propiedad que empeore respecto de la línea base es un blocker.
9. **Ejecutar lo generado** — Solo los escenarios nuevos o afectados, con el perfil de su plataforma. Si falla, `[[calidad-failure-triage-and-classification]]` y luego `[[calidad-test-self-correction-loop]]`, con los guardrails anti-cheating del chapter.
10. **Reportar y entregar** — Archivos tocados, steps reutilizados contra creados, resultado de la ejecución, hallazgos preexistentes detectados y no corregidos, y el bloque de `[[calidad-delivery-gate-contract]]`.

## Diagnóstico sin imposición

Al inventariar el arquetipo vas a encontrar defectos conocidos del stack. **Repórtalos con su evidencia y el fix sugerido; no los apliques por tu cuenta.** Corregir infraestructura ajena fuera del alcance pedido rompe la confianza y puede romper escenarios que no se estaban tocando. Callarlos deja al cliente con un falso verde que ya conocemos.

Los que más aparecen:

| Hallazgo | Por qué importa |
|---|---|
| Steps sin sufijo de plataforma | Ambigüedad garantizada al crecer las plataformas |
| Selectores literales en definiciones u objetos de pantalla | Un cambio de interfaz obliga a tocar código en varias plataformas |
| Un perfil que no carga las carpetas compartidas | Sus steps de autenticación quedan sin resolver |
| Perfiles que escriben el reporte al mismo directorio | La última plataforma pisa el reporte de la anterior |
| Escenarios sin tag de plataforma, o con dos | Nunca corren, o corren en el perfil equivocado |
| El servidor Appium asumido como ya levantado | Funciona en la máquina de quien lo escribió, falla en el pipeline |
| Credenciales, identificadores de dispositivo o equipos de firma literales en el código | Fuga que sobrevive en el historial del repositorio |
| Llamadas HTTP a servicios de terceros dentro de la clase base de pantallas | Convierte la clase base en un objeto que todo lo hace, e impide probar el framework |
| Escenarios con placeholder de trazabilidad sin asignar | Cobertura reportada que no está trazada al ALM |

## Restricciones

- **No reescribir infraestructura** ni "modernizar" lo que funciona. El alcance es literal.
- **No importar las convenciones del greenfield** a un proyecto existente. Si el cliente nombra sus archivos de otra forma, se siguen sus nombres.
- **No modificar steps existentes** para que encajen en el escenario nuevo: los consumen otras épicas. Si el comportamiento difiere, es un step nuevo.
- **No tocar escenarios de suites protegidas** (`@security`, `@contract`, `@compliance`, `@regulatory`) bajo ningún concepto, ni siquiera para corregirlos: guardrail anti-cheating maestro del chapter.
- **No declarar éxito sin haber ejecutado** lo generado. Si el entorno no permite ejecutar, se reporta `partial` con el motivo y el comando exacto para que lo corra el cliente.
