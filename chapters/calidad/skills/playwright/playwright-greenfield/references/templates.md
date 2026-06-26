# Plantillas del proyecto generado

Cada seccion corresponde a un archivo que el agente debe materializar en la ruta indicada (relativa a la raiz del proyecto generado). Respeta los placeholders `{{...}}`.

## `README.md`

````markdown
# {{project_name}}

Proyecto de pruebas E2E web con Playwright generado a partir de `{{ui_source}}`.

## Prerequisitos

- **Node.js ≥ 18** (Playwright v1.42+ exige Node 18 LTS o superior).
- **`npx playwright install --with-deps`** descarga browsers + dependencias del sistema (incluido en quick start).
- **`pandoc`** opcional para convertir reportes HTML a PPTX/PDF. Default: sólo HTML.

Verificación rápida:

```bash
node --version    # debe mostrar v18+ o v20+
npm --version
```

## Quick start

```bash
npm install
npx playwright install --with-deps
./scripts/preflight.sh          # valida prereqs (Node, browsers instalados)
npx playwright test --project=chromium-live --grep @smoke
```

Para abrir el reporte HTML:

```bash
npx playwright show-report
```

## Modos de ejecución

El proyecto declara 3 tags por test:

- `@live` (default) — backend real apuntado por `BACKEND_URL`. Smoke obligatorio.
- `@mocked` (opt-in) — mocks via `page.route()`; útil sin backend disponible.
- `@hybrid` (opt-in) — live + mock de endpoints específicos.

```bash
npx playwright test --grep @live      # default / CI
npx playwright test --grep @mocked    # sin backend
npx playwright test --grep @hybrid    # mix
```

Override de URL:

```bash
BASE_URL=https://app.staging.example.com npx playwright test
```

## Estructura del proyecto

```
{{project_name}}/
├── package.json
├── playwright.config.ts
├── tsconfig.json
├── README.md
├── scripts/preflight.sh
├── tests/                            # specs por HU
│   ├── {{HU}}/
│   │   └── {{flow}}.spec.ts
│   ├── visual.spec.ts
│   └── accessibility.spec.ts
├── pages/                            # Page Objects
├── fixtures/
│   ├── base.fixture.ts
│   └── auth.setup.ts
├── mocks/                            # sólo si mock_mode != off
└── utils/
```

## Evidencia

Tras cada `npx playwright test`:

- `results/playwright/{YYYY-MM-DD}/{ISO}/html/` — reporte HTML.
- `results/playwright/{YYYY-MM-DD}/{ISO}/results.json` — JSON resumen.
- `results/playwright/{YYYY-MM-DD}/{ISO}-metadata.json` — metadata universal.
- `.evidence/execution-status.json` — sólo si hubo bloqueo de ambiente.

## Cobertura

Cada HU declara `effective_minimum >= 8` según la fórmula del Chapter. El delivery_gate audita que el conteo real de tests `@main-step` por HU cumpla el mínimo.

## Troubleshooting

| Síntoma | Causa | Solución |
|---|---|---|
| `Executable doesn't exist` | Browsers no instalados. | `npx playwright install --with-deps`. |
| Tests cuelgan en `networkidle` | SPA con polling. | Migrar a esperas semánticas (ver `references/waits-policy.md`). |
| `auth.setup.ts` falla | IdP caído o creds mal. | Revisar `.env`; ver `references/auth-detection-rules.md`. |
| `getByTestId` no encuentra elementos | HTML no expone `data-testid`. | Cambiar a `getByRole`/`getByLabel`. |
````

## `STRATEGY.md`

