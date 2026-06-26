# Plantillas del proyecto generado

Cada seccion corresponde a un archivo que el agente debe materializar en la ruta indicada (relativa a la raiz del proyecto generado). Respeta los placeholders `{{...}}`.

## `README.md`

````markdown
# {{project_name}}

Suite de performance testing K6 generada por el chapter calidad.

## Prerequisitos

| Herramienta              | Versión          | Obligatoriedad        | Notas                                                          |
|--------------------------|------------------|-----------------------|----------------------------------------------------------------|
| k6                       | `>= 0.50.0`      | Obligatorio           | Runtime de los scripts. Instalar desde https://k6.io/docs/      |
| jq                       | cualquier 1.x    | Recomendado, opcional | Pretty-print y extracción rápida de métricas en `results/*.json` |
| python (`json.tool`)     | `>= 3.6`         | Alternativa portable  | Reemplaza a `jq` cuando no esté disponible                      |
| node (`-e ...`)          | `>= 18`          | Alternativa portable  | Reemplazo extra cuando ni `jq` ni `python` estén disponibles    |

**Alternativas portables a `jq`** (cuando `jq` no está instalado):

```bash
# Opción A — python (suele venir preinstalado en mac/linux)
python -m json.tool results/*-summary.json

# Opción B — node
node -e 'console.log(JSON.parse(require("fs").readFileSync(0)))' < results/*-summary.json
```

## Variables de entorno

| Variable      | Obligatoriedad                                | Descripción                                                 |
|---------------|-----------------------------------------------|-------------------------------------------------------------|
| `BASE_URL`    | Obligatoria                                   | URL base del SUT                                            |
| `AUTH_TOKEN`  | Obligatoria si `auth_mode = external`         | Token Bearer emitido fuera de k6 (IdP, gateway, mTLS, etc.) |

## Quick start

Sin asumir `jq` instalado. Reemplazar `BASE_URL` por el valor real:

```bash
# 1. Verificar k6 instalado y versión >= 0.50.0
k6 version

# 2. Smoke 1:1 (validación end-to-end del scaffold, 1 VU + 1 iteración)
BASE_URL=https://api.example.com k6 run tests/smoke-test.js --vus 1 --iterations 1

# 3. Smoke completo según options.stages
BASE_URL=https://api.example.com k6 run tests/smoke-test.js

# 4. Suite completa (linea-base -> carga -> estres + opt-in)
BASE_URL=https://api.example.com bash run-all.sh

# 5. Ver resumen (sin jq) — alternativa portable
python -m json.tool results/*-summary.json | grep -E '(http_req_duration|http_req_failed|iterations)'
```

## Escenarios

Esta suite incluye 3 escenarios **obligatorios** y hasta 2 escenarios **opt-in** (activados con justificación documentada en `.evidence/scenarios-opt-in.md`):

| Negocio    | k6 docs | Default      | Archivo            |
|------------|---------|--------------|--------------------|
| Línea Base | Smoke   | Obligatorio  | `tests/smoke-test.js` |
| Carga      | Load    | Obligatorio  | `tests/load-test.js`  |
| Estrés     | Stress  | Obligatorio  | `tests/stress-test.js` |
| (opt-in)   | Spike   | Solo si aplica | `tests/spike-test.js` |
| (opt-in)   | Soak    | Solo si aplica | `tests/soak-test.js`  |

## Evidencia

Cada ejecución genera `results/<timestamp>-summary.json`. Conservar para trazabilidad y para alimentar `[[calidad-calibrate-k6-thresholds]]`.
````

## `STRATEGY.md`

