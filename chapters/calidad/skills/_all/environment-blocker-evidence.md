---
id: calidad-environment-blocker-evidence
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Schema universal .evidence/execution-status.json para reportar bloqueos de ambiente (WAF, red, auth, rate-limit, DNS, device, browser, JDK) sin auto-corregir."
tags: [evidence, environment, blockers, universal, mandatory]
enforcement: mandatory
---

# Environment Blocker Evidence — Schema universal `.evidence/execution-status.json`

Cuando una corrida termina sin poder validar el contrato porque el ambiente del cliente falla (no porque el código bajo prueba esté roto), el agente DEBE emitir `.evidence/execution-status.json` con el motivo categorizado y NO debe intentar "arreglar" el blocker con auto-corrección. El bloqueo es de infra/ambiente y se escala.

Este archivo es complementario a `[execution-metadata-schema](./execution-metadata-schema.md)`: el `metadata.json` describe la corrida; `execution-status.json` describe el bloqueo cuando lo hubo. Cuando el `reason` aplica, el campo `blockers[]` del metadata se llena con el mismo string (`environment_blocked_<type>`).

## Schema JSON universal

```json
{
  "exitCode": 1,
  "framework": "karate | playwright | k6 | appium",
  "endpoint_or_url": "https://api.example.com",
  "timestamp": "2026-06-05T10:30:15Z",
  "reason": "environment_blocked_waf | environment_blocked_network | environment_auth_fail | environment_rate_limit | environment_dns_fail | environment_device_unavailable | environment_browser_install_missing | environment_jdk_missing_or_wrong",
  "command": "mvn test -f pom.xml",
  "statusCode": 403,
  "responseHeaders": { "X-CDN": "Incapsula" },
  "stderr_tail": "...últimas N líneas del stderr para diagnóstico..."
}
```

## Categorías cerradas de `reason`

Lista cerrada (no inventar nuevas categorías; si una corrida no encaja, escalar):

| `reason` | Cuándo aplicar | Señal típica |
|---|---|---|
| `environment_blocked_waf` | El WAF/CDN intercepta requests y devuelve 403/406/451 sostenido independientemente del payload. | Header `X-CDN: Incapsula`/`Cloudflare`, body HTML con `Access Denied`. |
| `environment_blocked_network` | El runner no puede establecer conexión TCP/TLS al endpoint (firewall, egress restringido, allowlist faltante). | `connection refused`, `connect ETIMEDOUT`, TLS handshake aborted. |
| `environment_auth_fail` | El proveedor de auth (IdP, gateway) está caído o el token no se puede renovar. | 401/403 de `/oauth/token`, IdP `503`, claims rechazados sostenidamente. |
| `environment_rate_limit` | Rate limit del gateway impide la corrida planificada. | 429 sostenido con `Retry-After` mayor al horizonte de la prueba. |
| `environment_dns_fail` | El hostname del SUT no resuelve. | `getaddrinfo ENOTFOUND`, `name or service not known`. |
| `environment_device_unavailable` | El device/emulator Android requerido por la corrida no está conectado o el server Appium no responde. | `adb devices` vacío, Appium server `ECONNREFUSED 4723`. |
| `environment_browser_install_missing` | Playwright no encuentra browser binary (falta `npx playwright install`). | `Executable doesn't exist at ...`/`browserType.launch: ...`. |
| `environment_jdk_missing_or_wrong` | JDK ausente o versión incompatible (Karate exige 11/17, Appium exige 21). | `UnsupportedClassVersionError`, `java: command not found`, `mvn` aborta por toolchain. |

## Reglas

- El status final del delivery_gate es `partial` (NUNCA `success`) con `blocker: "environment_blocked_<type>"`.
- La auto-corrección con guardrails NUNCA intenta resolver un bloqueo de ambiente. Mod
ificar el test para evitar el WAF, o relajar matchers para sortear un 403, es **anti-cheating grave**.
- El agente reporta el bloqueo al usuario o al equipo de infra del cliente con el JSON crudo de `execution-status.json` como evidencia.
- Si la corrida tuvo bloqueo de ambiente, `metadata.json` se emite igualmente con `exit_code` real, `totals` parciales y `blockers: ["environment_blocked_<type>"]`. El `execution-status.json` es el detalle.
- Path canónico: `.evidence/execution-status.json` en la raíz del proyecto generado. Si hay múltiples corridas, postfijar con timestamp: `.evidence/execution-status-{ISO}.json`.

## Quién detecta y cómo

| Stack | Mecanismo de detección |
|---|---|
| Karate | Hook AfterAll del runner inspecciona `karate-summary.json`; si `featuresFailed == featuresTotal` y todos los failures retornaron mismo status (ej. 403 + header CDN), emite `execution-status.json` con `reason="environment_blocked_waf"`. |
| Playwright | Custom reporter `onEnd`: si `failureRate > 0.5` y todos los errores son `net::ERR_*` o `expect status 403`, emite el archivo. Pre-flight script detecta `environment_browser_install_missing` antes de `playwright test`. |
| K6 | Dentro de `handleSummary` se inspeccionan `http_req_failed`, `http_reqs{status:403}`, y headers vistos. Ver `[execution-status-and-blockers](../k6/k6-greenfield/references/execution-status-and-blockers.md)`. |
| Appium | Pre-flight script (`preflight-appium.sh`) valida `adb devices`, Appium server y JDK. Gradle `doFirst` aborta y escribe el archivo si el preflight falla. |

## Cross-links

`[[calidad-delivery-gate-contract]]`, `[execution-metadata-schema](./execution-metadata-schema.md)`, `[results-structure-universal](./results-structure-universal.md)`, `[[calidad-post-generation-protocol]]`, `[[calidad-test-evidence-and-traceability]]`.