```markdown
# STRATEGY.md — {{project_name}} (Playwright)

Documento de estrategia previo a la generación de código. Debe estar aprobado explícitamente por el usuario antes de emitir el primer `.spec.ts`. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- SUT: {{sut_name}} — frontend web. {{sut_description}}
- Tipo de SUT: SPA / SSR / MPA / Storybook publicado — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}}
- Stack tecnológico del SUT: {{sut_stack}} (framework UI, build tool)
- Tipo de relación: greenfield (proyecto Playwright nuevo)
- `ui_source`: {{ui_source}}
- `ui_source_type`: {{ui_source_type}} (live-url / figma / user-story / storybook / hybrid)
- `base_url` frontend: {{base_url}}
- `backend_url`: {{backend_url}}
- Firma: {{firma}}

## 2. Volumen y SLAs

Playwright cubre E2E web. Los SLAs aplicables:

- Cumplimiento por HU: 100% de los tests `@user-story:HUT-XXX` pasan determinísticamente.
- Cobertura mínima por página: `effective_minimum = happy + 2_boundary + 2_negative + 1_edge` mínimo 8.
- A11y WCAG 2.1 AA: 0 findings `critical` y 0 `serious` en páginas CRITICAL y HIGH.
- Performance browser (opcional, declarar): page load p95, TTI p95.

| Métrica | Valor declarado |
|---|---|
| % éxito mínimo por HU | 100% |
| WCAG 2.1 AA critical | 0 |
| WCAG 2.1 AA serious | 0 |
| Page load p95 | {{page_load_p95}} |
| TTI p95 | {{tti_p95}} |

## 3. Alcance funcional

- Páginas en scope: {{pages_in_scope}}
- Páginas fuera de scope: {{pages_out_of_scope}} (justificación: {{out_of_scope_reason}})
- HUs cubiertas: {{user_stories}}
- Criterios de aceptación por HU: {{acceptance_criteria}}

## 4. Dependencias externas

- Auth strategy: {{auth_strategy}} (login real con `auth.setup.ts` + `storageState`, o sin auth, o auth mockeada). La existencia de `security` en OpenAPI **no** justifica per se auth real — confirmar con UI.
- APIs backend consumidas por el frontend: {{backend_apis}}
- Servicios externos (3rd party widgets, captchas, CDNs): {{third_parties}}

## 5. Riesgos conocidos

- Captchas en flujos críticos: {{captcha_status}} (impacto: pueden bloquear automatización en `live`).
- WAF en frontend: {{waf_status}}
- Datos sensibles tratados: {{sensitive_data}}
- Variabilidad visual (fechas dinámicas, banners): mitigar con `mask` en visual snapshots.

## 6. Próximos pasos

- Archivos a generar: `playwright.config.ts`, `tsconfig.json`, `package.json`, `pages/*.ts`, `tests/*.spec.ts`, `fixtures/base.fixture.ts`, opcional `mocks/api-handlers.ts`, opcional `fixtures/auth.setup.ts`, `tests/visual.spec.ts`, `tests/accessibility.spec.ts`, `README.md`.
- Comando de ejecución: `npx playwright test --project=live-chromium` (variantes según `mock_mode`).
- Reporte ejecutivo: formato {{report_format}} (default `html`).

## 7. Estrategia Playwright

### 7.1 Pages identificadas

| Page | Route frontend | Prioridad | Page type | Mocked endpoints requeridos |
|---|---|---|---|---|
| LoginPage | /login | CRITICAL | auth | — |
| DashboardPage | /dashboard | HIGH | landing | GET /me, GET /metrics |
| CheckoutPage | /checkout | CRITICAL | flow | POST /orders |

### 7.2 Mock mode elegido

- `mock_mode`: {{mock_mode}} (`off` default / `full` / `partial`).
- Justificación: {{mock_mode_reason}}
- Si `mock_mode != off`, listar `mock_endpoints`: {{mock_endpoints}}

### 7.3 Priorities por página

Las prioridades provienen de `priority_assignments` provisto por el usuario/PO. NUNCA se infieren por nombre. Páginas `CRITICAL` y `HIGH` reciben además cobertura visual y a11y.

### 7.4 Auth strategy

- Modo: {{auth_mode}} (real / mock / sin auth).
- Si real: `fixtures/auth.setup.ts` + `storageState: '.auth/user.json'` + projects con `dependencies: ['setup']`.
- Credenciales: {{credentials_source}} (env vars `USER_EMAIL` / `USER_PASSWORD`, vault, etc.).

### 7.5 Visual y a11y

- Visual: tests `tests/visual.spec.ts` con `@live` para páginas CRITICAL y HIGH. Threshold: `maxDiffPixelRatio: {{max_diff_pixel_ratio}}`.
- A11y: tests `tests/accessibility.spec.ts` con axe + WCAG 2.1 AA para CRITICAL y HIGH.

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar páginas y tests.
```

## `a11y-audit.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility audit suite — one test per page declared in {{pages_to_audit}}.
 * Replace the {{pages_to_audit}} block with one describe/test pair per page.
 *
 * Coverage rules:
 *   - 0 critical violations on WCAG 2.0 A + AA.
 *   - Keyboard navigation: Tab moves focus through interactive elements in order.
 *   - All <img> elements expose alt text (or alt="" for purely decorative ones).
 */