```markdown
# STRATEGY.md — {{project_name}} (K6)

Documento de estrategia previo a la generación de scripts. Debe estar aprobado explícitamente por el usuario antes de emitir el primer `.js` de test. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- SUT: {{sut_name}} — {{sut_description}}
- Tipo de SUT: API REST / GraphQL — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}} (Dev, Infra, QA lead, PO, capacity planner si aplica)
- Stack tecnológico del SUT: {{sut_stack}}
- Tipo de relación: greenfield (proyecto K6 nuevo)
- Spec: {{spec_path}} ({{spec_format}})
- `base_url`: {{base_url}}
- Firma (perfil del sistema): {{firma}} — derivar tier inicial (mission-critical → Conservative; business-as-usual → Moderate; internal → Relaxed)
- `auth_mode`: {{auth_mode}} (`spec` default / `external`)

## 2. Volumen y SLAs

Sección crítica para K6 — alimenta `options.thresholds` de cada escenario.

| SLA | Valor declarado | Notas |
|---|---|---|
| Usuarios concurrentes sostenido | {{concurrent_users_sustained}} | base para `carga` |
| Usuarios concurrentes peak | {{concurrent_users_peak}} | base para `estres` |
| Peak QPS | {{peak_qps}} | si aplica executor `ramping-arrival-rate` |
| p50 latencia | < {{p50_ms}} ms | global o por endpoint |
| p95 latencia | < {{p95_ms}} ms | global o por endpoint |
| p99 latencia | < {{p99_ms}} ms | opcional |
| Error rate máximo | < {{error_rate_pct}}% | `http_req_failed` |
| Disponibilidad objetivo | >= {{availability_pct}}% | (1 - error_rate) * 100 |
| Ventana de mantenimiento | {{maintenance_window}} | requerida para `carga`, `estres`, `spike`, `soak` |

## 3. Alcance funcional

- Endpoints en scope: {{endpoints_in_scope}}
- Endpoints fuera de scope: {{endpoints_out_of_scope}} ({{out_of_scope_reason}})
- CRUD flows detectados: {{crud_flows}}
- Endpoint objetivo principal vs auxiliares: {{primary_vs_auxiliary}}

## 4. Dependencias externas

- Auth: `auth_mode = {{auth_mode}}`. Si `external`, declarar env var `AUTH_TOKEN` obligatoria en README.
- Endpoint de obtención de token (si aplica `setup()` o `per-vu`): {{auth_endpoint}}
- Refresh policy: {{auth_refresh_strategy}} (setup única / per-vu / refresh on 401)
- Bases de datos: {{database_dependencies}}
- Servicios externos consumidos por el SUT durante la carga: {{external_services}}

## 5. Riesgos conocidos

- WAF en ambiente de prueba: {{waf_status}} — proveedor: {{waf_provider}}. **Allowlist coordinada con Infra es prerrequisito para ejecutar `carga`, `estres`, `spike`, `soak`** (de lo contrario los fallos serán `ENVIRONMENT_BLOCKED`, no SUT_BUG).
- Rate limits documentados: {{rate_limits}}
- Ambiente compartido vs dedicado: {{environment_isolation}}
- Restricciones regulatorias (HIPAA/SOX/PCI/FedRAMP): {{regulatory_constraints}} (modo default `dry-run` si aplica)
- Costo de carga (si SUT cobra por request a terceros): {{cost_per_run}}

## 6. Próximos pasos

- Archivos a generar: 3 obligatorios + opt-in (ver 7.1) + `utils.js`, `config.js`, `package.json`, `run-all.sh`, `README.md`.
- Comando smoke (gate del loop): `k6 run -e BASE_URL=$BASE_URL tests/smoke-test.js` con 1 VU y 1 iteración.
- Comando suite completa: `run-all.sh` orquesta `linea-base → carga → estres`.
- Reporte ejecutivo: formato {{report_format}} (default `html`) con sección K6 (latencias, error rate, disponibilidad, comparación corrida-a-corrida).

## 7. Estrategia K6

### 7.1 Escenarios

Los 3 escenarios obligatorios siempre se generan. `spike` y `soak` son opt-in con justificación.

| Escenario | Obligatorio | Workload (% sostenido) | VUs / arrival rate | Duración | Executor | Justificación opt-in |
|---|---|---|---|---|---|---|
| linea-base (smoke) | sí | 20-30% del sostenido | {{baseline_vus}} | {{baseline_duration}} | `ramping-vus` | — |
| carga (load) | sí | 100% del sostenido | {{load_vus}} | {{load_duration}} | `ramping-vus` o `ramping-arrival-rate` | — |
| estres (stress) | sí | 200-300% del sostenido | {{stress_vus}} | {{stress_duration}} | `ramping-vus` | — |
| spike | no | picos cortos N× sostenido | {{spike_vus}} | {{spike_duration}} | `ramping-arrival-rate` | {{spike_reason}} |
| soak | no | sostenido prolongado | {{soak_vus}} | {{soak_duration}} (1-8 h) | `constant-vus` | {{soak_reason}} |

### 7.2 Tier de thresholds elegido

- Tier: {{thresholds_tier}} (Conservative / Moderate / Relaxed)
- Justificación: {{tier_reason}} (deriva de `user_story.SLA` → `firma.SLA` → default Moderate)
- Aplicar `[thresholds-three-tiers](thresholds-three-tiers.md)` para los valores numéricos exactos por tier.

### 7.3 Auth strategy

- `auth_mode`: {{auth_mode}}
- Modo de adquisición del token: {{token_acquisition}} (setup única en `setup()` / refresh en handler / per-vu)
- Env vars necesarias: `BASE_URL`{{auth_env_vars_extra}}

### 7.4 Data correlation y CRUD

- Flows CRUD detectados (full / partial): {{crud_detail}}
- IDs dinámicos: aplicar `[crud-dynamic-id-correlation](crud-dynamic-id-correlation.md)` con guard clause.
- Payload builders en `utils.js` (`buildXxxBody`).

### 7.5 Bloqueos esperados de ambiente

Si se prevé que carga / estres dispare WAF, rate limit, o agote DB, declararlo aquí ANTES de correr para que los fallos no se clasifiquen erróneamente como `SUT_BUG` en el reporte ejecutivo:

- {{expected_environment_blockers}}

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar scripts K6.
```

## `config.js`

