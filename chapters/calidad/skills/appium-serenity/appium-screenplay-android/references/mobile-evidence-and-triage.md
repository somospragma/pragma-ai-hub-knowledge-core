
# Evidencia y triage mobile — el protocolo de observación

Complementa a `[[calidad-failure-triage-and-classification]]` con lo específico de mobile. Origen: una PoC completa donde casi todos los diagnósticos erróneos se habrían descartado **mirando algo que ya existía**. La lección central: verificar antes de teorizar.

## Instrumentar ANTES de la primera corrida (no cuando ya estás a ciegas)

- Appium server SIEMPRE con logfile: `appium --log .evidence/appium-server.log` — sin él no hay forma de inspeccionar qué comandos viajaron.
- Mockoon con `--log-transaction` cuando se va a diagnosticar (registra bodies request/response).
- Hook `@After` de evidencia por fallo: screenshot **y page source** a `.evidence/failures/{escenario}.{png,xml}` (template en `templates.md`). El page source es diagnóstico de primera línea: revela `clickable=false`, resource-id ausentes, nodos duplicados — cosas que una imagen no muestra.
- `take.screenshots=AFTER_EACH_STEP` + `resized.image.width` en `serenity.conf`.
- Salidas de comandos largas: **a archivo y leer el archivo** — el output de terminal truncado, entremezclado o stale ya produjo diagnósticos falsos en campo. Nunca diagnosticar sobre un terminal reusado.

## El orden obligatorio del triage (ante CUALQUIER fallo de UI)

```
1. SCREENSHOT del momento del fallo — ¿qué se ve? ("los campos están vacíos" invalida
   en 5 segundos una teoría de horas sobre lectura de texto)
2. PAGE SOURCE parseado COMO ÁRBOL — nunca deducir topología de la indentación
   impresa (la indentación de un dump engaña; padre-hijo vs hermanos se consulta
   con XPath/parser, no a ojo). Contar nodos por candidato de locator: el único
   conteo sano es 1.
3. LOG DEL MOCK/BACKEND — ¿llegó la petición? ¿con qué body? Un payload
   {"documentNumber":"","pin":""} cierra en una línea el caso "no escribe".
4. RECIÉN ENTONCES, hipótesis.
```

Regla dura: **prohibido formular la segunda hipótesis sin haber completado los pasos 1-3**. Y prohibido marcar una causa como "confirmada" si la evidencia también es compatible con otra explicación (los campos vacíos en el page source del login sin interactuar son legítimamente vacíos — no prueban que "no se puede leer").

## Reglas de método (cada una costó horas en campo)

1. **Una variable por iteración.** Cambiar cinco cosas a la vez (locators + interactions + config) y medir el total produce regresiones inatribuibles. Adoptar patrones de un proyecto de referencia también es de a UNO, midiendo.
2. **Sonda mínima ante ambigüedad**: un test/script desechable con criterio de éxito NO interpretable ("¿el payload llegó al mock?", no "¿se ve el texto?"). Un runner de diagnóstico aislado es herramienta legítima (también evita el arrastre `thisIsAnExceptionBubblingUpFromAPreviousFailure`).
3. **Prior bayesiano de atribución**: entre "la API usada por miles de proyectos está rota" y "mi XPath recién inventado apunta al nodo equivocado", la probabilidad está abrumadoramente del lado de lo propio. Exigir evidencia extraordinaria antes de culpar a la librería (en campo: se construyeron 140 líneas de workaround sobre la tesis de que `Enter.theValue` fallaba; el locator era el problema).
4. **Una ausencia solo es evidencia si el generador corrió.** "No hay screenshots" con `aggregate` UP-TO-DATE no prueba nada; "cero peticiones al mock" consultado sin token de Admin API tampoco. Verificar la herramienta de medición antes de aceptar su resultado.
5. **Verificar el comando que se busca**: en W3C, `driver.pressKey()` viaja como `execute/sync` con `"script":"mobile: pressKey"` — buscar el endpoint legacy (`press_keycode`) da 0 ocurrencias y descarta en falso una solución que sí corría. Para verificar "¿la interacción se ejecutó?": grep del log de Appium por `execute/sync` + `mobile: *`, `click`, `setValue`.
6. **N intentos fallidos → cambiar de MÉTODO, no de intento.** Presupuesto explícito: a la tercera hipótesis fallida sobre la misma vía, parar y cambiar de instrumento (sonda, bisección, evidencia que no se ha mirado). No es perseverancia, es tunelización.
7. **Bisección de sistema antes de componente**: ante "el APK no lanza" — ¿otro paquete DE USUARIO del emulador resuelve su activity? (30 segundos). Si tampoco: el problema es el AVD (estado corrupto del PackageManager: `adb reboot` no basta, `-wipe-data` o cambiar de AVD), no el APK. Solo si otras apps sí lanzan, entrar al APK (DEX, plugin Kotlin, ABIs). Mismo principio para "no escribe": ¿ALGO se ejecuta? (si falta el SerenityReporter, ninguna estrategia corre y compararlas es ruido).
8. **Distinguir "el asset está mal" de "yo lo apliqué mal"** al reportar hallazgos — no contaminar el backlog del chapter con errores de aplicación propios.

