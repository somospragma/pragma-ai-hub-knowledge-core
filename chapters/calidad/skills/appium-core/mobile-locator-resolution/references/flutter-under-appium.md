
# Apps Flutter bajo Appium — y el prototipo de app pre-desarrollo

## Qué ve Appium en una app Flutter (y por qué importa)

Flutter no usa widgets nativos: dibuja su UI en un canvas propio. Lo que UiAutomator2 encuentra **no es la UI sino el árbol de semántica** que Flutter proyecta a la accesibilidad de Android. Consecuencias directas:

- **`Semantics(identifier: ...)`** (Flutter 3.19+) se proyecta como `resource-id` en la jerarquía Android y `accessibilityIdentifier` en iOS. **PERO — verificado en campo — `AppiumBy.id` NO lo resuelve** (ni pelado ni con prefijo de paquete): la resolución correcta en Android es `AppiumBy.androidUIAutomator("new UiSelector().resourceId(\"...\")")` o XPath `//*[@resource-id='...']`. La matriz completa de estrategias y el procedimiento de verificación están en `[[calidad-mobile-locator-resolution]]` — aplicarlo SIEMPRE antes de escribir Targets.
- **`semanticsLabel`** se expone como `content-desc` → `AppiumBy.accessibilityId`. Es la estrategia de proyectos que localizan por label/texto visible (válida y muy común en campo); su costo: los labels cambian con i18n, así que el catálogo de textos pasa a ser parte del contrato.
- **Identidad ≠ capacidad**: el nodo del identifier suele ser un contenedor `clickable=false`; el elemento que recibe clicks/texto es un descendiente (o hermano con los mismos bounds) — típicamente el `android.widget.EditText` real en campos. Flutter llega a generar **dos nodos `EditText` con bounds idénticos** por campo. Escribir "no funciona" casi siempre significa que el locator apunta al nodo equivocado, no que la API falle. Resolución: el protocolo de locators.
- Las clases de elemento son genéricas (`android.view.View`): **selectores por clase nativa no sirven** como discriminante principal.
- **Race del árbol de semántica**: la app puede tardar varios segundos (medido en campo: ~9s) en publicar el árbol tras el `Displayed` de la activity; buscar un elemento a los 0.7s devuelve lista vacía. La espera correcta es **polling de presencia del identificador ancla** de la pantalla (tope 20-30s), nunca `Thread.sleep` ni asumir que "la app abrió = el árbol está".
- **El árbol nunca queda "idle" y eso bloquea CADA comando**: UiAutomator2 espera a que la interfaz se aquiete antes de resolver un `find` o un `getPageSource`, hasta agotar `waitForIdleTimeout` (default **10 000 ms**). Un árbol de semántica que emite eventos de forma continua mientras hay animaciones nunca le da ese estado, así que la espera se paga completa una y otra vez. Medido en campo sobre dispositivo físico con las animaciones del sistema en `1.0`: **un solo `getPageSource` tardó 111 segundos** en arranque en frío, y el siguiente sobre la misma pantalla, 121 ms. En la granja no se reproduce porque los dispositivos vienen con las escalas de animación en `0`. Contramedida —`disableWindowAnimation` más `waitForIdleTimeout` y `actionAcknowledgmentTimeout` bajos en el perfil local— y protocolo de diagnóstico en [[calidad-appium-wdio-greenfield]] (consultar `references/local-run-stalls-and-host-timers.md` en su subfolder). **Es la causa más cara de confundir con "la app Flutter es lenta"**: la app no es lenta, el driver está esperando.
- Semántica lazy en scrollables, quirks del IME y patrones de gesto: ver `[[calidad-mobile-interactions]]`.

**Contrato con desarrollo** (extiende `[[calidad-ui-locator-map-contract]]`): para apps Flutter, el equipo dev declara en el mapa su convención (`semantics_identifier` o `semantics_label`) y se compromete a las prácticas que hacen automatizable cada elemento: rol (`button:`, `header:`, `textField:`), `ExcludeSemantics` en componentes compuestos (un componente = UN nodo; coincidencias múltiples = falta `ExcludeSemantics`), **`explicitChildNodes: true` en campos editables** (es lo que conserva el nodo del campo alcanzable y escribible), `enabled`/`value`/`checked` reflejando estado real, y mensajes de error como `liveRegion` (esperables por la suite).

## Variante: appium-flutter-integration-driver

Existe un driver específico (`appium driver install --source npm appium-flutter-integration-driver`, basado en `integration_test` — sucesor del deprecado appium-flutter-driver). Exige colaboración de dev: dependencia `appium_flutter_server` en `pubspec.yaml` y build con flags especiales. Usarlo SOLO cuando el equipo dev lo adopte formalmente; no es la base del chapter porque acopla la prueba al build de desarrollo. Con el árbol de semántica + UiAutomator2 + el protocolo de locators se cubre el caso general.

## Prototipo de app (opt-in pre-desarrollo) — la tecnología la dicta la app real

