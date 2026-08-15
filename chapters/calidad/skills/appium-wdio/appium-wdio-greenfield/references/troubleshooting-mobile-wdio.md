# Fallos conocidos: causa y solución

Orden de diagnóstico, siempre el mismo: **evidencia primero** (screenshot, árbol de pantalla, contexto activo, log), hipótesis después. Ver `mobile-evidence-and-video.md`.

## Arranque de sesión

| Síntoma | Causa | Solución |
|---|---|---|
| Timeout conectando al servidor Appium | El servidor no está corriendo, o está en otro puerto | El gestor del framework debe verificar y arrancar. Comprobar con `curl http://127.0.0.1:4723/status` |
| `Could not find a driver for automationName` | El driver de la plataforma no está instalado | `appium driver install uiautomator2` / `xcuitest` |
| Sesión rechazada por puerto ocupado | Un servidor de una corrida anterior quedó vivo | `lsof -Pi :4723 -sTCP:LISTEN -t` y terminar el proceso |
| Funciona en local, falla en CI con `command not found` | El PATH del runner no trae el SDK de Android ni Appium | Rutas de binarios por variable de entorno |
| El emulador aparece pero la sesión falla | Estado `offline`: sigue arrancando | Esperar el arranque completo, no solo el estado `device` |

## iOS y WebDriverAgent

| Síntoma | Causa | Solución |
|---|---|---|
| Timeout al crear la sesión, sin más detalle | WebDriverAgent está compilando por primera vez y el timeout es el de por defecto | Subir `wdaLaunchTimeout` y `wdaConnectionTimeout` a los valores de `capabilities-matrix-ios.md` |
| Fallo de firma al instalar WebDriverAgent | Falta el equipo de firma, o el identificador por defecto no es firmable con esa cuenta | Declarar `xcodeOrgId`, `xcodeSigningId` y `updatedWDABundleId` |
| El error de sesión no dice nada útil | El log de Xcode está oculto | `showXcodeLog: true` y volver a correr |
| Falla intermitente al arrancar la sesión en dispositivo físico | El arranque de WebDriverAgent es intermitente por naturaleza | `wdaStartupRetries` con intervalo explícito |
| La primera corrida del día falla y las siguientes pasan | Recompilación de WebDriverAgent tras reinicio o actualización | Esperado. Compilarlo como paso previo del pipeline y usar `usePrebuiltWDA: true` |
| El dispositivo pide confiar en el certificado a mitad de la corrida | El perfil de desarrollo no está confiado en el dispositivo | Confiar manualmente una vez en los ajustes del dispositivo |

## Android

| Síntoma | Causa | Solución |
|---|---|---|
| No encuentra el dispositivo | El UDID está fijado y ya no corresponde | Autodetección con `adb devices` filtrando por estado `device` |
| `device unauthorized` | El dispositivo no aceptó la depuración por USB | Aceptar el diálogo en el dispositivo y volver a conectar |
| Un diálogo de permisos bloquea el primer escenario | Los permisos no se conceden al instalar | `autoGrantPermissions: true` |
| El primer escenario pasa y el segundo falla | Estado de la app persistido entre sesiones | Revisar `noReset` / `fullReset` con la tabla de decisión |
| El clic golpea el teclado en vez del botón | El teclado tapa el elemento siguiente | Ocultar el teclado tras escribir |
| El texto se escribe incompleto o desordenado | Autocompletado o campo con máscara | Tocar el campo, limpiar, escribir, verificar el valor resultante |
| Cada `find` o `getPageSource` tarda segundos, y alguno decenas de segundos | La UI nunca queda "idle" para el driver: animaciones activas o árbol de accesibilidad que emite en continuo. Se agota `waitForIdleTimeout` (default 10 s) en cada comando | Capabilities anti-idle del perfil local, en `capabilities-matrix-android.md`. Diagnóstico en `local-run-stalls-and-host-timers.md` |
| El arranque de cada sesión pierde ~5 s sin explicación | `adb connect` invocado con el serial de un dispositivo USB: adb lo resuelve como hostname y bloquea sincrónicamente | Invocar `connect` solo si el UDID tiene forma `host:puerto` |

## Cuelgues en ejecución local

| Síntoma | Causa | Solución |
|---|---|---|
| El escenario "se queda pegado" a ratos y muere por timeout, pero en la granja pasa siempre | Varias causas distintas comparten este síntoma. **No concluir sin medir** | Protocolo de huecos entre requests de `local-run-stalls-and-host-timers.md`: separa dispositivo, app y proceso cliente en una sola corrida |
| El log del servidor muestra un hueco de decenas de segundos **sin un solo request**, con el servidor respondiendo en milisegundos antes y después | El proceso cliente quedó suspendido entre comandos: los `setTimeout` internos no despiertan a tiempo | Temporizador recurrente `unref()`-eado durante la corrida, solo en modo local. Ver `local-run-stalls-and-host-timers.md` |
| No pasa nada en el dispositivo y el runner termina sin ejecutar | Script que anida otro script y pierde los argumentos por el camino | El script invoca el binario del runner directo. Ver `[[calidad-appium-wdio-run-and-profiles]]` |
| El fallo desaparece al agregar instrumentación para diagnosticarlo | La instrumentación cambió la condición que producía el fallo. **Es el hallazgo, no un estorbo** | A/B con la instrumentación como única variable, varias corridas por brazo. Ver `[[calidad-failure-triage-and-classification]]` |

