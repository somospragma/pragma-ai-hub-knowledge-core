# Mobile Cloud Providers — Comparativa para Suites Appium

Ejecutar Appium en devices reales requiere infraestructura cara y de mantenimiento alto. Los cloud providers son la opción estándar para CI.

## Comparativa

| Provider           | Real devices | Emuladores | Paralelismo típico | Coste relativo | Fortaleza                                          |
| ------------------ | ------------ | ---------- | ------------------ | -------------- | -------------------------------------------------- |
| BrowserStack       | Sí (>30k)    | Sí         | 5-150              | Alto           | Catálogo masivo, integración Appium trivial        |
| Sauce Labs         | Sí           | Sí         | 5-100              | Alto           | Analítica profunda, soporte enterprise             |
| AWS Device Farm    | Sí           | Sí         | 5-50               | Medio          | Pago por minuto, integración AWS nativa            |
| Firebase Test Lab  | Sí (Android) | Sí         | Pool dinámico      | Bajo           | Solo Android, integrado a Firebase, barato         |

## Cuándo elegir cada uno

- **BrowserStack App Automate**: cliente con catálogo amplio de dispositivos (LATAM = muchos Android low-end), suites cross-platform iOS+Android, equipos sin expertise AWS.
- **Sauce Labs Real Device Cloud**: cliente enterprise con SLAs estrictos, necesidad de analítica detallada de performance mobile.
- **AWS Device Farm**: cliente ya en AWS, pricing por uso (suites infrecuentes), integración con CodePipeline.
- **Firebase Test Lab**: solo Android, presupuesto ajustado, integración con Crashlytics, validación pre-release de Play Store.

## Snippets de capabilities

### BrowserStack

```java
DesiredCapabilities caps = new DesiredCapabilities();
caps.setCapability("bstack:options", Map.of(
    "userName", System.getenv("BROWSERSTACK_USERNAME"),
    "accessKey", System.getenv("BROWSERSTACK_ACCESS_KEY"),
    "projectName", "QA-Pragma",
    "buildName", System.getenv("BUILD_NUMBER"),
    "sessionName", "Login Test",
    "deviceName", "Samsung Galaxy S23",
    "osVersion", "13.0",
    "appiumVersion", "2.0.1"
));
caps.setCapability("app", "bs://abc123...");  // app uploaded previamente

URL hubUrl = new URL("https://hub.browserstack.com/wd/hub");
driver = new AndroidDriver(hubUrl, caps);
```

Upload del APK/IPA:
```bash
curl -u "$BROWSERSTACK_USERNAME:$BROWSERSTACK_ACCESS_KEY" \
  -X POST "https://api-cloud.browserstack.com/app-automate/upload" \
  -F "file=@app.apk" \
  -F "custom_id=QA_Pragma_App"
```

### Sauce Labs

```java
DesiredCapabilities caps = new DesiredCapabilities();
caps.setCapability("sauce:options", Map.of(
    "username", System.getenv("SAUCE_USERNAME"),
    "accessKey", System.getenv("SAUCE_ACCESS_KEY"),
    "build", System.getenv("BUILD_NUMBER"),
    "name", "Login Test",
    "deviceName", "iPhone_15_Pro_Max",
    "platformVersion", "17",
    "appiumVersion", "2.0.1"
));
caps.setCapability("app", "storage:filename=app.ipa");

URL hubUrl = new URL("https://ondemand.us-west-1.saucelabs.com/wd/hub");
driver = new IOSDriver(hubUrl, caps);
```

Upload:
```bash
curl -u "$SAUCE_USERNAME:$SAUCE_ACCESS_KEY" \
  -X POST "https://api.us-west-1.saucelabs.com/v1/storage/upload" \
  -F "payload=@app.ipa" \
  -F "name=app.ipa"
```

### AWS Device Farm

AWS Device Farm tiene dos modos: **scheduled runs** (tradicional) y **direct device access** (Appium remoto en tiempo real).

```java
// Modo direct device access
DesiredCapabilities caps = new DesiredCapabilities();
// AWS genera un endpoint efímero — obtenerlo via aws CLI:
// aws devicefarm create-test-grid-url --project-arn $PROJECT_ARN --expires-in-seconds 3600
String endpoint = System.getenv("DEVICEFARM_GRID_URL");
driver = new AndroidDriver(new URL(endpoint), caps);
```

### Firebase Test Lab

Firebase Test Lab NO usa Appium remoto tradicional. Ejecuta una APK + Test APK directamente:

```bash
gcloud firebase test android run \
  --type instrumentation \
  --app app-debug.apk \
  --test app-debug-androidTest.apk \
  --device model=oriole,version=33,locale=en,orientation=portrait \
  --device model=blueline,version=29,locale=en,orientation=portrait \
  --timeout 10m
```

Para Appium server-driven en Firebase: NO soportado directamente — usar BrowserStack/Sauce.

## Paralelismo y coste

Patrón típico Pragma:
- **PR**: 1-2 emuladores locales (Android Studio AVD, sin coste).
- **Nightly**: 5-10 devices reales en BrowserStack (matrix de top devices LATAM).
- **Release**: 20-30 devices, cross-OS, incluyendo low-end Android (Pragma LATAM = importantes).

```yaml
# matrix LATAM top devices
matrix:
  device:
    - {name: 'Samsung Galaxy A14', os: '13'}    # Top Android LATAM
    - {name: 'Xiaomi Redmi Note 12', os: '13'}  # Top mid-range
    - {name: 'Motorola Moto G84', os: '14'}     # Top Motorola
    - {name: 'iPhone 14', os: '17'}             # Top iPhone region
    - {name: 'iPhone 13', os: '16'}             # iPhone gen previa
```

## Seguridad

- NUNCA commitear `BROWSERSTACK_ACCESS_KEY` ni `SAUCE_ACCESS_KEY`. Inyectar via `secrets-in-pipelines.md`.
- Para apps con datos sensibles, usar **private device pools** (BrowserStack y Sauce ofrecen devices dedicados que no se comparten).
- Encriptar APK/IPA con datos de test antes de upload si contienen PII de fixtures.

## Anti-patterns

- Correr suite completa en device cloud en cada PR (coste explota a miles USD/mes).
- Usar emuladores locales para validar UI critica (los emuladores no reproducen issues de hardware reales — touch sensibility, GPU rendering).
- Reutilizar el mismo build de app entre PR y release (siempre rebuildar para verificar el binario que se va a distribuir).
- Ejecutar pruebas en iPhone Simulator (no es Apple-firma-able, no detecta crashes reales de iOS).
