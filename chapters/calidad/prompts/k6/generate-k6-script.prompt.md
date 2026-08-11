---
id: calidad-k6-generate-script-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [k6]
description: Prompt para generar UN script K6 completo (smoke, load, stress, spike o soak) con stages, thresholds y correlación dinámica.
tags: [k6, prompt, script, smoke, load, stress, spike, soak]
---

# Prompt — Generate K6 script

## Variables

- `{{script_type}}`: uno de `smoke | load | stress | spike | soak`.
- `{{endpoints}}`: lista de endpoints (path, method, operationId, request body schema).
- `{{crud_flows}}`: lista de flujos CRUD detectados (`full` / `partial`), con base path normalizado y métodos disponibles.
- `{{user_story}}`: historia de usuario (puede declarar SLA).
- `{{firma}}`: perfil del sistema (puede declarar tier — mission-critical, business-as-usual, internal).

## Prompt

```
Eres un generador de scripts K6. Producirás UN único archivo `tests/{{script_type}}-test.js`
completo y listo para ejecutar.

INPUTS:
- script_type: {{script_type}}
- endpoints: {{endpoints}}
- crud_flows: {{crud_flows}}
- user_story: {{user_story}}
- firma: {{firma}}

Estructura obligatoria del archivo (en este orden):

1. Imports:
   import http from 'k6/http';
   import { check, sleep } from 'k6';
   import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
   import { config } from './config.js';
   import { getDefaultHeaders, uuidv4, buildXxxBody /* funciones reales */ } from './utils.js';

2. export const options = {
     stages: [/* perfil según script_type */],
     thresholds: {/* tier derivado de user_story.SLA → firma.SLA → Moderate */},
   };

3. export default function () {
     const headers = getDefaultHeaders();
     // Requests HTTP por endpoint, cada uno con check() validando status + AL MENOS un campo
     // del response (no solo status code).
     // Si hay flujo CRUD: aplicar correlación dinámica de ID con guard clause.
     sleep(1);
   }

4. export function handleSummary(data) {
     const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
     return {
       [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
       stdout: textSummary(data, { indent: ' ', enableColors: true }),
     };
   }

Stages por script_type:
- smoke:  1m→3 VUs, 5m@3, 1m→0
- load:   2m→10, 5m→30, 10m→50, 3m→0
- stress: 2m→50, 5m→100, 5m→200, 5m→300, 5m→50, 3m→0
- spike:  1m→10, 30s→200, 3m@200, 30s→10, 2m@10
- soak:   5m→50, 4h@50, 5m→0

Thresholds (Moderate default si no hay SLA):
http_req_duration: ['p(95)<1000', 'p(99)<2000']
http_req_failed:   ['rate<0.01']
checks:            ['rate>0.95']

Correlación CRUD (cuando aplique):
- POST: capturar `resourceId = res.json('id') || res.json('data.id')` (priorizar id, Id, ID, _id; luego data.id, data.Id, data.ID, data._id).
- Guard clause: `if (!resourceId) { console.warn('...'); return; }`.
- GET/PUT/DELETE usan `${config.baseUrl}/resources/${resourceId}`.

Reglas estrictas:
- NO hardcodear IDs en flujos CRUD.
- NO declarar headers ni payloads inline; importar desde `utils.js`.
- NO incluir Authorization si el spec no define security.
- NO inventar endpoints ni campos.
- Salida: solo el código del script, sin explicaciones ni markdown.
```

## Notas

Invocar este prompt una vez por `script_type` (5 invocaciones por proyecto). Stages y thresholds detallados en [[calidad-k6-greenfield]] (consultar `references/five-script-types.md` en su subfolder) y [[calidad-k6-greenfield]] (consultar `references/thresholds-three-tiers.md` en su subfolder). Correlación CRUD en [[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder). Evidencia en [[calidad-k6-greenfield]] (consultar `references/handle-summary-evidence.md` en su subfolder).
