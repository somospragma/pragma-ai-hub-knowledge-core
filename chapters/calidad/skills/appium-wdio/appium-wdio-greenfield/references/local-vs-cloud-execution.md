# Ejecución local y en device farm con la misma suite

## El principio

La misma suite, los mismos escenarios y los mismos objetos de pantalla corren en un dispositivo sobre el escritorio y en una granja de dispositivos remota. Lo único que cambia son las capabilities y el punto de conexión, resueltos por una variable de entorno.

```bash
npm run test:android                      # local
EXECUTION_MODE=cloud npm run test:android # device farm
```

Si correr en la nube exige tocar código, la suite se bifurca y las dos ramas divergen: la de la nube se degrada porque nadie la corre en local, o al revés.

## El punto de bifurcación

Es uno solo, en el motor de conexión:

```typescript
async setup(world: HookWorld): Promise<void> {
  if (isCloudMode()) {
    await this.connectCloud(world, testName);
  } else {
    await this.connectLocal(world, testName);
  }
}
```

Todo lo demás —steps, pantallas, test-data, evidencia— es idéntico. Si aparece un `if (isCloudMode())` en un step, hay un error de diseño: esa diferencia pertenece al perfil de plataforma.

## Catálogo de dispositivos con fallback

Un dispositivo concreto de una granja puede estar ocupado, en mantenimiento o retirado del inventario. Fijar un modelo produce corridas que fallan por razones ajenas a la app.

```typescript
async resolveDevices(
  plataforma: 'ios' | 'android',
  fallback: DeviceInfo[],
  tipo?: 'phone' | 'tablet'
): Promise<DeviceInfo[]> {
  const disponibles = await getAvailableDevices(plataforma, tipo);
  if (disponibles.length > 0) {
    log.info(`${disponibles.length} dispositivos disponibles para ${plataforma}`);
    return disponibles;
  }
  log.warn(`No se pudo consultar el inventario de ${plataforma}, usando la lista de respaldo`);
  return fallback;
}
```

- El **catálogo remoto** se consulta al inicio: da la lista real de lo que hay libre ahora.
- La **lista de respaldo** vive en el código, por plataforma y tipo de dispositivo, y cubre el caso de que la API del inventario no responda. Son modelos y versiones de sistema conocidos como estables, no una lista exhaustiva.

Luego se intenta en orden, quedándose con el primero que conecte:

```typescript
for (const device of await resolveDevices(...)) {
  try {
    capabilities.deviceName = device.deviceName;
    capabilities.platformVersion = device.platformVersion;
    driver = await connectWithQueueCancel(opciones, testName);
    world.device = device;             // queda en la evidencia del escenario
    break;
  } catch (err) {
    ultimoError = err as Error;
    log.warn(`No disponible: ${device.deviceName} ${device.platformVersion}`);
  }
}
if (!driver) throw ultimoError ?? new Error(profile.noDeviceErrorMessage);
```

El dispositivo que finalmente se usó se registra en el World y se adjunta al reporte. Sin ese dato, un fallo que solo ocurre en una versión de sistema concreta es indiagnosticable.

## Cancelación de la sesión encolada

Cuando todos los dispositivos de un modelo están ocupados, la granja **encola** la petición en vez de rechazarla. El cliente se queda esperando minutos por un dispositivo que quizá nunca se libere, mientras hay otros modelos libres.

```typescript
async connectWithQueueCancel(
  opciones: RemoteOptions,
  testName: string,
  intervaloMs = 20_000
): Promise<WebdriverIO.Browser> {
  let cancelada = false;
  let conectado = false;

  const timer = setInterval(async () => {
    if (conectado) return;
    const seCancelo = await cancelQueuedSession(testName);
    if (seCancelo) {
      if (conectado) return;                 // conectó mientras esperábamos la respuesta
      cancelada = true;
      log.warn(`Sesión en cola cancelada para ${testName}, probando el siguiente dispositivo`);
    }
  }, intervaloMs);

  try {
    const driver = await remote(opciones);
    conectado = true;
    clearInterval(timer);
    return driver;
  } catch (err) {
    clearInterval(timer);
    if (cancelada) throw new Error(`Dispositivo en cola cancelado: ${(err as Error).message.split('\n')[0]}`);
    throw err;
  }
}
```

Dos detalles que parecen redundantes y no lo son:

- **La doble comprobación de `conectado`**, antes y después de la llamada de cancelación: hay una ventana en la que la sesión se asigna mientras la petición de cancelación viaja. Sin ella, se cancela una sesión ya activa y el escenario muere con un error sin relación aparente.
- **`clearInterval` en ambas ramas**: un temporizador vivo tras el fallo sigue cancelando sesiones de escenarios posteriores.

El efecto conjunto: en vez de esperar por un modelo ocupado, la suite salta al siguiente disponible en decenas de segundos.

## Capabilities específicas de la granja

Las granjas exigen un bloque propio de capabilities con credenciales, nombre de build y opciones de captura. Ese bloque se construye aparte y se mezcla con las de la plataforma:

```typescript
{
  'cloud:options': {
    username: env('CLOUD_USERNAME'),
    accessKey: env('CLOUD_ACCESS_KEY'),
    build: world.buildName,          // agrupa la corrida completa
    name: testName,                  // identifica el escenario
    project: env('CLOUD_PROJECT'),
    video: true,
    network: true,                   // captura de tráfico para diagnóstico
    deviceLog: true
  }
}
```

Las credenciales van **siempre** por variable de entorno. Un valor literal en el código es una fuga que sobrevive en el historial de git aunque se borre después.

El nombre de build agrupa todos los escenarios de una corrida en el panel de la granja: sin él, cada escenario aparece suelto y el reporte es inservible en suites grandes.

## Reporte de estado y evidencia

La granja no sabe si el escenario pasó: hay que decírselo, o todo queda marcado como "completado" sin distinción.

```typescript
await driver.execute(`cloud-status=${resultado === 'PASSED' ? 'passed' : 'failed'}`);
```

Y la URL de la sesión se adjunta al reporte de Cucumber, que es lo que convierte un fallo remoto en algo investigable:

```typescript
world.attach(urlSesion, 'text/uri-list');
world.attach(`Dispositivo: ${device.deviceName} ${device.platformVersion}`, 'text/plain');
```

## Cuándo cada modo

| | Local | Device farm |
|---|---|---|
| Desarrollo de escenarios nuevos | Sí: ciclo rápido, depuración con el dispositivo delante | No |
| Matriz de versiones de sistema y modelos | No | Sí: es su razón de ser |
| Pipeline de integración continua | Solo con emuladores en el runner | Sí |
| Flujos con biometría, cámara, push | Dispositivo físico local | Según lo que exponga la granja |
| Diagnóstico de un fallo intermitente | Sí | Con el video y el log de la sesión |

El modo se declara en el delivery gate junto al resultado: una suite verde en emulador local no certifica lo mismo que una verde sobre la matriz de dispositivos reales.
