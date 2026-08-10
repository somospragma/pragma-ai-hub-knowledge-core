# Plantillas del proyecto generado

Cada seccion corresponde a un archivo que el agente debe materializar en la ruta indicada (relativa a la raiz del proyecto generado). Respeta los placeholders `{{...}}`.

**Regla de precedencia**: ante cualquier discrepancia entre estas plantillas y `gradle-version-matrix.md`, **la matriz manda** (versiones, forma de declarar el plugin, scopes). Las contradicciones template-vs-matrix ya costaron una PoC entera; si detectas una, corrige el template y repórtala.

## `SuiteRunner.java` — UN SOLO runner por proyecto

```java
package co.com.pragma.runners;

import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

import static io.cucumber.core.options.Constants.GLUE_PROPERTY_NAME;

@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "co.com.pragma.stepdefinitions")
// SIN @ConfigurationParameter(FILTER_TAGS_PROPERTY_NAME, ...): un tag fijo aquí
// SOBREESCRIBE el -Dcucumber.filter.tags de la CLI y hace que "correr el smoke"
// ejecute otra cosa (causa raíz verificada en campo).
public class SuiteRunner {
}
```

**Reglas del runner** (las tres causas de ejecuciones fantasma vistas en campo):

1. **Un solo runner por proyecto.** Nada de `SmokeRunner` + `RegressionRunner`: Gradle los ejecuta todos y cada uno aplica sus propios tags.
2. **Cero tags hardcodeados** en el runner; el filtro llega siempre por CLI.
3. **Cero defaults de tags en `build.gradle`** (`systemProperty 'cucumber.filter.tags', ... '@smoke'`): reintroduce el problema por la puerta de atrás y, combinado con `aggregate`, re-ejecuta y sobrescribe resultados.

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
- **(b) Locators diferidos** marcados con `// TODO: update real locator`. Permite que `@smoke` pase con BUILD SUCCESSFUL pero sin gestos reales. El equipo completa locators después via workflow `[[calidad-complete-deferred-locators]]`.

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
| `Task 'aggregate' not found` | Plugin Serenity no aplicado. | Revisar `build.gradle` (ver `[no-aggregate-collision](no-aggregate-collision.md)`). |
| `cannot find symbol` en `compileJava` | Package declarations no coinciden con path físico. | Verificar `co.com.pragma.*` ↔ `src/main/java/co/com/pragma/*`. |
| `Activity class ... does not exist` al lanzar | Puede ser el APK — o el PackageManager del AVD corrupto. | BISECAR PRIMERO: ¿otro paquete de usuario del emulador resuelve su activity? Si tampoco → el problema es el AVD: `adb reboot` no basta, arrancar con `-wipe-data` o cambiar de AVD. Solo si otras apps sí resuelven, investigar el APK (DEX, plugin Kotlin aplicado en `app/build.gradle.kts`). |
| Reporte con `0 tests` o menos escenarios que los diseñados | Falso verde de reportería. | Correr el checklist de verificación de reportería (`[mobile-evidence-and-triage](mobile-evidence-and-triage.md)`): SerenityReporter en cucumber.plugin, junit-vintage presente, aggregate no UP-TO-DATE. |
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
- iOS: NO está en scope (`[android-only-scope-rationale](android-only-scope-rationale.md)`).
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

## 6. Execution target y plan de switchover (mock vs real)

Resuelto por `[[calidad-sut-readiness-gate]]` — obligatoria aunque el target sea `real`:

- `execution_target`: {{execution_target}} (real / mock / hybrid)
- Tecnología de la app real: {{app_technology}} (flutter / nativa / react-native — determina la estrategia de locators Y la tecnología del prototipo si aplica)
- Si mock: data file Mockoon en `mocks/mockoon/environment.json`, seed Faker {{faker_seed}}, purga de estado entre escenarios vía Admin API (hook `@Before`).
- Si app prototype: `mocks/app-prototype/` en la MISMA tecnología declarada, gate de paridad selector a selector antes del smoke.
- Plan de switchover: la URL del backend vive en un único punto ({{switchover_mechanism}}); certificación pendiente hasta re-ejecutar contra la app real (`certification: pending_real_integration`).

## 7. Próximos pasos

- Archivos a generar: `build.gradle`, `settings.gradle`, `gradlew`, `gradle/wrapper/gradle-wrapper.properties`, `serenity.properties`, `android.conf`, `README.md`, Page Objects bajo `co.com.pragma.*`, Tasks (`LoginTask`, etc.), `*.feature` con escenarios `@smoke-gate` (uno) + `@smoke` + `@proposed`, `SuiteRunner.java` (único).
- Comando de ejecución: `./gradlew clean test aggregate -p <project_path> -Dcucumber.filter.tags=@smoke`.
- Reporte ejecutivo: formato {{report_format}} (default `html`) con device matrix y locators auto-discovery vs deferred.

## 8. Estrategia Appium

### 8.1 Capabilities

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

### 8.2 Device matrix