Cuando la app real no existe, el agente PUEDE generar una app descartable desde el Figma + locator map para ejecutar los tests en emulador antes del desarrollo. **Solo a elección explícita del usuario, nunca por defecto**, con la advertencia obligatoria: valida la mecánica de la suite, no el producto.

**Insumo de máximo valor si existe**: un **prototipo interactivo de diseño** (export navegable de Figma Make / design capture) es la especificación del prototipo — se recorre headless y de él salen textos exactos, datos, formato de moneda, estados y grafo de navegación. Ver [[calidad-playwright-greenfield]] (consultar `references/interactive-design-prototype-source.md` en su subfolder). Sin explotarlo, el prototipo se construye por inferencia y el gate de aceptación lo va a rebotar.

**Regla previa innegociable — preguntar la tecnología de la app real**: lo que Appium "ve" depende de con qué se construya (árbol de semántica en Flutter; widgets nativos con `resource-id` de layout en Android nativo; views con `testID` en React Native). El prototipo se construye con la **misma tecnología declarada de la app real**; una distinta produce una jerarquía diferente y valida en falso — está prohibido. Tecnología sin definir → no hay prototipo fiel posible: camino oficial (deferred + ejecución diferida). Lo que sigue documenta el **caso Flutter**; para nativa/RN aplicar el mismo principio con la convención de esa tecnología.

### Contrato de fidelidad del prototipo

El prototipo replica **lo que la app real publicará hacia afuera**, no lo que le conviene al test:

1. **La convención de semántica declarada** en el locator map (`semantics_identifier` o `semantics_label`) — si el equipo dev localizará por label, el prototipo usa labels con los textos exactos del catálogo.
2. **Si existe documento de prácticas del design system del cliente, ese documento ES la especificación del prototipo**: roles, `ExcludeSemantics` en compuestos, `explicitChildNodes: true` en campos, `enabled`/`value` reales, labels por defecto sin traducir, catálogo de textos idéntico carácter a carácter (tildes, signos de apertura, mayúsculas) en todos los idiomas soportados, y rutas de navegación con las mismas cadenas.
3. **Estados realistas por pantalla**: loading / éxito / error / vacío distinguibles **en el árbol de semántica** (no solo visualmente), errores como `liveRegion`. El identificador ancla de cada pantalla se expone **solo cuando la pantalla es interactuable** — exponerlo antes le enseña a la suite un timing falso.
4. **PROHIBIDO ajustar la semántica del prototipo para que una prueba pase** (ej. agregar `MergeSemantics` para "arreglar" un locator): es resolver el síntoma en el único lugar donde no se podrá cuando llegue la app real. Criterio único: ¿la app real lo hará así? Se verifica contra el design system o preguntando a dev — nunca lo decide la conveniencia del test. (Regla anti-cheating del chapter extendida al prototipo.)

### Restricciones que lo mantienen trivial

1. Un solo `main.dart` (o un archivo por pantalla): `MaterialApp` + rutas del locator map + formularios. Sin state management, sin paquetes salvo `http`.
2. **Cero lógica de negocio y cero datos hardcodeados**: los datos y respuestas vienen del mock Mockoon. Backend por `--dart-define`:

```bash
flutter build apk --debug --dart-define=BASE_URL=http://10.0.2.2:3010/api
```

Un prototipo con sus datos embebidos (listas de productos, saldos, cuotas en el propio código) **no cumple el contrato**: la suite pasará sin que el mock intervenga y el contrato del backend nunca se ejercita. El punto 5 del gate de aceptación existe exactamente para detectarlo.

3. Vive en `mocks/app-prototype/`, fuera del árbol de tests; se genera desde el mapa, no se mantiene. Si el mapa cambia, se regenera.
4. Emulador: bootstrap según `[[calidad-appium-apk-auto-discovery]]` (consultar `adb-and-emulator-bootstrap.md` en su subfolder); `adb install` del APK debug.

### Receta operativa del build (lo que la práctica cobró)

- **`flutter create` PRIMERO, siempre**: un prototipo con solo `lib/` y `pubspec.yaml` no compila (`flutter build apk` falla por falta de la estructura `android/`). Secuencia correcta:

```bash
flutter create . --org co.com.pragma --project-name <nombre_snake_case> --platforms android
# luego: sobrescribir lib/, ajustar pubspec, crear assets/ si se declaran fuentes o imágenes
flutter pub get
```

