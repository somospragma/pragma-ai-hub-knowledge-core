
# Estructura del proyecto Playwright (greenfield)

## Árbol

```
{project_name}/
├── package.json                  # @playwright/test ^1.45.0, @axe-core/playwright ^4.9.0; scripts: test, test:headed, test:ui, test:debug, test:visual, test:a11y, report
├── playwright.config.ts          # baseURL desde process.env.BASE_URL; 3 projects (chromium, firefox, webkit); use: { trace, screenshot, video, timeout }
├── tsconfig.json                 # strict: true; lib: ["ES2020", "dom", "dom.iterable"]; paths: @pages/*, @fixtures/*, @mocks/*, @utils/*
├── .gitignore                    # node_modules/, test-results/, playwright-report/, .auth/, **/.env
├── README.md                     # Español; comandos de instalación, modos de corrida, override de BASE_URL
├── tests/
│   ├── {resource}.spec.ts        # 1 por flujo CRUD; importa test y expect desde @fixtures/base.fixture
│   ├── visual.spec.ts            # 1 test por página priorizada; Chromium-only
│   └── accessibility.spec.ts     # 1 test por página priorizada; WCAG 2.1 AA
├── pages/
│   ├── NavigationBar.ts          # Componente compartido de navegación
│   ├── {Resource}Page.ts         # 1 por recurso (list page)
│   └── {Resource}DetailPage.ts   # 1 por recurso con patrón {id}
├── fixtures/
│   ├── base.fixture.ts           # test.extend<Pages>() con todos los Page Objects + mockApi (auto)
│   └── auth.setup.ts             # SOLO si la UI real tiene flujo de login propio (ver auth-storage-state.md)
├── mocks/
│   ├── api-handlers.ts           # setupMocks(page) con page.route() agrupado por path
│   └── data/                     # {resource}.ts con datos mock exportados
└── utils/
    └── test-data.ts              # factory functions (createUserPayload, randomEmail, etc.)
```

## Responsabilidades por carpeta

- `tests/` — Solo specs. Importan Page Objects vía fixture; no instancian Page Objects directamente.
- `pages/` — Page Object Model (ver `[[playwright-page-object-model]]`). Una clase por página. Sin aserciones.
- `fixtures/` — Composición de test extendido (ver `[[playwright-fixtures-composition]]`) y, opcionalmente, `auth.setup.ts` (ver `[[playwright-auth-storage-state]]`).
- `mocks/` — Handlers de red (ver `[[playwright-mocks-page-route]]`) y datos sintéticos en `mocks/data/`.
- `utils/` — Factories de datos de test y helpers puros.
- `.auth/` (runtime) — Generada por `auth.setup.ts`. Listada en `.gitignore`.
- `test-results/`, `playwright-report/`, `tests/__screenshots__/` — Artefactos de corrida; los baselines de screenshots SÍ se versionan.
