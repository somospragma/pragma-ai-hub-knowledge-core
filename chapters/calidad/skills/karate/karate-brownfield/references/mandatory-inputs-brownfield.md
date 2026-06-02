
# Inputs obligatorios — brownfield

Extiende `[[calidad-mandatory-inputs-protocol]]` con los inputs específicos de Karate brownfield.

## Base (greenfield + brownfield)

| Input | Obligatorio | Notas |
|---|---|---|
| `spec` | Sí | OpenAPI 3.x, Swagger 2.0 o WSDL del nuevo endpoint. |
| `user_story` | Recomendado | Para tag `@user-story:HUT-XXX` y trazabilidad. |
| `firma` | Recomendado | Documento técnico complementario. |

## Extras brownfield

| Input | Obligatorio | Default | Notas |
|---|---|---|---|
| Archivos del proyecto existente | Sí | — | Mínimo `karate-config.js` + 1 `.feature`. Sin estos no se pueden detectar convenciones. |
| `ticket_id` | Sí cuando el cliente impone convenciones cliente-específicas; recomendado en otros | — | Identificador de historia/ticket (formato propio del cliente: `JIRA-XXX`, `TICKET-NNNN`, `HU-NNN`, etc.). |
| `Body_Mode` | Sí | `A` | `A` = body en JSON externo; `B` = body inline / step-by-step. |
| `Scenario_Prefix` | No | Autodetectado | Prefijo de scenarios y/o nombre de feature, derivado del patrón detectado en features existentes. |

## Reglas cuando el cliente impone convenciones cliente-específicas

Cuando el proyecto exhibe convenciones cliente-específicas detectables (ver `client-specific-conventions.md`), dos inputs cambian de estatus:

- `user_story` → **OBLIGATORIO**.
- `firma` → **OBLIGATORIO**.

Si faltan, detente y solicítalos explícitamente antes de generar nada.
