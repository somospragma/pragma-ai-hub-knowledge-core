---
id: appium-generate-cucumber-feature-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [automation]
description: Prompt para generar login.feature con 2 escenarios @smoke ejecutables + @proposed aspiracionales derivados de user_story/test_cases.
tags: [appium, cucumber, gherkin, feature, prompt, smoke, proposed]
---

# Prompt — Generar `login.feature` (Appium Android)

## Variables

- `{{user_story}}` — historia de usuario en texto libre (opcional).
- `{{test_cases}}` — lista de casos en texto libre (opcional). Al menos uno entre `user_story` y `test_cases` debe venir.
- `{{include_login_case}}` — boolean (ya coercionado por `[[appium-validate-inputs-prompt]]`).

## Plantilla

```
Eres un generador Gherkin del Chapter Calidad de Pragma. Produce UN UNICO archivo `login.feature` valido, UTF-8 sin BOM, line endings LF. Cumple las reglas de [[appium-gherkin-syntax-rules]]: tags ASCII puro `@[A-Za-z0-9_]+`, sin acentos en tags, sin inline `# note` despues de step keywords, comentarios `#` solo al inicio de linea.

user_story: {{user_story}}
test_cases: {{test_cases}}
include_login_case: {{include_login_case}}

Reglas:

1. Header decorativo con `=` permitido. Un solo `Feature:` al inicio.
2. Generar SIEMPRE los 2 escenarios @android @smoke (literalmente, no parametrizar):

@android @smoke
Scenario: Flujo base de login sin localizadores finales
  Given el usuario abre la app movil
  When ejecuta el flujo base de login sin localizadores definitivos
  Then la app responde al flujo base

@android @smoke
Scenario: Validacion de carga y DOM de la aplicacion
  Given el usuario abre la app movil
  When la aplicacion termina de cargar
  Then la pantalla principal es visible y la app responde

3. Por cada item de `test_cases` (y/o por `user_story` si `test_cases` esta vacio), generar un `@android @proposed`:
   - Title: primeros 80 caracteres del item, newlines → espacios, sin acentos en tags ni en el title si el title forma parte de un tag.
   - Stub steps:

@android @proposed
Scenario: <title 80 chars max>
  Given el usuario abre la app movil
  When intenta el escenario propuesto
  Then queda pendiente la implementacion real
  # TODO: implementar steps para este escenario

4. Si `include_login_case` es false, igual generar los 2 @smoke (son base, no dependen del flag). El flag controla si se PRIORIZA login en los @proposed.
5. Acentos OK en strings de steps; PROHIBIDOS en tags (`@validacion` OK, `@validación` NO).
6. NO inventar payloads, credenciales ni endpoints — esto es mobile UI, no API.
7. Output: solo el contenido del archivo `login.feature`, sin prosa.

Ejemplo de salida (test_cases con 1 item "Login con credenciales invalidas muestra error"):

# =================================
# Login mobile - Appium Android
# =================================
Feature: Login en la aplicacion mobile

  @android @smoke
  Scenario: Flujo base de login sin localizadores finales
    Given el usuario abre la app movil
    When ejecuta el flujo base de login sin localizadores definitivos
    Then la app responde al flujo base

  @android @smoke
  Scenario: Validacion de carga y DOM de la aplicacion
    Given el usuario abre la app movil
    When la aplicacion termina de cargar
    Then la pantalla principal es visible y la app responde

  @android @proposed
  Scenario: Login con credenciales invalidas muestra error
    Given el usuario abre la app movil
    When intenta el escenario propuesto
    Then queda pendiente la implementacion real
    # TODO: implementar steps para este escenario
```
