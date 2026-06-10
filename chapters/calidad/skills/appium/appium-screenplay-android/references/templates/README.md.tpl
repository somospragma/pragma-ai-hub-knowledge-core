# {{project_name}}

Proyecto de pruebas mobile (Android) con Appium V2 + Screenplay + Serenity + Cucumber, generado a partir de `{{input_source}}`.

## Prerequisitos

- **JDK 21** (Serenity 4.1.14 + Appium Java Client 8.6.0 lo exigen).
- **Gradle wrapper** incluido (no hace falta Gradle global).
- **Appium 2.x** con driver **UiAutomator2** instalado.
- **Android SDK** + emulador (AVD) o device físico con `adb`.
- **`adb`** y **`aapt`** en `PATH` (parte de Android SDK platform-tools/build-tools).

Verificación rápida:

```bash
java -version           # debe mostrar 21
appium --version        # 2.x
appium driver list      # debe listar uiautomator2 instalado
adb devices             # debe listar al menos un emulator/device "device"
aapt version            # opcional, para inspeccionar el .apk
```

## Quick start

```bash
./scripts/preflight.sh                                # valida JDK, Appium, adb, device
./gradlew clean test aggregate -Dcucumber.filter.tags=@smoke
```

Filtros por tag:

```bash
./gradlew test -Dcucumber.filter.tags=@android
./gradlew test -Dcucumber.filter.tags=@main-step
./gradlew test -Dcucumber.filter.tags="@smoke and not @proposed"
```

Override de capabilities:

```bash
./gradlew test -Denv=staging -Dappium.server.url=http://127.0.0.1:4723
```

## Auto-discovery vs deferred locators

Al generar el proyecto, el agente pregunta cuál estrategia usar para los selectores:

- **(a) Auto-descubrir selectores reales** recorriendo la app con Appium Inspector / crawler (~3-5 minutos extra; recomendado si el `.apk` está disponible). Resultado: locators reales en `userinterfaces/`.
- **(b) Locators diferidos** marcados con `// TODO: update real locator`. Permite que `@smoke` pase con BUILD SUCCESSFUL pero sin gestos reales. El equipo completa locators después via workflow `[[complete-deferred-locators]]`.

## Estructura del proyecto

```
{{project_name}}/
├── build.gradle
├── settings.gradle
├── gradlew + gradlew.bat
├── gradle/wrapper/gradle-wrapper.properties
├── serenity.properties
├── android.conf
├── README.md
├── scripts/preflight-appium.sh
└── src/
    ├── main/java/co/com/pragma/
    │   ├── tasks/
    │   ├── questions/
    │   ├── interactions/
    │   ├── userinterfaces/
    │   ├── models/
    │   └── utils/
    └── test/
        ├── java/co/com/pragma/{runners,stepdefinitions}/
        └── resources/
            ├── serenity.conf
            ├── junit-platform.properties
            └── features/                # .feature por capability/HU
```

## Evidencia

Tras cada `./gradlew test aggregate`:

- `target/site/serenity/` — reporte Serenity HTML.
- `target/site/serenity/serenity.summary.json` — summary JSON.
- `results/appium/{YYYY-MM-DD}/{ISO}-metadata.json` — metadata universal.
- `.evidence/execution-status.json` — sólo si hubo bloqueo (device unavailable, JDK wrong, Appium down).

## Troubleshooting

| Síntoma | Causa | Solución |
|---|---|---|
| `adb devices` vacío | Emulador no arrancó o device no conectado. | `emulator -avd <name>` o conectar device con USB-debug. |
| `ECONNREFUSED 4723` | Appium server no corre. | `appium` en otra terminal. |
| `UnsupportedClassVersionError` | JDK < 21. | Instalar JDK 21 (Temurin, Corretto). |
| `Task 'aggregate' not found` | Plugin Serenity no aplicado. | Revisar `build.gradle` (ver `[[appium-no-aggregate-collision]]`). |
| `cannot find symbol` en `compileJava` | Package declarations no coinciden con path físico. | Verificar `co.com.pragma.*` ↔ `src/main/java/co/com/pragma/*`. |
