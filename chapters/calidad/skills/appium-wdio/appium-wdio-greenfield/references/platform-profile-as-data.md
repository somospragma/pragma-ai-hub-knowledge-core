# El perfil de plataforma como dato

## El problema que resuelve

Un arquetipo que cubre Android, iOS, iPad, tablet y navegador móvil termina con seis hooks `Before` de doscientas líneas cada uno, idénticos en un noventa por ciento. La consecuencia no es estética: **una corrección se aplica en cinco de los seis**, y el sexto falla meses después sin que nadie recuerde por qué es distinto.

La abstracción correcta separa lo que varía —capabilities, etiquetas, timeouts, estrategia de video— de lo que no varía —el algoritmo de conexión, el fallback de dispositivos, la instrumentación—. Lo que varía se declara como datos; lo que no, se escribe una vez.

## El tipo

```typescript
export interface MobilePlatformProfile {
  // Identidad y selección
  tagExpression: string;              // '@android', '@ios-web'
  label: string;                      // etiqueta legible para logs y reportes
  logPlatformKey: string;             // clave estable para logging estructurado
  defaultTestName: string;

  // Ciclo de vida
  timeoutMs: number;                  // timeout del hook de creación, en minutos
  metricName: string;

  // Resolución de dispositivo
  deviceKind: 'android' | 'ios';      // familia del driver
  deviceType: 'phone' | 'tablet';     // filtro de catálogo
  fallbackDevices: DeviceInfo[];      // lista si el catálogo remoto no responde
  noDeviceErrorMessage: string;

  // Capabilities
  buildLocalCapabilities: (world: HookWorld) => Record<string, unknown>;
  applyCloudLanguage: (caps: CloudCapabilities, world: HookWorld) => void;
  forceBrowserName?: string;          // 'Chrome' | 'Safari' en perfiles web
  deleteCapabilityKeys?: string[];    // capabilities de app a quitar en perfiles web

  // Entorno local
  getLocalPort: () => number;
  ensureLocalDeviceReady?: () => Promise<void>;
  passPortToRemote: boolean;
  afterLocalConnect?: (world: HookWorld) => Promise<void>;

  // Evidencia
  videoStrategyKind: 'native' | 'ffmpeg-mjpeg';
  ffmpegLogTag?: string;
}
```

Cada campo existe porque una plataforma real difiere de otra en ese punto. Los opcionales son las excepciones legítimas: solo el perfil que las necesita las declara.

## Los perfiles

```typescript
export const androidProfile: MobilePlatformProfile = {
  tagExpression: '@android',
  label: 'Android',
  logPlatformKey: 'android',
  defaultTestName: 'Prueba Android',
  timeoutMs: 420_000,
  metricName: 'android_driver_creation',
  deviceKind: 'android',
  deviceType: 'phone',
  fallbackDevices: ANDROID_FALLBACK_DEVICES,
  noDeviceErrorMessage: 'No hay dispositivos Android disponibles',
  buildLocalCapabilities: world => withLanguage({ ...mobileConfig.android }, world),
  applyCloudLanguage: (caps, world) => applyAndroidLikeLanguage(caps, world),
  getLocalPort: () => appiumServerManager.getPort('android'),
  ensureLocalDeviceReady: () => appiumServerManager.ensureAndroidDeviceReady(),
  passPortToRemote: true,
  videoStrategyKind: 'native'
};

// Un perfil web móvil es el mismo dispositivo con el navegador en vez de la app
export const androidWebProfile: MobilePlatformProfile = {
  ...androidProfile,
  tagExpression: '@android-web',
  label: 'Android Web',
  logPlatformKey: 'android-web',
  metricName: 'android_web_driver_creation',
  forceBrowserName: 'Chrome',
  deleteCapabilityKeys: ['appium:appPackage', 'appium:appActivity'],
  buildLocalCapabilities: world => {
    const caps = withLanguage({ ...mobileConfig.android }, world);
    caps['browserName'] = 'Chrome';
    delete caps['appium:appPackage'];
    delete caps['appium:appActivity'];
    return caps;
  }
};

// Una tablet es un teléfono con otro filtro de catálogo
export const tabletProfile: MobilePlatformProfile = {
  ...androidProfile,
  tagExpression: '@tablet',
  label: 'Tablet Android',
  logPlatformKey: 'tablet',
  metricName: 'tablet_driver_creation',
  deviceType: 'tablet',
  fallbackDevices: TABLET_FALLBACK_DEVICES,
  noDeviceErrorMessage: 'No hay tablets Android disponibles'
};

export const ALL_PROFILES = [
  androidProfile, androidWebProfile, iosProfile, iosWebProfile, ipadProfile, tabletProfile
];
```

Agregar iPad o tablet cuesta un objeto literal con tres campos distintos. Ese es el resultado que valida el diseño.

## El motor único

```typescript
export class GenericMobileDriver {
  constructor(private readonly profile: MobilePlatformProfile) {}

  async setup(world: HookWorld): Promise<void> {
    const testName = world.testName || this.profile.defaultTestName;
    PerformanceMetrics.start(this.profile.metricName);

    if (isCloudMode()) {
      await this.connectCloud(world, testName);
    } else {
      await this.connectLocal(world, testName);
    }
  }

  private async connectLocal(world: HookWorld, _testName: string): Promise<void> {
    await this.profile.ensureLocalDeviceReady?.();
    const port = this.profile.getLocalPort();
    await appiumServerManager.ensureRunning(port);

    world.driver = await remote({
      ...mobileConfig.appiumServer,
      ...(this.profile.passPortToRemote ? { port } : {}),
      capabilities: this.profile.buildLocalCapabilities(world) as WebdriverIO.Capabilities
    });

    await this.profile.afterLocalConnect?.(world);
    await createVideoRecorder(this.profile.videoStrategyKind, this.profile.ffmpegLogTag)
      .start(world, this.profile.label);
  }

  private async connectCloud(world: HookWorld, testName: string): Promise<void> {
    // Fallback de dispositivos y cancelación de cola: ver local-vs-cloud-execution.md
  }
}
```

## El cableado de hooks

Con los perfiles como datos, los seis hooks se generan en un bucle:

```typescript
for (const profile of ALL_PROFILES) {
  Before({ tags: profile.tagExpression, timeout: profile.timeoutMs }, async function (this: HookWorld) {
    await new GenericMobileDriver(profile).setup(this);
  });
}
```

Y el teardown se resuelve con una única expresión de tags:

```typescript
const MOBILE_TAGS = ALL_PROFILES.map(p => p.tagExpression).join(' or ');

After({ tags: MOBILE_TAGS }, async function (this: HookWorld, { result }) {
  await mobileTeardownService.finalize(this, result);
});
```

## Reglas de diseño

- **Si un perfil necesita lógica que ningún otro tiene**, se agrega como campo opcional del tipo (`afterLocalConnect`), no como rama `if (plataforma === 'ios-web')` dentro del motor. La rama es donde vuelve a crecer la duplicación.
- **Los perfiles derivados extienden al base con spread** y sobrescriben lo que difiere. Copiar el objeto entero reintroduce el problema.
- **El motor no conoce nombres de plataforma.** Si aparece un `switch` sobre plataforma dentro del motor, ese comportamiento pertenece al perfil.
- **Los timeouts son por perfil.** Provisionar un dispositivo real en un device farm tarda minutos; arrancar un simulador local, segundos. Un timeout único los sirve mal a los dos.
- **`buildLocalCapabilities` recibe el World** porque hay capabilities que dependen del escenario: idioma, credenciales, variantes del dispositivo. Construirlas en tiempo de módulo las congela para toda la corrida.
