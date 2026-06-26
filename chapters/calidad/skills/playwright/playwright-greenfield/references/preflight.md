# Pre-flight check — Playwright greenfield

Antes de generar cualquier artefacto Playwright el agente debe validar el entorno local y la accesibilidad de la UI fuente. Si una validación falla, aplicar la degradación documentada y reportar al usuario antes de continuar. El protocolo de enforcement está descrito en `[[calidad-pre-generation-protocol]]`.

## Validaciones obligatorias

- `node --version` debe reportar Node.js 18 o superior. Playwright 1.45.x requiere Node 18 LTS como mínimo; Node 16 ya está EOL.
- `npx playwright --version` debe estar disponible (verifica que el CLI esté en el `PATH` o resuelva vía `npx`).
- Browsers instalados o, en su defecto, `npx playwright install --with-deps` ejecutable sin errores. En CI air-gapped, validar que el cache de browsers `~/.cache/ms-playwright/` ya esté poblado.
- `BASE_URL` (frontend) accesible vía `curl -sI --max-time 5 "$BASE_URL"`. Timeout de 5 segundos.
- `BACKEND_URL` (si se especificó) accesible con la misma validación que `BASE_URL`.
- Si las HU mencionan login real (palabras clave: `carrito`, `dirección personal`, `mis pedidos`, `checkout`, `perfil`, `dashboard privado`), exigir credenciales de autenticación antes de generar `auth.setup.ts`. Sin credenciales válidas, degradar a `scaffold-only` para esas suites.

## Degradación cuando hay URLs inaccesibles

Si `BASE_URL` o `BACKEND_URL` no responden dentro del timeout:

1. Reportar la URL exacta y el código devuelto (timeout, DNS fail, 4xx/5xx).
2. Degradar a `scaffold-only` para la suite afectada. Los locators serán placeholders y los Page Objects vendrán marcados con `// TODO: confirmar selector con app viva`.
3. Documentar la razón en `.evidence/preflight-result.json`.
4. Recordar al usuario que la suite `@live` no podrá ejecutarse hasta que la URL sea alcanzable; sugerir `@mocked` mientras tanto si `mock_mode` está disponible.

## Script shippeable

El agente debe copiar ``references/templates.md` (sección `preflight-playwright.sh`)` al proyecto generado bajo `scripts/preflight.sh`. El script reproduce las validaciones en CI o en máquinas de desarrolladores. Ver `[[calidad-delivery-gate-contract]]` para la convención de entregables y `[[calidad-post-generation-protocol]]` para el archivado del resultado.