test.describe('Accessibility audit', { tag: ['@a11y', '@regression'] }, () => {

  // ---- Per-page audit ------------------------------------------------------
  // {{pages_to_audit}} format: array of { name, route }
  // Emit one test('axe scan - <name>', ...) per entry.

  test('axe scan - {{pages_to_audit}}', async ({ page }) => {
    await page.goto('{{pages_to_audit}}');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const critical = results.violations.filter((v) => v.impact === 'critical');
    expect(critical, JSON.stringify(critical, null, 2)).toEqual([]);
  });

  // ---- Keyboard navigation -------------------------------------------------

  test('keyboard navigation reaches interactive elements - {{pages_to_audit}}',
    async ({ page }) => {
      await page.goto('{{pages_to_audit}}');

      const interactive = await page.locator(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ).count();
      expect(interactive).toBeGreaterThan(0);

      // Tab through the first few elements and verify a focusable element receives focus.
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => document.activeElement?.tagName);
      expect(focused).not.toBeUndefined();
      expect(focused).not.toBe('BODY');
    }
  );

  // ---- Image alt text ------------------------------------------------------

  test('all images expose alt text - {{pages_to_audit}}', async ({ page }) => {
    await page.goto('{{pages_to_audit}}');

    const images = page.locator('img');
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      // alt="" is valid for decorative images; null/undefined is a violation.
      expect(alt, `img[${i}] is missing alt attribute`).not.toBeNull();
    }
  });
});
```

## `auth.setup.ts`

```typescript
import { test as setup, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const STORAGE_STATE = path.resolve('.auth/user.json');

setup('authenticate', async ({ page }) => {
  // Ensure .auth/ directory exists before saving storage state.
  fs.mkdirSync(path.dirname(STORAGE_STATE), { recursive: true });

  await page.goto('{{login_url}}');

  // Use semantic locators. Adjust labels to the real UI of the SUT.
  await page.getByLabel(/email|usuario|correo/i).fill('{{email}}');
  await page.getByLabel(/password|contraseña/i).fill('{{password}}');
  await page.getByRole('button', { name: /log\s*in|ingresar|iniciar sesi[oó]n/i }).click();

  // Wait for the post-login URL or a stable DOM signal — NEVER waitForTimeout.
  await page.waitForURL('{{expected_url_after_login}}');
  await expect(page).toHaveURL('{{expected_url_after_login}}');

  // Persist auth cookies + localStorage so tests can reuse the session.
  await page.context().storageState({ path: STORAGE_STATE });
});
```

## `package.json`

```json
{
  "name": "{{project_name}}",
  "version": "1.0.0",
  "private": true,
  "description": "Playwright E2E test suite for {{project_name}}",
  "scripts": {
    "test": "playwright test --grep @live",
    "test:live": "playwright test --grep @live",
    "test:mocked": "playwright test --grep @mocked",
    "test:hybrid": "playwright test --grep @hybrid",
    "test:all": "playwright test",
    "test:headed": "playwright test --headed",
    "test:ui": "playwright test --ui",
    "test:debug": "playwright test --debug",
    "test:visual": "playwright test tests/visual.spec.ts",
    "test:a11y": "playwright test tests/a11y-audit.spec.ts",
    "test:security": "playwright test --grep @security",
    "report": "playwright show-report",
    "lint": "eslint ."
  },
  "devDependencies": {
    "@playwright/test": "^1.45.0",
    "@axe-core/playwright": "^4.9.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "eslint": "^8.57.0",
    "eslint-plugin-playwright": "^1.6.0",
    "typescript": "^5.4.0"
  },
  "eslintConfig": {
    "root": true,
    "parser": "@typescript-eslint/parser",
    "plugins": ["@typescript-eslint", "playwright"],
    "extends": [
      "eslint:recommended",
      "plugin:@typescript-eslint/recommended",
      "plugin:playwright/recommended"
    ],
    "rules": {
      "no-restricted-syntax": ["error", {
        "selector": "MemberExpression[property.name='waitForTimeout']",
        "message": "Prohibido waitForTimeout. Usa waitForResponse, waitFor({state:'visible'}) o expect().not.toHaveText()."
      }],
      "playwright/no-skipped-test": "error",
      "playwright/no-focused-test": "error",
      "playwright/no-wait-for-timeout": "error"
    }
  }
}
```

## `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

/**
 * BASE_URL: URL del frontend (lo que ve Playwright en page.goto).
 * BACKEND_URL: URL del backend / API que el frontend consume.
 * Override por ambiente:
 *   BASE_URL=https://dev.app.com BACKEND_URL=https://api.dev.app.com npx playwright test
 */
const BASE_URL = process.env.BASE_URL || '{{baseUrl}}';
const BACKEND_URL = process.env.BACKEND_URL || '{{baseUrl}}';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['html', { open: 'never' }], ['list']],

  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    extraHTTPHeaders: {
      'x-backend-url': BACKEND_URL,
    },
  },

  // Opcional: levantar el frontend localmente antes de correr la suite.
  // Descomentar SOLO si el equipo lo necesita.
  //
  // webServer: {
  //   command: 'npm run dev',
  //   url: BASE_URL,
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120_000,
  // },

  projects: [
    // Setup project: ejecuta auth.setup.ts y guarda storageState en .auth/user.json
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // @live (default): contra backend real
    {
      name: 'live-chromium',
      grep: /@live/,
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/user.json',
      },
    },
    {
      name: 'live-firefox',
      grep: /@live/,
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Firefox'],
        storageState: '.auth/user.json',
      },
    },
    {
      name: 'live-webkit',
      grep: /@live/,
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Safari'],
        storageState: '.auth/user.json',
      },
    },

    // @mocked (opt-in): toda la red interceptada vía mockApi fixture
    {
      name: 'mocked-chromium',
      grep: /@mocked/,
      use: { ...devices['Desktop Chrome'] },
    },

    // @hybrid (opt-in): live + mock dirigido
    {
      name: 'hybrid-chromium',
      grep: /@hybrid/,
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/user.json',
      },
    },
  ],
});
```

## `preflight-playwright.sh`

```bash
#!/usr/bin/env bash
set -e
echo "=== Playwright pre-flight ==="

