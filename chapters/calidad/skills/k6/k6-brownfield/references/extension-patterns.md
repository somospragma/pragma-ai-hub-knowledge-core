
# Patrones de extensión en K6 brownfield

Catálogo de los cambios más frecuentes y cómo entregarlos respetando las convenciones detectadas (``convention-detection.md``). Cada patrón muestra el patch mínimo: el resto del archivo permanece intacto.

## 1. Añadir un endpoint a un script existente

Caso: el spec sumó `PUT /users/{id}/status` y se quiere ejercitarlo en el `load-test.js` actual. No se crea un nuevo script.

```javascript
// tests/load-test.js — patch
+ import { buildUpdateUserStatusBody } from './utils.js';

  export default function () {
    group('users', function () {
      // ... POST/GET existentes ...

+     group('update status', function () {
+       const res = http.put(
+         `${config.baseUrl}/users/${userId}/status`,
+         JSON.stringify(buildUpdateUserStatusBody()),
+         { headers: getDefaultHeaders() }
+       );
+       check(res, {
+         'update status 200': (r) => r.status === 200,
+         'response has updatedAt': (r) => r.json('updatedAt') !== undefined,
+       });
+     });
    });
  }
```

Reglas:
- `group()` respeta `groups_naming` detectado (idioma, prefijos).
- `check()` valida campo del response, no solo status.
- Si el endpoint depende de un ID previo, **reusa** el patrón de captura ya presente en el script; no introduzcas uno nuevo.

## 2. Crear un nuevo script (otro tipo)

Caso: el proyecto sólo tiene `smoke-test.js` y `load-test.js`; se necesita un `spike-test.js` adicional.

- Genera el archivo en `tests_dir` con `script_naming` detectado (kebab-case → `spike-test.js`).
- Copia el esqueleto de los scripts existentes (mismo `import` style, mismo `handleSummary`).
- Stages y thresholds: usa el tier dominante detectado; no introduzcas otro tier salvo pedido explícito.
- Si el spec define security o el proyecto está en `auth_mode = external`, asegúrate de que `Authorization` ya viene de `getDefaultHeaders()` (no lo inyectes inline).

## 3. Añadir un threshold a un script existente

Caso: el equipo decidió medir `http_req_failed` además de `http_req_duration`.

```javascript
// tests/stress-test.js — patch en options
  export const options = {
    stages: [/* ... sin cambios ... */],
    thresholds: {
      http_req_duration: ['p(95)<800'],
+     http_req_failed: ['rate<0.05'],
+     checks: ['rate>0.95'],
    },
  };
```

Reglas:
- Mantén el formato exacto del archivo (comas, indentación, comillas).
- No reordenes thresholds existentes.

## 4. Cambiar de tier (p. ej. Moderate → Conservative)

Caso: la calibración (`[[calidad-calibrate-k6-thresholds]]`) demostró que el SLA real es más estricto.

- Reemplaza los valores numéricos en `options.thresholds` de los 5 scripts según el tier nuevo (`[[calidad-k6-greenfield]] (consultar `references/thresholds-three-tiers.md` en su subfolder)`).
- Documenta en el commit message la justificación con referencia al `results/${timestamp}-summary.json` que motivó el cambio.
- NO toques `package.json`, `README.md` (a menos que el usuario lo pida explícitamente para actualizar la sección de "tier vigente").

## 5. Agregar un CRUD flow nuevo respetando el patrón existente

Caso: el spec sumó `/orders` (POST + GET + DELETE).

- Detecta cómo el proyecto extrae IDs hoy (`existing_id_correlation_pattern`). Reusa la **misma** función / mismo estilo de guard clause.
- Añade los `buildXxxBody()` necesarios como patch en `utils.js` (no regeneres el archivo entero).
- Si la clave del id es distinta (p. ej. `orderId` en lugar de `id`), confirma con el spec y mantén consistencia con la convención observada.
- Patrón obligatorio en `[[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder)`.

## 6. Migrar `auth_mode = spec` a `auth_mode = external`

Caso: el microservicio quedó detrás de un API gateway nuevo (Kong / API Gateway / Apigee) o se introdujo un IdP externo. El proyecto fue generado con `auth_mode = spec` y la spec no declara security, por lo que `authToken`/`Authorization` no se emiten. Ahora todos los requests deben llevar `Authorization: Bearer <token>`.

Patch en `tests/config.js`:

```javascript
  export const config = {
    baseUrl: __ENV.BASE_URL || 'http://localhost:8080',
+   // Modo external-auth: token obtenido out-of-band (gateway / IdP).
+   authToken: __ENV.AUTH_TOKEN || '',
    documentNames: ['CC', 'TI', 'CE'],
    // ...
  };
```

Patch en `tests/utils.js`:

```javascript
  export function getDefaultHeaders() {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Transaction-Id': uuidv4(),
      'X-Correlation-Id': uuidv4(),
      'Channel': config.channels[Math.floor(Math.random() * config.channels.length)],
+     'Authorization': `Bearer ${config.authToken}`,
    };
  }
```

Acciones complementarias (entregadas como nota al usuario, NO como modificación automática):

- `AUTH_TOKEN` pasa a ser env var **obligatoria**: el usuario debe actualizar manualmente el `README.md` y el pipeline CI para inyectarla como secret.
- Verificar que el smoke-test pasa con un token válido antes de correr load/stress/spike/soak.
- Si el proyecto tenía un `run-all.sh` que sólo exportaba `BASE_URL`, advertir al usuario que ahora debe exportar también `AUTH_TOKEN`. No modificar `run-all.sh` sin permiso explícito (es infraestructura).

Detalle completo del modo en `[[calidad-k6-greenfield]] (consultar `references/enums-headers-security-extraction.md` en su subfolder)`.
