# `options.scenarios` y executors nativos de K6

Documento de referencia para elegir el executor adecuado al objetivo de cada workload bajo la arquitectura modular (``modular-architecture.md``).

Cross-links: `[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-k6-greenfield]]`, ``modular-architecture.md``.

## Por qué `options.scenarios` y no `vus + duration`

`vus + duration` es la API legacy de K6: levanta una única ejecución implícita, no permite tags por escenario, no permite múltiples ejecuciones concurrentes y no expone control fino sobre la curva de carga. `options.scenarios` declara explícitamente uno o más bloques con su executor, su tagging y su curva, habilitando:

- Múltiples escenarios concurrentes (p. ej. browsing + checkout) en un mismo `k6 run`.
- Tags por scenario para segmentar métricas en Grafana/Prometheus.
- Elección del executor adecuado al objetivo (control de VUs vs control de QPS).
- Composición predecible con `workloads/*.js` aislados de la lógica HTTP.

## Comparativa de executors nativos

| Executor | Cuándo usarlo | Controla | Ejemplo |
|---|---|---|---|
| `ramping-vus` | Baseline / Load / Spike con rampa progresiva de VUs | Concurrencia | start 0, ramp a 50 en 5min, sostener 10min, ramp a 0 |
| `constant-vus` | Carga sostenida sin rampa (soak, smoke 1-endpoint) | Concurrencia | 30 VUs por 10min |
| `ramping-arrival-rate` | Stress con control explícito de QPS (no de VUs) | Throughput (req/s) | 100 req/s incrementando a 500 req/s en 10min |
| `constant-arrival-rate` | SLA QPS estricto / test de capacidad | Throughput (req/s) | 200 req/s sostenido por 15min |
| `per-vu-iterations` | CRUD flows determinísticos por VU | Iteraciones por VU | 5 VUs × 10 iter cada uno |
| `shared-iterations` | Total fijo de iteraciones distribuido entre VUs | Iteraciones totales | 1000 iter total entre 10 VUs |

### Notas por executor

- **`ramping-vus`**: la unidad de presión es el VU (usuario virtual). El throughput resultante depende de la latencia del backend: si el sistema se degrada, los VUs se quedan esperando y el QPS efectivo baja. Útil para simular usuarios reales.
- **`ramping-arrival-rate`** y **`constant-arrival-rate`**: la unidad de presión es la **request por segundo** (QPS). K6 levanta tantos VUs como necesite (`preAllocatedVUs`, `maxVUs`) para sostener el rate aunque el backend se degrade. Útil para tests de capacidad y stress real: el sistema recibe la presión declarada incluso si la latencia explota.
- **`per-vu-iterations`** y **`shared-iterations`**: cierran al completar las iteraciones, no por tiempo. Útil para suites determinísticas (regresión por endpoint, datasets fijos).

## Qué executor para qué escenario

| Escenario | Executor recomendado | Racional |
|---|---|---|
| Línea Base / Smoke | `ramping-vus` o `constant-vus` | Baja concurrencia (20-30% del peak), foco en validar flow + baseline de latencia. |
| Carga / Load | `ramping-vus` | 100% del peak esperado, rampa progresiva para observar comportamiento bajo carga normal. |
| Estrés / Stress | `ramping-arrival-rate` (preferido) o `ramping-vus` | 200-300% del peak. `arrival-rate` garantiza que la presión se aplica aun si el sistema se degrada. |
| Spike | `ramping-vus` con stages cortos y target alto | Pico súbito (30s) + recuperación, valida resiliencia y elasticidad. |
| Soak | `constant-vus` con duración larga (2-8h) | Detección de memory leaks, drift de latencia, agotamiento de connection pools. |

## Anti-patterns

- **Usar solo `vus + duration` sin `scenarios`**: se pierde control de carga, tagging por escenario y composabilidad. **Prohibido en proyectos greenfield modulares.**
- **Usar `ramping-vus` para stress real cuando el SLA es QPS**: si el backend se degrada, el QPS efectivo cae y el test deja de aplicar la presión declarada. Para stress por QPS, usar `ramping-arrival-rate`.
- **Mezclar lógica HTTP y `options` en el mismo archivo bajo `scenarios/`**: viola la separación scenario vs workload (``modular-architecture.md``).
- **Omitir `tags: { scenario: '...' }`**: impide segmentar métricas por workload en dashboards.
- **`preAllocatedVUs` muy bajo en `arrival-rate`**: K6 emite warning `insufficient VUs` y el rate efectivo cae. Dimensionar `preAllocatedVUs` ≈ rate × latencia_p95_segundos.
