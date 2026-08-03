
# Apps Flutter bajo Appium — y el prototipo Flutter pre-desarrollo

## Qué ve Appium en una app Flutter (y por qué importa)

Flutter no usa widgets nativos: dibuja su UI en un canvas propio. Lo que UiAutomator2 encuentra **no es la UI sino el árbol de semántica** que Flutter proyecta a la accesibilidad de Android. Consecuencias directas para el diseño de locators y tests:

- **`Semantics(identifier: ...)`** (Flutter 3.19+) se mapea a `resource-id` en la jerarquía Android (`AccessibilityNodeInfo.setViewIdResourceName`) y a `accessibilityIdentifier` en iOS → `AppiumBy.id` funciona con el stack estándar del chapter (UiAutomator2), **sin driver especial**. Es la estrategia primaria.
- `semanticsLabel` se expone como `content-desc` → `AppiumBy.accessibilityId`. Válido como secundario, pero el label es texto de accesibilidad real (puede cambiar con i18n); el identifier es estable por diseño.
- Las clases de elemento son genéricas (`android.view.View`, no `android.widget.Button`): **selectores por clase nativa no sirven** contra Flutter.
- Semántica lazy en scrollables: los elementos fuera de viewport pueden no existir aún en la jerarquía — los scrolls se diseñan con `UiScrollable`/gestos y espera del identifier, no asumiendo presencia.
- Entrada de texto: los campos Flutter tienen quirks con el IME; preferir `sendKeys` sobre el elemento enfocado y validar con el valor semántico.
- Si la app no fuerza la creación del árbol, puede requerir `SemanticsBinding`/`ensureSemantics` activo; con `Semantics(identifier:)` explícitos el nodo se crea siempre.

**Contrato con desarrollo** (extiende `[[calidad-ui-locator-map-contract]]`): para apps Flutter, el compromiso del equipo dev es envolver cada elemento interactivo del mapa en `Semantics(identifier: '<valor del mapa>')`. La columna `mobile` del locator map declara la estrategia: `semantics_identifier` (preferido) o `semantics_label`.

## Variante: appium-flutter-integration-driver

Existe un driver específico (`appium driver install --source npm appium-flutter-integration-driver`, basado en `integration_test` — sucesor del deprecado appium-flutter-driver). Exige colaboración de dev: dependencia `appium_flutter_server` en `pubspec.yaml` y build con flags especiales. Usarlo SOLO cuando el equipo dev lo adopte formalmente; no es la base del chapter porque acopla la prueba al build de desarrollo. Con Semantics identifiers + UiAutomator2 se cubre el caso general.

## Prototipo de app (opt-in pre-desarrollo) — la tecnología la dicta la app real

Equivalente móvil del front prototype web: cuando la app real no existe, el agente PUEDE generar una app descartable desde el Figma + locator map para ejecutar los tests en emulador antes del desarrollo. **Solo a elección explícita del usuario, nunca por defecto**, con la advertencia obligatoria: el prototipo no es fiel a la app real — valida la mecánica de la suite (locators, gestos, correlación con el backend mock), no el producto.

**Regla previa innegociable — preguntar la tecnología de la app real**: lo que Appium "ve" depende de con qué se construya la app (árbol de semántica en Flutter; widgets nativos con `resource-id` de layout en Android nativo; views con `testID` en React Native). El prototipo se construye con la **misma tecnología declarada de la app real**; una distinta produce una jerarquía diferente y valida en falso — está prohibido. Si la tecnología aún no está definida, no hay prototipo fiel posible: camino oficial (deferred + ejecución diferida). Lo que sigue documenta en detalle el **caso Flutter**; para nativa Android o React Native aplicar el mismo principio (identificadores del mapa en la convención nativa de esa tecnología: `android:id` / `testID`) con receta análoga.

### Restricciones que lo mantienen trivial

1. Un solo `main.dart` (o un archivo por pantalla): `MaterialApp` + rutas del locator map + formularios. Sin state management, sin arquitectura, sin paquetes salvo `http`.
2. Cada elemento interactivo envuelto en `Semantics(identifier:)` con los valores **exactos** del mapa — el prototipo es la especificación ejecutable del contrato con dev.
3. Cero lógica de negocio: los datos y respuestas vienen del mock Mockoon. Backend por `--dart-define`:

```bash
flutter build apk --debug --dart-define=BASE_URL=http://10.0.2.2:3010/api
```

(`10.0.2.2` es el alias del host desde el emulador Android — el Mockoon corre en la máquina.)

4. Vive en `mocks/app-prototype/` fuera del árbol de tests; se genera, no se mantiene.
5. Emulador: bootstrap según `[[calidad-appium-apk-auto-discovery]]` (consultar `adb-and-emulator-bootstrap.md` en su subfolder). El APK debug del prototipo se instala con `adb install`.

### Prerequisito y fallback

El SDK de la tecnología declarada (Flutter SDK para este caso) es condición de preflight para la opción; sin SDK, el camino es el estándar (scaffold + deferred locators + ejecución diferida) — nunca un mock en otra tecnología: si la app real será Flutter, un prototipo nativo/WebView produce una jerarquía distinta y valida en falso (y viceversa).

### Qué NO valida el prototipo (declaración obligatoria al cierre)

Lógica real de la app, plugins nativos, diálogos de permisos, performance, navegación real. El delivery gate registra `app_prototype: true` en `mock_evidence` y cierra con `certification: pending_real_integration`; la suite se re-ejecuta contra la app real al llegar (previa validación de drift del locator map).
