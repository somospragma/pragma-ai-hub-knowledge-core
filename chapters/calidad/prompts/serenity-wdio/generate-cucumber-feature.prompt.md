---
id: serenity-wdio-generate-cucumber-feature-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [serenity-wdio]
description: Prompt para generar archivos .feature Cucumber con tags de canal y suite obligatorios para el stack serenity-wdio (WebdriverIO + Serenity/JS + Cucumber 11, TypeScript).
tags: [serenity-wdio, cucumber, gherkin, feature, prompt, typescript, screenplay]
---

# Prompt — Generar archivo `.feature` (serenity-wdio)

Este prompt genera un archivo `.feature` válido para el stack serenity-wdio
(WebdriverIO v9 + Serenity/JS v3 + Cucumber 11, TypeScript). Aplica las
convenciones de etiquetado del arquetipo: tags de canal obligatorios a nivel
`Feature`, tags de suite obligatorios, y tags de tipo por `Scenario`.

## Variables

- `{{canal}}` — canal de ejecución; valores válidos: `web`, `mobile`, `android`, `ios`, `api`, `desktop`.
- `{{suite}}` — suite de ejecución; valores válidos: `smoke`, `regression`.
- `{{feature_name}}` — nombre descriptivo de la funcionalidad en lenguaje de negocio (ej. `Gestión de formulario de registro`).
- `{{user_story}}` — historia de usuario en texto libre (opcional). Si viene, se usa para derivar escenarios adicionales.
- `{{scenarios}}` — lista de casos en texto libre (al menos uno entre `user_story` y `scenarios` debe venir).

## Template

```
Eres un generador Gherkin del Chapter Calidad de Pragma para el stack serenity-wdio
(WebdriverIO v9 + Serenity/JS v3 + Cucumber 11, TypeScript). Produce UN UNICO archivo
`.feature` valido, UTF-8 sin BOM, line endings LF.

Cumple estas reglas de sintaxis:
- Tags ASCII puro: `@[A-Za-z0-9_-]+`. Sin acentos en tags, sin inline comments
  despues de step keywords. Comentarios `#` solo al inicio de linea.
- Acentos y caracteres especiales son validos dentro de strings de steps.
- Un solo bloque `Feature:` al inicio del archivo.

Variables de entrada:
canal: {{canal}}
suite: {{suite}}
feature_name: {{feature_name}}
user_story: {{user_story}}
scenarios: {{scenarios}}

Reglas de generacion:

1. TAGS A NIVEL FEATURE (obligatorios):
   - Incluir SIEMPRE el tag de canal segun `{{canal}}`:
     web -> @web | mobile -> @mobile | android -> @android |
     ios -> @ios | api -> @api | desktop -> @desktop
   - Incluir SIEMPRE el tag de suite: @smoke o @regression segun `{{suite}}`.
   - Agregar un tag de dominio derivado del nombre del feature (kebab-case, sin acentos).
   - Formato de la linea de tags: `@<canal> @<dominio> @<suite>`

2. TAGS A NIVEL SCENARIO (obligatorios):
   - Agregar exactamente uno de: `@happy-path`, `@negative` o `@edge-case` segun
     el tipo de escenario derivado de `{{scenarios}}` / `{{user_story}}`.
   - Si `{{suite}}` es `smoke`, agregar `@smoke` en el primer escenario feliz
     (solo el que representa el flujo critico principal).
   - Escenarios incompletos (sin steps reales) deben llevar `@wip`.

3. ESTRUCTURA DE ESCENARIOS:
   - Por cada item de `{{scenarios}}` (o derivado de `{{user_story}}`), generar
     un `Scenario:` con steps en Given/When/Then.
   - Steps en INGLES (verbos de accion en infinitivo sin sujeto explicito).
   - Steps concretos, orientados a comportamiento observable. No inventar datos
     sensibles ni endpoints reales.
   - Si un escenario no tiene steps claros en la entrada, generar stub con `@wip`:

     @wip
     Scenario: <titulo del caso>
       Given the user is on the initial screen
       When the pending scenario is executed
       Then the implementation is still in progress
       # TODO: implement real steps for this scenario

4. REGLAS GENERALES:
   - `@smoke` es subconjunto de `@regression`. Si `{{suite}}` es `smoke`,
     etiquetar SOLO el escenario critico principal con `@smoke`.
   - NO inventar credenciales, endpoints ni datos sensibles.
   - Prosa interna del `.feature` (Feature: title, Scenario: title) en ESPAÑOL.
   - Steps en INGLES.
   - Sin emojis en ninguna parte del archivo.

5. OUTPUT: solo el contenido del archivo `.feature`, sin prosa adicional.

Ejemplo de salida para canal=web, suite=regression, feature_name="Gestion de formulario
de registro", scenarios=["Registro exitoso de usuario", "Registro con email invalido",
"Registro con campos obligatorios vacios"]:

@web @form @regression
Feature: Gestion de formulario de registro

  @smoke @happy-path
  Scenario: Registro exitoso de usuario
    Given the user navigates to the registration form
    When they complete all mandatory fields with valid data
    Then the system confirms the successful registration

  @negative
  Scenario: Registro con email invalido
    Given the user navigates to the registration form
    When they enter an email address with an incorrect format
    Then the system displays a validation error message

  @edge-case
  Scenario: Registro con campos obligatorios vacios
    Given the user navigates to the registration form
    When they submit the form without filling in any mandatory fields
    Then the system displays an error for each empty mandatory field
```

