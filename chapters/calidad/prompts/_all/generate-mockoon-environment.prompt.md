---
id: calidad-generate-mockoon-environment-prompt
version: 1.0.0
scope: chapter
type: prompt
chapter: calidad
description: "Prompt que genera el data file de Mockoon (environment JSON) desde un spec OpenAPI/Swagger/WSDL, con CRUD stateful, respuestas de error por rules y templating determinista. Solo se invoca cuando execution_target es mock o hybrid."
tags: [mockoon, mock, prompt, service-virtualization, openapi, soap, environment, opt-in]
---

# Prompt — Generar environment Mockoon (opt-in)

## Cuándo invocar este prompt

**Por defecto NO se invoca.** Se activa solo cuando `[[calidad-sut-readiness-gate]]` resolvió `execution_target: mock | hybrid` y el mock requerido es a nivel backend (Karate, K6 smoke, Playwright backend-level, Appium con APK configurable, serenity-wdio modo `api` o backend-level en modos `web`/`web_movil`). Gobernado por `[[calidad-service-virtualization-mockoon]]`.

## Variables

- `{{spec}}` — Contenido completo del OpenAPI/Swagger/WSDL ya validado por `[[calidad-spec-validation]]`. Debe incluir response schemas por status code (contrato del gate); si no los tiene, NO generar: reportar el faltante.
- `{{user_story}}` — Opcional. Ajusta datos de ejemplo al lenguaje de negocio (nunca agrega reglas que el spec no declare).
- `{{stateful_resources}}` — Lista de recursos con flujo CRUD detectado (ej. `["users", "payments"]`); cada uno se modela como CRUD route + data bucket.
- `{{faker_seed}}` / `{{faker_locale}}` — Seed y locale alineados con la suite (`FAKER_SEED` de `[[calidad-test-data-management]]`). El seed se aplica al arrancar el CLI (`--faker-seed`), no dentro del data file: documentarlo en el comando de salida.
- `{{port}}` — Default `3010`.
- `{{proxy_host}}` — Solo `hybrid`: URL del backend real para passthrough de rutas no mockeadas.

## Instrucción para el LLM

Genera UN solo archivo `mocks/mockoon/environment.json` válido para Mockoon v9+, siguiendo estrictamente [[calidad-service-virtualization-mockoon]] (consultar `references/mockoon-environment-file.md`, `references/openapi-to-mock.md` y `references/stateful-crud-and-data-buckets.md` en su subfolder):

- Environment con `name` = `{project_name}-mock`, `port` = `{{port}}`, `endpointPrefix` según el base path del spec, `cors: true`, header global `Content-Type: application/json` (o XML para SOAP).
- **Una ruta por path×method del spec.** Recursos en `{{stateful_resources}}` → ruta `type: "crud"` ligada a un data bucket con dataset inicial templado (`{{#repeat}}` + Faker); el resto → rutas `http`.
- **Respuesta default por ruta** = el status code de éxito del spec, con body derivado del response schema: campos eco del request vía `{{urlParam}}`/`{{body}}`, ids vía `{{uuid}}`, datos de relleno vía `{{faker ...}}`, enums vía `{{oneOf (array ...)}}` con los valores literales del spec.
- **Respuestas de error adicionales** por cada status 4xx/5xx declarado en el spec, discriminadas por rules (body inválido → 400/422 con regla "valid JSON Schema" cuando haya schema en bucket; sin header de auth → 401 si el spec declara `security`; id inexistente lo maneja el CRUD con 404 automático).
- **Ruta `GET /health-probe`** estática (200, body `{"status":"up"}`) para el healthcheck de CI.
- WSDL/SOAP → aplicar el patrón de `references/soap-xml-mocking.md` (una ruta POST por endpoint, rules por operación sobre el body xml-js, respuestas envelope XML, Fault como default).
- `hybrid` → `proxyMode: true`, `proxyHost: {{proxy_host}}`, y SOLO rutas para los endpoints no desplegados; el resto pasa al real.
- UUIDs únicos y estables por entidad (no regenerar en actualizaciones posteriores del archivo: mantiene diffs de git legibles).
- **NUNCA** inventar campos, enums, reglas o endpoints que no estén en el spec/firma/user story. Si un schema es ambiguo, emitir el campo con `// TODO` en el reporte de salida (no dentro del JSON, que debe ser válido).

## Salida esperada

1. El archivo `mocks/mockoon/environment.json` completo y parseable.
2. El comando de arranque documentado para el README del proyecto:

```bash
mockoon-cli start --data mocks/mockoon/environment.json --port 3010 \
  --faker-seed {{faker_seed}} --faker-locale {{faker_locale}} \
  --admin-api-token "$MOCKOON_ADMIN_API_TOKEN"
```

3. El comando de purge de estado para el setup de la suite (`POST /mockoon-admin/state/purge`).
4. Lista de decisiones tomadas (recursos CRUD modelados, errores cubiertos, TODOs pendientes).
