---
id: k6-greenfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [k6]
description: Genera un proyecto K6 completo de performance testing desde un spec OpenAPI/Swagger.
tags: [k6, greenfield, openapi, swagger, performance, load-testing, javascript]
---

# K6 Greenfield

## Cuándo aplicar

Cuando el usuario solicita generar un proyecto K6 **desde cero** para pruebas de performance (smoke, load, stress, spike, soak) a partir de un spec OpenAPI 3.x o Swagger 2.0. Si el usuario provee archivos de un proyecto K6 previo, este skill no aplica (ver `[[k6-brownfield]]`).

Antes de activarlo: valida el spec con `[[calidad-spec-validation]]`, confirma intent con `[[calidad-intent-detection]]`, recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]` y aplica la perspectiva del chapter con `[[calidad-chapter-perspective]]`. Para distinguir greenfield/brownfield revisa `[[calidad-brownfield-vs-greenfield]]`.

## Inputs

Además de los gobernados por `[[calidad-mandatory-inputs-protocol]]` (spec, project_name, output_path, base_url), este skill acepta:

- `auth_mode` (opcional). Valores admitidos: `spec` (default) | `external`.
  - `spec`: el comportamiento histórico. `authToken` / `Authorization` se incluyen únicamente si el spec declara `security` (`components.securitySchemes` o `securityDefinitions`).
  - `external`: override. `authToken: __ENV.AUTH_TOKEN || ''` se incluye SIEMPRE en `config.js` y `Authorization: Bearer ${config.authToken}` se incluye SIEMPRE en `getDefaultHeaders()`, aunque el spec no declare security. Casos de uso: API gateway delante del microservicio, token emitido por IdP externo (Cognito/Keycloak/Okta), AWS SigV4 / JWS request signing, mTLS, tokens obtenidos out-of-band por el equipo de performance. Equivalente: env var `EXTERNAL_AUTH=true`. Detalle en `[[k6-enums-headers-security-extraction]]`.

## Instrucción

0. **Resolver vocabulario de escenarios** — Antes de cualquier otra acción, consulta [vocabulary-and-scenario-mapping](references/vocabulary-and-scenario-mapping.md) para decidir si el proyecto usa nomenclatura de negocio (Línea Base / Carga / Estrés) o nomenclatura k6 docs (smoke / load / stress). La decisión se aplica a filenames, carpetas, scripts npm, `run-all.sh`, reports y `delivery_gate`. Adicionalmente, evalúa si Spike y/o Soak aplican como opt-in según `user_story`, `firma` o `risk_map` y registra la justificación en `.evidence/scenarios-opt-in.md`.
1. **Validar spec** — Verifica OpenAPI 3.x / Swagger 2.0 (>200 chars, JSON o YAML, presencia de `openapi`/`swagger`, `info`, `paths`). Si falla, detente y reporta el motivo.
2. **Extraer endpoints** — Lista cada `path` con su `method`, `operationId`, parámetros de ruta, query, headers y referencia al schema de request/response. Emite el checklist humano-legible antes de generar código.
3. **Extraer config data** — Aplica `[[k6-enums-headers-security-extraction]]`: enums (top-level y por propiedad), headers requeridos por endpoint, security schemes (`components.securitySchemes` o `securityDefinitions`) y path params.
4. **Detectar CRUD flows** — Normaliza el path (recorta `/{param}` final), agrupa por base path, clasifica como `full` (POST+GET+DELETE) o `partial` (≥2 métodos). Detalle en `[[k6-crud-dynamic-id-correlation]]`.
5. **Generar utils template** — Construye `utils.js` con `uuidv4()`, `getDefaultHeaders()` y `buildXxxBody()` por endpoint con request body. Para `Authorization` aplica la rama según `auth_mode`: en `spec` (default) sólo si el spec define `security`; en `external` siempre. Plantilla en `[[k6-config-and-utils-modules]]`.
6. **Emitir tests primero** — Sigue `[[calidad-streaming-files-protocol]]`: persiste primero los 3 scripts **obligatorios** (`smoke-test.js`, `load-test.js`, `stress-test.js`) y luego los opt-in activados (`spike-test.js`, `soak-test.js`) si `user_story` / `firma` / `risk_map` los amerita (ver [vocabulary-and-scenario-mapping](references/vocabulary-and-scenario-mapping.md)). **No entregar solo smoke aunque por economía pareciera suficiente** — ver `references/coverage-formula.md`. Aplica stages y thresholds del tier elegido (`[[k6-five-script-types]]`, `[[k6-thresholds-three-tiers]]`). La fuente autoritativa del contenido textual de cada script está en `references/templates/` (`smoke-test.js.tpl`, `load-test.js.tpl`, `stress-test.js.tpl`, `spike-test.js.tpl`, `soak-test.js.tpl`).
7. **Generar config/utils/infra** — Luego `utils.js`, `config.js`, y por último `package.json`, `README.md`, `run-all.sh`, `.gitignore`. Estructura completa en `[[k6-project-structure]]`. Plantillas inmutables en `references/templates/` (`config.js.tpl`, `utils.js.tpl`, `package.json.tpl`, `run-all.sh.tpl`). Incluye `handleSummary()` (ver `[[k6-handle-summary-evidence]]`) en cada script.
8. **Validar checklist** — Antes de cerrar, recorre el DoD de 10 items del workflow `[[generate-k6-suite]]` y enlaza traza según `[[calidad-test-evidence-and-traceability]]`. Aplica `[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]` y `[[calidad-delivery-gate-contract]]` para declarar/verificar coverage y tier.

## Salidas

Estructura completa del proyecto (detalle en `[[k6-project-structure]]`):

```
{project_name}/
├── package.json
├── README.md
├── run-all.sh
├── .gitignore
└── tests/
    ├── config.js
    ├── utils.js
    ├── smoke-test.js
    ├── load-test.js
    ├── stress-test.js
    ├── spike-test.js
    └── soak-test.js
