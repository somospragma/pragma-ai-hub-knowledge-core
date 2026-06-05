# Plantilla específica de K6 para el reporte ejecutivo

Esta plantilla guía las secciones del reporte ejecutivo cuando `framework = k6`. Complementa `report-structure.md`. Se invoca desde el Paso 6 del `SKILL.md`. Es el stack con mayor densidad de métricas: la plantilla pone foco en latencias, error rate, disponibilidad y comparación corrida-a-corrida.

## Fuentes primarias

- `results/<scenario>/<timestamp>/summary.json` por cada escenario ejecutado (smoke, load, stress, spike, soak).
- `metadata.json` por escenario (timestamp, commit, branch, environment, comando exacto, tier de thresholds, auth_mode, VUs, duración).
- Logs de ejecución (`results/<scenario>/<timestamp>/k6-stdout.log`) para detectar bloqueos de ambiente.

## Sección 2 — Cumplimiento de SLAs (vista K6)

Mapear desde `STRATEGY.md`:

- `http_req_duration` p50, p90, p95, p99 vs threshold declarado por escenario.
- `http_req_failed` (error rate) vs threshold.
- Disponibilidad calculada: `(1 - http_req_failed) * 100` por escenario.
- Throughput observado (`http_reqs/s`) vs throughput declarado.

Tabla:

| Escenario | Métrica | Declarado | Observado | Cumple |
|---|---|---|---|---|
| linea-base | p95 | < 800 ms | 712 ms | OK |
| linea-base | error rate | < 1% | 0.3% | OK |
| carga | p95 | < 1500 ms | 1623 ms | FAIL |
| carga | error rate | < 1% | 1.2% | FAIL |
| estres | disponibilidad | >= 95% | 96.4% | OK |

## Sección 3 — Resultados por escenario y por endpoint

Tabla principal por escenario:

| Escenario | VUs pico | Duración | Iteraciones | p50 | p90 | p95 | p99 | Error rate | Disponibilidad | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| linea-base | 5 | 5 min | 1840 | 312 ms | 580 ms | 712 ms | 1.1 s | 0.3% | 99.7% | verde |
| carga | 20 | 10 min | 11200 | 421 ms | 1.2 s | 1.6 s | 2.4 s | 1.2% | 98.8% | amarillo |
| estres | 60 | 15 min | 28400 | 894 ms | 2.8 s | 3.9 s | 6.2 s | 3.6% | 96.4% | rojo |

Sub-tabla por endpoint dentro de cada escenario (mostrar solo los top-5 con peor p95):

| Endpoint | Iteraciones | p95 | Error rate | Cumple SLA propio |
|---|---|---|---|---|
| POST /pet | 4200 | 1.9 s | 2.1% | FAIL |
| GET /pet/{id} | 12000 | 480 ms | 0.1% | OK |

## Sección 4 — Comparación corrida-a-corrida con porcentaje delta

| Escenario | Métrica | Corrida anterior | Corrida actual | Delta absoluto | Delta % |
|---|---|---|---|---|---|
| linea-base | p95 | 820 ms | 712 ms | -108 ms | -13.2% |
| carga | p95 | 1.45 s | 1.62 s | +170 ms | +11.7% |
| carga | error rate | 0.8% | 1.2% | +0.4 pp | +50% |
| estres | disponibilidad | 97.1% | 96.4% | -0.7 pp | -0.7% |

Cualquier degradación > 10% en p95 o > 30% en error rate se destaca en rojo y se incluye en hallazgos.

## Sub-sección: bloqueos de ambiente detectados

Si `k6-stdout.log` muestra patrones de WAF (403 sostenido, headers de CDN, captchas, `Permitted-Cross-Domain-Policies`), `429` rate limit no documentado, DNS no resuelve, o TLS handshake roto, listarlos aquí con cita literal del log:

| Patrón detectado | Escenario | Endpoint | Ocurrencias | Clasificación |
|---|---|---|---|---|
| `Server: cloudfront` + 403 | carga | POST /pet | 142 | ENVIRONMENT_BLOCKED |
| `429 Too Many Requests` | estres | GET /pet/{id} | 893 | ENVIRONMENT_BLOCKED (rate limit no declarado) |

Estos casos NO son `SUT_BUG` y NO son `THRESHOLD_TOO_STRICT`: requieren coordinación con Infra antes de re-correr.

## Sección 7 — Anexos específicos K6

- Comando exacto por escenario (`k6 run -e BASE_URL=$BASE_URL tests/<escenario>/main.js`).
- `auth_mode` aplicado (`spec` / `external`).
- `tier` de thresholds (`Conservative` / `Moderate` / `Relaxed`).
- Paths a `summary.json` por escenario.
- Hardware del runner (cpu / ram / región si está en metadata) — relevante para reproducir latencias.
- Recordar al lector: si los thresholds resultaron irreales (`THRESHOLD_TOO_STRICT` recurrente), invocar `[[calibrate-k6-thresholds]]` antes de la siguiente corrida.
