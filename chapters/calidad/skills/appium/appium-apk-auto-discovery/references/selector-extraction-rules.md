# Reglas de extracción de selectores

Por cada elemento descubierto durante el crawl, generar TODAS las alternativas de locator posibles, scoreárlas (ver `locator-confidence-scoring.md`), elegir la de mayor score como primaria, y persistir las demás como `fallback_candidates` en `.evidence/locators-discovered.json`.

## Prioridad (de más estable a menos)

1. **`resource-id`** — ID semántico declarado en el layout XML del developer. Sobrevive a cambios visuales, i18n y refactors de UI. **PREFERIR SIEMPRE**.
2. **`content-desc`** — Accessibility label. Estable porque los devs evitan cambiarlo (rompe accesibilidad). Útil para iconos sin `resource-id`.
3. **`text`** — Texto visible. Frágil por internationalization (i18n) y por copy changes. Usar solo si no hay `resource-id` ni `content-desc`.
4. **`xpath` con atributos** — Combinación de `class` + un atributo discriminante. Aceptable cuando los anteriores no aplican.
5. **`xpath` posicional** — Con índices `[1]/[2]/[3]`. **ANTI-PATTERN**. Último recurso, score muy bajo, marcar como healing candidate.

## Mapping a Java (AppiumBy)

```java
// 1. resource-id completo "com.example.app:id/login_button"
AppiumBy.id("com.example.app:id/login_button")
// O abreviado (UiAutomator2 resuelve el package prefix automáticamente):
AppiumBy.id("login_button")

// 2. content-desc "Iniciar sesión"
AppiumBy.accessibilityId("Iniciar sesión")

// 3. text "Login" (vía xpath, no hay AppiumBy.text directo)
AppiumBy.xpath("//*[@text='Login']")

// 4. xpath por atributos combinados
AppiumBy.xpath("//android.widget.Button[@content-desc='Continuar']")

// 5. UiSelector (cuando hace falta combinar text + clase + scrolling)
AppiumBy.androidUIAutomator(
    "new UiSelector().className(\"android.widget.Button\").text(\"Login\")"
)

// 6. UiSelector con scroll automático (útil para elementos en listas largas)
AppiumBy.androidUIAutomator(
    "new UiScrollable(new UiSelector().scrollable(true))" +
    ".scrollIntoView(new UiSelector().resourceId(\"com.example.app:id/item_42\"))"
)
```

## Reglas anti-frágil

### Nunca generar

- xpath posicional puro: `//android.widget.LinearLayout[1]/android.widget.Button[2]`.
- xpath con coordenadas absolutas o `bounds`.
- xpath con `@index` (cambia con scroll).
- Locators basados en `focused` o `selected` (estado transitorio).

### Siempre preferir

- Atributos semánticos: `@resource-id`, `@content-desc`.
- Combinación class + atributo cuando el atributo solo no es único.
- `accessibilityId` como segundo candidato canónico — además mejora la auditoría de accesibilidad de la app.

## Manejo de unicidad

Para cada locator candidato, verificar contra el view hierarchy de la pantalla:

- **Único en pantalla** → score alto, usar como primario.
- **No único pero único entre clickables** → score medio, usar con qualifier (ej. dentro de un container).
- **No único entre clickables** → bajar a la siguiente alternativa o combinar (class + resource-id).

## Casos especiales

### Elementos sin ningún atributo identificable

Si un clickable solo tiene `class` y `bounds`:

1. Buscar parent con `resource-id` y construir xpath relativo: `//*[@resource-id='com.example.app:id/container']/android.widget.Button`.
2. Si no hay parent identificable: usar xpath con `class` + posición del sibling. Score muy bajo. Marcar `HEALING_CANDIDATE`.
3. Documentar en `.evidence` la situación para que self-healing del runtime tenga contexto.

### EditText (campos de input)

Casi siempre tienen `resource-id`. Si no:

- Usar `content-desc` (los devs suelen poner hint accessibility).
- Como último recurso, `androidUIAutomator` con `new UiSelector().className("android.widget.EditText").instance(N)`.

### Items en RecyclerView / ListView

Los items dinámicos pueden no tener `resource-id` único (todos comparten el mismo). Estrategia:

- Locator basado en `text` del child relevante: `AppiumBy.xpath("//*[@resource-id='com.example.app:id/item_title' and @text='Producto X']")`.
- Marcar como `data_dependent: true` en el evidence para indicar que depende del contenido de la lista.

### Tabs / BottomNavigation

Los items suelen tener `content-desc` distintos pero el mismo `resource-id`. Preferir `accessibilityId` aquí.

## Output por elemento

Cada selector emitido genera una entrada con esta forma (persistida en `.evidence/locators-discovered.json`):

```json
{
  "screen_hash": "a3f2c1...",
  "screen_label": "LoginScreen",
  "element_label": "LoginButton",
  "primary": {
    "strategy": "id",
    "value": "com.example.app:id/login_button",
    "java": "AppiumBy.id(\"com.example.app:id/login_button\")",
    "score": 95
  },
  "fallbacks": [
    {
      "strategy": "accessibility id",
      "value": "Iniciar sesión",
      "java": "AppiumBy.accessibilityId(\"Iniciar sesión\")",
      "score": 85
    },
    {
      "strategy": "xpath",
      "value": "//android.widget.Button[@text='Iniciar sesión']",
      "java": "AppiumBy.xpath(\"//android.widget.Button[@text='Iniciar sesión']\")",
      "score": 55
    }
  ],
  "metadata": {
    "class": "android.widget.Button",
    "clickable": true,
    "bounds": "[100,500][980,620]"
  }
}
```

## Naming de elementos (`element_label`)

Derivar el nombre del elemento Java desde:

1. `resource-id` (sin package): `login_button` → `LoginButton`.
2. `content-desc`: `Iniciar sesión` → `IniciarSesionButton` (PascalCase, sin tildes/espacios).
3. `text`: igual que content-desc.
4. Fallback: `Element{N}` con `N` autoincremental por pantalla.

El nombre se usa para generar el campo Java del Page Object: `private final By loginButton = ...`.