```javascript
// {{project_name}} — configuracion compartida
//
// Slots dependientes del spec:
//   {{baseUrl}}             — URL base por default (puede sobrescribirse con BASE_URL).
//   {{enumArrays}}           — arrays generados desde schema.enum / properties.{f}.enum.
//   {{constantHeaders}}      — valores constantes de headers (e.g. True-Client-IP).
//
// Reglas:
//   - baseUrl SIEMPRE desde __ENV.BASE_URL con fallback local.
//   - authToken SOLO si auth_mode='spec' y el spec declara security, o si auth_mode='external'.
//   - Nunca hardcodear credenciales o URLs en los tests/*.js — solo aqui o via __ENV.

export const config = {
  baseUrl: __ENV.BASE_URL || '{{baseUrl}}',
  authToken: __ENV.AUTH_TOKEN || '',

  // Enums extraidos del spec (top-level y property-level)
  // {{enumArrays}} — placeholder a expandir por el generador.
  documentNames: ['CC', 'TI', 'CE'],
  channels: ['APP', 'WEB'],

  // Valores constantes de headers documentados en el spec
  trueClientIp: '192.168.1.100',
};
```

## `load-test.js`

```javascript
// DEPRECATED: monolithic single-file template. Use modular structure instead: scenarios/ + workloads/ + tests/{escenario}/main.js + shared/.
// See references/modular-architecture.md and references/options-scenarios-executors.md.
// Keep this file only for brownfield projects that already use the monolithic pattern.

// {{project_name}} — load-test.js
// Proposito: carga normal y pico esperado, validar SLAs declarados.
// VUs ramping 0 -> 10 -> 30 -> 50 -> 0, duration ~20m. Tier por default: Moderate.

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

import { config } from './config.js';
import { getDefaultHeaders, buildCreateUserBody } from './utils.js';

export const options = {
  stages: [
    { duration: '2m',  target: 10 },
    { duration: '5m',  target: 30 },
    { duration: '10m', target: 50 },
    { duration: '3m',  target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
};

export default function () {
  let resourceId;

  group('users-crud', function () {
    const createRes = http.post(
      `${config.baseUrl}/users`,
      JSON.stringify(buildCreateUserBody()),
      { headers: getDefaultHeaders(), tags: { endpoint: 'POST /users', scenario: 'load' } },
    );
    check(createRes, {
      'POST /users status is 201': (r) => r.status === 201,
    }, { endpoint: 'POST /users', scenario: 'load' });

    try {
      resourceId = createRes.json('id');
    } catch (_e) {
      resourceId = undefined;
    }

    sleep(randomIntBetween(1, 5));

    if (!resourceId) {
      console.warn('load: skipping GET/DELETE because resourceId is missing from POST response');
      return;
    }

    const getRes = http.get(
      `${config.baseUrl}/users/${resourceId}`,
      { headers: getDefaultHeaders(), tags: { endpoint: 'GET /users/{id}', scenario: 'load' } },
    );
    check(getRes, {
      'GET /users/{id} status is 200': (r) => r.status === 200,
    }, { endpoint: 'GET /users/{id}', scenario: 'load' });

    sleep(randomIntBetween(1, 5));

    const delRes = http.del(
      `${config.baseUrl}/users/${resourceId}`,
      null,
      { headers: getDefaultHeaders(), tags: { endpoint: 'DELETE /users/{id}', scenario: 'load' } },
    );
    check(delRes, {
      'DELETE /users/{id} status is 204': (r) => r.status === 204,
    }, { endpoint: 'DELETE /users/{id}', scenario: 'load' });
  });

  sleep(randomIntBetween(1, 5));
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

## `package.json`

```json
{
  "name": "{{project_name}}",
  "version": "1.0.0-SNAPSHOT",
  "description": "K6 performance suite for {{project_name}}",
  "private": true,
  "engines": {
    "k6": ">=0.50.0"
  },
  "scripts": {
    "smoke":  "k6 run tests/smoke-test.js",
    "load":   "k6 run tests/load-test.js",
    "stress": "k6 run tests/stress-test.js",
    "spike":  "k6 run tests/spike-test.js",
    "soak":   "k6 run tests/soak-test.js",
    "all":    "bash run-all.sh",
    "report:summary": "jq '.metrics.http_req_duration.values' results/*-summary.json 2>/dev/null || python -m json.tool results/*-summary.json | grep http_req_duration"
  },
  "devDependencies": {}
}
```

## `preflight-k6.sh`

```bash
#!/usr/bin/env bash
set -e
echo "=== K6 pre-flight ==="

if ! command -v k6 > /dev/null 2>&1; then
  echo "[fail] k6 no encontrado en PATH."
  echo "Sugerencia: brew install k6 | apt install k6 | choco install k6"
  exit 1
fi

K6_VERSION=$(k6 version 2>/dev/null | head -n 1 | awk '{print $2}' | sed 's/^v//')
echo "k6 version: $K6_VERSION"
K6_MAJOR=$(echo "$K6_VERSION" | cut -d. -f1)
K6_MINOR=$(echo "$K6_VERSION" | cut -d. -f2)
if [[ "$K6_MAJOR" == "0" && "$K6_MINOR" -lt 50 ]]; then
  echo "[warn] k6 $K6_VERSION < 0.50.0. Recomendado actualizar para handleSummary y thresholds compuestos."
fi
echo "[ok] k6 disponible"

if [[ -n "$BASE_URL" ]]; then
  echo "Verificando BASE_URL=$BASE_URL ..."
  curl -sI --max-time 5 "$BASE_URL" > /dev/null || {
    echo "[fail] BASE_URL inaccesible (timeout 5s). Degradar a scaffold-only."
    exit 1
  }
  echo "[ok] BASE_URL alcanzable"
