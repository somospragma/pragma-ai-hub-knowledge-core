# Plantillas del proyecto generado

Cada seccion corresponde a un archivo que el agente debe materializar en la ruta indicada (relativa a la raiz del proyecto generado). Respeta los placeholders `{{...}}`.

## `LoginRunner.java`

```java
package co.com.pragma.runners;

import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

import static io.cucumber.core.options.Constants.FILTER_TAGS_PROPERTY_NAME;
import static io.cucumber.core.options.Constants.GLUE_PROPERTY_NAME;

@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "co.com.pragma.stepdefinitions")
@ConfigurationParameter(key = FILTER_TAGS_PROPERTY_NAME, value = "@smoke")
public class LoginRunner {
}
```

## `README.md`

````markdown
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
````

## `STRATEGY.md`

```markdown
# STRATEGY.md — {{project_name}} (Appium Android)

Documento de estrategia previo a la generación de scaffolding Gradle / Screenplay / Cucumber. Debe estar aprobado explícitamente por el usuario antes de emitir el primer `.feature` o `.java`. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- App bajo prueba: {{app_name}} — {{app_description}}
- Tipo de SUT: Mobile Android nativa / híbrida — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}}
- Stack tecnológico de la app: {{app_stack}}
- Tipo de relación: greenfield (proyecto Appium nuevo)
- iOS: NO está en scope (`[[appium-android-only-scope-rationale]]`).
- APK: {{apk_path}} (validado vía `aapt dump badging`)
- `app_package`: {{app_package}} (default `com.example.app` si falta — declarar TODO en README)
- `app_activity`: {{app_activity}} (default `.MainActivity` si falta — declarar TODO en README)
- Firma: {{firma}}

## 2. Volumen y SLAs

Appium cubre validación E2E mobile. Los SLAs aplicables:

- Cumplimiento por feature: 100% de los escenarios `@android @smoke` pasan determinísticamente en la device matrix declarada.
- Tiempo de arranque máximo de la app: {{startup_time_max}} ms (verificado por `AppIsResponsive`).
- Cobertura de locators reales: >= {{real_locators_pct}}% (si se eligió auto-discovery).
- Disponibilidad de Appium server durante la corrida: 100%.

| Métrica | Valor declarado |
|---|---|
| % éxito por feature @smoke por device | 100% |
| Startup máximo app | {{startup_time_max}} ms |
| Locators reales resueltos | >= {{real_locators_pct}}% |

## 3. Alcance funcional

- Screens / features en scope: {{features_in_scope}}
- Screens / features fuera de scope: {{features_out_of_scope}} ({{out_of_scope_reason}})
- User stories: {{user_stories}}
- Test cases adicionales (`@proposed`): {{test_cases}}

## 4. Dependencias externas

- Auth: {{auth_strategy}} (login real con credenciales reales, login mockeado backend, sin auth).
- Backend al que la app consume: {{backend_url}}
- Servicios push / notifications / 3rd party SDKs: {{external_sdks}}
- Data de prueba: {{test_data_strategy}} (usuario seed, cleanup post-run, etc.)

## 5. Riesgos conocidos

- Estabilidad del emulador / device: {{device_stability_risk}}
- Variabilidad por versión de Android: {{android_version_variability}}
- Permisos runtime (cámara, ubicación, notificaciones): {{runtime_permissions}}
- Datos sensibles tratados por la app: {{sensitive_data}}
- Restricciones regulatorias: {{regulatory_constraints}}

## 6. Próximos pasos

- Archivos a generar: `build.gradle`, `settings.gradle`, `gradlew`, `gradle/wrapper/gradle-wrapper.properties`, `serenity.properties`, `android.conf`, `README.md`, Page Objects bajo `co.com.pragma.*`, Tasks (`LoginTask`, etc.), `*.feature` con escenarios `@smoke` + `@proposed`, `LoginRunner.java`.
- Comando de ejecución: `./gradlew clean test aggregate -p <project_path> -Dcucumber.filter.tags=@smoke`.
- Reporte ejecutivo: formato {{report_format}} (default `html`) con device matrix y locators auto-discovery vs deferred.

## 7. Estrategia Appium

### 7.1 Capabilities

| Capability | Valor |
|---|---|
| platformName | Android |
| platformVersion | {{platform_version}} (default 12.0) |
| deviceName | {{device_name}} (default `Android Emulator`) |
| automationName | {{automation_name}} (default `UiAutomator2`) |
| appPackage | {{app_package}} |
| appActivity | {{app_activity}} |
| app | {{apk_path}} |
| appiumServerUrl | {{appium_server_url}} (default `http://127.0.0.1:4723`) |
| noReset | {{no_reset}} |
| autoGrantPermissions | {{auto_grant_permissions}} |

