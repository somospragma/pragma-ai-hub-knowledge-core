---
id: k6-extract-config-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [automation]
description: Prompt para extraer enums, headers y security desde un spec OpenAPI/Swagger y producir el contenido de config.js.
tags: [k6, prompt, openapi, swagger, config, extraction]
---

# Prompt — Extract config from OpenAPI

## Variables

- `{{spec}}`: contenido completo del spec OpenAPI 3.x o Swagger 2.0 (JSON o YAML).

## Prompt

```
Eres un generador de configuración para K6. Recibirás un spec OpenAPI/Swagger y producirás
únicamente el contenido del archivo `tests/config.js`.

SPEC:
{{spec}}

Tu tarea:

1. Extrae todos los enums:
   - Top-level: `components.schemas.{Schema}.enum`
   - Property-level: `components.schemas.{Schema}.properties.{field}.enum`
   Conviértelos en arrays en camelCase plural (ej. `documentName` → `documentNames`).

2. Extrae todos los headers requeridos transversales (presentes en la mayoría de endpoints
   con `in: header` y `required: true`). Mapea nombres HTTP a camelCase (ej. `X-Request-Id` → `xRequestId`).
   Asigna valores constantes razonables o dejarlos como placeholders documentados.

3. Detecta si el spec define security:
   - OpenAPI 3.x: `components.securitySchemes` (no vacío) o `security` global / por operación.
   - Swagger 2.0: `securityDefinitions` (no vacío).
   - Si SÍ define security, incluye `authToken: __ENV.AUTH_TOKEN || ''`.
   - Si NO define security, NO incluyas `authToken` ni ninguna referencia a Authorization.

4. `baseUrl` siempre desde `__ENV.BASE_URL` con fallback `'http://localhost:8080'`.

Salida (sin explicaciones, solo el código):

export const config = {
  baseUrl: __ENV.BASE_URL || 'http://localhost:8080',
  // authToken: __ENV.AUTH_TOKEN || '',  ← incluir SOLO si el spec define security
  // enums extraídos
  // valores de headers
};

Reglas estrictas:
- NO inventes enums, headers ni campos que no estén en el spec.
- NO incluyas comentarios ficticios; solo los necesarios.
- NO uses TypeScript ni `const enum`. ES modules planos.
```

## Notas

Salida esperada: el contenido literal de `tests/config.js`, listo para persistir. Consume las reglas de `[[k6-enums-headers-security-extraction]]` y `[[k6-config-and-utils-modules]]`.