else
  echo "[fail] BASE_URL no definido. Exportar antes de ejecutar el smoke."
  exit 1
fi

if [[ "$AUTH_REQUIRED" == "true" ]]; then
  if [[ -z "$AUTH_TOKEN" ]]; then
    echo "[fail] AUTH_TOKEN requerido por el spec (security) pero no exportado."
    exit 1
  fi
  echo "[ok] AUTH_TOKEN presente"
fi

echo "=== preflight ok ==="
```

## `run-all.sh`

```bash
#!/usr/bin/env bash
# {{project_name}} — orquestador de la suite K6 modular.
#
# Tras generar el proyecto: chmod +x run-all.sh
# Ejecucion: ./run-all.sh   (o npm run all)
#
# set -e detiene en el primer fallo: linea-base debe pasar antes que carga, etc.
# Si necesitas correr todos los escenarios ignorando fallos, comenta la siguiente linea.
set -euo pipefail

BASE_URL="${BASE_URL:-{{baseUrl}}}"
AUTH_TOKEN="${AUTH_TOKEN:-}"

export BASE_URL
export AUTH_TOKEN

mkdir -p results

for scenario in linea-base carga estres; do
  echo "==> Running $scenario"
  mkdir -p "results/$scenario"
  k6 run \
    -e BASE_URL="$BASE_URL" \
    -e AUTH_TOKEN="$AUTH_TOKEN" \
    -e SCENARIO_NAME="$scenario" \
    "tests/$scenario/main.js"
done

