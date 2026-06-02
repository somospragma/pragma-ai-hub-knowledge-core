# Over-Healing Guardrails — Reglas Duras Anti-Cheating

**Crítico.** Este documento define las reglas duras para **no curar**. El healing mal aplicado esconde bugs reales, da falsa seguridad al cliente y viola el principio rector del chapter (`[[calidad-test-self-correction-loop]]`: anti-cheating es regla maestra).

Cualquier ingeniero del chapter que aplique healing fuera de estas reglas comete falta operativa documentable.

## Reglas duras

### 1. Cambios breaking del SUT → NO curar, reportar bug

Si el cambio en el SUT es **breaking**, prohibido curarlo. Ejemplos:

- Campo requerido eliminado del response (`id`, `email`, `status`).
- Endpoint movido a otra ruta (`/v1/users` → `/v2/customers`).
- Status code cambió (`200 OK` → `4xx` o `5xx`) en flujo previamente funcional.
- Schema GraphQL eliminó un type usado por el cliente.
- Pantalla mobile cambió de flujo (login → onboarding intermedio).
- Permiso del SO mobile añadido sin documentación.

Acción: reportar como bug vía `[[calidad-failure-triage-and-classification]]`, abrir ticket con prioridad acorde a `[[calidad-business-driven-prioritization]]`, **revertir** cualquier healing intentado.

### 2. Threshold semanal: >3 healings → deshabilitar healing en ese test

Si el mismo test se cura **más de 3 veces en 1 semana calendario**, el orquestador (`[[calidad-test-execution-orchestration]]`) marca el test con tag `healing-suspended` y exige intervención humana. Es señal de que el SUT cambió de verdad y no de flake transitorio.

El ticket se abre automáticamente desde la telemetría con:

- `test_id` y suite afectada.
- Lista de timestamps de los healings.
- Selectors original y resuelto en cada caso.
- Owner del módulo según el código (CODEOWNERS).

### 3. Cambiar la semántica del assertion ≠ healing → ESCALAR

Si la "reparación" requiere modificar la semántica del test, **no es healing**, es **modificar el test**:

- Cambiar `==` por `contains` para que pase.
- Cambiar el valor esperado (`expected: "active"` → `expected: "ACTIVE"` cuando antes funcionaba).
- Convertir un `match each` Karate en un `match` con filtros para excluir elementos que fallan.
- Reducir el número de iteraciones de K6 para evadir el threshold.

Acción: escalar al lead del chapter; nunca commit silencioso. La modificación del assertion requiere PR con justificación de negocio (no técnica).

### 4. Suites bloqueadas para healing

Healing está **bloqueado totalmente** en los siguientes tags:

- `@security` — toda variación contra el contrato de seguridad es señal de vulnerabilidad potencial.
- `@contract` — los contract tests existen precisamente para detectar drift; curarlos los invalida.
- `@regression-strict` — diseñados para detectar cambios de selectors / shapes.
- `@compliance` — auditoría exige determinismo.
- `@release-gate` — fallas aquí bloquean release; curarlas es fraude operativo.

El orquestador inyecta `NoHealing` (ver `healing-aware-page-object.md`) automáticamente al detectar estos tags. Si un ingeniero overridea esta inyección, es falta operativa.

### 5. Karate: prohibido convertir `#string` requerido en `##string`

El matcher `##string` (opcional con type check) **solo** puede aplicarse a campos documentados como opcionales en el contrato (OpenAPI / GraphQL schema). Convertir un campo `#string` requerido a `##string` para que pase un test que está fallando esconde bug de contrato y es falta operativa.

### 6. K6: prohibido aflojar thresholds sin justificación

Los thresholds (`http_req_duration`, `http_req_failed`, `iteration_duration`) **nunca** se aflojan para evadir falla. Si el SUT degradó performance, es bug de performance, no es healing.

Excepciones (todas requieren PR aprobada por lead):

- El threshold original estaba mal calibrado (probar con baseline histórico).
- Cambió la SLA con el cliente (incluir PDF del SLA en el PR).
- El test mide la operación equivocada (refactor explícito del test).

### 7. Expiration: healings tienen 30 días de vigencia

Cada healing aplicado tiene un campo `expires_at = now + 30d`. Pasado el plazo:

- Si el primary locator volvió a funcionar → cerrar healing como recuperado.
- Si sigue fallando → convertir en **deuda técnica**, ticket auto-creado con prioridad `medium` mínimo.
- Si el primary lleva >60 días fallando → escalar a prioridad `high` y bloquear el suite hasta que se decida (refactor o aceptar el cambio del SUT).

### 8. Logs de healing son evidencia inmutable

El log estructurado de cada healing (paso 4 del SKILL) es parte de la evidencia entregable (`[[calidad-test-evidence-and-traceability]]`). Borrarlo, modificarlo o silenciarlo en producción **invalida la entrega** del chapter.

### 9. Healing en producción exige auditoría

Si el suite corre contra producción (smoke en prod, canary tests), **toda** activación de healing dispara notificación al canal de operaciones del cliente en tiempo real. No hay healing "silencioso" en producción.

## Resumen ejecutivo

| Situación | ¿Curar? | Acción |
|---|---|---|
| Selector primario falló por reflow cosmético | Sí | Fallback chain + log |
| Campo opcional ausente | Sí | `##type` + log |
| 5xx transitorio | Sí | Retry hook + log |
| Campo requerido eliminado | NO | Bug, escalar |
| Endpoint movido | NO | Bug, escalar |
| Status code cambió 200 → 4xx | NO | Bug, escalar |
| Assertion necesita cambio semántico | NO | Modificar test vía PR |
| Test con >3 healings/semana | NO | Suspender, ticket |
| Suite `@security` / `@contract` | NO | Bloqueado por orquestador |
| Healing en prod | Sí (con auditoría) | Notificar cliente + ticket |
