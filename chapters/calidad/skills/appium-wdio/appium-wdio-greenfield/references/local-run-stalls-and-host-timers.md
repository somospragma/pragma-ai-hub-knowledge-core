# Cuelgues en ejecución local: cómo separar el dispositivo del proceso que lo maneja

Este es el fallo que más sesiones consume en mobile local: el escenario "se queda pegado" a ratos y muere por timeout, pero **en la granja pasa siempre**. La conclusión fácil —"el dispositivo local no sirve, hay que correr en la granja"— es cara y casi siempre falsa: significa perder el ciclo rápido de desarrollo y depender de una infraestructura compartida para cualquier iteración.

Las causas reales se reparten en tres capas y **el síntoma es idéntico en las tres**. Separarlas es lo primero que hay que hacer, y se hace con una sola medición.

## El protocolo: medir los huecos entre requests

Appium es un servidor HTTP. Cada acción del test es un request. Eso convierte el diagnóstico en algo objetivo: si hay un hueco de 78 segundos, o el servidor tardó en responder, o **el cliente no envió nada**. Son dos mundos distintos y el log lo dice sin ambigüedad.

Levantar el servidor con timestamps y nivel de detalle:

```bash
appium --port 4723 --log-timestamp --log-level debug > appium.log 2>&1 &
```

Correr el escenario que se cuelga y leer el log buscando el hueco:

```
16:39:15:172 [HTTP] --> POST /session/.../appium/device/activate_app
16:39:15:353 [HTTP] <-- POST .../activate_app 200 181 ms - 14
                        <- 71 SEGUNDOS SIN UN SOLO REQUEST
16:40:26:583 [HTTP] --> POST /session/.../appium/device/terminate_app
```

La lectura del hueco decide toda la investigación:

| Lo que muestra el log | Capa responsable | Dónde seguir |
|---|---|---|
| El request salió y la **respuesta** tardó | Dispositivo, app o driver | Sección "la UI que nunca queda idle" |
| El servidor respondió en milisegundos y después **no hay request** | El proceso cliente (Node) | Sección "el proceso que se duerme" |
| Requests fluidos y el fallo es una aserción | Funcional o de datos | `[[calidad-failure-triage-and-classification]]` |

Un resumen útil del log completo, que ordena los huecos de mayor a menor y los ubica:

```bash
# Marca de tiempo de cada request y el hueco contra el anterior
grep -E '^\d{2}:\d{2}:\d{2}:\d{3} \[HTTP\] -->' appium.log
```

Con eso se obtienen tres números que valen más que cualquier hipótesis: **cantidad de requests, hueco máximo y hueco promedio**. Un hueco promedio de 0.25 s con un máximo de 7 s describe una corrida sana. Un máximo de 78 s con el servidor respondiendo en milisegundos describe un cliente bloqueado.

## El proceso que se duerme entre comandos

**Síntoma.** El servidor responde cada comando en milisegundos y luego el proceso pasa decenas de segundos sin enviar nada. Un `driver.pause(800)` tarda más de un minuto en despertar. Cucumber mata el step por timeout y el reporte culpa al step equivocado: el que estaba corriendo cuando venció el reloj, no el que se durmió.

**Causa.** Sin ningún temporizador recurrente activo, el proceso de Node puede quedar suspendido entre comandos por la gestión de energía del sistema operativo del host, y los `setTimeout` internos del cliente WebDriver no despiertan a tiempo. En macOS los sospechosos son App Nap y el *coalescing* de temporizadores; **el mecanismo exacto no está confirmado**, la relación causa-efecto sí.

**Contramedida.** Mantener un temporizador recurrente vivo durante la corrida, **solo en modo local**:

```typescript
/**
 * Sin un timer periódico activo, el proceso puede quedar suspendido entre
 * comandos: los `setTimeout` de `driver.pause()` no despiertan a tiempo y la
 * suite pasa decenas de segundos sin enviar un request, hasta que el runner
 * mata el step por timeout.
 */
export class EventLoopKeepAlive {
  private timer: NodeJS.Timeout | null = null;

  start(intervalMs = 500): void {
    if (this.timer) return;
    this.timer = setInterval(() => { /* no-op deliberado */ }, intervalMs);
    this.timer.unref();          // no impide que el proceso termine
  }

  stop(): void {
    if (!this.timer) return;
    clearInterval(this.timer);
    this.timer = null;
  }
}
```

Se arranca y se detiene en el ciclo de vida del framework, nunca en un step:

```typescript
if (isCloudMode()) {
  this.outputCapture.start();
} else {
  eventLoopKeepAlive.start();     // ver esta reference
}
```

Tres detalles que no son opcionales:

- **`unref()`**: sin él, el temporizador mantiene vivo el proceso y la suite no termina sola.
- **Solo en local**: en la granja el cliente conversa con un servidor remoto y el patrón no aparece. Encender el temporizador en la nube agrega ruido sin beneficio.
- **El no-op es deliberado y va comentado.** Un temporizador vacío sin explicación es exactamente lo que un refactor futuro elimina por "código muerto", devolviendo el fallo meses después.

**Es un workaround, no un fix, y así se documenta.** Se sostiene sobre la medición, no sobre la explicación.

## La UI que nunca queda idle

