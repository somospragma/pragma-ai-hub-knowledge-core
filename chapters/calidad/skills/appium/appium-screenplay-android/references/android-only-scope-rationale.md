
# Appium — Alcance Android del scaffolder vs. capacidad iOS del Chapter

Este documento separa dos cosas que históricamente se confundieron:

1. La **limitación del scaffolder V2** (auto-generador `[[calidad-appium-screenplay-android]]`).
2. La **capacidad real del Chapter Calidad** para automatizar Appium en iOS y Android.

No son lo mismo. El scaffolder no agotó las capacidades del Chapter.

## 1. Limitación del scaffolder V2 (Android-only)

El generador automático `[[calidad-appium-screenplay-android]]` produce hoy **únicamente** proyectos Android. Las razones son tooling, no estrategia:

- **Driver UiAutomator2.** El stack V2 fija `automation_name=UiAutomator2`, que es exclusivo de Android.
- **Selector mapping limitado.** El generador soporta `AppiumBy.id`, `AppiumBy.xpath` y `AppiumBy.accessibilityId`. NO emite `AppiumBy.iOSClassChain` ni `AppiumBy.iOSNsPredicateString`, que son los selectores idiomáticos de XCUITest.
- **Sin pre-requisitos iOS automatizables.** XCUITest exige macOS + Xcode + provisioning profile + Apple Developer account + simulador o device físico con UDID; el scaffolder no puede asumir ni configurar esos pre-requisitos.
- **Acceptance criterion 1 del scaffolder.** V2 ships un solo stack para garantizar exit 0 sin cambios manuales en cualquier máquina del chapter.

Por eso, si `platform_name` (cuando viene en los inputs del generador) en minúsculas no es `"android"`, el scaffolder responde:

```
En Appium V2 solo se soporta Android.
```

Este mensaje aplica **al scaffolder**, no al chapter completo.

## 2. Capacidad del Chapter Calidad (Android e iOS)

Pragma's Chapter Calidad **sí soporta automatización Appium para iOS** usando exactamente el mismo patrón Screenplay + Serenity + Cucumber documentado en `[[calidad-appium-screenplay-android]]`. Lo que cambia es:

- El **driver** (`XCUITest` en lugar de `UiAutomator2`).
- Las **capabilities** (`platformName=iOS`, `deviceName`, `platformVersion`, `bundleId` o `app`, `udid` para device real).
- Los **selectores** (`AppiumBy.iOSClassChain`, `AppiumBy.iOSNsPredicateString`, `AppiumBy.accessibilityId`).
- El **proceso de instalación** (Appium con driver XCUITest, WebDriverAgent firmado).

Las capas Screenplay (Task, Question, Interaction, UserInterface), el runner Serenity + Cucumber, la estructura Gradle, los tags `@smoke`/`@proposed`, las reglas Gherkin y la trazabilidad son las mismas. Solo cambia la implementación de los selectores y las capabilities.

Para un proyecto Appium iOS hoy, el desarrollador debe **scaffold manual** usando:

- La documentación oficial de Appium (driver XCUITest).
- La referencia ``screenplay-layers.md`` para el patrón.
- Las convenciones mobile QA del Chapter (package base `co.com.pragma.*`, tags, naming, gherkin language coherente con el proyecto).
- El skill `[[calidad-appium-brownfield]]` si extiende un proyecto iOS preexistente.

## Workaround para iOS hoy

Pasos concretos para iniciar manualmente un proyecto Appium iOS Screenplay alineado al Chapter:

1. **Instalar Appium con driver XCUITest** en macOS:
   ```bash
   npm install -g appium
   appium driver install xcuitest
   appium --version
   appium driver list --installed
   ```
2. **Pre-requisitos macOS:** Xcode + Command Line Tools, `xcode-select --install`, `carthage` (lo usa WebDriverAgent), cuenta Apple Developer si se ejecuta en device real.
3. **Levantar simulador o preparar device real:**
   ```bash
   xcrun simctl list devices
   xcrun simctl boot "iPhone 15"
   # device real: anotar UDID con `idevice_id -l` o Xcode > Devices.
   ```