- **Verificar el package real tras instalar** (no asumirlo): `flutter create` compone `org` + `project_name` tal cual, con guion bajo (`co.com.pragma.mi_prototipo`). Confirmar con `adb shell pm list packages | grep <nombre>` y usar ese valor exacto en `serenity.conf`.
- `AndroidManifest.xml`: permiso `INTERNET` + `network_security_config` con cleartext hacia `10.0.2.2` (sin esto la app no alcanza el mock y el fallo parece de la suite).
- Eliminar el widget test del andamio de `flutter create` (referencia clases reemplazadas y rompe el build).
- Síntoma `Activity class ... does not exist` con la clase ausente del DEX en andamios recientes → verificar que el plugin de Kotlin esté **aplicado** en `android/app/build.gradle.kts` (algunas versiones lo declaran `apply false` y no lo aplican al módulo). Es dependiente de versión: tratarlo como síntoma→diagnóstico, no como paso fijo.
- Mismo síntoma con el APK sano → **bisecar el emulador primero** (¿otra app de usuario resuelve? → AVD corrupto: `-wipe-data`), ver `[mobile-evidence-and-triage](mobile-evidence-and-triage.md)`.
- Flutter SDK >= 3.19 si la convención es `identifier` (versiones previas no lo proyectan — el preflight lo valida; construir con `semanticsLabel` "mientras tanto" sería validar contra un contrato distinto al acordado).

### Gate de aceptación del prototipo (ANTES de escribir un solo test)

El prototipo no verificado no se usa, y "verificado" son **cinco comprobaciones, no una**. Todas se ejecutan sobre el prototipo instalado y su resultado se persiste en `.evidence/prototype-acceptance.json`. Cada fallo aquí cuesta minutos; descubierto por un test rojo cuesta una sesión (verificado en campo: los defectos de datos y de pantallas incompletas se encontraron uno a uno, a golpe de rebuild de APK, cuando este gate los habría listado de entrada).

**1. Paridad de identificadores.** Volcar la jerarquía de cada pantalla y correr los selectores del locator map uno a uno: cada selector devuelve **exactamente una** coincidencia. Cero = falta el Semantics; múltiple = falta `ExcludeSemantics` (tan defectuoso como ninguna). Repetir en el idioma alterno si hay i18n.

**2. Fidelidad de textos.** Cada texto visible del prototipo se compara **carácter a carácter** con el catálogo del diseño de entrada (Figma, prototipo interactivo, HU). Tildes, signos de apertura, mayúsculas, espacios y **formato de moneda** (`"$180.000"` vs `"180.000 $"`) son parte del contrato: una divergencia rompe selectores por texto y aserciones de contenido.

**3. Fidelidad de datos.** Los valores del prototipo se **copian de la HU y del diseño**, no se recuerdan: saldos, cuotas, montos mínimos/máximos, nombres. Verificar además la **coherencia aritmética** que el feature exige (`cuota₁ + cuota₂ = total multiproducto`). En campo, dos productos quedaron con la misma cuota y un saldo quedó en 1.458.000 donde la HU decía 487.600 — el segundo nunca se detectó.

**4. Cada CA del feature es recorrible a mano.** Antes de escribir tests, recorrer el prototipo ejecutando cada criterio de aceptación del alcance: si un escenario no se puede completar (una pantalla no lista el segundo producto, un botón no navega, un estado no existe), el prototipo está **incompleto** y se completa ahora. Un test no puede pasar por un camino que la app no tiene.

**5. Tráfico real contra el mock.** Ejecutar un flujo end-to-end y **verificar en el log del Mockoon que llegaron las peticiones esperadas**. Si el log está vacío, el prototipo no está consumiendo el mock: sus datos están hardcodeados y toda la suite validará una app autónoma, no el contrato. Es un fallo bloqueante — en campo pasó desapercibido y la corrida se cerró declarando `mock_evidence.tool: mockoon` sin que la app hubiera hecho una sola llamada.

Registrar `parity_verified_<fecha>` en el locator map y el resultado de las cinco en `.evidence/prototype-acceptance.json` (lo consume el delivery gate). Recién entonces corre el smoke gate de la suite.

**Los arreglos al prototipo se verifican contra la fuente, no contra el test.** Cuando el gate detecta una desviación, la corrección se toma del diseño/HU/prototipo interactivo (que es donde está la verdad), nunca de lo que le convenga al escenario. Ajustar el prototipo "hasta que el test pase" es la variante de anti-cheating que este gate previene.

### Prerequisito y fallback

El SDK de la tecnología declarada (Flutter SDK para este caso) es condición de preflight; sin SDK, el camino estándar (scaffold + deferred + ejecución diferida) — nunca un mock en otra tecnología.

### Qué NO valida el prototipo (declaración obligatoria al cierre)

Lógica real de la app, plugins nativos, diálogos de permisos, performance, navegación real. El delivery gate registra `app_prototype: true` en `mock_evidence` y cierra con `certification: pending_real_integration`; la suite se re-ejecuta contra la app real al llegar (previa validación de drift del locator map).

### Flutter Web

Si el producto es Flutter multiplataforma, **el mismo prototipo Flutter sirve para web** (`flutter build web`) — pero la suite web (Playwright) tiene sus propias reglas: árbol `flt-semantics` que hay que ACTIVAR al arranque, selectores por `aria-label`/rol, campos como `<input>` reales solo con `explicitChildNodes`. Ver [[calidad-playwright-greenfield]] (consultar `references/front-prototype-recipe.md`).
