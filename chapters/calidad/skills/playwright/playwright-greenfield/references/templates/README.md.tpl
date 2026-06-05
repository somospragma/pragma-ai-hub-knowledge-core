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