### 7.2 Device matrix

| Device | Tipo | OS | Form factor | Prioridad |
|---|---|---|---|---|
| Pixel 6 (emulador) | emulator | Android 12 | phone | CRITICAL |
| Galaxy S22 (real) | real | Android 13 | phone | HIGH |
| Galaxy A52 (real) | real | Android 11 | phone | MEDIUM |

(Editar la matrix según devices realmente disponibles. Cada celda del reporte ejecutivo se desglosa por feature en esta matrix.)

### 7.3 Screens identificadas

| Screen | Page Object | Selectores estimados | Locator source |
|---|---|---|---|
| Login | LoginPage | 5 | {{login_locator_source}} |
| Dashboard | DashboardPage | 12 | {{dashboard_locator_source}} |
| Checkout | CheckoutPage | 8 | {{checkout_locator_source}} |

### 7.4 Locator strategy

- Modo: {{locator_mode}} (`auto-discovery` o `deferred`).
- Si `auto-discovery`: el agente recorre la app vía APK + emulador + Appium server (paso 4 del workflow) y persiste resultados en `.evidence/locators-discovered.json` con score de confianza por locator. Aplica `[[appium-apk-auto-discovery]]`.
- Si `deferred`: cada Page Object queda con `// TODO: update real locator`. El usuario completa después con `[[complete-deferred-locators]]` usando Appium Inspector.

### 7.5 Escenarios `@smoke` y `@proposed`

- 2 escenarios `@android @smoke` mínimos siempre: arranque + login básico (si `include_login_case = true`).
- N escenarios `@android @proposed` derivados de `user_story` / `test_cases`. Cumplir `[[appium-gherkin-syntax-rules]]` (≤80 chars por línea, newlines a espacios).

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar el scaffold Gradle + Screenplay.
```

## `build.gradle`

```groovy
plugins {
    id 'java'
}

sourceCompatibility = 21
targetCompatibility = 21

repositories {
    mavenCentral()
}

dependencies {
    // src/main/java/co/com/pragma/... vive la capa Screenplay (tasks, questions,
    // interactions, userinterfaces). Esas clases necesitan Serenity + Appium en
    // compileJava, por lo que TIENEN que estar en `implementation`.
    // Mover cualquiera de estas a testImplementation rompe la compilacion del
    // modulo principal con "cannot find symbol".
    implementation 'net.serenity-bdd:serenity-core:4.1.14'
    implementation 'net.serenity-bdd:serenity-cucumber:4.1.14'
    implementation 'net.serenity-bdd:serenity-screenplay:4.1.14'
    implementation 'net.serenity-bdd:serenity-screenplay-webdriver:4.1.14'
    implementation 'io.appium:java-client:8.6.0'
    implementation 'org.slf4j:slf4j-api:2.0.9'
    implementation 'ch.qos.logback:logback-classic:1.4.14'

    // src/test usa runners JUnit Platform + Cucumber + asserts. NO mover a
    // implementation (no aplican al main source set).
    testImplementation 'io.cucumber:cucumber-junit-platform-engine:7.14.0'
    testImplementation 'org.junit.platform:junit-platform-suite:1.10.2'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    testImplementation 'org.assertj:assertj-core:3.24.2'

    // Lombok solo en compile-time, sin runtime overhead.
    compileOnly 'org.projectlombok:lombok:1.18.30'
    annotationProcessor 'org.projectlombok:lombok:1.18.30'
}

test {
    // OBLIGATORIO useJUnitPlatform() para Cucumber JUnit Platform 7.14.0.
    // NO usar useJUnit() — corresponde a JUnit 4 y rompe el runner de Cucumber.
    useJUnitPlatform()
    systemProperties System.getProperties()
}

