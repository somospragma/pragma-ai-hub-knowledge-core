# Datos para Performance Testing — Específico k6

Las pruebas de performance imponen restricciones que no aplican a otros niveles: alto volumen de datos, alta concurrencia, presupuesto de memoria por VU. Este documento concentra los patrones que evitan saturar al runner y al repositorio.

## Principios

1. **Cargar el dataset una sola vez por proceso**, no por VU ni por iteración.
2. **Compartir memoria entre VUs** con `SharedArray` cuando aplique.
3. **Indexar por `__VU` y `__ITER`** para distribuir el uso del dataset sin colisiones.
4. **No commitear datasets pesados** al repo principal: usar Git LFS, DVC o descarga en CI.
5. **Pool de IDs pre-creados** para evitar dependencia de crear datos durante la prueba.

## SharedArray — patrón base

`SharedArray` carga un JSON una vez por proceso k6 y lo expone a todas las VUs sin duplicar memoria.

```javascript
import { SharedArray } from 'k6/data';
import http from 'k6/http';

const users = new SharedArray('users', () => {
  return JSON.parse(open('./fixtures/users-10k.json'));
});

export const options = {
  vus: 200,
  duration: '5m',
};

export default function () {
  const idx = (__VU * 1000 + __ITER) % users.length;
  const user = users[idx];
  http.get(`${__ENV.BASE_URL}/users/${user.id}`);
}
```

Notas:

- `open()` solo funciona en **init context** (top-level, fuera de `default`).
- `SharedArray` es read-only.
- La indexación `__VU * 1000 + __ITER` evita que múltiples VUs golpeen el mismo registro y rompan caché de DB.

## CSV con PapaParse

Para datasets en CSV (más comunes cuando el equipo de datos los entrega así):

```javascript
import { SharedArray } from 'k6/data';
import papaparse from 'https://jslib.k6.io/papaparse/5.1.1/index.js';

const csv = new SharedArray('users', () => {
  const f = open('./fixtures/users-10k.csv');
  return papaparse.parse(f, { header: true }).data;
});
```

## Generadores on-the-fly con seed

Para datasets que cambian frecuentemente o cuando el tamaño del fixture incomoda, generar en memoria con seed determinista:

```javascript
import { SharedArray } from 'k6/data';

function generateUsers(count, seed) {
  // Mulberry32 PRNG determinista
  let s = seed;
  const rand = () => {
    s |= 0; s = s + 0x6D2B79F5 | 0;
    let t = Math.imul(s ^ s >>> 15, 1 | s);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
  return Array.from({ length: count }, (_, i) => ({
    id: `user-${i}`,
    email: `synth-${Math.floor(rand() * 1e9)}@example.com`,
  }));
}

const users = new SharedArray('users', () => generateUsers(50000, 12345));
```

Pros: no requiere fixture en disco. Cons: setup más lento (50K objetos = ~300ms).

## Pool de IDs pre-creados via setup()

Cuando la prueba requiere registros existentes en DB (no se pueden inventar IDs), usar `setup()` para crearlos vía API admin y pasar la lista a `default`.

```javascript
import http from 'k6/http';

export const options = { vus: 100, duration: '3m' };

export function setup() {
  // Crea 5000 usuarios y devuelve sus IDs
  const res = http.post(`${__ENV.ADMIN_URL}/users/bulk`, JSON.stringify({
    count: 5000,
    prefix: 'k6-perf-',
  }), { headers: { Authorization: `Bearer ${__ENV.ADMIN_TOKEN}` } });

  return { ids: res.json('ids') };
}

export default function (data) {
  const id = data.ids[(__VU * 100 + __ITER) % data.ids.length];
  http.get(`${__ENV.BASE_URL}/users/${id}`);
}

export function teardown(data) {
  http.del(`${__ENV.ADMIN_URL}/users/bulk`,
    JSON.stringify({ ids: data.ids }),
    { headers: { Authorization: `Bearer ${__ENV.ADMIN_TOKEN}` } });
}
```

`setup()` corre **una sola vez** por ejecución, fuera del cómputo de carga. Su duración no cuenta para `duration`.

## Carga de fixtures pesados en CI

No commitear archivos >50MB al repo principal. Patrón:

```yaml
- name: Descargar dataset de perf
  run: |
    aws s3 cp s3://qa-datasets/perf/users-1m-v1.0.0.json.gz ./fixtures/
    gunzip ./fixtures/users-1m-v1.0.0.json.gz
    mv ./fixtures/users-1m-v1.0.0.json ./fixtures/users-perf.json

- name: k6 run
  run: k6 run scripts/load-search.js
  env:
    BASE_URL: ${{ secrets.PERF_API_URL }}
```

## Distribución de carga por VU

Anti-patrón: todas las VUs golpean los mismos N IDs (caching engaña la prueba).

```javascript
// MAL: todas las VUs leen el primer usuario
const user = users[0];

// BIEN: distribuir uniformemente
const user = users[(__VU * 7919 + __ITER) % users.length];
// 7919 es primo, mejora distribución
```

## Tamaño recomendado por tipo de prueba

| Tipo                 | Dataset sugerido      |
|----------------------|-----------------------|
| Smoke                | 10-100 registros      |
| Load                 | 10K-100K registros    |
| Stress               | 100K-1M registros     |
| Soak (largo plazo)   | 1M+ registros         |

Si la prueba requiere `cardinality` (datos únicos por iteración), el dataset debe tener al menos `vus * duration_iters` registros distintos.

## Anti-patrones específicos de k6

- **Llamar `open()` fuera del init context** → error en runtime.
- **Cargar JSON gigante sin `SharedArray`** → la memoria por VU explota a `1MB * vus * size`.
- **Generar el mismo dato en cada iteración con Faker sin seed** → CPU se va en generación, no en carga.
- **Crear datos en `default()`** → consume capacidad del SUT que debería medirse.
- **`teardown()` con borrado uno a uno** → puede demorar más que la prueba misma; usar bulk delete.

## Snippet completo: load test con dataset versionado

```javascript
import http from 'k6/http';
import { SharedArray } from 'k6/data';
import { check, sleep } from 'k6';

const users = new SharedArray('users-v1.2.0', () => {
  return JSON.parse(open('./fixtures/dataset-v1.2.0-perf-users-a3f1.json'));
});

export const options = {
  scenarios: {
    constant: {
      executor: 'constant-arrival-rate',
      rate: 500,
      timeUnit: '1s',
      duration: '10m',
      preAllocatedVUs: 200,
      maxVUs: 500,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<400', 'p(99)<800'],
    http_req_failed:   ['rate<0.01'],
  },
};

export default function () {
  const u = users[(__VU * 7919 + __ITER) % users.length];
  const res = http.get(`${__ENV.BASE_URL}/users/${u.id}`, {
    headers: { Authorization: `Bearer ${__ENV.API_TOKEN}` },
  });
  check(res, { 'status 200': r => r.status === 200 });
  sleep(0.1);
}

export function handleSummary(data) {
  const iso = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${iso}-summary.json`]: JSON.stringify({
      ...data,
      dataset: 'dataset-v1.2.0-perf-users-a3f1',
    }, null, 2),
  };
}
```

## Restricciones

- No commitees datasets >50MB al repo principal.
- No uses `Faker` dentro de `default()` en pruebas de carga reales (sólo en smoke).
- Documenta el dataset usado en `handleSummary()` para trazabilidad.
- Encadena con `[[calidad-test-evidence-and-traceability]]` y `datasets-versioning.md`.
