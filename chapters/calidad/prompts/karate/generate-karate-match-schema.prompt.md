---
id: calidad-karate-generate-match-schema-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [karate]
description: Prompt para generar un archivo {resource}-match.json siguiendo la notación Karate.
tags: [karate, contract-testing, match, schema, prompt]
---

# Prompt — Generar `-match.json`

## Variables

- `{{schema_name}}` — nombre del schema (kebab-case, sin extensión).
- `{{json_schema}}` — schema fuente (OpenAPI `components.schemas[X]` o Swagger 2.0 `definitions[X]`).

## Plantilla

```
Eres un QA del Chapter Calidad de Pragma. Genera UN UNICO archivo {{schema_name}}-match.json a partir del schema JSON provisto, usando la notacion Karate para contract testing.

Schema fuente:
{{json_schema}}

Reglas:

1. Mapeo de tipos:
   - string requerido          -> "#string"
   - string opcional           -> "##string"
   - number / integer req      -> "#number"
   - number / integer opcional -> "##number"
   - boolean requerido         -> "#boolean"
   - boolean opcional          -> "##boolean"
   - array requerido           -> "#[]" o "#[] #object" si los items son objetos
   - array opcional            -> "##[]"   (NUNCA "##[] #type")
   - object requerido          -> {...} con sus propiedades, o "#object" si shape libre
   - object opcional           -> "##object"
   - nullable explicito        -> "##null"  o  permitir tipo + "##null"
   - formato uuid              -> "#uuid"
   - not null sin tipo         -> "#notnull"

2. Requerido vs opcional segun el array "required" del schema. Lo que NO este en required es opcional.

3. Para objetos anidados, expande la estructura. Para arrays de objetos, define el shape de items.

4. NO inventes campos que no esten en el schema. NO inventes "required" si el schema no lo declara.

5. Salida: solo el JSON valido, sin prosa.

Ejemplo de salida esperado:

{
  "userId": "#uuid",
  "firstName": "#string",
  "middleName": "##string",
  "age": "#number",
  "active": "#boolean",
  "address": {
    "street": "#string",
    "zipCode": "##string"
  },
  "roles": "#[] #object",
  "tags": "##[]"
}
```
