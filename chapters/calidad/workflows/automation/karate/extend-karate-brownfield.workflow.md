---
id: extend-karate-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Flujo para extender un proyecto Karate existente con nuevos features, respetando convenciones detectadas y reglas de cliente.
tags: [karate, brownfield, workflow, mercantil]
---

# Workflow — Extender proyecto Karate brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` y `[[calidad-brownfield-vs-greenfield]]` identifican un escenario brownfield para Karate: el usuario provee al menos `karate-config.js` + un `.feature` del proyecto existente y solicita agregar pruebas para nuevos endpoints.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `spec` | Sí | OpenAPI 3.x, Swagger 2.0 o WSDL del nuevo endpoint. |
| Archivos de proyecto existente | Sí | Mínimo `karate-config.js` + 1 `.feature`. |
| `HUT_ID` | Sí en Mercantil; recomendado en otros | Identificador de historia. |
| `Body_Mode` | Sí | `A` (JSON externo) \| `B` (inline / step-by-step). |
| `Scenario_Prefix` | No | Default `PN-PR-BFF-`. |
| `user_story` | Obligatorio si Mercantil | Tag `@user-story:HUT-XXX`. |
| `firma` | Obligatorio si Mercantil | Documento técnico. |

Lista completa en `[[karate-mandatory-inputs-brownfield]]`.

## Pasos

### 1. Detectar cliente Mercantil
Pistas: paths con `PN-PR-BFF-`, variable `mercantilUrl`, naming de scenarios con "solicitud exitosa/fallida", headers `Transaction-Id` / `Sid` / `Auth-Id` / `X-Channel`. El usuario también puede declararlo explícitamente. Si es Mercantil, activa `[[karate-mercantil-conventions]]` y `[[karate-mercantil-security-headers]]`.

### 2. Validar inputs adicionales
Si Mercantil, exigir `user_story` y `firma`. Validar `Body_Mode` ∈ {A, B}. Si falta cualquier obligatorio, detente y solicítalo (`[[calidad-mandatory-inputs-protocol]]`).

### 3. Analizar convenciones existentes
Aplicar el algoritmo de `[[karate-convention-detection]]`. Anota `features_dir`, `bodies_dir`, `package_name`, `base_url_var`, `header_style`, `body_loading_style`, `scenario_naming_pattern`, variables de `karate-config.js`. Si hay conflicto entre convención detectada y reglas Mercantil, las reglas Mercantil ganan.

### 4. Calcular cobertura
Aplica `[[karate-negative-coverage-formula]]`. En Mercantil, suma los headers de `[[karate-mercantil-security-headers]]` aunque el spec no los marque como required.

### 5. Generar SOLO `.feature` y body JSON
- `.feature` en `features_dir` detectado, con naming y tags del proyecto (o de Mercantil si aplica).
- Body JSON sólo si `Body_Mode = A`; nombre y ubicación según `bodies_dir`.
- Sin tocar `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, ni schemas existentes.

### 6. Validar
- Convenciones detectadas respetadas al 100% (header_style, body_loading_style, naming, tags).
- Reglas Mercantil aplicadas si corresponde (naming, headers obligatorios, assertions field-by-field).
- Ningún archivo de infraestructura generado.
- Verifica que el `pom.xml` existente cumpla `[[karate-feature-file-location-constraint]]`; si no, repórtalo al usuario sin modificarlo.

Entrega con `[[calidad-streaming-files-protocol]]`, trazabilidad con `[[calidad-test-evidence-and-traceability]]`.

## Criterios de finalización

1. Convenciones detectadas respetadas al 100%.
2. Ningún archivo de infraestructura generado (`pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, schemas existentes intactos).
3. Reglas Mercantil aplicadas si corresponde:
   - Feature naming `{jira-prefix}-{us-description}.feature`.
   - Scenarios con prefijo `PN-PR-BFF-{jira} solicitud exitosa/fallida - ...`.
   - Tags `@happyPath @regression @smoke` (positivo) / `@negative @regression` (negativo).
   - Headers one-by-one, body step-by-step, assertions field-by-field.
   - Headers de seguridad Mercantil cubiertos (missing + invalid-format donde aplique).
4. Fórmula de cobertura aplicada y declarada.
5. Sin lógica condicional en aserciones; `Examples` sin celdas vacías.
6. Comando `mvn test` filtrado por tag de la nueva historia provisto en la entrega.
