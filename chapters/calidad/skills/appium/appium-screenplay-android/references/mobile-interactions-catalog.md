
# Catálogo de interacciones mobile (patrones de experto)

Repertorio destilado de proyectos reales de automatización sobre apps Flutter (aplica igual a nativas, ajustando locators). **Regla brownfield primero**: si el proyecto existente ya tiene Interactions/utilidades propias (Scroll, HideKeyboard, PressKey...), detectarlas y REUTILIZARLAS — son la convención del proyecto; no introducir un segundo repertorio en paralelo.

## Escritura en campos de texto — el canon

```java
WaitUntil.the(CAMPO, isVisible()).forNoMoreThan(12).seconds(),
Click.on(CAMPO),                 // 1. foco (abre el IME) — NUNCA escribir sin foco previo
Enter.theValue(valor).into(CAMPO),  // 2. escritura sobre el nodo CAPAZ (ver locator-resolution-protocol)
HideKeyboard.perform(),          // 3. cerrar el IME — tapa los controles inferiores en Flutter
```

- `Enter.theValue`/`sendKeys` **funcionan** en Flutter cuando apuntan al nodo capaz (el `EditText` real). Si "no escribe", el sospechoso #1 es el locator (nodo contenedor), no la API — ver el protocolo de resolución.
- **Después de abrir/cerrar el teclado el layout cambia**: re-scroll para revelar el botón de submit antes de tocarlo (patrón: `Scroll.untilVisibleTarget(BOTON)` post-escritura).
- **Limpiar campos**: `element.clear()` es poco fiable en Flutter. Alternativas en orden: botón de limpiar de la propia UI (si el design system lo expone), o `DeleteKey` (N pulsaciones de `AndroidKey.DEL` con el campo enfocado).
- iOS: el teclado no suele bloquear el flujo — `HideKeyboard` normalmente innecesario; los campos son directamente localizables.

## Campos pin/OTP (widgets que no aceptan sendKeys)

Cuando el widget de pin rechaza `Enter.theValue`: click en el primer dígito (foco + IME) y **key events nativos** dígito a dígito (`driver.pressKey(new KeyEvent(AndroidKey.DIGIT_n))`). Costos documentados: es Android-only (en iOS: `Enter.theValue` suele funcionar, o tap sobre las teclas del teclado `XCUIElementTypeKey[@name="n"]`); y **los key events NO aplican Shift** — para mayúsculas hace falta `KeyEventMetaModifier.SHIFT_ON` o el texto llega en minúsculas. Por eso es un **fallback**, no el default.

## Taps y gestos — W3C Actions, nunca TouchAction

`TouchAction` está deprecado. Todo gesto manual usa `PointerInput` + `Sequence`:

- **Tap por coordenadas** (último recurso, ej. área sin nodo): pointer move → down → up.
- **Scroll vertical robusto**: swipe de **media pantalla** (de `h/2` a `h/4`) con **~700 ms** de duración — deliberadamente corto y lento para que Flutter no dispare fling con inercia (un swipe rápido de pantalla completa se pasa de largo). En bucle con presupuesto de intentos, verificando en cada vuelta si el Target ya es visible+enabled. El scroll es best-effort: no falla si no encuentra — el fallo real y legible lo produce el `Click` posterior.
- **Scroll dentro de contenedor** (dropdowns, listas internas): mismas mecánicas pero el área se calcula desde los bounds del elemento contenedor, no de la ventana.
- **Carruseles horizontales**: drag desde el centro del elemento hasta el borde de pantalla (LEFT/RIGHT), 500 ms.
- **Semántica lazy de Flutter**: los elementos fuera de viewport pueden NO existir aún en la jerarquía — el patrón es scroll + espera de presencia del identificador, nunca asumir presencia.

## Esperas — política de tres capas