**Síntoma.** El request salió y la respuesta tardó una eternidad. Medido en campo: un solo `getPageSource` en arranque en frío tardó **111 segundos**; el siguiente, sobre la misma pantalla, 121 milisegundos.

**Causa.** UiAutomator2 espera a que la interfaz quede quieta antes de resolver cada comando, hasta agotar `waitForIdleTimeout`, cuyo valor por defecto es **10 000 ms**. Con animaciones activas —y con aplicaciones que emiten eventos de accesibilidad de forma continua, como las construidas sobre un árbol de semántica propio— ese estado quieto no llega nunca, y cada `find` paga la espera completa. En bucles de polling los bloqueos se acumulan hasta agotar el timeout del step.

**Por qué la granja no lo reproduce.** Los dispositivos de granja se entregan con las escalas de animación en `0`. Un dispositivo de escritorio las trae en `1.0`.

```bash
adb shell settings get global window_animation_scale       # 1.0 en local, 0 en la granja
adb shell settings get global transition_animation_scale
adb shell settings get global animator_duration_scale
```

**Contramedida**, en las capabilities del perfil local — detalle en `capabilities-matrix-android.md`:

```typescript
'appium:disableWindowAnimation': true,
'appium:settings[waitForIdleTimeout]': env('ANDROID_WAIT_FOR_IDLE_TIMEOUT', 100),
'appium:settings[actionAcknowledgmentTimeout]': env('ANDROID_ACTION_ACK_TIMEOUT', 300)
```

El efecto se verifica en el propio log del servidor, que imprime los valores aplicados al crear la sesión:

```
Applying the initial values to Appium settings parsed from W3C caps:
{"imageQuality":30,"waitForIdleTimeout":100,"actionAcknowledgmentTimeout":300}
```

Medido tras aplicarlo: los comandos más lentos de la corrida bajaron de ~1.7 s a ~0.7 s.

## Costos de arranque que parecen cuelgues

Tres cosas baratas de arreglar que se disfrazan del mismo síntoma:

**`adb connect` con un serial USB.** El comando solo aplica a dispositivos por red (`host:puerto`). Con el serial de un dispositivo conectado por cable, `adb` intenta resolverlo como nombre de host y bloquea unos **5 segundos sincrónicos** antes de fallar — bloqueando el event loop, en cada arranque:

```bash
$ time adb connect R58M88YBZCL
failed to resolve host: 'R58M88YBZCL': nodename nor servname provided
adb connect R58M88YBZCL  0.01s user 0.01s system 0% cpu 5.035 total
```

La resolución de UDID debe filtrar antes de invocarlo:

```typescript
if (/^[^\s]+:\d+$/.test(envUdid)) {          // solo host:puerto
  spawnSync(adbPath, ['connect', envUdid], { stdio: 'ignore', shell: false });
}
```

**El arranque del compilador.** En proyectos TypeScript sobre `ts-node`, la verificación de tipos en cada arranque duplica el tiempo hasta el primer step. Para el ciclo local, transpilar sin verificar (`TS_NODE_TRANSPILE_ONLY`) lo bajó de 40 s a 22 s. Los tipos se verifican aparte, con `tsc --noEmit`, que es donde corresponde: verlos fallar en el arranque de cada corrida no agrega información.

**Scripts que anidan el runner.** Un script que llama a otro script pierde los argumentos por el camino, y el síntoma es que **no pasa nada en el dispositivo** — indistinguible de un cuelgue. Ver `[[calidad-appium-wdio-run-and-profiles]]`.

## Cómo se cierra un diagnóstico de este tipo

La instrumentación que se agrega para medir **cambia lo que se mide**: un `setInterval` de heartbeat puesto para observar el event loop hace desaparecer el cuelgue del proceso dormido. Eso no invalida la medición, es el hallazgo — pero obliga a un A/B disciplinado antes de afirmar nada:

1. **Una sola variable** entre los dos brazos. Todo lo demás idéntico: mismo escenario, mismo dispositivo, misma app, mismo orden.
2. **Varias corridas por brazo.** Un cuelgue intermitente necesita al menos tres por lado para separarse del azar.
3. **La tabla se publica con los números crudos**, no con la conclusión:

| | Resultado | Duración |
|---|---|---|
| Con temporizador recurrente activo | 4/4 verdes | 65-75 s |
| Sin él | 3/3 colgadas | 138 s (muerte por timeout) |

4. **La verificación final corre sin la instrumentación.** Un verde obtenido con el andamio puesto no prueba que el fix funcione: prueba que el andamio funcionaba.

Detalle del protocolo en `[[calidad-failure-triage-and-classification]]` (consultar `references/re-run-protocol-for-determinism.md` en su subfolder).

## Cross-links

- `capabilities-matrix-android.md` — dónde viven las capabilities anti-idle y la resolución de UDID.
- `local-vs-cloud-execution.md` — qué difiere realmente entre local y granja, y cómo medirlo.
- `troubleshooting-mobile-wdio.md` — la tabla de síntomas que apunta acá.
- `[[calidad-mobile-locator-resolution]]` (consultar `references/flutter-under-appium.md` en su subfolder) — por qué un árbol de semántica propio nunca queda idle.
- `[[calidad-failure-triage-and-classification]]` — clasificación del fallo y protocolo de re-corridas.