| Device | Tipo | OS | Form factor | Prioridad |
|---|---|---|---|---|
| Pixel 6 (emulador) | emulator | Android 12 | phone | CRITICAL |
| Galaxy S22 (real) | real | Android 13 | phone | HIGH |
| Galaxy A52 (real) | real | Android 11 | phone | MEDIUM |

(Editar la matrix según devices realmente disponibles. Cada celda del reporte ejecutivo se desglosa por feature en esta matrix.)

### 8.3 Screens identificadas

| Screen | Page Object | Selectores estimados | Locator source |
|---|---|---|---|
| Login | LoginPage | 5 | {{login_locator_source}} |
| Dashboard | DashboardPage | 12 | {{dashboard_locator_source}} |
| Checkout | CheckoutPage | 8 | {{checkout_locator_source}} |

### 8.4 Locator strategy

- Modo: {{locator_mode}} (`auto-discovery`, `deferred` o `locator-map` con app Flutter/prototipo).
- Resolución verificada: aplicar el protocolo de `[locator-resolution-protocol](locator-resolution-protocol.md)` ANTES de escribir los Targets (identidad ≠ capacidad; conteo de nodos = 1; candar con test unitario).
- Si `auto-discovery`: el agente recorre la app vía APK + emulador + Appium server (paso 4 del workflow) y persiste resultados en `.evidence/locators-discovered.json` con score de confianza por locator. Aplica `[[calidad-appium-apk-auto-discovery]]`.
- Si `deferred`: cada Page Object queda con `// TODO: update real locator`. El usuario completa después con `[[calidad-complete-deferred-locators]]` usando Appium Inspector.

### 8.5 Escenarios `@smoke` y `@proposed`

- 2 escenarios `@android @smoke` mínimos siempre: arranque + login básico (si `include_login_case = true`).
- N escenarios `@android @proposed` derivados de `user_story` / `test_cases`. Cumplir `[gherkin-syntax-rules](gherkin-syntax-rules.md)` (≤80 chars por línea, newlines a espacios).

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar el scaffold Gradle + Screenplay.
```

## `build.gradle`

```groovy
plugins {
    id 'java'
    // El plugin va AQUI, en el bloque plugins{} con version explicita
    // (forma de gradle-version-matrix.md). NUNCA con `apply plugin:` suelto al
    // final: sin el plugin en el classpath del build script falla con
    // "Plugin with id ... not found".
    id 'net.serenity-bdd.serenity-gradle-plugin' version '4.1.14'
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

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
    implementation 'org.slf4j:slf4j-api:2.0.13'
    implementation 'ch.qos.logback:logback-classic:1.5.6'

    // src/test usa runners JUnit Platform + Cucumber + asserts. NO mover a
    // implementation (no aplican al main source set).
    testImplementation 'io.cucumber:cucumber-junit-platform-engine:7.14.0'
    testImplementation 'org.junit.platform:junit-platform-suite:1.10.2'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    // junit-vintage NO es opcional aunque suene a legacy: Serenity/Cucumber lo
    // usan para los ejemplos de Scenario Outline. Sin el, CADA ejemplo muere con
    // NoClassDefFoundError (org/junit/runners/ParentRunner) y los escenarios
    // data-driven (los BVA) se pierden EN SILENCIO del conteo.
    testImplementation 'org.junit.vintage:junit-vintage-engine:5.10.2'
    testImplementation 'org.assertj:assertj-core:3.25.3'

    // Lombok solo en compile-time, sin runtime overhead.
    compileOnly 'org.projectlombok:lombok:1.18.34'
    annotationProcessor 'org.projectlombok:lombok:1.18.34'
}

test {
    // OBLIGATORIO useJUnitPlatform() para Cucumber JUnit Platform 7.14.0.
    // NO usar useJUnit() — corresponde a JUnit 4 y rompe el runner de Cucumber.
    useJUnitPlatform()
    systemProperties System.getProperties()
    // El reporte se genera SIEMPRE, tambien (sobre todo) cuando hay fallos:
    // finalizedBy corre aggregate aunque test falle, sin ignoreFailures
    // (ignoreFailures=true daria BUILD SUCCESSFUL con rojos — inaceptable en CI).
    finalizedBy 'aggregate'
}

// serenity-gradle-plugin auto-registra la tarea `aggregate` (y `reports`, `clean`).
// NUNCA redefinir esas tareas con `task aggregate { ... }` ni
// `tasks.register('aggregate') { ... }` — colision garantizada en Gradle 8.x.
// Personalizacion permitida SOLO via tasks.named:
tasks.named('aggregate') {
    // Sin esto, Gradle puede marcar aggregate UP-TO-DATE (reporte viejo con "0
    // tests") u ordenarlo ANTES de test en la misma invocacion.
    outputs.upToDateWhen { false }
    mustRunAfter tasks.named('test')
}
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
#     la primera invocacion ./gradlew. Ver [health-check-pipeline](health-check-pipeline.md) y
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
# SerenityReporter en PRIMERA posicion es OBLIGATORIO. Sin el, Serenity nunca
# registra su BaseStepListener: los Click/Enter NO se ejecutan y los pasos
# reportan "passed" en falso (falso verde total, verificado en campo).
cucumber.plugin=io.cucumber.core.plugin.SerenityReporter, pretty, html:target/cucumber-reports/cucumber.html, json:target/cucumber-reports/cucumber.json
cucumber.glue=co.com.pragma.stepdefinitions
# PROHIBIDO declarar cucumber.features aqui: anula los selectores del @Suite
# (corren TODOS los features ignorando el filtro de tags -> el smoke gate deja
# de existir). Los features los selecciona @SelectClasspathResource del runner.
```

## `serenity.conf`

```hocon
# OBLIGATORIO en proyectos Appium: sin esto Serenity intenta levantar ChromeDriver
# (Chrome se abre en cada corrida y el actor puede acabar con el driver equivocado).
webdriver {
    driver = provided
    autodownload = false
}

