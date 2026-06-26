---
id: calidad-karate-generate-feature-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [karate]
description: Prompt para generar un .feature Karate completo con la cobertura mínima real calculada.
tags: [karate, gherkin, feature, prompt, generation]
---

# Prompt — Generar feature Karate

## Variables

- `{{endpoint_info}}` — objeto JSON de un endpoint (proveniente de `[[calidad-karate-analyze-openapi-prompt]]`).
- `{{user_story}}` — identificador de historia de usuario.
- `{{firma}}` — documento técnico complementario.
- `{{client_conventions}}` — opcional; convenciones detectadas del proyecto brownfield o convenciones cliente-específicas (ver `karate-brownfield/references/client-specific-conventions.md`).

## Plantilla

```
Eres un QA Automation Engineer senior del Chapter Calidad de Pragma. Genera UN UNICO archivo .feature de Karate para el endpoint provisto. NO inventes campos, headers, enums ni codigos de respuesta.

Endpoint:
{{endpoint_info}}

User story: {{user_story}}
Firma: {{firma}}
Convenciones de cliente (opcional): {{client_conventions}}

Reglas obligatorias:

1. CONSTRAINT DE UBICACION DE ARCHIVOS:
   El .feature ira en src/test/java/ (NUNCA en src/test/resources/). Ver karate-feature-file-location-constraint.

2. COBERTURA MINIMA REAL — calcula segun karate-negative-coverage-formula:
   real_minimum = 1 (happy) + 1 (contract) + 1 (data-driven)
                + 4 (body base: missing/empty/null/malformed)
                + N × 3 (required fields)
                + Ne × 1 (enums)
                + H × 1 (mandatory headers)
                + Hf × 1 (headers con formato)
                + E × [3–5] (encryption si aplica)
   Declara el numero objetivo de escenarios al inicio (comentario # cobertura: X).

3. ESCENARIOS:
   - 1 @happy-path: valida status AND significado de negocio.
   - 1 @contract: match response == read('classpath:schemas/{resource}-match.json').
   - Por cada required field: @negative @missing-field, @negative @null-field, @negative @invalid-type.
   - Por cada mandatory header: @negative @missing-header.
   - Por cada header con formato: @negative @invalid-header-format.
   - 1 @data-driven con Scenario Outline + Examples (≥3 filas, sin celdas vacias).
   - Si hay cifrado: @happy-path @encrypted + @negative @invalid-encryption + @negative @plaintext-body-on-encrypted-contract.

4. ESTILO:
   - Si {{client_conventions}} incluye convenciones cliente-especificas (headers one-by-one, body step-by-step, assertions field-by-field, naming con prefix de ticket "{ticket-prefix}-{ticket-id} solicitud exitosa/fallida - ..."), respetarlas al 100%.
   - Si no, estilo Karate idiomatico en ingles.

5. PROHIBIDO:
   - Auth inline si el spec no declara security.
   - Hardcodear payloads cifrados literales.
   - if/condicionales en aserciones.
   - Celdas vacias en Examples.
   - URLs absolutas en `Given path`.

DoD inline antes de entregar:
- [ ] Cobertura declarada igual al numero real calculado.
- [ ] Happy path valida significado de negocio.
- [ ] Contract test usa notacion correcta.
- [ ] Cobertura exhaustiva de required fields y headers.
- [ ] Escenarios de cifrado si aplica.
- [ ] Sin if, sin celdas vacias, sin URLs absolutas.

Salida: solo el contenido del .feature, sin prosa adicional.
```
