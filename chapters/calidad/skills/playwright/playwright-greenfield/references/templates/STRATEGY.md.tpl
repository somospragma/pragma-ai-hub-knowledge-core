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
