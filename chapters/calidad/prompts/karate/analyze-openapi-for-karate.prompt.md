---
id: calidad-karate-analyze-openapi-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [karate]
description: Prompt para analizar un spec OpenAPI/Swagger/WSDL y emitir un JSON estructurado consumible por los generadores Karate.
tags: [karate, openapi, swagger, wsdl, prompt, analysis]
---

# Prompt — Analizar spec para Karate

## Variables

- `{{spec}}` — contenido del spec OpenAPI 3.x, Swagger 2.0 o WSDL.
- `{{firma}}` — documento técnico complementario (opcional).
- `{{user_story}}` — identificador de historia de usuario (opcional).

## Plantilla

```
Eres un analista QA del Chapter Calidad de Pragma. Recibes un spec de API y debes producir UN ÚNICO objeto JSON con la información necesaria para generar pruebas Karate. NO inventes campos, headers, enums ni codigos de respuesta que no esten en el spec o en la firma.

Spec:
---
{{spec}}
---

Firma (opcional):
---
{{firma}}
---

User story (opcional): {{user_story}}

Produce un JSON con la siguiente forma exacta:

{
  "service_name": "kebab-case-from-info-title-or-filename",
  "base_url": "https://...",
  "is_wsdl": false,
  "security_info": {
    "has_security": false,
    "schemes": []
  },
  "endpoints": [
    {
      "path": "/resource/{id}",
      "method": "POST",
      "operationId": "...",
      "tags": [],
      "required_headers": [
        { "name": "X-Channel", "format": "enum:web|mobile|atm" }
      ],
      "body_fields": [
        { "name": "amount", "type": "number", "required": true, "enum": null, "format": null }
      ],
      "response_codes": [201, 400, 422]
    }
  ],
  "schemas": [
    { "name": "Transaction", "schema": { "...": "..." } }
  ],
  "enums": [
    { "field": "currency", "values": ["VES", "USD"] }
  ]
}

Reglas:
- service_name en kebab-case.
- base_url: servers[0].url (OpenAPI 3.x) | schemes+host+basePath (Swagger 2.0) | soap:address location (WSDL).
- Si el spec no declara security, security_info.has_security = false y schemes = [].
- required_headers.format: omitir el campo si el header no tiene formato validable; usar "uuid", "email", "date-time" o "enum:val1|val2" cuando aplique.
- body_fields.required reflejar exactamente el "required" del schema.
- enums: solo los detectados en el spec.
- Si es WSDL, llenar igual la estructura adaptando operations a endpoints.
- No emitir prosa, solo el JSON.
```
