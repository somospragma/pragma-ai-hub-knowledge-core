
# Modos de ejecución — `@live`, `@mocked`, `@hybrid`

## Qué valida un test Playwright con mocks (y qué NO)

**El objetivo de mockear servicios en Playwright es habilitar la interacción del front y la navegación que depende de ese backend** — que el flujo de UI pueda recorrerse cuando el servicio real no está. Las aserciones del test validan lo que el usuario ve y hace: navegación, estados visibles, mensajes, habilitación de controles, redirecciones.

**NO se validan los servicios ni sus respuestas.** Asertar el status code, el schema o los campos del response de un endpoint mockeado es (a) probar el mock contra sí mismo y (b) invadir el terreno de las pruebas de servicios — eso pertenece a `[[calidad-karate-greenfield]]`. Regla práctica: si una aserción desaparecería al reemplazar el mock por el backend real sin que la UI cambie, sobra.

## Caminos según disponibilidad de front y back

Resuelto en `[[calidad-sut-readiness-gate]]`; los tres caminos posibles:

| Camino | Front | Back | Qué se hace |
|---|---|---|---|
| 1 | No | No | **Oficial**: si existe el código del front (repo/build local aunque no esté desplegado), levantarlo localmente contra el mock del back y ejecutar. Si no existe ni el código: construcción completa (tests + locator map + mocks listos) con **ejecución diferida** — no hay SUT de UI que recorrer. |
| 2 | Sí | No | Front real (desplegado o local) + back mockeado: `@mocked` con `page.route()` full, o Mockoon backend-level vía `BACKEND_URL`. |
| 3 | Sí | Sí | Live con **mock dirigido** de servicios puntuales que hay que controlar (ej. forzar el response del login, un tercero inestable, un estado difícil de reproducir): `@hybrid` con `page.route()` parcial o Mockoon en proxy mode. |

**Opción opt-in del camino 1 — prototipo de front ("mock del front")**: el agente PUEDE generar un front descartable a partir del diseño (Figma + locator map) para ejecutar los tests antes de que exista el front real. Se ofrece SOLO a elección explícita del usuario, NUNCA por defecto, con esta advertencia obligatoria: el prototipo no es fiel al diseño real — los tests que pasen contra él validan la mecánica de la suite, no el front del producto, y traen riesgo de retrabajo cuando llegue el desarrollo. Reglas si el usuario lo acepta: los selectores salen del locator map (el prototipo implementa exactamente esos `data-testid`), el prototipo vive fuera del árbol de tests (ej. `mocks/front-prototype/`, descartable), el delivery gate registra `front_prototype: true` dentro de `mock_evidence` y la corrida cierra igual con `certification: pending_real_integration`.

Cada test Playwright declara su modo de ejecución mediante un tag en el título o en su `describe`. Esto evita el bug de "toda la suite es contrato del mock" y permite filtrar por pipeline.

## Tags

- **`@live` (default)** — Test corre contra backend real apuntado por `BACKEND_URL` y frontend en `BASE_URL`. Único modo que valida integración real. Obligatorio para suite smoke.
- **`@mocked` (opt-in)** — Test intercepta toda la red con `page.route()` usando `setupMocks(page)`. Requiere inyectar el fixture `mockApi`. Usar para: aislar UI en error states, dev offline, regresión del propio mock.
- **`@hybrid` (opt-in)** — Test corre live por default pero mock dirigido a endpoints concretos (servicios externos lentos, APIs no disponibles en dev). Requiere `mockApi` parcial.

## Variables de entorno

| Variable      | Descripción                                                       | Ejemplo                       |
|---------------|-------------------------------------------------------------------|-------------------------------|
| `BASE_URL`    | URL del frontend (SPA, sitio web).                                | `https://app.dev.example.com` |
| `BACKEND_URL` | URL del backend / API que consume el frontend.                    | `https://api.dev.example.com` |
| `MOCK_MODE`   | `off | full | partial`. Default `off`. Para CI híbrido.           | `partial`                     |

