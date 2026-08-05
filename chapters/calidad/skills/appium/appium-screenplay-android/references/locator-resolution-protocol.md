
# Protocolo de resolución de locators (identidad ≠ capacidad)

## El principio

**El identificador del contrato garantiza IDENTIDAD, no CAPACIDAD.** Que un nodo de la jerarquía tenga el `resource-id`/`content-desc` del locator map no significa que ese nodo sea el que recibe clicks o texto: en Flutter (y otros frameworks) el identificador suele vivir en un **contenedor `clickable=false`**, y el elemento capaz (el `EditText` real, el nodo clickable) es un **descendiente o hermano** con los mismos bounds. La capacidad se resuelve **en runtime contra la jerarquía real** y se verifica por un **efecto externo** a la jerarquía (¿el backend recibió el payload? ¿navegó?). Fijar en un asset el XPath que funcionó en UNA app produce el mismo fallo silencioso en la siguiente — lo que se fija es este protocolo, no la expresión.

## Matriz empírica de estrategias (Flutter + UiAutomator2, verificada en campo)

| Estrategia | ¿Resuelve `Semantics(identifier:)`? | Nota |
|---|---|---|
| `AppiumBy.id("mi_identifier")` | **NO** (ni pelado ni con prefijo de paquete) | El `resource-id` está en la jerarquía pero el driver no lo resuelve por esta vía en Flutter |
| `AppiumBy.androidUIAutomator("new UiSelector().resourceId(\"mi_identifier\")")` | **SÍ** | Estrategia primaria Android para identifier |
| `AppiumBy.xpath("//*[@resource-id='mi_identifier']")` | SÍ | Equivalente; útil como base para descender al nodo capaz |
| `AppiumBy.accessibilityId("mi_identifier")` | NO — encuentra el **label**, no el identifier | `accessibilityId` = `content-desc` (semantics label) |
| `AppiumBy.accessibilityId("<semantics label>")` | SÍ para estrategia por label | La vía de proyectos que localizan por label/texto |

En iOS el identifier se proyecta a `accessibilityIdentifier` y el label a `@name`; los campos suelen ser **directamente localizables** (sin descender a un hijo). La resolución por plataforma se encapsula en una fábrica de Targets (una sola capa: `FlutterTargets.byIdentifier(...)` resuelta por `-Dappium.platform=android|ios`); los Page Objects y Tasks no cambian.

## Patrones de composición (del campo)

- **Contenedor por semantics → hijo capaz**: `//*[contains(@content-desc,"page:login_input:username")]/android.widget.EditText` — el patrón canónico para escribir en campos Flutter/Android. iOS no lo necesita (el accessibilityId apunta al campo).
- **Eje `descendant-or-self` con discriminante de capacidad**: `//*[@resource-id='X']/descendant-or-self::*[@clickable='true']` — cuando no se sabe la clase del nodo capaz. OJO: verificado en campo que el nodo capaz puede ser descendiente cuando el volcado indentado "parece" mostrar hermanos — la indentación de un dump NO es el árbol (parsear, no interpretar el formato).
- **Label ancla + `following-sibling`**: `//*[contains(@content-desc,"Ingresa tu clave:")]/following-sibling::android.widget.EditText` — cuando el campo no tiene semantics propio y el label sí.
- **Locators dinámicos**: plantilla `.locatedBy("//*[contains(@content-desc,\"{0}\")]")` + `.of(valor)` para listas/carruseles. Cuidado con el typo `${0}` (no sustituye y falla en silencio).
- **`content-desc` con `\n` embebido**: Flutter concatena label + texto visible con salto de línea; el locator debe replicarlo literal o usar `contains()`.
- **Pantallas nativas del sistema** (permisos): ahí sí `AppiumBy.id("com.android.permissioncontroller:id/permission_allow_button")` — no son Flutter.

## El procedimiento (obligatorio antes de escribir Targets)

1. **Volcar la jerarquía real** de la pantalla (`driver.getPageSource()` o `adb shell uiautomator dump`) y **parsearla como árbol** — nunca deducir topología de la indentación impresa.
2. **Enumerar los ejes candidatos** desde el nodo del identificador: self, descendientes capaces, hermanos con mismos bounds.
3. **Contar nodos por candidato**: el único conteo aceptable es **1**. Cero = el locator no resuelve; dos o más = ambigüedad (el driver tomará cualquiera y el fallo será intermitente). Prohibido "resolver" ambigüedad con índice posicional `[1]` o unión `|`.
4. **Validar por efecto externo**: ejecutar la interacción y verificar fuera de la jerarquía (payload en el log del mock, navegación efectiva, estado persistido). "El valor se ve en la jerarquía" NO es prueba de que llegó a la app.
5. **Candar con test unitario** (`FlutterTargetsTest` o equivalente): la resolución elegida queda protegida para que nadie la "simplifique" de vuelta (ej. a `AppiumBy.id`) sin que el build avise.

## Prohibiciones

- Índice posicional (`(//x)[2]`) y uniones `|` como resolución de ambigüedad: el orden de nodos no está garantizado.
- Acoplarse a la clase nativa cuando no es necesaria (las clases en Flutter son genéricas `android.view.View`; en un rediseño cambian).
- Resolver el mismo elemento en dos capas distintas (Target + XPath inline en la Task): una sola capa de resolución.
- **El identificador del mapa sigue siendo la única ancla**: los ejes de capacidad parten de él; jamás anclar en texto visible o posición cuando existe identificador del contrato.
- Self-healing sobre esto: puede re-resolver la CAPACIDAD (el eje) cuando la topología cambie, pero NUNCA relajar el discriminante hasta que "algo" haga match — eso reintroduce la ambigüedad y produce verdes falsos. Ver `[[calidad-test-self-healing]]`.

## Relación con el locator map y brownfield

- El locator map (`[[calidad-ui-locator-map-contract]]`) declara la **convención de identidad** (`semantics_identifier` o `semantics_label`); este protocolo resuelve la **capacidad** por pantalla. Registrar en el mapa la resolución verificada (`resolution_verified_<fecha>`) cuando se corra el procedimiento.
- **Brownfield**: antes de resolver nada, leer los Page Objects existentes — la resolución que el proyecto ya usa ES la convención detectada (ej. contenedor→EditText, label+sibling) y se reutiliza; no se introduce una segunda estrategia en paralelo.
