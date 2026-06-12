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
