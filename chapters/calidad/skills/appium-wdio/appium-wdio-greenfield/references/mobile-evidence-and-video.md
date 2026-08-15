# Evidencia mobile: screenshots, árbol de pantalla y video

## Por qué se instrumenta antes de la primera corrida

Un fallo mobile sin evidencia obliga a reproducirlo, y reproducir en mobile cuesta un orden de magnitud más que en web: hay que tener el dispositivo, dejarlo en el estado previo y esperar el arranque. Si además el fallo ocurrió en un device farm o en la corrida nocturna, el dispositivo ya no existe.

La instrumentación se escribe **antes** de la primera ejecución, no cuando algo falla. Es lo que convierte un fallo en un diagnóstico de dos minutos.

## Orden de captura en un fallo

1. **Screenshot** — qué estaba en pantalla.
2. **Árbol de la pantalla** (`driver.getPageSource()`) — qué elementos existían y con qué atributos. Es lo que permite corregir un selector sin volver a correr.
3. **Contexto activo** — nativo o webview. Explica la mitad de los "elemento no encontrado".
4. **Log del dispositivo o del mock**, si aplica.
5. **Recién entonces**, la hipótesis.

Invertir el orden —hipótesis primero, evidencia después para confirmarla— es lo que produce ciclos largos de prueba y error sobre la causa equivocada.

```typescript
AfterStep(async function (this: HookWorld, { result, pickleStep }) {
  if (result?.status !== Status.FAILED || !this.driver) return;

  const captura = await this.driver.takeScreenshot();
  this.attach(await comprimir(captura), 'image/jpeg');

  const arbol = await this.driver.getPageSource();
  this.attach(arbol.slice(0, 100_000), 'text/plain');

  this.attach(`Contexto: ${await this.driver.getContext()}`, 'text/plain');
  this.attach(`Step: ${pickleStep.text}`, 'text/plain');
});
```

El árbol se trunca: en pantallas densas supera el megabyte y hace ilegible el reporte.

## Compresión de screenshots

Sin compresión, un reporte de doscientos escenarios con captura por paso pesa cientos de megabytes: no se abre, no se adjunta a un ticket y no se archiva.

```typescript
const comprimido = await sharp(Buffer.from(base64, 'base64'))
  .resize({ width: 720, withoutEnlargement: true })
  .jpeg({ quality: 60 })
  .toBuffer();
```

Complementariamente, el propio driver puede reducir la calidad en origen, que además acelera la captura:

```typescript
'appium:settings[imageQuality]': 30    // Android
'appium:screenshotQuality': 3          // iOS
```

Un screenshot de 720 píxeles de ancho al sesenta por ciento de calidad sigue siendo legible para diagnosticar un flujo. Guardar la resolución nativa del dispositivo es peso sin información adicional.

## Video

Dos estrategias, según lo que soporte la plataforma:

### Grabación nativa del driver

Funciona en Android y en simulador iOS. La graba el propio dispositivo y se recupera en base64 al detenerla.

```typescript
await driver.startRecordingScreen({ videoType: 'mp4', videoFps: 30, videoSize: '1280x720' });
// … escenario …
const base64 = await driver.stopRecordingScreen();
fs.writeFileSync(ruta, Buffer.from(base64, 'base64'));
```

Límite a tener presente: la grabación nativa tiene un tope de duración por sesión. En escenarios largos se corta sin aviso y el video termina antes que el fallo.

### Captura del flujo MJPEG

Necesaria en iOS físico, donde la grabación nativa es poco fiable. WebDriverAgent expone un flujo MJPEG que se captura con una herramienta externa:

```typescript
{ 'appium:mjpegServerPort': 9100, 'appium:mjpegServerFramerate': 10 }
```