1. **Explícitas por intención**: `WaitUntil.the(X, isVisible()).forNoMoreThan(N).seconds()` con presupuestos declarados por tipo (arranque de pantalla 12-30s, elemento post-interacción 3-5s, evento externo tipo correo/push 60s). `isClickable()` para botones antes de tocarlos.
2. **Por Target inline**: `TARGET.waitingForNoMoreThan(Duration.ofSeconds(N))` en Questions.
3. **`serenity.step.delay`** (500-1000 ms) como amortiguador global de animaciones Flutter — es un tradeoff declarado (ralentiza toda la suite); documentarlo en el STRATEGY, no esconderlo.

**Sobre `isVisible()` en Flutter**: los nodos contenedores pueden reportar visibilidad de forma poco fiable. Para "pantalla lista" la espera correcta es **presencia del identificador ancla** de la pantalla + un efecto observable, no visibilidad de un contenedor. `Thread.sleep`/`Wait.theSeconds` solo para eventos genuinamente asíncronos externos (y encapsulado como Interaction para que aparezca en el reporte).

## Pantallas condicionales y recuperación de estado

- **`Check.whether(Question).andIfSo(...).otherwise(...)`** para todo lo que puede o no aparecer: diálogo de dispositivo confiable, pantalla de permisos, modal de biometría, onboarding. La rama se decide por presencia, no por orden fijo.
- **Questions condicionales que NO explotan**: capturan `TimeoutException` y devuelven `false` con log — así el `Check.whether` puede decidir. (Distinto de las Questions contractuales de verificación, que sí deben fallar fuerte.)
- **Estado sucio del SUT**: si el flujo requiere un estado inicial (sin tarjeta activa, sin compañero guardado), verificarlo y **limpiarlo primero** (deshacer por UI, por API o por DB según lo que el proyecto disponga) — el escenario construye su precondición, no la asume.
- **Escenarios auto-limpiantes**: lo que el escenario activa, lo desactiva al final (biometría, toggles) para no contaminar al siguiente.
- **Permisos nativos**: `autoGrantPermissions: true` (Android) / `autoDismissAlerts: true` (iOS) como primera línea; los diálogos propios de la app se manejan con `Check.whether`.

## Estado de datos entre escenarios

Diseñarlo ANTES de la primera corrida (no descubrirlo como falso rojo dependiente del orden):

- **Contra mock**: purga del estado del Mockoon en hook `@Before` (`POST /mockoon-admin/state/purge` con `MOCKOON_ADMIN_API_TOKEN`) — cada escenario arranca del mismo estado. Ver el template de Hooks en `templates.md`.
- **Contra ambiente real**: o el escenario trae sus seeds y limpia lo suyo (API/DB), o los valores esperados se calculan desde el estado leído al inicio (`remember` saldo inicial → esperar `inicial - monto`), nunca hardcodear un valor que otro escenario puede haber movido.
- **Memoria del actor** (`remember`/`recall`) para correlación dentro del escenario (saldos iniciales, ids generados, timestamps para filtrar OTP/correos).

## Acceso al driver desde Interactions

`BrowseTheWeb.as(actor).getDriver()` devuelve un `WebDriverFacade` de Serenity; para APIs de Appium (hideKeyboard, pressKey, executeScript `mobile: *`) hay que **desenvolver** con `getProxiedDriver()` (o castear según topología). Encapsular en un helper único (`AppiumDriverOf.theActor(actor)`) y — regla dura — **si el helper no puede obtener el driver, LANZA excepción**: un `return null` con fallback silencioso produce interacciones que "corren" sin ejecutarse (verificado en campo: la implementación nueva nunca se invocó y se iteró a ciegas sobre ella).

## Verificaciones que valen (Questions contractuales)

Asertar **contenido contra el contrato**, no visibilidad: el saldo parseado y comparado con el valor esperado, el mensaje de error comparado con el `message` exacto del `ApiError` del spec, el comprobante contra su patrón (`^TRX-[0-9]{6}$`). "Una tarjeta de saldo vacía pasa un assert de visibilidad" — las Questions contractuales son lo que detecta el gap. Cuando Flutter colapsa una card en un solo nodo, el patrón es leer el `content-desc` completo y asertar `allOf(containsString(...))` sobre las piezas esperadas, o regex para extraer el valor numérico.