4. **Configurar capabilities iOS** en el `serenity.conf` (perfil iOS) o en el `DriverManager` Screenplay:
   ```hocon
   webdriver {
     driver = "appium"
     capabilities {
       platformName = "iOS"
       "appium:automationName" = "XCUITest"
       "appium:deviceName" = "iPhone 15"
       "appium:platformVersion" = "17.4"
       "appium:app" = "/abs/path/to/MyApp.app"          // o "appium:bundleId" si la app ya está instalada
       "appium:udid" = "00008110-XXXXXXXXXXXXXXXX"       // solo device real; quitar en simulador
       "appium:xcodeOrgId" = "TEAMID"                    // solo device real
       "appium:xcodeSigningId" = "iPhone Developer"      // solo device real
       "appium:noReset" = false
     }
   }
   ```
5. **Modelar selectores iOS** en los `UserInterface` Screenplay con los `By` idiomáticos de XCUITest:
   ```java
   import io.appium.java_client.AppiumBy;
   import net.serenitybdd.screenplay.targets.Target;

   public class LoginPage {
     public static final Target EMAIL_INPUT =
         Target.the("email input")
               .located(AppiumBy.iOSClassChain("**/XCUIElementTypeTextField[`label == \"Email\"`]"));

     public static final Target PASSWORD_INPUT =
         Target.the("password input")
               .located(AppiumBy.iOSNsPredicateString("type == 'XCUIElementTypeSecureTextField' AND label == 'Password'"));

     public static final Target LOGIN_BUTTON =
         Target.the("login button")
               .located(AppiumBy.accessibilityId("loginButton"));
   }
   ```
   Reglas: `accessibilityId` primero cuando exista; `iOSClassChain` para jerarquías predecibles; `iOSNsPredicateString` para filtros por atributo. Evitar XPath en iOS por performance.
6. **Ejecutar en simulador**:
   ```bash
   appium --base-path /wd/hub
   ./gradlew clean test aggregate -Denv=ios-sim
   ```
7. **Ejecutar en device real** (requiere WebDriverAgent firmado con el `xcodeOrgId` indicado y el device confiando en el certificado):
   ```bash
   ./gradlew clean test aggregate -Denv=ios-device
   ```

El proyecto resultante respeta las mismas restricciones del chapter (no redefinir `aggregate`/`reports`/`clean`, package `co.com.pragma.*`, no usar `OnlineCast` —dispara ChromeDriver—, etc.).

## Alternativa: el stack Appium sobre TypeScript

Antes de asumir scaffold manual para iOS, evalúa si el ecosistema del equipo admite el otro stack Appium del chapter: `[[calidad-appium-wdio-greenfield]]` genera iOS de forma nativa —simulador y dispositivo físico— sobre TypeScript, WebdriverIO y cucumber-js, sin las limitaciones del scaffolder JVM.

La decisión no es del agente: la determina el ecosistema del equipo (un equipo Java no adopta TypeScript por conveniencia del generador) y, en brownfield, el proyecto que ya existe. Ver la tabla de desambiguación en `[[calidad-intent-detection]]`.

Si el camino es JVM con scaffold manual, la matriz completa de capabilities iOS —incluido el bloque WebDriverAgent con sus timeouts, reintentos e identificadores de firma, que es donde falla la primera sesión en cualquier máquina nueva— está documentada en `references/capabilities-matrix-ios.md` de `[[calidad-appium-wdio-greenfield]]`. Las capabilities son del servidor Appium y aplican igual desde Java: solo cambia la sintaxis con la que se declaran.

## Roadmap

- **V3 del scaffolder** incluirá un generador iOS con perfiles dual Android/iOS, mapeo de selectores `iOSClassChain` y `iOSNsPredicateString`, plantillas de capabilities para simulador y device real, y health-check específico para XCUITest.
- **Mientras tanto**, el scaffold manual está **totalmente soportado por el Chapter Calidad**: se aplican ``screenplay-layers.md``, ``gherkin-syntax-rules.md``, ``smoke-vs-proposed-scenarios.md``, ``deferred-locators-strategy.md`` y `[[calidad-appium-run-and-tags]]` sin cambios.
- Para extender proyectos iOS o Android existentes, usar `[[calidad-appium-brownfield]]`: detecta plataforma desde las capabilities del proyecto y respeta sus convenciones.

Ver también las restricciones declaradas en `[[calidad-appium-screenplay-android]]`.
