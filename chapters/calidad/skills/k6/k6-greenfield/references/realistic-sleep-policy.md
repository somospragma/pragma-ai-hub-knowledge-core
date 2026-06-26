
# Realistic sleep policy — K6 (K-E)

Politica de think-time entre requests dentro de un VU. K6 no inyecta latencia humana automaticamente: si los VUs disparan back-to-back, el perfil de carga es artificial y los resultados (RPS, P95, error rate bajo concurrencia) NO reflejan produccion.

## Regla

- **PROHIBIDO** `sleep(1)` constante dentro de un flow CRUD o cualquier escenario que simule comportamiento humano (load/stress/spike/soak). Un sleep constante genera "marching VUs": todos pausan y reanudan al mismo tiempo, produciendo ondulaciones artificiales en RPS y enmascarando contencion real.
- **OBLIGATORIO** `sleep(randomIntBetween(1, 5))` para think-time variable. El rango (min,max) debe alinearse a la naturaleza del endpoint (ver tabla).
- **Permitido** `sleep(1)` solo en smoke aislado de funcionalidad puramente protocolar (un solo endpoint, sin CRUD, sin flow). Si el smoke encadena varios endpoints, aplica la regla de variabilidad.

## Import obligatorio

```javascript
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
```

Si el entorno es air-gapped, vendorizar `k6-utils` igual que `k6-summary` (ver ``handle-summary-evidence.md``).

## Tabla cuando-cada-uno

| Tipo de flujo | Rango sugerido | Razon |
|---|---|---|
| Smoke 1-endpoint (validacion protocolar) | `sleep(1)` permitido | Sin think-time humano que simular. |
| Smoke CRUD multi-endpoint | `sleep(randomIntBetween(1, 3))` | Hay flow; usuario tarda en pasar entre pantallas. |
| Load test, comportamiento normal | `sleep(randomIntBetween(1, 5))` | Think-time tipico web (1-5s). |
| Stress test (busca quiebre) | `sleep(randomIntBetween(1, 3))` | Ritmo agresivo pero variable. |
| Spike test (rafagas) | `sleep(randomIntBetween(1, 2))` | Picos rapidos, poco think-time. |
| Soak test (estabilidad larga) | `sleep(randomIntBetween(2, 8))` | Comportamiento humano completo, distribucion ancha. |
| API-to-API (sin usuario) | `sleep(randomIntBetween(0, 1))` o sin sleep | No hay humano; el upstream controla la cadencia. |

## Snippets

```javascript
// CORRECTO — think-time variable
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { sleep } from 'k6';

sleep(randomIntBetween(1, 5));
```

```javascript
// INCORRECTO — think-time constante (anti-pattern)
import { sleep } from 'k6';
sleep(1);  // produce trafico sincronico artificial
```

## Anti-pattern relacionado: 0 sleep

Tampoco es valido eliminar todos los sleeps "para maximizar RPS". Maximizar RPS sin think-time NO es una metrica de capacidad real del servicio — es una metrica de saturacion del cliente. Si el caso de uso requiere alto RPS sin sleeps, usar `executor: 'constant-arrival-rate'` con `rate:` fijo en RPS objetivo, no eliminar sleeps de un VU executor.

## Cross-links

- ``five-script-types.md`` — perfiles VU/duracion.
- ``crud-dynamic-id-correlation.md`` — donde aplican los sleeps entre POST/GET/DELETE.
- `[[calidad-test-self-correction-loop/references/anti-cheating-guardrails]]` — entrega que aflojar es trampa; eliminar sleeps lo es tambien.