`BASE_URL` se inyecta en `playwright.config.ts` como `use.baseURL`. `BACKEND_URL` queda disponible como `process.env.BACKEND_URL` para Page Objects y mocks que necesiten la URL absoluta del backend.

## Filtros en CLI

```bash
# Smoke / CI por defecto: solo live
npx playwright test --grep @live

# Desarrollo offline sin backend disponible
npx playwright test --grep @mocked

# Regresión completa (live + hybrid; sin mocked puros)
npx playwright test --grep "@live|@hybrid"

# Excluir mocked en producción
npx playwright test --grep-invert @mocked
```

## Sample — projects en `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: process.env.BASE_URL,
  },
  projects: [
    {
      name: 'live-chromium',
      grep: /@live/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mocked-chromium',
      grep: /@mocked/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'hybrid-chromium',
      grep: /@hybrid/,
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

## Risk matrix

| Modo      | Capta bugs de integración | Determinismo / flake     | Velocidad | Riesgo principal                                   |
|-----------|---------------------------|--------------------------|-----------|----------------------------------------------------|
| `@live`   | Sí (es para esto)         | Bajo determinismo / alto flake si backend es flaky | Media     | Falsos negativos cuando dev backend está degradado |
| `@mocked` | No (pasa con backend roto) | Alto determinismo / bajo flake | Alta      | Falsos positivos cuando contrato real cambia        |
| `@hybrid` | Sí (parcial)              | Medio                    | Media     | Confusión sobre qué endpoint está mockeado          |

## Guía operacional

- **Suite smoke**: 100% `@live`. Sin excepciones. Es el contrato real con el backend.
- **Suite regresión**: mayormente `@live`, mezcla puntual de `@hybrid` para endpoints externos costosos.
- **Suite de error states / edge UI**: `@mocked` para forzar 500, 429, latencias.
- **CI**: pipeline por project filtrado por `grep`; cada modo reporta separado.
- **Dev local sin backend**: `npx playwright test --grep @mocked`.

## Convención de declaración

```typescript
// Recomendado: tag en el título del test
test('@live crea un usuario', async ({ usersPage }) => { /* ... */ });
test('@mocked muestra error 500', async ({ usersPage, mockApi }) => { /* ... */ });

// Alternativa: tag en describe para todo el bloque
test.describe('@live UsersPage CRUD', () => {
  test('crea', async ({ usersPage }) => { /* ... */ });
  test('lista', async ({ usersPage }) => { /* ... */ });
});
```

Más detalle del fixture `mockApi` y por qué NO es `auto`: `[fixtures-composition](fixtures-composition.md)`. Patrón de handlers: `[mocks-page-route](mocks-page-route.md)`.

## Mock a nivel backend con Mockoon (complementario, no reemplazo)

`page.route()` intercepta en el browser context y es la **primera opción** para `@mocked`/`@hybrid`. Hay casos donde no alcanza y el mock debe ser un servidor de red real (`[[calidad-service-virtualization-mockoon]]`):

- Tráfico que no pasa por el context (webviews, service workers con estrategias propias, llamadas server-side del frontend SSR).
- Pruebas construidas **antes de que el backend exista** (`execution_target: mock` del `[[calidad-sut-readiness-gate]]`) donde el mismo mock se comparte con la suite Karate del proyecto — un solo contrato mockeado, dos suites.
- CRUD stateful con correlación de IDs entre tests (data buckets), que con `page.route()` exige mantener estado a mano.

En ese caso, `BACKEND_URL` apunta al mock (`http://localhost:3010`) y los tests siguen taggeados `@mocked`/`@hybrid` según el alcance; el switchover a real es cambiar `BACKEND_URL` (cero cambios en tests). La regla no cambia: smoke de certificación siempre `@live` contra backend real, y la corrida contra mock cierra con `certification: pending_real_integration` en el delivery gate.
