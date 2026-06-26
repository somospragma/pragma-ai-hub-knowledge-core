# Estrategia de autenticación: `setup()` vs refresh vs per-VU

Decidir dónde y cuándo se obtiene el token de autenticación es una decisión de diseño que impacta directamente la validez de las métricas de performance. Si el flujo autentica en cada iteración cuando auth NO es el SUT, las métricas del endpoint objetivo quedan distorsionadas y el provider de auth recibe una carga artificial.

## Decision tree

1. ¿El token es válido durante toda la corrida (TTL ≥ duración del script)?
   - Sí → usar `setup()` global. El token se obtiene una vez y se comparte a todos los VUs vía el return value de `setup()`.
2. ¿El token expira mid-run (TTL < duración del script)?
   - Sí → usar refresh controlado. Un helper a nivel de módulo cachea el token y lo refresca cuando se acerca a su expiración.
3. ¿El objetivo del test es medir el costo del auth flow (auth ES el SUT)?
   - Sí → autenticar per-VU (cada iteración hace login). El costo de auth se mide como parte del test.
4. Cualquier otro caso → default `setup()` + refresh handler conservador.

## Estrategia 1 — `setup()` global (preferida para load/stress/soak)

`setup()` corre una sola vez al inicio de la corrida, antes de instanciar VUs. Su return value se pasa como argumento a cada invocación del `default function`.

```javascript
import http from 'k6/http';
import { config } from './config.js';

export function setup() {
  const res = http.post(`${config.authUrl}/token`, {
    grant_type:    'client_credentials',
    client_id:     __ENV.CLIENT_ID,
    client_secret: __ENV.CLIENT_SECRET,
  });
  if (res.status !== 200) {
    throw new Error(`setup auth failed: status=${res.status} body=${res.body}`);
  }
  return { token: res.json('access_token') };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };
  // ... resto del flujo, sin autenticar nuevamente
}
```

Ventajas:

- El endpoint de auth recibe 1 request, no N×iteraciones.
- La métrica `http_req_duration` del SUT no se mezcla con la del IdP.
- Reproducibilidad: el mismo token se reusa en toda la corrida.

## Estrategia 2 — Refresh controlado (token expira mid-run)

Cuando la corrida dura más que el TTL del token (típico en `soak` o `stress` largo), `setup()` por sí solo no alcanza. Usar un helper con cache + chequeo de expiración:

```javascript
import http from 'k6/http';
import { config } from './config.js';

let token = null;
let expiresAt = 0;

export function getToken() {
  if (token && Date.now() < expiresAt) {
    return token;
  }
  const res = http.post(
    `${config.authUrl}/token`,
    { grant_type: 'client_credentials', client_id: __ENV.CLIENT_ID, client_secret: __ENV.CLIENT_SECRET },
    { tags: { name: 'auth', endpoint: 'auth', step: 'auth' } },
  );
  if (res.status !== 200) {
    throw new Error(`auth refresh failed: status=${res.status}`);
  }
  token = res.json('access_token');
  // restar 60s como buffer para evitar usar un token que expira durante la request
  expiresAt = Date.now() + (res.json('expires_in') * 1000) - 60000;
  return token;
}
```

Uso en el default function:

```javascript
export default function () {
  const headers = { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' };
  // ... request al SUT
}
```

Nota: en k6 cada VU tiene su propio contexto JS (no comparten el módulo de manera literal). El cache local por VU es suficiente para evitar autenticar en cada iteración. Si el IdP cobra/limita por request de auth, evaluar `--vus` bajo o usar `setup()`.

## Estrategia 3 — Per-VU auth (solo cuando auth ES el SUT)

Si el objetivo explícito del test es medir el login flow (capacidad de un IdP, throughput de un endpoint `/login`, etc.), autenticar dentro del `default function` es correcto y deseable:

```javascript
export default function () {
  const authRes = http.post(
    `${config.authUrl}/token`,
    { ...credentials },
    { tags: { name: 'auth', endpoint: 'auth', step: 'main', scenario: __ENV.SCENARIO_NAME } },
  );
  check(
    authRes,
    {
      'auth status is 200': (r) => r.status === 200,
      'has access_token': (r) => typeof r.json('access_token') === 'string' && r.json('access_token').length > 0,
      'expires_in is positive number': (r) => Number.isFinite(r.json('expires_in')) && r.json('expires_in') > 0,
    },
    { endpoint: 'auth', step: 'main', scenario: __ENV.SCENARIO_NAME },
  );
}
```

En esta estrategia el tag `step: 'main'` aplica a auth porque AUTH es el SUT. Documentarlo en `.evidence/auth-strategy.md`.

## Anti-pattern (Hallazgo #12)

Autenticar en CADA iteración cuando auth NO es el SUT:

```javascript
// MAL: cada iteración hace login + request al SUT
export default function () {
  const authRes = http.post(`${config.authUrl}/token`, { ...credentials });
  const token = authRes.json('access_token');
  const res = http.get(`${config.baseUrl}/transactions`, { headers: { Authorization: `Bearer ${token}` } });
  // ...
}
```

Consecuencias:

- `http_req_duration` agregado mezcla latencia de auth + latencia del SUT. El p95 deja de reflejar el comportamiento del SUT.
- El provider de auth recibe N×iteraciones de requests, lo cual puede activar rate limits, gatillar bloqueos del WAF, o disparar costos del IdP.
- La métrica `http_req_failed` agregada se infla con fallos de auth (timeouts del IdP, rate limit 429), enmascarando la salud real del SUT.
- En `stress` y `spike`, el IdP puede colapsar antes que el SUT, y el test queda midiendo el IdP en vez del SUT.

## Documentar la decisión

Registrar la estrategia elegida en `.evidence/auth-strategy.md` con:

- Estrategia: `setup` | `refresh` | `per-vu`.
- Justificación: TTL del token observado, duración del script, si auth es el SUT.
- Cómo se obtienen credenciales: `__ENV.CLIENT_ID` / `__ENV.CLIENT_SECRET` (nunca hardcoded).
- TTL asumido y buffer de refresh (si aplica).

## Cross-links

- `[[calidad-k6-greenfield]]`
- ``enums-headers-security-extraction.md``
- ``tag-policy-and-metrics-isolation.md``
- `[[calidad-pre-generation-protocol]]`
- `[[calidad-post-generation-protocol]]`
- `[[calidad-delivery-gate-contract]]`