## Checklist de verificación de reportería (correr en la PRIMERA corrida y tras cambios de build)

Los falsos verdes de reportería son indetectables leyendo el reporte; estas 5 comprobaciones los detectan en un minuto:

```bash
# 1. Serenity registró la corrida (sin SerenityReporter en cucumber.plugin: 0 JSONs y pasos "passed" sin ejecutar)
ls target/site/serenity/*.json | wc -l          # > 0

# 2. El conteo del reporte coincide con lo diseñado
#    (index.html "N tests" == escenarios del alcance; menos = pérdida silenciosa)

# 3. Scenario Outlines vivos (sin junit-vintage cada ejemplo muere en silencio)
#    tests= del XML de build/test-results == escenarios del cucumber.json

# 4. Hay screenshots (> 0) en el reporte

# 5. Prueba del generador: forzar UN fallo deliberado y verificar que el reporte
#    se genera igual y lo muestra en rojo (aggregate corre en fallo — finalizedBy)

# 6. Si el conteo NO coincide, revisar en este orden ANTES de culpar a la herramienta:
#    a) tag hardcodeado en el runner            grep -rn "FILTER_TAGS_PROPERTY_NAME" src/test
#    b) runner duplicado                        ls src/test/java/**/runners/
#    c) default de tags en build.gradle         grep -n "cucumber.filter.tags" build.gradle
#    d) aggregate re-ejecutando test            ./gradlew aggregate --dry-run
```

Cualquier discrepancia bloquea la declaración del smoke gate: un gate que lee un reporte falso no es un gate.

## "Limitación conocida" es una conclusión, no una excusa

Prohibido archivar una discrepancia como *"comportamiento conocido de la herramienta"* sin **causa raíz probada**. Ocurrió en campo: el reporte mostraba 1 test de 4 ejecutados y se cerró como limitación de Serenity — cuando la causa real (un default de tags en `build.gradle` que hacía re-ejecutar y sobrescribir en cada `aggregate`) estaba a un `grep` de distancia.

Para declarar una limitación se exige, en este orden: (1) causa raíz identificada con evidencia, (2) intento de corrección documentado, (3) referencia externa (issue/doc oficial) que la respalde, (4) **workaround verificado**. Sin las cuatro, la discrepancia es un **blocker abierto** y así se reporta en la traza y en el delivery gate. Un reporte que miente sobre cuántos tests corrieron invalida el gate que lo lee.

## Anti-cheating del triage (extensión al prototipo/mock)

Cuando el SUT es un prototipo o mock **bajo control del QA**, hay una tentación estructural de "resolver" el fallo ahí (ajustar la semántica del prototipo, relajar una rule del mock). Criterio único: **¿esta corrección seguirá siendo válida cuando el SUT sea el real?** Si no, es cheating aunque el verde sea inmediato — la estrategia de la prueba es lo que se mejora, no el SUT simulado. (Los cambios legítimos al prototipo son los que lo acercan a lo que la app real hará, verificados contra el design system o con el equipo dev.)
