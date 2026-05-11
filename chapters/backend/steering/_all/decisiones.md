---
id: backend-steering-decisiones
version: "1.0"
scope: chapter
type: steering
chapter: backend
---

# Decisiones Técnicas Obligatorias — Transversales

Estas decisiones aplican a TODOS los proyectos backend sin excepción.

## Testing

- Testing obligatorio: unit tests + integration tests.
- Cobertura mínima en dominio: **80%**.
- Cobertura mínima general: **70%**.
- Todo test DEBE tener assertions explícitas que verifiquen comportamiento.
- Tests de integración DEBEN usar contenedores (Testcontainers o equivalente) para dependencias externas.

## Health Check

- Todo servicio DEBE exponer un endpoint de health check (`/health` o `/actuator/health`).
- El health check DEBE verificar el estado de las dependencias críticas (base de datos, colas, servicios externos).
- DEBE retornar HTTP 200 cuando el servicio está saludable y HTTP 503 cuando no.
- DEBE incluir detalle de cada dependencia verificada.

## Graceful Shutdown

- Todo servicio DEBE implementar graceful shutdown:
  1. Recibir señal SIGTERM.
  2. Dejar de aceptar nuevas peticiones.
  3. Completar las peticiones en curso (con timeout máximo configurable).
  4. Cerrar conexiones a bases de datos, colas y servicios externos.
  5. Terminar el proceso con código 0.

## Structured Logging

- SIEMPRE usar logging estructurado en formato JSON.
- Campos obligatorios en cada log entry:
  - `timestamp` — ISO 8601.
  - `level` — TRACE, DEBUG, INFO, WARN, ERROR.
  - `message` — Descripción del evento.
  - `correlationId` — ID de trazabilidad de la petición.
  - `service` — Nombre del servicio.
- NUNCA loguear en texto plano en ambientes no-locales.
- Niveles de log: ERROR para fallos, WARN para situaciones anómalas recuperables, INFO para eventos de negocio, DEBUG para desarrollo.

## Idempotencia y Atomicidad

- Operaciones de escritura DEBEN ser idempotentes cuando sea posible.
- Usar idempotency keys en endpoints de creación/mutación.
- Operaciones que modifican múltiples recursos DEBEN ser atómicas (transacciones).
- Preferir upsert sobre insert + update separados cuando la semántica lo permita.
- Si una operación no puede ser atómica, DEBE implementar compensación (saga pattern o equivalente).
