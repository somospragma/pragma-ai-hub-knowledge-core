
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
| `HUT_ID` | Sí en Mercantil; recomendado en otros | — | Identificador de historia (`HUT-1234`). |
| `Body_Mode` | Sí | `A` | `A` = body en JSON externo; `B` = body inline / step-by-step. |
| `Scenario_Prefix` | No | `PN-PR-BFF-` | Prefijo de scenarios y/o nombre de feature. |

## Reglas Mercantil

Cuando el proyecto pertenece al cliente Mercantil, dos inputs cambian de estatus:

- `user_story` → **OBLIGATORIO**.
- `firma` → **OBLIGATORIO**.

Si faltan, detente y solicítalos explícitamente antes de generar nada.
