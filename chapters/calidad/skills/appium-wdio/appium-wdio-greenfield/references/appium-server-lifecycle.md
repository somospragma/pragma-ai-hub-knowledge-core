# Ciclo de vida del servidor Appium y de los emuladores

## El principio

**El framework levanta lo que necesita.** Un arquetipo cuyo README dice "abre otra terminal y ejecuta appium" funciona en la máquina de quien lo escribió y falla en CI, en la máquina del que llega nuevo y en la corrida nocturna. El servidor Appium y el emulador son dependencias de la suite, y una suite gestiona sus dependencias.

## Verificar antes de arrancar

Arrancar a ciegas produce dos servidores compitiendo por el puerto. La verificación es por puerto en escucha, no por proceso: un proceso `appium` zombi sin puerto abierto no sirve, y un puerto ocupado por otra cosa tampoco.

```typescript
async isRunning(port: number): Promise<boolean> {
  try {
    await spawnAsync(LSOF, ['-Pi', `:${port}`, '-sTCP:LISTEN', '-t']);
    return true;
  } catch {
    return false;
  }
}

async ensureRunning(port: number): Promise<void> {
  if (await this.isRunning(port)) {
    log.info(`Appium ya está corriendo en el puerto ${port}`);
    return;
  }
  await this.start(port);
}
```

En Windows el equivalente es `netstat -ano | findstr :{port}`. El gestor abstrae esa diferencia; el resto del arquetipo no la conoce.

## Arranque desacoplado con espera activa

```typescript
private async start(port: number): Promise<void> {
  spawn(APPIUM, ['--port', String(port), '--allow-insecure=uiautomator2:adb_shell'], {
    shell: false,
    detached: true,
    stdio: ['ignore', 'ignore', 'ignore']
  }).unref();

  for (let i = 0; i < 30; i++) {
    await sleep(1000);
    if (await this.isRunning(port)) {
      log.info(`Servidor Appium iniciado en el puerto ${port}`);
      return;
    }
  }
  throw new Error(`Appium no pudo iniciar en el puerto ${port} en 30 segundos`);
}
```

Cuatro decisiones deliberadas:

- **`detached: true` con `unref()`**: el servidor sobrevive al proceso de la suite. Sin esto, terminar la corrida mata el servidor a mitad del teardown y las sesiones quedan colgadas en el dispositivo.
- **`shell: false`**: nada de lo que se pasa aquí viene de entrada del usuario, y no se interpreta por un shell.
- **Espera activa con límite**: sondear el puerto cada segundo hasta un máximo. Un `sleep` fijo es una apuesta: demasiado corto falla en máquinas lentas, demasiado largo suma medio minuto a cada corrida.
- **`--allow-insecure`** solo con las funciones que el arquetipo usa de verdad. Habilitarlo en bloque abre capacidades que la suite no necesita.

## Puertos y paralelismo

Dos sesiones de plataformas distintas contra el mismo puerto se estorban. La asignación por plataforma resuelve el caso común —Android e iOS en paralelo— sin gestor de puertos:

```typescript
getPort(platform: 'ios' | 'android'): number {
  const base = Number(process.env.APPIUM_PORT ?? 4723);
  const parallel = Number(process.env.PARALLEL ?? 1);
  if (parallel >= 2) {
    return platform === 'ios' ? base : base + 1;
  }
  return base;
}
```

Con paralelismo mayor, cada worker necesita su puerto y su dispositivo: la asignación pasa a ser un pool, y el arquetipo debe declarar cuántos dispositivos hay disponibles. Un paralelismo mayor que el número de dispositivos produce fallos por sesión rechazada que se confunden con fallos de la app.

## Emulador Android

```typescript
async ensureAndroidDeviceReady(): Promise<void> {
  if (process.env.ANDROID_DEVICE_TYPE !== 'emulator') return;   // físico: nada que arrancar

  const avd = process.env.ANDROID_EMULATOR_NAME!;
  const salida = await spawnAsync(ADB, ['devices']).catch(() => '');
  if (salida.includes('emulator') && salida.includes('device')) {
    log.info('El emulador ya está corriendo');
    return;
  }
  await this.startAndroidEmulator(avd);
}

private async startAndroidEmulator(avd: string): Promise<void> {
  spawn(EMULATOR, ['-avd', avd], { shell: false, detached: true, stdio: 'ignore' }).unref();

  for (let i = 0; i < 60; i++) {
    await sleep(2000);
    const salida = await spawnAsync(ADB, ['devices']).catch(() => '');
    if (salida.includes('emulator') && salida.includes('device')) {
      log.info('Emulador iniciado');
      return;
    }
  }
  throw new Error('El emulador no pudo iniciar en 2 minutos');
}
```

La condición de listo es **el estado `device` en `adb devices`**, no la aparición de la ventana. Un emulador en estado `offline` está arrancando: crear la sesión contra él falla con un error que no menciona el arranque.

Para suites largas conviene endurecer la condición esperando a que el sistema termine de arrancar:

```bash
adb wait-for-device shell 'while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done'
```

Un emulador en estado `device` pero sin el arranque completo acepta la sesión y falla al buscar el primer elemento, porque el lanzador todavía no está.

## Rutas de los binarios

Todo binario externo se resuelve por variable de entorno con valor por defecto:

```typescript
const ADB      = process.env.ADB_PATH      ?? 'adb';
const APPIUM   = process.env.APPIUM_PATH   ?? 'appium';
const EMULATOR = process.env.EMULATOR_PATH ?? 'emulator';
```

En CI el PATH rara vez trae el SDK de Android. Sin esta indirección, el arquetipo funciona en local y falla en el pipeline con un `command not found` que aparece a mitad del primer hook.

## Apagado

El servidor levantado por la suite se apaga en `AfterAll` **solo si lo levantó la suite**. Matar un servidor que ya estaba corriendo interrumpe la sesión de depuración de quien lo tenía abierto:

```typescript
// El gestor recuerda si fue él quien arrancó el proceso
if (appiumServerManager.startedByUs) {
  await appiumServerManager.stop();
}
```

En CI da igual porque el contenedor muere; en local es la diferencia entre una herramienta usable y una molesta.

## Diagnóstico

| Síntoma | Verificación | Causa habitual |
|---|---|---|
| Timeout conectando al servidor | `curl http://127.0.0.1:4723/status` | El servidor no arrancó, o arrancó en otro puerto |
| `Could not find a driver for automationName` | `appium driver list --installed` | Falta instalar el driver de la plataforma |
| Puerto ocupado por otro proceso | `lsof -Pi :4723 -sTCP:LISTEN` | Un servidor de una corrida anterior quedó vivo |
| El emulador aparece pero la sesión falla | `adb devices` muestra `offline` | Todavía está arrancando: falta esperar el arranque completo |
| Funciona en local, falla en CI | `which adb appium` en el runner | El PATH del runner no trae el SDK ni Appium |