```

## Restricciones

- **Los 3 escenarios obligatorios son Línea Base / Carga / Estrés** (Smoke / Load / Stress en docs k6). Spike y Soak son **opt-in con justificación documentada** en `.evidence/scenarios-opt-in.md` (ver [vocabulary-and-scenario-mapping](references/vocabulary-and-scenario-mapping.md)). No es válido entregar solo Línea Base "porque el resto sigue el mismo patrón". Coverage formula en `references/coverage-formula.md`.
- **Sleep variable obligatorio** en flows multi-endpoint. `sleep(1)` constante prohibido salvo en smoke 1-endpoint puramente protocolar. Usar `sleep(randomIntBetween(1, 5))`. Detalle en `references/realistic-sleep-policy.md`.
- **Tier de thresholds declarado** en `.evidence/tier-declared.md` antes de generar. Aflojar thresholds para hacer pasar smoke es violación grave (anti-cheating). Default Moderate. Detalle en `references/threshold-tier-justification.md`.
- **IDs hardcodeados PROHIBIDOS en flujos CRUD.** Todo flujo CRUD debe capturar el ID del response del POST y reusarlo en GET/PUT/DELETE con guard clause. Detalle y patrón obligatorio en `[[k6-crud-dynamic-id-correlation]]`.
- **Header `Authorization` y `authToken`** dependen de `auth_mode`. Default `spec`: incluir SOLO si el spec declara `security` (`components.securitySchemes` o `securityDefinitions`). Override `external` (input `auth_mode: external` o env `EXTERNAL_AUTH=true`): incluir SIEMPRE. Detalle en `[[k6-enums-headers-security-extraction]]`.
- No inventes endpoints, campos, enums, headers ni códigos de error que no estén en el spec.
- Credenciales y `baseUrl` se leen únicamente desde `__ENV` con fallback en `config.js` (DoD #4). Nunca hardcoded en los `tests/*.js`. En modo `external`, `AUTH_TOKEN` debe documentarse en el `README.md` como variable de entorno **obligatoria** en runtime.
- Headers se construyen vía `getDefaultHeaders()` de `utils.js`; payloads vía `buildXxxBody()`. Nada inline en los tests.
- `options.stages` y `options.thresholds` son obligatorios en cada script emitido (los 3 obligatorios y los opt-in activados).
- `handleSummary()` debe exportar JSON a `results/${timestamp}-summary.json` en cada script.
- Entrega los archivos vía `[[calidad-streaming-files-protocol]]` (tests primero) y registra la traza según `[[calidad-test-evidence-and-traceability]]`.