echo "==> {{project_name}}: all scenarios completed"
```

## `scenarios/README.md`

````markdown
# scenarios/

Logica HTTP reusable. Cada archivo exporta una funcion `default` que ejecuta la secuencia de pasos de un flujo (auth, main, cleanup) usando `group()`, `http.*`, `check()` y `sleep()`.

## Reglas

- **No** definir `options` aqui. La curva de carga la decide el workload (`workloads/*.js`).
- Importar configuracion desde `../shared/config.js` y helpers desde `../shared/utils.js`.
- Si el flow requiere autenticacion, delegar a `auth.js` (`import { login } from './auth.js'`), no inlinear login.
- Etiquetar requests y checks con `tags: { endpoint, step }` para segmentar metricas.
- Usar `sleep(randomIntBetween(1, 5))` entre pasos para simular think-time realista.

## Composicion

Un scenario se combina con un workload en `tests/{escenario}/main.js`:

```javascript
export { options } from '../../workloads/linea-base.js';
export { default } from '../../scenarios/{{main-flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
```

El mismo scenario se reutiliza para linea-base, carga y estres cambiando solo el workload importado.

Detalle en `[modular-architecture](modular-architecture.md)`.
````

## `scenarios/auth.js`

```javascript
// {{project_name}} — scenarios/auth.js
// Flow reusable de autenticacion. Devuelve { token } o lanza error.
//
// Uso desde otro scenario:
//   import { login } from './auth.js';
//   const { token } = login();
//
// No define options: la carga la determina el workload que lo invoque.

import http from 'k6/http';
import { check, group } from 'k6';
import { config } from '../shared/config.js';

export function login() {
  let token;

  group('auth', () => {
    const res = http.post(
      `${config.authUrl}/login`,
      JSON.stringify({
        username: __ENV.AUTH_USERNAME || '{{auth_username}}',
        password: __ENV.AUTH_PASSWORD || '{{auth_password}}',
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        tags: { endpoint: 'login', step: 'auth' },
      },
    );

    check(res, {
      'auth status 200': (r) => r.status === 200,
      'auth has token': (r) => typeof r.json('token') === 'string',
    }, { endpoint: 'login', step: 'auth' });

    try {
      token = res.json('token');
    } catch (_e) {
      token = undefined;
    }
  });

  if (!token) {
    throw new Error('auth: login no devolvio token. Verificar credenciales / endpoint.');
  }

  return { token };
}

// Default export opcional: permite usar este scenario aislado para validar el endpoint de login.
export default function () {
  login();
}
```

## `scenarios/main-flow.js`

```javascript
// {{project_name}} — scenarios/{{endpoint_name}}.js
// Flow HTTP reusable para el endpoint objetivo. NO define options.
// El workload (workloads/*.js) decide la curva de carga.
//
// Slots:
//   {{endpoint_name}}  — nombre logico (e.g. retrieveTransactions, createUser)
//   {{path}}           — path relativo (e.g. /transactions, /users/{id})
//   {{method}}         — get | post | put | del | patch
//   {{checks}}         — checks especificos del endpoint

import http from 'k6/http';
import { group, check, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { config } from '../shared/config.js';
import { getAuthHeaders } from '../shared/utils.js';
// import { login } from './auth.js'; // descomentar si el endpoint requiere auth previa

export default function () {
  // const { token } = login(); // opcional, solo si el flow requiere auth dinamica por iteracion

  group('{{endpoint_name}}', () => {
    const res = http.{{method}}(
      `${config.baseUrl}{{path}}`,
      // null, // payload: usar JSON.stringify(buildXxxBody()) para POST/PUT/PATCH
      {
        headers: getAuthHeaders(),
        tags: { endpoint: '{{endpoint_name}}', step: 'main' },
      },
    );

    check(res, {
      'status 200': (r) => r.status === 200,
      // {{checks}} — agregar checks especificos del contrato (campos requeridos, tipos, rangos)
    }, { endpoint: '{{endpoint_name}}', step: 'main' });

    sleep(randomIntBetween(1, 3));
  });
}
```

## `shared/config.js`

```javascript
// {{project_name}} — shared/config.js
// Configuracion centralizada. Todos los modulos (scenarios, workloads, tests) la importan desde aqui.
//
// Reglas:
//   - baseUrl / authUrl SIEMPRE desde __ENV con fallback local.
//   - Nunca hardcodear credenciales en tests/*.js — solo aqui o via __ENV.
//   - Enums y headers constantes extraidos del spec se declaran aqui.

export const config = {
  baseUrl: __ENV.BASE_URL || '{{baseUrl}}',
  authUrl: __ENV.AUTH_URL || '{{authUrl}}',
  authToken: __ENV.AUTH_TOKEN || '',

  // Enums extraidos del spec (top-level y property-level).
  // {{enumArrays}} — placeholder a expandir por el generador.
  documentNames: ['CC', 'TI', 'CE'],
  channels: ['APP', 'WEB'],

  // Headers constantes documentados en el spec.
  trueClientIp: '192.168.1.100',
};
```

## `shared/handle-summary.js`

```javascript
// {{project_name}} — shared/handle-summary.js
// handleSummary compartido. Importado y re-exportado desde cada tests/{escenario}/main.js.
// Single source of truth: evita duplicar el bloque en cada test.
//
// Salida:
//   - results/{scenario}/{timestamp}-summary.json (estructura por escenario + fecha).
//   - stdout: textSummary con colores.
//
// SCENARIO_NAME se inyecta via env (-e SCENARIO_NAME=linea-base) desde run-all.sh.

import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const scenarioName = __ENV.SCENARIO_NAME || 'default';
  const outputPath = `results/${scenarioName}/${timestamp}-summary.json`;

  return {
    [outputPath]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

## `shared/thresholds.js`

```javascript
// {{project_name}} — shared/thresholds.js
// Thresholds centralizados por tier (Conservative / Moderate / Relaxed) y por escenario.
//
// Tiers (ver [thresholds-three-tiers](thresholds-three-tiers.md) y [threshold-tier-justification](threshold-tier-justification.md)):
//   - Conservative: SLAs estrictos, sistemas criticos (banca, salud).
//   - Moderate:     default, sistemas productivos estandar.
//   - Relaxed:      MVP, sistemas nuevos sin baseline, batch internos.
//
// Por escenario:
//   - thresholdsBaseline: SLAs estrictos, baseline limpio bajo carga minima.
//   - thresholdsCarga:    SLAs nominales bajo carga sostenida (100% peak).
//   - thresholdsEstres:   SLAs relajados, foco en no caer y degradar controladamente.

// === Tiers genericos ===
export const tiers = {
  Conservative: {
    http_req_duration: ['p(95)<500',  'p(99)<1000'],
    http_req_failed:   ['rate<0.001'],
    checks:            ['rate>0.99'],
  },
  Moderate: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
  Relaxed: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],
    http_req_failed:   ['rate<0.05'],
    checks:            ['rate>0.90'],
  },
};

// === Por escenario ===
// Por default todos heredan de Moderate. Ajustar segun tier declarado en .evidence/tier-declared.md.
export const thresholdsBaseline = {
  http_req_duration: ['p(95)<800',  'p(99)<1500'],
  http_req_failed:   ['rate<0.005'],
  checks:            ['rate>0.98'],
};

export const thresholdsCarga = {
  http_req_duration: ['p(95)<1000', 'p(99)<2000'],
  http_req_failed:   ['rate<0.01'],
  checks:            ['rate>0.95'],
};

export const thresholdsEstres = {
  http_req_duration: ['p(95)<2000', 'p(99)<5000'],
  http_req_failed:   ['rate<0.05'],
  checks:            ['rate>0.90'],
};
```

## `shared/utils.js`

```javascript
// {{project_name}} — shared/utils.js
// Helpers cross-cutting reutilizables por todos los scenarios.
//
// Exports:
//   - uuidv4()                     RFC 4122 v4 para Transaction-Id / Correlation-Id.
//   - getAuthHeaders()             headers default + Authorization si auth_mode lo requiere.
//   - getDefaultHeaders()          alias de getAuthHeaders para compatibilidad.
//   - randomIntBetween             re-export de la jslib oficial.
//   - buildXxxBody()               un builder por cada endpoint con request body.
//
// Reglas:
//   - Payloads usan randomIntBetween / Math.random para variabilidad realista.
//   - Nunca devolver el mismo body en cada iteracion: cache hits artificiales enmascaran latencia.

import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { config } from './config.js';

export { randomIntBetween };

export function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function getAuthHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Transaction-Id': uuidv4(),
    'X-Correlation-Id': uuidv4(),
    'Channel': config.channels[Math.floor(Math.random() * config.channels.length)],
  };

  // Authorization solo si auth_mode='external' o el spec declara security.
  if (config.authToken) {
    headers['Authorization'] = `Bearer ${config.authToken}`;
  }

  return headers;
}

// Alias para compatibilidad con scenarios que usen el nombre historico.
export const getDefaultHeaders = getAuthHeaders;

// Ejemplo canonico: reemplazar por buildXxxBody() por cada endpoint con request body del spec.
export function buildCreateUserBody() {
  return {
    email: `test+${Math.random().toString(36).substring(7)}@example.com`,
    documentName: config.documentNames[Math.floor(Math.random() * config.documentNames.length)],
    documentNumber: String(randomIntBetween(1_000_000_000, 9_999_999_999)),
    age: randomIntBetween(18, 80),
  };
}
```

## `smoke-test.js`

```javascript
// DEPRECATED: monolithic single-file template. Use modular structure instead: scenarios/ + workloads/ + tests/{escenario}/main.js + shared/.
// See references/modular-architecture.md and references/options-scenarios-executors.md.
// Keep this file only for brownfield projects that already use the monolithic pattern.

// {{project_name}} — smoke-test.js
// Proposito: validacion basica del flujo + baseline minimo.
// VUs=3, duration~5m. Tier por default: Moderate (ver threshold-tier-justification.md).

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

import { config } from './config.js';
import { getDefaultHeaders, buildCreateUserBody } from './utils.js';

export const options = {
  stages: [
    { duration: '1m', target: 3 },
    { duration: '5m', target: 3 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
};

export default function () {
  let resourceId;

  group('users-crud', function () {
    // CREATE
    const createRes = http.post(
      `${config.baseUrl}/users`,
      JSON.stringify(buildCreateUserBody()),
      { headers: getDefaultHeaders(), tags: { endpoint: 'POST /users', scenario: 'smoke' } },
    );
    check(createRes, {
      'POST /users status is 201': (r) => r.status === 201,
    }, { endpoint: 'POST /users', scenario: 'smoke' });

    try {
      resourceId = createRes.json('id');
    } catch (_e) {
      resourceId = undefined;
    }

    sleep(randomIntBetween(1, 5));

    if (!resourceId) {
      console.warn('smoke: skipping GET/DELETE because resourceId is missing from POST response');
      return;
    }

    // READ
    const getRes = http.get(
      `${config.baseUrl}/users/${resourceId}`,
      { headers: getDefaultHeaders(), tags: { endpoint: 'GET /users/{id}', scenario: 'smoke' } },
    );
    check(getRes, {
      'GET /users/{id} status is 200': (r) => r.status === 200,
    }, { endpoint: 'GET /users/{id}', scenario: 'smoke' });

    sleep(randomIntBetween(1, 5));

    // DELETE
    const delRes = http.del(
      `${config.baseUrl}/users/${resourceId}`,
      null,
      { headers: getDefaultHeaders(), tags: { endpoint: 'DELETE /users/{id}', scenario: 'smoke' } },
    );
    check(delRes, {
      'DELETE /users/{id} status is 204': (r) => r.status === 204,
    }, { endpoint: 'DELETE /users/{id}', scenario: 'smoke' });
  });

  sleep(randomIntBetween(1, 5));
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

## `soak-test.js`

```javascript
// DEPRECATED: monolithic single-file template. Use modular structure instead: scenarios/ + workloads/ + tests/{escenario}/main.js + shared/.
// See references/modular-architecture.md and references/options-scenarios-executors.md.
// Keep this file only for brownfield projects that already use the monolithic pattern.

// {{project_name}} — soak-test.js
// Proposito: estabilidad a largo plazo (memory leaks, drift, connection pools).
// VUs constante 50, duration 2h por default (rango 2-8h). Tier por default: Moderate.

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

import { config } from './config.js';
import { getDefaultHeaders, buildCreateUserBody } from './utils.js';

export const options = {
  stages: [
    { duration: '5m', target: 50 },
    { duration: '2h', target: 50 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
};

export default function () {
  let resourceId;

  group('users-crud', function () {
    const createRes = http.post(
      `${config.baseUrl}/users`,
      JSON.stringify(buildCreateUserBody()),
      { headers: getDefaultHeaders(), tags: { endpoint: 'POST /users', scenario: 'soak' } },
    );
    check(createRes, {
      'POST /users status is 201': (r) => r.status === 201,
    }, { endpoint: 'POST /users', scenario: 'soak' });

    try {
      resourceId = createRes.json('id');
    } catch (_e) {
      resourceId = undefined;
    }

    sleep(randomIntBetween(1, 5));

    if (!resourceId) {
      console.warn('soak: skipping GET/DELETE because resourceId is missing from POST response');
      return;
    }

    const getRes = http.get(
      `${config.baseUrl}/users/${resourceId}`,
      { headers: getDefaultHeaders(), tags: { endpoint: 'GET /users/{id}', scenario: 'soak' } },
    );
    check(getRes, {
      'GET /users/{id} status is 200': (r) => r.status === 200,
    }, { endpoint: 'GET /users/{id}', scenario: 'soak' });

    sleep(randomIntBetween(1, 5));

    const delRes = http.del(
      `${config.baseUrl}/users/${resourceId}`,
      null,
      { headers: getDefaultHeaders(), tags: { endpoint: 'DELETE /users/{id}', scenario: 'soak' } },
    );
    check(delRes, {
      'DELETE /users/{id} status is 204': (r) => r.status === 204,
    }, { endpoint: 'DELETE /users/{id}', scenario: 'soak' });
  });

  sleep(randomIntBetween(1, 5));
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

## `spike-test.js`

```javascript
// DEPRECATED: monolithic single-file template. Use modular structure instead: scenarios/ + workloads/ + tests/{escenario}/main.js + shared/.
// See references/modular-architecture.md and references/options-scenarios-executors.md.
// Keep this file only for brownfield projects that already use the monolithic pattern.

// {{project_name}} — spike-test.js
// Proposito: picos subitos de demanda + recuperacion.
// VUs 10 -> 200 -> 10, duration ~7m. Tier por default: Moderate.

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

import { config } from './config.js';
import { getDefaultHeaders, buildCreateUserBody } from './utils.js';

export const options = {
  stages: [
    { duration: '1m',  target: 10 },
    { duration: '30s', target: 200 },
    { duration: '3m',  target: 200 },
    { duration: '30s', target: 10 },
    { duration: '2m',  target: 10 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
};

export default function () {
  let resourceId;

  group('users-crud', function () {
    const createRes = http.post(
      `${config.baseUrl}/users`,
      JSON.stringify(buildCreateUserBody()),
      { headers: getDefaultHeaders(), tags: { endpoint: 'POST /users', scenario: 'spike' } },
    );
    check(createRes, {
      'POST /users status is 201': (r) => r.status === 201,
    }, { endpoint: 'POST /users', scenario: 'spike' });

    try {
      resourceId = createRes.json('id');
    } catch (_e) {
      resourceId = undefined;
    }

    sleep(randomIntBetween(1, 5));

    if (!resourceId) {
      console.warn('spike: skipping GET/DELETE because resourceId is missing from POST response');
      return;
    }

    const getRes = http.get(
      `${config.baseUrl}/users/${resourceId}`,
      { headers: getDefaultHeaders(), tags: { endpoint: 'GET /users/{id}', scenario: 'spike' } },
    );
    check(getRes, {
      'GET /users/{id} status is 200': (r) => r.status === 200,
    }, { endpoint: 'GET /users/{id}', scenario: 'spike' });

    sleep(randomIntBetween(1, 5));

    const delRes = http.del(
      `${config.baseUrl}/users/${resourceId}`,
      null,
      { headers: getDefaultHeaders(), tags: { endpoint: 'DELETE /users/{id}', scenario: 'spike' } },
    );
    check(delRes, {
      'DELETE /users/{id} status is 204': (r) => r.status === 204,
    }, { endpoint: 'DELETE /users/{id}', scenario: 'spike' });
  });

  sleep(randomIntBetween(1, 5));
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

## `stress-test.js`

```javascript
// DEPRECATED: monolithic single-file template. Use modular structure instead: scenarios/ + workloads/ + tests/{escenario}/main.js + shared/.
// See references/modular-architecture.md and references/options-scenarios-executors.md.
// Keep this file only for brownfield projects that already use the monolithic pattern.

// {{project_name}} — stress-test.js
// Proposito: encontrar el punto de quiebre del sistema.
// VUs agresivos 0 -> 50 -> 100 -> 200 -> 300 -> 50 -> 0, duration ~25m. Tier por default: Moderate.

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

import { config } from './config.js';
import { getDefaultHeaders, buildCreateUserBody } from './utils.js';

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '5m', target: 100 },
    { duration: '5m', target: 200 },
    { duration: '5m', target: 300 },
    { duration: '5m', target: 50 },
    { duration: '3m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
};

export default function () {
  let resourceId;

  group('users-crud', function () {
    const createRes = http.post(
      `${config.baseUrl}/users`,
      JSON.stringify(buildCreateUserBody()),
      { headers: getDefaultHeaders(), tags: { endpoint: 'POST /users', scenario: 'stress' } },
    );
    check(createRes, {
      'POST /users status is 201': (r) => r.status === 201,
    }, { endpoint: 'POST /users', scenario: 'stress' });

    try {
      resourceId = createRes.json('id');
    } catch (_e) {
      resourceId = undefined;
    }

    sleep(randomIntBetween(1, 5));

    if (!resourceId) {
      console.warn('stress: skipping GET/DELETE because resourceId is missing from POST response');
      return;
    }

    const getRes = http.get(
      `${config.baseUrl}/users/${resourceId}`,
      { headers: getDefaultHeaders(), tags: { endpoint: 'GET /users/{id}', scenario: 'stress' } },
    );
    check(getRes, {
      'GET /users/{id} status is 200': (r) => r.status === 200,
    }, { endpoint: 'GET /users/{id}', scenario: 'stress' });

    sleep(randomIntBetween(1, 5));

    const delRes = http.del(
      `${config.baseUrl}/users/${resourceId}`,
      null,
      { headers: getDefaultHeaders(), tags: { endpoint: 'DELETE /users/{id}', scenario: 'stress' } },
    );
    check(delRes, {
      'DELETE /users/{id} status is 204': (r) => r.status === 204,
    }, { endpoint: 'DELETE /users/{id}', scenario: 'stress' });
  });

  sleep(randomIntBetween(1, 5));
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

## `tests/carga/main.js`

```javascript
// {{project_name}} — tests/carga/main.js
// Ejecutable: k6 run tests/carga/main.js
//
// Orquesta scenario + workload + handleSummary. No contiene logica propia.
// Mismo scenario que linea-base, cambia la curva de carga.

export { options } from '../../workloads/carga.js';
export { default } from '../../scenarios/{{main_flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
```

## `tests/estres/main.js`

```javascript
// {{project_name}} — tests/estres/main.js
// Ejecutable: k6 run tests/estres/main.js
//
// Orquesta scenario + workload + handleSummary. No contiene logica propia.
// Mismo scenario que linea-base / carga, cambia la curva (ramping-arrival-rate, 200-300% del peak).

export { options } from '../../workloads/estres.js';
export { default } from '../../scenarios/{{main_flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
```

## `tests/linea-base/main.js`

```javascript
// {{project_name}} — tests/linea-base/main.js
// Ejecutable: k6 run tests/linea-base/main.js
//
// Orquesta scenario + workload + handleSummary. No contiene logica propia.
// Cambiar el workload (linea-base / carga / estres) NO requiere tocar el scenario.

export { options } from '../../workloads/linea-base.js';
export { default } from '../../scenarios/{{main_flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
```

## `utils.js`

```javascript
// {{project_name}} — helpers compartidos
//
// uuidv4() RFC 4122 v4
// getDefaultHeaders() respetando auth_mode (spec/external)
// buildXxxBody() por cada endpoint con request body
//
// Reglas:
//   - Payloads usan randomIntBetween / Math.random para variabilidad realista (no constantes).
//   - Nunca devolver el mismo body en cada iteracion: VUs con payloads identicos generan
//     cache hits artificiales y enmascaran latencia real.

import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { config } from './config.js';

export function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function getDefaultHeaders() {
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Transaction-Id': uuidv4(),
    'X-Correlation-Id': uuidv4(),
    'Channel': config.channels[Math.floor(Math.random() * config.channels.length)],
    // 'Authorization': `Bearer ${config.authToken}`, // descomentar segun auth_mode
  };
}

// Ejemplo canonico: buildCreateUserBody. Reemplazar por buildXxxBody por endpoint del spec.
export function buildCreateUserBody() {
  return {
    email: `test+${Math.random().toString(36).substring(7)}@example.com`,
    documentName: config.documentNames[Math.floor(Math.random() * config.documentNames.length)],
    documentNumber: String(randomIntBetween(1_000_000_000, 9_999_999_999)),
    age: randomIntBetween(18, 80),
  };
}
```

## `workloads/carga.js`

```javascript
// {{project_name}} — workloads/carga.js
// Workload de Carga: 100% del peak esperado.
// Objetivo: validar SLAs bajo carga nominal sostenida.
// Executor: ramping-vus (rampa progresiva hasta peak, sostener, descender).

import { thresholdsCarga } from '../shared/thresholds.js';

export const options = {
  scenarios: {
    carga: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m',  target: 10 },
        { duration: '5m',  target: 30 },
        { duration: '10m', target: 50 },
        { duration: '3m',  target: 0 },
      ],
      tags: { scenario: 'carga' },
    },
  },
  thresholds: thresholdsCarga,
};
```

## `workloads/estres.js`

```javascript
// {{project_name}} — workloads/estres.js
// Workload de Estres: 200-300% del peak esperado, progresivo.
// Objetivo: encontrar el punto de quiebre y validar degradacion controlada.
// Executor: ramping-arrival-rate (control de QPS, no de VUs).
//
// Por que ramping-arrival-rate y no ramping-vus:
//   - Si el backend se degrada, ramping-vus baja el QPS efectivo (VUs esperando).
//   - ramping-arrival-rate mantiene la presion declarada aunque la latencia explote.
//   - preAllocatedVUs ~ rate * latencia_p95_segundos. maxVUs >> preAllocatedVUs para soportar degradacion.

import { thresholdsEstres } from '../shared/thresholds.js';

export const options = {
  scenarios: {
    estres: {
      executor: 'ramping-arrival-rate',
      startRate: 50,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 500,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 200 },
        { duration: '5m', target: 300 },
        { duration: '5m', target: 500 },
        { duration: '3m', target: 50 },
      ],
      tags: { scenario: 'estres' },
    },
  },
  thresholds: thresholdsEstres,
};
```

## `workloads/linea-base.js`

```javascript
// {{project_name}} — workloads/linea-base.js
// Workload de Linea Base: 20-30% del peak esperado.
// Objetivo: validar el flow + baseline de latencia bajo carga minima.
// Executor: ramping-vus (rampa progresiva, control de concurrencia).

import { thresholdsBaseline } from '../shared/thresholds.js';

export const options = {
  scenarios: {
    linea_base: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 5 },
        { duration: '3m', target: 5 },
        { duration: '1m', target: 0 },
      ],
      tags: { scenario: 'linea-base' },
    },
  },
  thresholds: thresholdsBaseline,
};
```