serenity {
    project.name = "{{project_name}}"
    take.screenshots = AFTER_EACH_STEP
    # Redimensionar para no inflar el reporte con screenshots full-res
    resized.image.width = 600
    logging = VERBOSE
    # El ciclo de vida del driver lo maneja el proyecto (hooks), no Serenity:
    restart.browser.for.each = NEVER
    report.encoding = utf8
}

# REGLAS DE ESTE BLOQUE (aprendidas en campo, no negociables):
# 1. Las claves van SIN el prefijo "appium:" — Serenity 4.x las espera peladas
#    dentro del bloque appium{} y las convierte el solo. Con prefijo falla con
#    "The browser under test or path to the app ... needs to be provided".
# 2. `app` exige RUTA ABSOLUTA al APK. Usar `app` (no appPackage/appActivity
#    solos) cuando se necesita garantizar (re)instalacion y foco de la app.
# 3. PROHIBIDO nombrar una system property "appium.app" para sustituirla aqui:
#    ${?appium.app} dentro del bloque appium{} es una referencia circular que
#    HOCON descarta EN SILENCIO. Nombrarla fuera del namespace, ej:
#    app = ${?credimovil.apk.path}
appium {
    platformName = Android
    automationName = UiAutomator2
    deviceName = "{{device_name}}"
    platformVersion = "{{platform_version}}"
    app = "{{apk_absolute_path}}"
    autoGrantPermissions = true
    hub = "{{appium_server_url}}"
}
```

## `Hooks.java` (stepdefinitions)

```java
package co.com.pragma.stepdefinitions;

import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.Scenario;
import net.serenitybdd.core.Serenity;
import net.serenitybdd.screenplay.actors.Cast;
import net.serenitybdd.screenplay.actors.OnStage;

import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;

public class Hooks {

    @Before(order = 0)
    public void setTheStage() {
        // Cast.ofStandardActors() — NUNCA OnlineCast: Serenity crearia ademas un
        // ChromeDriver y Chrome se abriria en cada corrida (verificado en campo).
        // El AndroidDriver se asigna al actor aparte:
        //   OnStage.theActorCalled("usuario").can(BrowseTheWeb.with(androidDriver));
        OnStage.setTheStage(Cast.ofStandardActors());
    }

    // SOLO con execution_target: mock — aislamiento de datos entre escenarios.
    // Purga buckets + variables globales del Mockoon para que cada escenario
    // arranque del MISMO estado (sin esto, una transferencia del escenario N
    // contamina el saldo que espera el escenario N+1: falso rojo dependiente
    // del orden que parece flakiness). Requiere MOCKOON_ADMIN_API_TOKEN
    // (el Admin API responde 401 sin token — exportarlo tambien para la suite).
    @Before(order = 1)
    public void purgeMockState() throws Exception {
        String mockUrl = System.getenv().getOrDefault("MOCK_BASE_URL", "http://10.0.2.2:3010");
        String token = System.getenv("MOCKOON_ADMIN_API_TOKEN");
        if (token == null) return; // sin mock (execution_target: real) no aplica
        HttpURLConnection con = (HttpURLConnection) new URL(
                mockUrl.replace("10.0.2.2", "localhost") + "/mockoon-admin/state/purge").openConnection();
        con.setRequestMethod("POST");
        con.setRequestProperty("Authorization", "Bearer " + token);
        if (con.getResponseCode() != 200) {
            throw new IllegalStateException("Mock state purge fallo: HTTP " + con.getResponseCode());
        }
    }

    // Evidencia de primera linea por fallo: screenshot + PAGE SOURCE.
    // El page source es el diagnostico que una imagen no da (clickable=false,
    // resource-id ausente, nodos duplicados). Se persiste SIEMPRE que un
    // escenario falla, ANTES de cualquier hipotesis de triage.
    @After(order = 100)
    public void captureFailureEvidence(Scenario scenario) throws Exception {
        if (!scenario.isFailed()) return;
        WebDriver driver = net.serenitybdd.core.Serenity.getDriver();
        Path dir = Paths.get(".evidence", "failures");
        Files.createDirectories(dir);
        String name = scenario.getName().replaceAll("[^a-zA-Z0-9-]", "_");
        byte[] png = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES);
        Files.write(dir.resolve(name + ".png"), png);
        Files.writeString(dir.resolve(name + ".xml"), driver.getPageSource());
    }
}
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