NODE_VERSION=$(node --version 2>/dev/null | sed 's/^v//' | cut -d. -f1)
if [[ -z "$NODE_VERSION" ]]; then
  echo "[fail] node no encontrado en PATH"
  exit 1
fi
echo "Node major version: $NODE_VERSION"
if [[ "$NODE_VERSION" -lt 18 ]]; then
  echo "[fail] Node $NODE_VERSION < 18. Playwright 1.45.x requiere Node 18+."
  echo "Sugerencia: nvm install 18 && nvm use 18"
  exit 1
fi
echo "[ok] Node $NODE_VERSION compatible"

npx --no-install playwright --version > /dev/null 2>&1 || npx playwright --version > /dev/null 2>&1 || {
  echo "[fail] playwright CLI no disponible. Ejecutar: npm i -D @playwright/test"
  exit 1
}
echo "[ok] Playwright CLI disponible"

if [[ ! -d "${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}" ]]; then
  echo "[warn] cache de browsers no encontrado. Ejecutar: npx playwright install --with-deps"
fi

if [[ -n "$BASE_URL" ]]; then
  echo "Verificando BASE_URL=$BASE_URL ..."
  curl -sI --max-time 5 "$BASE_URL" > /dev/null || {
    echo "[fail] BASE_URL inaccesible (timeout 5s). Degradar a scaffold-only."
    exit 1
  }
  echo "[ok] BASE_URL alcanzable"
else
  echo "[warn] BASE_URL no definido. Suite @live no podrá ejecutarse hasta exportarlo."
fi

