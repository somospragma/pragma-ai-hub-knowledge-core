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

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Este workflow **es naturalmente un caso de self-healing** del chapter: los locators provienen de Appium Inspector (humano) en el paso 3, pero el loop runtime habilita reparación asistida cuando el DOM mobile drifta entre versiones del APK. Auto-corrección aplica EXCLUSIVAMENTE a los `Target.the(...).located(...)` recién actualizados; NUNCA a Tasks, Questions o Interactions, ni a tests preexistentes del cliente.

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` porque por definición este workflow se ejecuta con device/emulador + Appium server + APK ya disponibles (son inputs obligatorios). Clientes regulados (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) defaultean a `dry-run` (entregar diff de locators sin aplicar). `scaffold-only` no aplica acá.
2. **Ejecutar** los 2 escenarios `@android @smoke` (ahora contra DOM real) vía `[[calidad-test-execution-orchestration]]`: `./gradlew clean test -Dcucumber.filter.tags=@smoke`. Capturar `target/site/serenity/` como evidencia.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky. Causas típicas: locator extraído mal en Appium Inspector, drift del DOM entre versiones del APK, `accessibilityId` no único, race condition con `WebDriverWait`, capability `automationName` desalineada.
4. Si triage habilita correcciones: invocar `[[test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` (multi-locator fallback en orden `accessibilityId → id → xpath`, LLM-driven selector repair contra el page source). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca volver al `TODO: update real locator`, nunca reemplazar la `Interaction` real (`TapOn`, `Enter`) por el flag en memoria, nunca debilitar `AppIsResponsive`, nunca downgrade a smoke trivial (`assertTrue(true)`) para forzar verde.
5. Reportar estado final: `success` (los 2 smokes pasan contra DOM real) | `partial` (algún locator quedó pendiente y requiere otra sesión con Appium Inspector) | `failed` (escalado a humano con stage, screenshot del Inspector, page source y locator propuesto).
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`. Si el guardrail CI del paso 6 detecta `TODO` residual, marca el reporte como `partial` automáticamente.

## Criterios de finalización

1. Cero `// TODO: update real locator` restantes en `src/`.
2. Los 2 escenarios `@android @smoke` siguen pasando (ahora contra DOM real).
3. `LoginTask.performAs` invoca al menos una `Interaction` real (`TapOn`, `Enter`, etc.).
4. `AppIsResponsive` valida visibilidad real del elemento principal.
5. Guardrail CI agregado (si aplica).
6. Opcional: ≥1 escenario `@android @proposed` implementado con step definitions concretas (deja de ser stub).
7. Los 2 escenarios `@android @smoke` ejecutados al menos una vez contra DOM real. Estado: `success` / `partial` / `failed` reportado.
8. Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
9. Si hubo correcciones aplicadas vía multi-locator fallback o LLM repair: audit log persistido con anti-cheating guardrails verificados (no se volvió a `TODO`, no se debilitó `AppIsResponsive`, no se downgrade a smoke trivial).
10. Si el modo es `dry-run`: diff de locators propuesto entregado; ningún cambio aplicado sin aprobación humana.
11. Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory`, `@accessibility` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).

Ver `[[appium-deferred-locators-strategy]]` para el rationale del patrón y `[[appium-smoke-vs-proposed-scenarios]]` para la división original.
