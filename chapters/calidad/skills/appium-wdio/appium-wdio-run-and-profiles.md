---
id: calidad-appium-wdio-run-and-profiles
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium-wdio]
description: Cómo ejecutar un arquetipo Appium WebdriverIO por perfil, filtrar por tags y combinar plataforma, modo de ejecución y tipo de dispositivo.
tags: [appium, webdriverio, cucumber, ejecucion, perfiles, tags]
---

# Ejecución por perfiles y filtros por tag

## Instrucción

El comando de ejecución de este stack combina cuatro ejes independientes. Documentarlos por separado es lo que evita el README con veinte comandos que nadie mantiene.

| Eje | Cómo se expresa | Ejemplo |
|---|---|---|
| Plataforma | Perfil de cucumber-js | `--profile android` |
| Subconjunto de escenarios | Expresión de tags | `--tags '@smoke and not @ignore'` |
| Dónde corre | Variable de entorno | `EXECUTION_MODE=cloud` |
| Qué dispositivo | Variable de entorno | `ANDROID_DEVICE_TYPE=emulator` |

```bash
# Base: una plataforma completa
npx cucumber-js --config cucumber.config.js --profile android

# Con filtro de tags
npx cucumber-js --config cucumber.config.js --profile ios --tags '@smoke and not @ignore'

# Cambiando dónde y en qué corre, sin tocar el comando base
EXECUTION_MODE=cloud npm run test:android
ANDROID_DEVICE_TYPE=emulator npm run test:android
IOS_DEVICE_TYPE=simulator npm run test:ios
```

## Reglas de ejecución

1. **El perfil manda sobre el tag.** El perfil decide qué definiciones se cargan; el tag solo filtra escenarios dentro de lo cargado. Un `--tags '@ios'` sobre el perfil `android` no ejecuta nada: los steps con sufijo iOS no están cargados.
2. **Nunca fijar tags en el archivo de configuración de un perfil más allá del tag de plataforma y la exclusión.** Un perfil que trae `@smoke` fijo hace que el filtro de la línea de comandos no pueda ampliar el alcance, y la suite de regresión no corre nunca.
3. **Todo perfil filtra el tag de exclusión** (`and not @ignore`). Sin eso, los escenarios deshabilitados corren igual.
4. **Un directorio de reporte por perfil.** Dos perfiles que escriben al mismo sitio hacen que el último pise al anterior, y el reporte consolidado miente.
5. **El paralelismo está limitado por los dispositivos disponibles.** Un `parallel: 4` con dos dispositivos produce fallos por sesión rechazada que parecen fallos de la app.

## Expresiones de tags útiles

```bash
--tags '@smoke and not @ignore'                    # camino crítico
--tags '@regression and not @ignore'               # suite completa
--tags '@NT-31233'                                 # un caso concreto del ALM
--tags '@android and @smoke'                       # intersección
--tags '@smoke and not @flaky'                     # excluir inestables conocidos
--tags '(@smoke or @regression) and not @ignore'   # unión con exclusión
```

Para diagnosticar sin ejecutar nada contra un dispositivo:

```bash
npx cucumber-js --profile android --dry-run
```

El modo dry resuelve todos los steps sin ejecutarlos: detecta `undefined` y `ambiguous` en segundos y sin dispositivo. Es el chequeo más barato del stack y debe correr en cada pull request.

## Verificación previa a una corrida real

```bash
npx tsc --noEmit                                   # tipos
npx eslint 'src/**/*.ts' --max-warnings 0          # estilo
npx cucumber-js --profile android --dry-run        # resolución de steps
adb devices                                        # dispositivo Android en estado 'device'
xcrun xctrace list devices                         # dispositivo iOS visible
curl -s http://127.0.0.1:4723/status               # servidor Appium (si ya está levantado)
```

Los cuatro primeros no necesitan dispositivo. Correr la suite sin haberlos pasado es gastar minutos de dispositivo en errores que se detectan en segundos.

## Qué documentar en el README

Por cada perfil soportado: comando, prerequisitos de entorno, variables de entorno obligatorias, ruta del reporte y limitaciones conocidas (qué flujos no se pueden validar en simulador, qué requiere dispositivo físico).

Un README que solo lista comandos sin prerequisitos hace que el primer intento de quien recibe el proyecto falle, y ese primer fallo es el que decide si la suite se adopta o se abandona.