if [[ -n "$BACKEND_URL" ]]; then
  echo "Verificando BACKEND_URL=$BACKEND_URL ..."
  curl -sI --max-time 5 "$BACKEND_URL" > /dev/null || {
    echo "[fail] BACKEND_URL inaccesible (timeout 5s)."
    exit 1
  }
  echo "[ok] BACKEND_URL alcanzable"
fi

echo "=== preflight ok ==="
```

## `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020", "dom", "dom.iterable"],
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "baseUrl": ".",
    "paths": {
      "@pages/*": ["pages/*"],
      "@fixtures/*": ["fixtures/*"],
      "@mocks/*": ["mocks/*"],
      "@utils/*": ["utils/*"],
      "@data/*": ["data/*"]
    }
  },
  "include": [
    "tests/**/*",
    "pages/**/*",
    "fixtures/**/*",
    "mocks/**/*",
    "utils/**/*",
    "data/**/*",
    "playwright.config.ts"
  ],
  "exclude": ["node_modules", "test-results", "playwright-report", ".auth"]
}
```

## `xss-prevention.spec.ts`

```typescript
import { test, expect, Page } from '@playwright/test';

/**
 * Security smoke suite — XSS, SQLi probes, and security headers.
 * Tag: @security. Runs as part of the regression gate; non-blocking for smoke.
 *
 * Replace {{pages_with_inputs}} with the list of routes that expose user inputs,
 * and {{api_endpoint_to_probe}} with the backend URL whose response headers
 * are inspected (e.g. https://api.example.com/health).
 */

const XSS_PAYLOAD = '<script>alert(1)</script>';
const SQLI_PAYLOAD = "'; DROP TABLE users; --";

let alertFired = false;

test.describe('Security smoke - XSS & SQLi probes', { tag: ['@security'] }, () => {

  test.beforeEach(async ({ page }) => {
    alertFired = false;
    page.on('dialog', async (dialog) => {
      alertFired = true;
      await dialog.dismiss();
    });
  });

  test('XSS payload is not executed in any input - {{pages_with_inputs}}',
    async ({ page }) => {
      await page.goto('{{pages_with_inputs}}');

      const inputs = page.locator('input:not([type="hidden"]), textarea');
      const count = await inputs.count();
      expect(count, 'no inputs found to probe').toBeGreaterThan(0);

      for (let i = 0; i < count; i++) {
        const input = inputs.nth(i);
        if (!(await input.isVisible())) continue;
        await input.fill(XSS_PAYLOAD);
        await input.blur();
      }

      // No JS alert from the payload must have fired.
      expect(alertFired, 'XSS payload triggered an alert dialog').toBe(false);

      // The rendered DOM must not contain an actual <script> node from the payload.
      const injectedScripts = await page.evaluate((payload) => {
        return Array.from(document.scripts).filter((s) => s.textContent?.includes(payload)).length;
      }, 'alert(1)');
      expect(injectedScripts, 'injected <script> survived in the DOM').toBe(0);
    }
  );

  test('SQLi probe is not reflected verbatim - {{pages_with_inputs}}',
    async ({ page }) => {
      await page.goto('{{pages_with_inputs}}');

      const inputs = page.locator('input:not([type="hidden"]), textarea');
      const count = await inputs.count();

      for (let i = 0; i < count; i++) {
        const input = inputs.nth(i);
        if (!(await input.isVisible())) continue;
        await input.fill(SQLI_PAYLOAD);
        await input.blur();
      }

      const bodyHTML = await page.content();
      // The literal payload must not be rendered unescaped as an error stack trace.
      expect(bodyHTML).not.toContain('syntax error at or near');
      expect(bodyHTML).not.toContain('SQLSTATE');
    }
  );
});

test.describe('Security headers', { tag: ['@security'] }, () => {

  test('response exposes hardening headers - {{api_endpoint_to_probe}}',
    async ({ request }) => {
      const response = await request.get('{{api_endpoint_to_probe}}');
      const headers = response.headers();

      expect(headers['x-frame-options'] || headers['content-security-policy'],
        'missing X-Frame-Options or CSP frame-ancestors').toBeTruthy();
      expect(headers['content-security-policy'],
        'missing Content-Security-Policy header').toBeTruthy();
      expect(headers['strict-transport-security'],
        'missing Strict-Transport-Security header').toBeTruthy();
    }
  );
});
```

