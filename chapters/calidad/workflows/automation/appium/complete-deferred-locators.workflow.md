---
id: complete-deferred-locators
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Reemplaza los placeholders TODO de LoginPage con selectores reales extraídos con Appium Inspector y promueve los smoke a validación real.
tags: [appium, locators, inspector, smoke, technical-debt, completion]
---

# Workflow — Completar locators diferidos

## Cuándo usar

Después de generar el scaffold con `[[generate-appium-screenplay-android]]`, cuando el equipo ya tiene el APK funcional instalado en un dispositivo/emulador y va a reemplazar los placeholders `// TODO: update real locator` por selectores reales para que los `@smoke` validen contra el DOM real (en vez del flag en memoria).

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| Proyecto generado | Sí | Output de `[[generate-appium-screenplay-android]]`. |
| APK funcional | Sí | El mismo `apk_path` validado. |
| Device/emulador Android | Sí | Conectado y visible en `adb devices`. |
| Appium Server | Sí | Corriendo en `appium_server_url` (default `http://127.0.0.1:4723`). |

## Pasos

### 1. Instalar APK en emulador/device
```bash
adb install -r /path/to/app.apk
adb shell am start -n {app_package}/{app_activity}
```

### 2. Abrir Appium Inspector
Configurar capabilities desde `android.conf` o `serenity.conf`. Iniciar sesión y navegar a la pantalla de login.

### 3. Extraer selectores reales
Por cada elemento (`USERNAME`, `PASSWORD`, `LOGIN_BUTTON`), obtener el selector más estable en orden de preferencia:
1. `AppiumBy.accessibilityId("...")`
2. `AppiumBy.id("com.empresa.app:id/...")`
3. `AppiumBy.xpath("//android.widget.EditText[@content-desc='...']")` (último recurso).

### 4. Reemplazar constantes en `LoginPage.java` (y otras pages)
```java
// Antes
// TODO: update real locator
public static final Target USERNAME = Target.the("Username field").located(AppiumBy.id("login_username"));

// Despues
public static final Target USERNAME = Target.the("Username field").located(AppiumBy.id("com.empresa.app:id/etUsername"));
```
Quitar los comentarios `// TODO: update real locator`.

### 5. Reemplazar `LoginTask.performAs` para invocar gestos UI reales
```java
@Override
public <T extends Actor> void performAs(T actor) {
    actor.attemptsTo(
        Enter.theValue(username).into(LoginPage.USERNAME),
        Enter.theValue(password).into(LoginPage.PASSWORD),
        TapOn.theElement(LoginPage.LOGIN_BUTTON)
    );
}
```
Reforzar `AppIsResponsive` para validar visibilidad real (`LoginPage.LOGIN_BUTTON.resolveFor(actor).isVisible()` en vez del flag en memoria).

### 6. Agregar guardrail CI (opcional pero recomendado)
```bash
if grep -R "// TODO: update real locator" src/ ; then
  echo "Locators diferidos pendientes — bloqueando build productivo"
  exit 1
fi
```
Agregar este step al pipeline CI para que falle si quedan TODOs.

## Criterios de finalización

1. Cero `// TODO: update real locator` restantes en `src/`.
2. Los 2 escenarios `@android @smoke` siguen pasando (ahora contra DOM real).
3. `LoginTask.performAs` invoca al menos una `Interaction` real (`TapOn`, `Enter`, etc.).
4. `AppIsResponsive` valida visibilidad real del elemento principal.
5. Guardrail CI agregado (si aplica).
6. Opcional: ≥1 escenario `@android @proposed` implementado con step definitions concretas (deja de ser stub).

Ver `[[appium-deferred-locators-strategy]]` para el rationale del patrón y `[[appium-smoke-vs-proposed-scenarios]]` para la división original.
