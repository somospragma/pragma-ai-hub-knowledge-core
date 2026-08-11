---
id: calidad-k6-generate-utils-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [k6]
description: Prompt para generar utils.js con uuidv4, getDefaultHeaders y payload builders por endpoint.
tags: [k6, prompt, utils, payloads, uuid, headers]
---

# Prompt — Generate K6 utils and payloads

## Variables

- `{{endpoints_with_body}}`: lista de endpoints (path, method, operationId, request body schema con campos exactos).
- `{{required_headers}}`: headers transversales requeridos por el spec.
- `{{enums}}`: enums extraídos (top-level y property-level).
- `{{security_info}}`: indicador booleano + detalle del scheme (`bearer`, `apiKey`, etc.) si el spec define security; null si no.
- `{{auth_mode}}`: modo de autenticación elegido. Valores: `spec` (default) | `external` (override). Controla si `Authorization` se emite siempre o solo cuando `security_info` no es null. Ver [[calidad-k6-greenfield]] (consultar `references/enums-headers-security-extraction.md` en su subfolder).

## Prompt

```
Eres un generador de utilidades K6. Producirás el contenido completo de `tests/utils.js`.

INPUTS:
- endpoints_with_body: {{endpoints_with_body}}
- required_headers: {{required_headers}}
- enums: {{enums}}
- security_info: {{security_info}}
- auth_mode: {{auth_mode}}  // "spec" (default) | "external" (override)

Estructura obligatoria:

1. Import:
   import { config } from './config.js';

2. function uuidv4() — RFC 4122 v4:
   export function uuidv4() {
     return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
       const r = Math.random() * 16 | 0;
       const v = c === 'x' ? r : (r & 0x3 | 0x8);
       return v.toString(16);
     });
   }

3. function getDefaultHeaders():
   - Content-Type: 'application/json'
   - Accept: 'application/json'
   - Un header por cada `required_header` transversal (UUID/correlation/transaction generados con uuidv4()
     cuando el tipo del header es UUID; enums random cuando aplique).
   - Decisión de Authorization según auth_mode:
       * auth_mode == "external": SIEMPRE incluir `Authorization: \`Bearer ${config.authToken}\``,
         aunque security_info sea null. AUTH_TOKEN se inyecta en runtime; sin él la API responderá 401.
       * auth_mode == "spec" (o ausente): incluir `Authorization: \`Bearer ${config.authToken}\``
         SOLO si security_info indica bearer. Si security_info es null, NO incluyas Authorization.

4. function buildXxxBody() por cada endpoint con request body:
   - Nombre: `build` + PascalCase(operationId) + `Body`. Ej: createUser → buildCreateUserBody.
   - Genera un objeto con los campos EXACTOS del schema.
   - Strings: usar generadores razonables (`'test+' + Math.random().toString(36).substring(7) + '@example.com'` para emails).
   - Enums: usar random pick desde `config.{enumName}` (ej. config.documentNames[Math.floor(Math.random() * config.documentNames.length)]).
   - Números: rangos razonables.
   - UUIDs: uuidv4().
   - NO inventar campos que no estén en el schema.

Reglas estrictas:
- ES modules (`export function`).
- NO TypeScript.
- Authorization se emite según auth_mode (ver paso 3); NO lo omitas en modo external aunque security_info sea null.
- NO campos inventados.
- Salida: solo el código de utils.js, sin explicaciones.
```

## Notas

Consume reglas de [[calidad-k6-greenfield]] (consultar `references/config-and-utils-modules.md` en su subfolder) y [[calidad-k6-greenfield]] (consultar `references/enums-headers-security-extraction.md` en su subfolder). El resultado se persiste como `tests/utils.js` antes de la infraestructura, según `[[calidad-streaming-files-protocol]]`.