## Webviews y contextos

| Síntoma | Causa | Solución |
|---|---|---|
| Elemento nativo no encontrado en un escenario web | La sesión está en contexto de webview | `switchContext('NATIVE_APP')` antes de tocarlo |
| Un selector CSS no encuentra nada | La sesión está en contexto nativo | Cambiar al webview correcto por nombre exacto |
| `getContexts()` solo devuelve el contexto nativo en iOS | Web Inspector desactivado en el dispositivo | Activarlo en los ajustes de Safari del dispositivo |
| El webview conecta pero no responde a comandos | Incompatibilidad entre Chromedriver y la versión de Chrome o WebView | Fijar el Chromedriver de la major correspondiente |
| Un error de versiones de Chromedriver sin decir cuál | El automático descargó una versión que no corresponde | Fijar el binario por ruta explícita |
| El diálogo de enlace universal no aparece | La URL inicial es una página en blanco, o el driver ya aceptó el diálogo | URL real y desactivar la aceptación automática de alertas |
| El webview tarda en aparecer tras navegar | Se registra después de la navegación | Espera activa sobre `getContexts()` |

## Cucumber y resolución de steps

| Síntoma | Causa | Solución |
|---|---|---|
| `Ambiguous step definition` | Dos definiciones matchean el mismo texto | Sufijo de plataforma, y eliminar el duplicado. Ver `[[calidad-cucumber-bdd-conventions]]` |
| Un step queda `undefined` con la implementación escrita | El perfil no carga esa carpeta, o el sufijo no coincide entre feature y definición | Revisar los globs del perfil y el texto exacto |
| Un escenario nunca corre y nadie lo nota | Falta el tag de plataforma, o tiene `@ignore` | Propiedad 6 de las verificaciones estáticas |
| El escenario corre en el browser equivocado | Falta el tag de browser en un escenario web | Propiedad 7 |
| El reporte de una plataforma pisa el de otra | Los perfiles escriben al mismo directorio | Un directorio de reporte por perfil |

## Ejecución en device farm

| Síntoma | Causa | Solución |
|---|---|---|
| La sesión queda minutos esperando y expira | La petición está encolada porque el modelo está ocupado | Cancelación de cola y salto al siguiente dispositivo |
| Todos los escenarios aparecen como completados sin distinción | No se reportó el estado a la granja | Marcar el estado explícitamente en el teardown |
| Un fallo remoto no se puede investigar | No se adjuntó la URL de la sesión | Adjuntarla siempre, junto al dispositivo y la versión de sistema |
| Falla solo en una versión de sistema | Defecto real de compatibilidad, o selector dependiente de versión | El dispositivo asignado debe estar en la evidencia para poder afirmarlo |
| La corrida siguiente no encuentra dispositivos | Sesiones que no se cerraron | Cerrar todas las sesiones en el teardown, con `allSettled` |

## Estabilidad de la suite

| Síntoma | Causa | Solución |
|---|---|---|
| Fallo que no se reproduce en local | Tiempos distintos entre dispositivo real y emulador | Esperas por condición, nunca fijas |
| Fallo intermitente en el mismo step | Espera del camino feliz cuando hay varios desenlaces legítimos | Esperar cualquiera de los desenlaces posibles |
| La suite pasa aislada y falla completa | Estado compartido entre escenarios | Todo el estado en el World; nada en variables de módulo |
| Un elemento visible al que el clic no le llega | Contenedor que intercepta el evento | Tap por coordenadas del centro, documentando por qué |
| El escenario falla en el primer step con el driver sin definir | El tag de plataforma no tiene hook que lo atienda | Verificar que el perfil está en la lista de perfiles |

## Antes de escalar

Antes de reportar un defecto de la aplicación, descartar en este orden:

1. ¿El contexto activo es el correcto?
2. ¿El selector existe en el árbol de pantalla capturado?
3. ¿El elemento está visible y habilitado, o solo presente?
4. ¿El escenario anterior dejó estado?
5. ¿Ocurre en más de un dispositivo o versión de sistema?

Un fallo que sobrevive a las cinco preguntas, con evidencia adjunta, es un defecto reportable. Clasificación y escalado según `[[calidad-failure-triage-and-classification]]`.
