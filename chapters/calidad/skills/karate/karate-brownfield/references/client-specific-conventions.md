# Convenciones cliente-específicas en proyectos Karate brownfield

Cuando un proyecto Karate existente del cliente impone convenciones no documentadas en el spec (estilo de headers, naming de features, manera de construir bodies, patrón de assertions, headers transversales obligatorios), el brownfield detecta y respeta esas convenciones — nunca las "corrige" hacia el estilo greenfield del chapter.

## Patrones comunes a detectar

### 1. Naming de features con prefix de ticket
Algunos clientes prefijan el nombre del feature con su identificador de historia (formato propio: `JIRA-XXX`, `TICKET-NNNN`, `HU-NNN`, etc.).
- Archivo: `{prefix}-{descripcion-corta}.feature`
- Detección: regex sobre nombres de features existentes.
- Acción brownfield: respetar el prefix detectado para nuevos features. Si el cliente declara `Scenario_Prefix` como input, usarlo; si no, derivar del patrón detectado.

### 2. Scenarios con prefix + estado
Patrón típico: `{ticket-prefix} solicitud exitosa - {descripción}` (positivo) / `{ticket-prefix} solicitud fallida - {descripción}` (negativo).
Tags acompañantes habituales: `@happyPath @regression @smoke` (positivo) / `@negative @regression` (negativo).
Detección: leer scenarios de features existentes y extraer el patrón.

### 3. Headers one-by-one vs configure-headers
Detección: si el proyecto usa `And header X-Name = 'value'` (línea por línea) en lugar de `* configure headers = { ... }` (objeto inline), respetar ese estilo.
Razón habitual del cliente: visibilidad en logs de pipeline — cada header aparece como step ejecutado, facilitando debugging.

### 4. Body step-by-step vs inline JSON
Detección: si el proyecto construye el request body con `* def body = {}` + múltiples `* set body.field = value` en lugar de pasar JSON inline en `And request {...}`, respetar ese estilo.
Razón habitual del cliente: cada `set` aparece como step independiente, permitiendo identificar el campo exacto donde se quiebra el escenario.

### 5. Assertions field-by-field vs match contra schema
Detección: si el proyecto valida la respuesta con múltiples `And match response.field == '#type'` (campo por campo) en lugar de `And match response == read('classpath:schemas/...-match.json')`, respetar ese estilo.
Razón habitual del cliente: trazabilidad granular del fallo + evitar dependencia de archivos externos en la pipeline.

### 6. Headers transversales obligatorios no declarados en spec
Algunos clientes exigen headers de identificación/seguridad que NO aparecen en el OpenAPI/Swagger pero son requeridos por su gateway o capa de seguridad (`X-Transaction-Id`, `X-Session-Id`, `X-Auth-Id`, `X-Channel`, etc., con nombres específicos del cliente).
Detección: si TODOS los features existentes incluyen el mismo set de headers, asumir que son transversales obligatorios.
Acción brownfield:
- Incluir los mismos headers transversales en cada nuevo feature.
- Por cada header transversal detectado generar 1 escenario `@negative @missing-header` que verifique el rechazo del request si falta.
- Si el header tiene formato validable (UUID, ISO8601, enum cerrado), generar también 1 escenario `@negative @invalid-header-format`.

### 7. Tag conventions del cliente
Si el cliente usa tags propios (`@regresion-cliente`, `@smoke-prod`, `@critico-negocio`, etc.), detectarlos en features existentes y aplicarlos a los nuevos. NUNCA imponer los tags greenfield del chapter sobre proyectos del cliente.

## Inputs adicionales para brownfield con convenciones cliente

Cuando el cliente impone convenciones, el brownfield exige inputs adicionales:
- `ticket_prefix`: el prefijo de ticket usado en feature/scenario naming (si no se autodetecta inequívocamente).
- `body_mode`: `external-json` (archivos `bodies/*.json` referenciados) o `inline-step-by-step`.
- `transversal_headers`: lista de headers obligatorios cross-endpoint (si no se autodetecta).
- `user_story`: las convenciones cliente-específicas suelen implicar trazabilidad estricta a historias de negocio — `user_story` y `firma` pasan a obligatorios.

## Regla maestra

El brownfield NUNCA "moderniza" un proyecto del cliente al estilo greenfield del chapter. Lo que el cliente eligió es lo correcto para el cliente. Auto-corrección está prohibida sobre convenciones del cliente — el `[[calidad-test-self-correction-loop]]` respeta convenciones detectadas como invariantes.
