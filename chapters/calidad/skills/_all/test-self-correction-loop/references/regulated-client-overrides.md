# Regulated Client Overrides

Reglas adicionales aplicables a clientes regulados. Sobrescriben los defaults del loop. Cualquier conflicto se resuelve **siempre** a favor de la regla más estricta.

## Clientes en alcance

- **HIPAA** (salud, EE.UU.).
- **SOX** (financiero, EE.UU.).
- **PCI-DSS Level 1** (pagos con tarjeta, global).
- **FedRAMP** (gobierno federal EE.UU.).
- **GDPR bajo DPIA** (datos personales, UE — cuando hay Data Protection Impact Assessment activo).
- Sectores equivalentes: HITRUST, ISO 27001 con compromiso contractual de auditoría, banca regulada local (SARLAFT, SFC en Colombia; CNBV en México).

> Si el perfil del cliente no está claro, invocar `[[calidad-mandatory-inputs-protocol]]` para confirmar antes de iniciar el loop.

## Overrides

### 1. Modo obligatorio `dry-run`

- Default no negociable.
- El loop **nunca** aplica correcciones automáticamente.
- Cada propuesta se entrega como patch + justificación + evidencia y queda pendiente de aprobación humana explícita.

### 2. Aprobación humana por cada corrección (no batch)

- Cada iteración del loop con propuesta de cambio requiere aprobación individual.
- Prohibido aprobar "todas las correcciones del run" en bloque — cada cambio se valida en su contexto.
- La aprobación debe quedar registrada (nombre del aprobador, timestamp, justificación) en el audit log.

### 3. Retención de audit log alineada a regulación

| Regulación | Retención mínima |
|---|---|
| HIPAA | 6 años (HHS guidance; muchos estados de EE.UU. exigen 7+) |
| SOX | 7 años |
| PCI-DSS Level 1 | 1 año online + retención histórica según política del cliente |
| FedRAMP | 3 años post-decommission |
| GDPR bajo DPIA | según base legal (típicamente 3 años; máximo el tiempo del propósito declarado) |

Coordinar con la política definitiva del cliente; si el cliente exige más que el mínimo, prevalece el cliente.

### 4. Cambios al test son parte del expediente de auditoría del release

- Cada corrección aplicada (o propuesta y rechazada) forma parte del paquete de evidencia entregado al equipo de compliance del cliente en cada release.
- El audit log debe ser exportable en formato auditable (JSONL + reporte humano en PDF/markdown).
- Cualquier corrección aplicada sin entrada en el audit log invalida el release desde el punto de vista de compliance.

### 5. "No AI modifications to tests" — modo report-only

Si el cliente exige explícitamente que ninguna modificación a tests sea originada por agentes AI:

- Forzar modo `dry-run` con flag adicional `report_only=true`.
- El loop produce **únicamente** reportes y propuestas; jamás aplica.
- El humano evalúa cada propuesta fuera del loop, en su propio toolchain.
- El audit log registra `outcome: report_only_proposed` y `applied: false`.

### 6. Suites regladas — restricción absoluta

Adicional a la Regla 9 de `anti-cheating-guardrails.md`: en clientes regulados, los suites etiquetados `@security`, `@contract`, `@compliance`, `@regulatory`, `@audit`, `@hipaa`, `@sox`, `@pci`, `@fedramp` **no entran al loop en ningún modo**.

- Fallo en cualquiera de esos tests es siempre bug del SUT o del entorno.
- El loop transiciona inmediatamente a `ESCALATED` sin pasar por `DIAGNOSING`.
- Escalation report incluye flag `regulatory_suite_failure` con prioridad máxima.

### 7. Logging redundante

- El audit log se replica en al menos dos destinos: el evidence storage del run y el sistema de auditoría del cliente (SIEM, log management, S3 con object lock, Azure Immutable Storage).
- Pérdida de log invalida la corrección retroactivamente.

### 8. Separación de roles

- El agente que aplica el cambio no puede ser el mismo que aprueba la corrección.
- Aprobación siempre humana; nunca por otro agente AI.
- Trazabilidad: `change.applied_by`, `change.approved_by` deben ser identidades distintas (humano para `approved_by`).

### 9. Ventanas de cambio

- Los cambios aplicados a tests durante el loop, aunque sean en `dry-run`, deben respetar las ventanas de cambio del cliente (change windows).
- Si el loop ocurre fuera de ventana, suspender hasta la próxima ventana válida o degradar a `scaffold-only`.

### 10. Reporte regulatorio adicional

Cada release que haya pasado por el loop en cliente regulado debe acompañarse de un reporte que liste:

- Cantidad de tests que entraron al loop.
- Cantidad de correcciones propuestas / aprobadas / rechazadas / revertidas.
- Cantidad de escalations.
- Violaciones de guardrails detectadas (importante para auditoría de control interno).
- Tests en `@quarantine` con SLA vencido (deuda regulatoria).
