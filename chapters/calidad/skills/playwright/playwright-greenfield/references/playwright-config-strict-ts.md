
# Configuración estricta de TS + Playwright

## `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

/**
 * BASE_URL: URL del frontend (lo que ve Playwright en page.goto).
 * BACKEND_URL: URL del backend / API que el frontend consume.
 *   Disponible como process.env.BACKEND_URL para Page Objects y mocks.
 * MOCK_MODE: off | full | partial. Default off. Solo informativo aquí;
 *   el filtrado real se hace por tags (@live, @mocked, @hybrid).
 */
const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000';
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8080';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
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
  // Descomentar SOLO si el equipo lo necesita; por defecto se asume
  // que BASE_URL apunta a un ambiente ya desplegado (dev/staging).
  //
  // webServer: {
  //   command: 'npm run dev',
  //   url: BASE_URL,
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120_000,
  // },

  projects: [
    // @live (default): contra backend real
    {
      name: 'live-chromium',
      grep: /@live/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'live-firefox',
      grep: /@live/,
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'live-webkit',
      grep: /@live/,
      use: { ...devices['Desktop Safari'] },
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
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

## `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020", "dom", "dom.iterable"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "baseUrl": ".",
    "paths": {
      "@pages/*": ["pages/*"],
      "@fixtures/*": ["fixtures/*"],
      "@mocks/*": ["mocks/*"],
      "@utils/*": ["utils/*"]
    }
  },
  "include": ["tests/**/*", "pages/**/*", "fixtures/**/*", "mocks/**/*", "utils/**/*"]
}
```

## `package.json` (scripts y dependencias clave)

```json
{
  "name": "{project_name}",
  "version": "1.0.0",
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
    "test:a11y": "playwright test tests/accessibility.spec.ts",
    "report": "playwright show-report"
  },
  "devDependencies": {
    "@playwright/test": "^1.45.0",
    "@axe-core/playwright": "^4.9.0",
    "axe-playwright": "^2.0.0",
    "typescript": "^5.4.0"
  }
}
```

## Notas

- `BASE_URL` sale de `process.env.BASE_URL` para permitir override por ambiente (ej. `BASE_URL=https://dev.app.com BACKEND_URL=https://api.dev.app.com npx playwright test`).
- `BACKEND_URL` no entra en `use.baseURL` (eso lo consume `page.goto`); se expone vía `extraHTTPHeaders` y/o como `process.env.BACKEND_URL` para que mocks/Page Objects la lean.
- El `webServer` block está comentado por diseño: por defecto la suite asume un frontend ya desplegado. Descomentar solo en proyectos que quieren spin-up local automático.
- Filtros por `grep` por project: `npm run test:live` (default), `npm run test:mocked`, `npm run test:hybrid`, `npm run test:all` (todo).
- Path aliases en `tsconfig.json` alineados con la estructura de carpetas declarada en `[project-structure](project-structure.md)`.
- Detalle de modos: `[execution-modes-live-mocked-hybrid](execution-modes-live-mocked-hybrid.md)`.
