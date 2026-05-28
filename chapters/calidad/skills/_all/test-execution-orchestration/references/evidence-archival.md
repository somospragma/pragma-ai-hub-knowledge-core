# Evidence Archival

Política de archivado de evidencia generada por cada run. Aplica a todos los frameworks. Coordinar con `[[calidad-test-evidence-and-traceability]]` para la trazabilidad requisito → test → resultado → evidencia.

## Naming

Convención de path:

```
evidence/{client}/{date}/{framework}/{run_id}/
```

Donde:

- `{client}` — slug del cliente en kebab-case (ej. `acme-corp`, `banco-xyz`).
- `{date}` — fecha del run en formato `YYYY-MM-DD` (UTC).
- `{framework}` — `karate` | `playwright` | `k6` | `appium`.
- `{run_id}` — UUID generado por el orquestador (mismo que en `result-schema-common.md`).

Ejemplos:

```
evidence/acme-corp/2026-05-28/playwright/4f9c1e2a-7b8d-4f3e-9a1b-c2d3e4f5a6b7/
evidence/banco-xyz/2026-05-28/karate/8d2e3f4a-1b5c-6d7e-8f9a-0b1c2d3e4f5a/
```

## Storage por cliente

| Cliente / Tipo | Backend recomendado | Justificación |
|---|---|---|
| Cliente AWS-native | S3 con versioning + lifecycle | Costo bajo, integración nativa con CloudWatch/Athena. |
| Cliente Azure-native | Azure Blob Storage (Hot → Cool → Archive tiers) | Integración con Azure DevOps Pipelines. |
| Cliente GCP-native | GCS con object lifecycle | Integración con Cloud Build. |
| Cliente on-prem | Artifactory / Nexus Raw | Cuando no se permite cloud externo. |
| Cliente regulado sin cloud | Storage interno + WORM | HIPAA/SOX requieren inmutabilidad. |

El backend se confirma como parte de `[[calidad-mandatory-inputs-protocol]]` al inicio del engagement.

## Retención

| Perfil de cliente | Retención mínima | Storage tier |
|---|---|---|
| No regulado, runs de PR / smoke | 30 días | Hot/Standard. |
| No regulado, nightly / release | 90 días | Hot 30d → Cool 60d. |
| Regulado financiero (PCI, SOX) | 7 años | Hot 90d → Cool 1y → Archive/Glacier 6y. |
| Regulado salud (HIPAA) | 6 años post-última actividad | Hot 90d → Cool 1y → Archive ≥ 5y. |
| Regulado gobierno | Según contrato (típico 5-10 años) | Confirmar tier según política del cliente. |

La retención debe estar declarada en el lifecycle policy del bucket/container, no depender de scripts manuales.

## Contenido del bundle

Por cada `run_id` se archiva el siguiente conjunto:

- `normalized.json` — resultado parseado al esquema común (ver `result-schema-common.md`).
- `summary.{json,html}` — summary nativo del framework.
- `junit.xml` o `results.json` — output estructurado original (no transformado).
- `report/` — HTML report navegable (Karate, Playwright, Serenity).
- `screenshots/` — todas las capturas, organizadas por test id.
- `traces/` — Playwright `trace.zip` por test fallido.
- `videos/` — videos cuando estén habilitados.
- `logs/run.log` — stdout/stderr completo capturado por `tee`.
- `metadata.json` — `{run_id, client, framework, started_at, duration_ms, exit_code, status, git_sha, ci_build_id}`.

## Enmascaramiento de datos sensibles

Antes de archivar:

- Tokens, secrets y credenciales en logs → reemplazar con `***REDACTED***`.
- PII en payloads / screenshots → enmascarar si el contrato del cliente lo exige.
- Headers `Authorization`, `Cookie`, `Set-Cookie` en traces → strip antes de upload.

Coordinar con la política de seguridad del cliente. La omisión de enmascaramiento sobre datos productivos es una violación contractual potencial.

## Inmutabilidad

Para clientes regulados, los buckets/containers deben configurarse con:

- **Object Lock** (S3) / **Immutable Blob Storage** (Azure) en modo WORM.
- **Versioning** habilitado.
- **Borrado bloqueado** durante el período de retención.

Esto garantiza que la evidencia no pueda ser modificada post-facto, requisito típico de auditoría.

## Indexación y búsqueda

Para facilitar consultas:

- Tag los objetos con metadata: `client`, `framework`, `status`, `git_sha`, `branch`.
- Mantener un índice consultable (DynamoDB / Cosmos DB / tabla en data lake) con `run_id → path`.
- Permitir queries del tipo "todos los runs failed del último mes para el cliente X".

## Integración con `[[calidad-test-evidence-and-traceability]]`

El `run_id` y los paths de evidencia se inyectan en el sistema de trazabilidad (Allure / ReportPortal / matriz ALM) para cerrar el ciclo: **requisito → test → run → evidencia archivada**. Ver detalle en ese skill.