// serenity-gradle-plugin auto-registra la tarea `aggregate` (y `reports`, `clean`).
// NUNCA redefinir esas tareas con `task aggregate { ... }` ni
// `tasks.register('aggregate') { ... }` — colision garantizada en Gradle 8.x.
// Si necesitas personalizar, usar `tasks.named('aggregate') { ... }`.
apply plugin: 'net.serenity-bdd.serenity-gradle-plugin'
```

## `gradle-wrapper.properties`

```properties
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.10-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
```

## `gradlew`

```text
# Este archivo NO se mantiene a mano.
#
# `gradlew` (script bash) y `gradlew.bat` (script batch para Windows) deben
# generarse ejecutando:
#
#   gradle wrapper --gradle-version 8.10
#
# en la raiz del proyecto recien scaffoldeado, antes de cualquier otra cosa.
# Esto produce:
#
#   gradlew                              (bash, debe quedar 0755)
#   gradlew.bat                          (batch)
#   gradle/wrapper/gradle-wrapper.jar    (binario)
#   gradle/wrapper/gradle-wrapper.properties  (ver gradle-wrapper.properties.tpl)
#
# Reglas:
#   - El agente DEBE correr `chmod +x gradlew` despues de generar el wrapper.
#     Sin esto, el health-check del workflow falla con "Permission denied" en
#     la primera invocacion ./gradlew. Ver [[appium-health-check-pipeline]] y
#     el acceptance criteria #5 del skill.
#   - El distribution URL fijado debe coincidir con `gradle-wrapper.properties.tpl`
#     (Gradle 8.10). NO regenerar wrapper con otra version.
#   - Si el agente NO puede ejecutar shell, deja un TODO destacado en el README:
#       > "Antes de correr ./gradlew, ejecutar: gradle wrapper --gradle-version 8.10
#       >  && chmod +x gradlew"
#   - NO commitear `gradle/wrapper/gradle-wrapper.jar` manualmente — debe venir
#     de la version oficial 8.10 (el comando `gradle wrapper` lo descarga).
#
# Resumen: este `.tpl` es una NOTA, no el script. El script real lo emite
# Gradle, no el generador.
```

## `junit-platform.properties`

```properties
cucumber.junit-platform.naming-strategy=long
cucumber.plugin=pretty, html:target/cucumber-reports/cucumber.html, json:target/cucumber-reports/cucumber.json
cucumber.glue=co.com.pragma.stepdefinitions
cucumber.features=src/test/resources/features
```

## `preflight-appium.sh`

```bash
#!/usr/bin/env bash
set -e
echo "=== Appium Screenplay Android pre-flight ==="

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | cut -d. -f1)
echo "Java major version: $JAVA_VERSION"
if [[ "$JAVA_VERSION" != "21" ]]; then
  echo "[fail] Java $JAVA_VERSION detectado. Serenity 4.x + scaffold requiere JDK 21."
  echo "Sugerencia macOS: export JAVA_HOME=\$(/usr/libexec/java_home -v 21)"
  exit 1
fi
echo "[ok] JDK 21 disponible"

if [[ -x "./gradlew" ]]; then
  GRADLE_VERSION=$(./gradlew --version 2>/dev/null | grep '^Gradle' | awk '{print $2}')
  echo "Gradle wrapper version: $GRADLE_VERSION"
  if [[ "$GRADLE_VERSION" != 8.10* ]]; then
    echo "[warn] Gradle $GRADLE_VERSION distinto del esperado 8.10. Ver appium-gradle-version-matrix."
  fi
  echo "[ok] gradlew presente"
else
  echo "[fail] gradlew no encontrado o no ejecutable."
  echo "Sugerencia: gradle wrapper --gradle-version 8.10 && chmod +x gradlew"
  exit 1
fi

if ! command -v appium > /dev/null 2>&1; then
  echo "[fail] appium no encontrado. Sugerencia: npm i -g appium && appium driver install uiautomator2"
  exit 1
fi
APPIUM_VERSION=$(appium --version 2>/dev/null)
echo "Appium version: $APPIUM_VERSION"
APPIUM_MAJOR=$(echo "$APPIUM_VERSION" | cut -d. -f1)
if [[ "$APPIUM_MAJOR" -lt 2 ]]; then
  echo "[fail] Appium $APPIUM_VERSION < 2.0.0. El scaffold requiere V2."
  exit 1
fi
echo "[ok] Appium V2 disponible"

if ! command -v adb > /dev/null 2>&1; then
  echo "[fail] adb no encontrado. Instalar Android SDK platform-tools."
  exit 1
fi

DEVICES=$(adb devices | tail -n +2 | grep -c "device$" || true)
if [[ "$DEVICES" -eq 0 ]]; then
  echo "[warn] adb no detecta devices/emuladores. Modo full no ejecutable; degradar a scaffold-only."
else
  echo "[ok] $DEVICES device(s) detectado(s)"
fi

if [[ -n "$APK_PATH" ]]; then
  if [[ ! -f "$APK_PATH" ]]; then
    echo "[fail] APK_PATH=$APK_PATH no existe"
    exit 1
  fi
  if command -v aapt > /dev/null 2>&1; then
    PKG=$(aapt dump badging "$APK_PATH" 2>/dev/null | grep "^package:" | head -n 1)
    echo "APK package info: $PKG"
  else
    echo "[warn] aapt no disponible; no se puede leer appPackage/appActivity reales"
  fi
fi

echo "=== preflight ok ==="
```