```typescript
const proceso = spawn('ffmpeg', [
  '-y', '-f', 'mjpeg', '-r', '10',
  '-i', `http://localhost:${puerto}`,
  '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', rutaSalida
], { shell: false });
```

Al terminar el escenario se cierra el proceso con señal de interrupción, no con terminación forzada: `ffmpeg` necesita cerrar el contenedor o el archivo queda corrupto.

```typescript
proceso.kill('SIGINT');
await esperarCierre(proceso, 10_000);
```

La estrategia se declara en el perfil de plataforma (`videoStrategyKind`), y el teardown elige la implementación según lo que el perfil declaró. Ver `platform-profile-as-data.md`.

## Activación selectiva

Grabar siempre cuesta tiempo por escenario y espacio en disco. Se activa por variable de entorno, y se deja encendido en la corrida nocturna y en el device farm, donde reproducir es caro:

```typescript
if (process.env.RECORD_VIDEO !== 'true') return;
```

## El costo de la captura tiene un techo

La instrumentación de evidencia se paga en cada step, y en local —donde cada comando ya cuesta más que en la granja— puede pasar a dominar la corrida. El caso que más sorprende es el adorno visual: un realzador que dibuja un recuadro sobre el elemento usado **vuelve a consultar cada selector del step** para obtener su posición y tamaño. Con tres consultas por selector y varios selectores por step, son segundos por step que no aportan diagnóstico: el screenshot sin recuadro ya muestra la pantalla.

Tres reglas que mantienen la evidencia útil sin que se coma la corrida:

- **La captura reutiliza lo que el step ya resolvió**, nunca vuelve a buscar un elemento solo para adornar la imagen.
- **Lo cosmético se separa de lo diagnóstico** y se activa por variable de entorno, igual que el video. El screenshot y el árbol de pantalla son diagnóstico; el recuadro no.
- **Si la evidencia se sospecha del costo, se mide**: correr el mismo escenario con la captura encendida y apagada, y comparar. Sin ese número es una discusión de opiniones. El protocolo de A/B está en `[[calidad-failure-triage-and-classification]]`.

## Teardown: el orden importa

```typescript
async finalize(world: HookWorld, result?: ScenarioResult): Promise<void> {
  // 1. Detener y guardar el video (necesita la sesión viva)
  if (world.recordingStarted) await this.detenerVideo(world);

  // 2. Screenshot del fallo (necesita la sesión viva)
  if (result?.status === Status.FAILED && world.driver) await this.capturarFallo(world);

  // 3. Marcar el estado en la granja remota (necesita la sesión viva)
  if (world.device && world.driver) await this.reportarEstadoRemoto(world, result);

  // 4. Cerrar la sesión, siempre, al final
  await this.cerrarSesiones(world);
}
```

Cerrar la sesión primero deja sin evidencia justo el escenario que falló, que es el único cuya evidencia importa. Y cada paso va envuelto en captura de errores: un fallo guardando el video no debe enmascarar el fallo del escenario ni impedir que la sesión se cierre.

```typescript
private async cerrarSesiones(world: HookWorld): Promise<void> {
  const sesiones = [world.driver, world.driverAndroid, world.driverIos].filter(Boolean);
  await Promise.allSettled(sesiones.map(d => d!.deleteSession()));
}
```

`allSettled` y no `all`: si una sesión falla al cerrar, la otra debe cerrarse igual. Una sesión que no se cierra deja el dispositivo ocupado y hace fallar la corrida siguiente por falta de dispositivos.

## Lo que se adjunta al reporte

| Adjunto | Cuándo | Tipo |
|---|---|---|
| Screenshot del fallo | Siempre que el escenario falla | `image/jpeg` |
| Árbol de la pantalla | Siempre que el escenario falla | `text/plain` |
| Contexto activo | Siempre que el escenario falla | `text/plain` |
| URL de la sesión remota | Ejecución en device farm | `text/uri-list` |
| Dispositivo y versión de sistema | Ejecución en device farm | `text/plain` |
| Video | Si la grabación está activa | Archivo referenciado |

Los dos últimos son los que se olvidan y los que más rinden: sin saber en qué dispositivo y versión corrió, un fallo que solo ocurre en una versión concreta parece intermitente.

Trazabilidad y archivado del conjunto según `[[calidad-test-evidence-and-traceability]]`.
