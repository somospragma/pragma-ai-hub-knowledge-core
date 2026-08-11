
# Receta del prototipo de front (opt-in pre-desarrollo)

Materializa la opción opt-in del camino "sin front y sin back" (`execution-modes-live-mocked-hybrid.md`): un front descartable generado desde el Figma + locator map, para ejecutar la suite antes de que exista el front real. Solo a elección explícita del usuario, con la advertencia de fidelidad declarada.

## Regla previa: ¿con qué tecnología se construirá el front real?

Preguntar SIEMPRE antes de generar — la tecnología del prototipo la dicta el front real:

| Front real | Prototipo | Por qué |
|---|---|---|
| Framework DOM (React, Angular, Vue, server-rendered...) | **HTML/CSS/JS plano** (esta receta) | Playwright ve DOM en ambos casos; el contrato `data-testid` transfiere si dev lo implementa |
| **Flutter Web** | **Flutter Web** (`flutter build web`) | Flutter renderiza a canvas: NO hay DOM de la UI; solo existe el árbol `flt-semantics`, que además hay que **activar**. Un prototipo HTML validaría `getByTestId` que la app real jamás tendrá — valida en falso, prohibido |
| Sin definir | No hay prototipo fiel posible | Camino oficial: construcción + ejecución diferida |

**Caso Flutter Web** — lo que cambia respecto a esta receta:

- El prototipo es la app Flutter (si el producto es multiplataforma, **el mismo prototipo del stack Appium sirve**: `flutter build web` — ver [[calidad-appium-screenplay-android]], [[calidad-mobile-locator-resolution]] (`references/flutter-under-appium.md`), incluido su contrato de fidelidad y gate de paridad).
- **Arranque**: el árbol de accesibilidad se construye cuando la app lo publica; la suite debe ejecutar la secuencia de activación ANTES de localizar nada (navegar con `domcontentloaded`, esperar el botón de activación adjunto al documento, activarlo por despacho de evento, esperar los nodos semánticos). El prototipo debe ofrecer el mismo punto de activación que la app real (o habilitar semántica permanente en AMBAS, jamás solo en el prototipo).
- **Selectores**: `flt-semantics[role="button"]:has-text("...")`, `[aria-label="..."]` — NO `data-testid`. Los campos con `explicitChildNodes: true` producen `<input>` reales (localizables como input); sin él no hay elemento de formulario. La columna `web` del locator map usa esta convención (aria-label/rol/texto del catálogo).
- **Textos = contrato**: los selectores buscan por texto visible; el catálogo de traducciones es el catálogo de selectores (paridad carácter a carácter, ambos idiomas, labels por defecto en inglés sin traducir).
- **Gate de paridad** idéntico al mobile: cada selector del mapa → exactamente una coincidencia, en ambos idiomas, antes de usar el prototipo.

## Reglas de construcción

1. **HTML/CSS/JS plano por defecto** (una página por pantalla del mapa o SPA mínima con router por hash). Vite solo si el flujo exige estado no trivial. Sin frameworks, sin build salvo necesidad.
2. **Fidelidad estructural, no visual**: el objetivo NO es parecerse al diseño — es implementar *exactamente* los `data-testid` del locator map, las rutas del mapa y los flujos de navegación. Los Page Objects validados contra el prototipo son los mismos que correrán contra el front real.
3. **Cero lógica de negocio**: el prototipo hace `fetch` REALES al backend mock (Mockoon vía `BACKEND_URL`) — así también se valida la integración por red (CORS, shape de requests, manejo de estados HTTP en la UI). No hardcodear respuestas en el JS: eso duplicaría el mock y desincroniza.
4. Estados observables mínimos por pantalla: loading, éxito, error visible — los tests de error states los necesitan.
5. Vive en `mocks/front-prototype/`, fuera del árbol de tests; se genera desde el mapa, no se mantiene a mano. Si el mapa cambia, se regenera.

## Cómo corre

```bash
# 1. Mock backend
mockoon-cli start --data mocks/mockoon/environment.json --port 3010 --faker-seed $FAKER_SEED &

# 2. Prototipo (servidor estático local)
npx serve mocks/front-prototype -l 4173 &

# 3. Suite contra el prototipo
BASE_URL=http://localhost:4173 BACKEND_URL=http://localhost:3010 \
  npx playwright test --grep @smoke --project=mocked-chromium --workers=1
```

El prototipo se inyecta el `BACKEND_URL` en runtime (ej. `window.__BACKEND_URL__` escrito por un `config.js` generado, o query param) — nunca hardcodeado, para que el mismo prototipo sirva contra otro puerto/ambiente de mock.

## Esqueleto mínimo (por pantalla del mapa)

```html
<!-- mocks/front-prototype/login.html -->
<form data-testid="login-form">
  <input data-testid="login-username" type="text" />
  <input data-testid="login-password" type="password" />
  <button data-testid="login-submit">Entrar</button>
  <p data-testid="login-error" hidden></p>
</form>
<script>
  document.querySelector('[data-testid=login-form]').addEventListener('submit', async (e) => {
    e.preventDefault();
    const res = await fetch(`${window.__BACKEND_URL__}/api/auth/login`, { method: 'POST', /* ... */ });
    if (res.ok) location.href = 'home.html';
    else { const el = document.querySelector('[data-testid=login-error]'); el.hidden = false; el.textContent = 'Credenciales inválidas'; }
  });
</script>
```

Los `data-testid` salen del locator map (`[[calidad-ui-locator-map-contract]]`) — el prototipo es la especificación ejecutable del contrato: el equipo de front real tiene el ejemplo corriendo de los identifiers que se comprometió a implementar.

## Qué NO valida (declaración obligatoria al cierre)

El front real (su framework, su estado, su render), estilos/diseño, performance, accesibilidad del producto. El delivery gate registra `front_prototype: true` en `mock_evidence` y cierra con `certification: pending_real_integration`; al llegar el front real: validación de drift del locator map y re-ejecución (`@live` de certificación).
