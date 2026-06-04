# Estrategia de crawling

El crawler recorre la app de forma sistemática pero conservadora: privilegia cobertura sobre profundidad, evita bucles, y nunca ejecuta acciones destructivas (logout, delete account, pagos). El objetivo no es probar la app sino mapear pantallas y elementos para extraer selectores reales.

## Principios

1. **Determinismo por hash de pantalla**: cada pantalla se identifica por hash SHA-1 del XML del view hierarchy, normalizado (quitar coords absolutos, timestamps, IDs efímeros). Dos capturas con el mismo hash = misma pantalla; no recurrir.
2. **Cobertura amplitud-primero (BFS)**: explorar todos los clickables de la pantalla actual antes de profundizar.
3. **Profundidad máxima 5**: a partir de nivel 5, dejar de recurrir aunque haya pantallas nuevas. Reportarlo como `coverage_truncated_at_depth: 5`.
4. **Time budget 10 minutos**: si se cumple, abortar limpiamente y reportar `partial` con lo descubierto hasta ese punto.
5. **Read-only mindset**: nunca interactuar con elementos cuyo `content-desc` o `text` matchea patrones destructivos (`eliminar`, `borrar`, `delete`, `logout`, `cerrar sesión`, `pagar`, `confirmar compra`, `enviar`, `submit payment`).

## Algoritmo

```
visited_screens = {}            # hash -> {selectors_found, depth, parent_hash}
queue = [(initial_screen_hash, depth=0, parent=None)]

while queue and time_budget_remaining() and depth_overall < 5:
    screen_hash, depth, parent = queue.pop(0)
    if screen_hash in visited_screens:
        continue
    visited_screens[screen_hash] = {...}

    source_xml = appium.get_source()
    clickables = parse_clickables(source_xml)   # filtrar clickable=true & enabled=true & displayed=true
    scrollables = parse_scrollables(source_xml)

    # 1. Extraer selectores de todos los clickables visibles (NO clickear todavía)
    for el in clickables:
        emit_selector_candidate(screen_hash, el)

    # 2. Swipe en scrollables para descubrir más items
    for scroll in scrollables:
        swipe_within(scroll)
        new_source = appium.get_source()
        new_hash = hash_normalized(new_source)
        if new_hash != screen_hash:
            # se reveló contenido nuevo: extraer y continuar
            for el in parse_clickables(new_source):
                emit_selector_candidate(new_hash, el)

    # 3. Tap en cada clickable NO destructivo (top-to-bottom, left-to-right por bounds)
    for el in clickables_sorted_by_bounds(clickables):
        if is_destructive(el):
            log_skipped(el, reason="destructive_pattern")
            continue
        appium.tap(el)
        sleep(1)
        post_tap_source = appium.get_source()
        post_tap_hash = hash_normalized(post_tap_source)
        if post_tap_hash != screen_hash:
            queue.append((post_tap_hash, depth+1, screen_hash))
        appium.back()
        sleep(0.5)
        # validar que volvimos al hash anterior; si no, intentar back adicional o re-launch
        if hash_normalized(appium.get_source()) != screen_hash:
            recover_to(screen_hash)   # ver "recuperación de contexto"
```

## Filtrado de clickables

Incluir solo nodos que cumplan TODAS:

- `clickable="true"`
- `enabled="true"`
- `displayed="true"`
- `bounds` dentro de la pantalla visible (no `[0,0][0,0]`)

Excluir clases típicamente decorativas: `android.view.ViewGroup` raíz, contenedores sin `resource-id` ni `content-desc`.

## Normalización del XML para hash

Antes de hashear:

1. Quitar atributo `bounds` (coords varían por densidad/orientación).
2. Quitar atributo `index` (cambia con scroll).
3. Quitar atributos `focused`, `selected` (estado transitorio).
4. Ordenar atributos alfabéticamente por nodo.
5. Hash SHA-1 del XML resultante.

Esto evita que dos capturas de la misma pantalla con scroll diferente cuenten como pantallas distintas.

## Swipe para scrolls

Detectar contenedores cuya `class` matchee:

- `androidx.recyclerview.widget.RecyclerView`
- `android.widget.ScrollView`
- `androidx.viewpager.widget.ViewPager`
- `android.widget.ListView`

Swipe vertical dentro del rectángulo del contenedor: de 80% altura → 20% altura. Máximo 3 swipes por scroll antes de declarar "fin del contenido".

## Anti-loop / anti-explosión

- Si el mismo hash aparece >5 veces en el path → marcar como cycle y abortar esa rama.
- Si dos pantallas distintas tienen el mismo set de selectores (set-equality) → tratarlas como equivalentes y no duplicar trabajo.
- Si el crawl genera >50 pantallas únicas → truncar y reportar `coverage_truncated_at_screens: 50`.

## Recuperación de contexto

Si después de un `back` no volvimos a `screen_hash`:

1. Intentar `back` adicional (hasta 3 veces).
2. Si sigue sin volver: relaunch — `am start -n $APP_PACKAGE/$APP_ACTIVITY` y navegar siguiendo el path almacenado en BFS hasta `screen_hash`.
3. Si la navegación reproducible falla 2 veces: marcar `screen_hash` como `lost_context` y continuar con la siguiente entrada del queue.

## Casos especiales

### Diálogos / modales

Detectar por presencia de nodos `class="android.app.Dialog"` o root con `bounds` no full-screen. Estrategia:

- Si el modal es de permisos del sistema (`com.android.permissioncontroller`) → tap "Permitir" / "Allow" para no bloquear el flujo.
- Si es modal de la app → extraer sus selectores como pantalla nueva, luego cerrar con `back`.
- Nunca interactuar con dialogs cuyo texto matchea patrones destructivos.

### Teclado virtual

Si aparece IME (`com.google.android.inputmethod.*` u otro):

- No escribir texto durante el crawl.
- Cerrar con `back` antes de continuar.
- Marcar el `EditText` que lo invocó como `requires_input: true` en los selectores emitidos.

### Pantallas de login

NO completar credenciales durante el crawl. Marcar la pantalla como `login_screen: true` y reportar al usuario que la cobertura post-login requiere credenciales válidas (que el skill no manipula).

### Onboarding multi-paso

Si la primera pantalla es onboarding (carousel de bienvenida), avanzar con tap en "Siguiente"/"Next" hasta llegar al primer paso interactivo real. Documentar cada pantalla del onboarding como parte del mapa.
