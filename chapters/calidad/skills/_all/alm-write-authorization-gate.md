---
id: calidad-alm-write-authorization-gate
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Compuerta obligatoria para toda escritura en el ALM del cliente (gestor de proyectos y gestor de pruebas). Leer es libre; crear, editar, transicionar, comentar, mover, subir o adjuntar exige autorización humana explícita, previa y específica, pedida con una ficha de operación que incluye conteo y efectos colaterales."
tags: [alm, jira, xray, azure-devops, escritura, autorizacion, gate, mandatory, universal, seguridad]
enforcement: mandatory
verification:
  - check: "toda operación que alteró estado en el ALM fue precedida por una ficha de operación aprobada explícitamente por el usuario en la misma sesión"
    failure_message: "Bloqueado: se escribió en el ALM del cliente sin autorización explícita. El daño en el ALM de un cliente no se deshace con un undo: notifica a terceros, altera métricas y deja rastro."
  - check: "la ficha de autorización declaró operación, sistema destino, proyecto/ambiente, conteo exacto de elementos afectados y efectos colaterales previsibles"
    failure_message: "Bloqueado: se pidió autorización sin conteo o sin alcance. 'Voy a crear varios casos' no es una autorización pedida."
  - check: "cada escritura ejecutada quedó registrada en la bitácora de sesión con quién autorizó, cuándo y el resultado real de la operación"
    failure_message: "Bloqueado: hay escrituras en el ALM sin registro de autorización. Sin traza no se puede auditar qué tocó el agente en el sistema del cliente."
---

# ALM Write Authorization Gate — Nada se Escribe sin Permiso

## Principio

**Leer es libre. Toda operación que altere estado en el ALM del cliente exige autorización humana explícita, previa y específica.**

Un agente que escribe en el ALM sin autorización puede ensuciar el tablero de un equipo entero, disparar notificaciones a decenas de personas, alterar métricas de sprint, transicionar issues que otro estaba trabajando o crear decenas de elementos duplicados que después alguien borra a mano. **El daño no es reversible con un deshacer y ocurre fuera de nuestro perímetro**, en el sistema de trabajo del cliente.

Esta compuerta gobierna a `[[calidad-alm-mcp-integration]]` y a `[[calidad-alm-test-publishing-cycle]]`, y es más estricta que la regla que traía el primero: aquí **no hay distinción entre crear y modificar**. Ambas son escritura.

## Cuándo aplicar

Antes de **cada** operación de escritura, en cualquier ruta (funcional o de automatización), con cualquier vía técnica (MCP, REST directa, GraphQL del gestor de pruebas, CLI o script del repositorio del cliente). La vía no cambia la regla: lo que importa es que el estado del ALM cambie.

## Qué cuenta como escritura

Todas estas, sin excepción ni gradación:

| Categoría | Operaciones |
|---|---|
| Creación | casos de prueba, defectos, historias, subtareas, ciclos o ejecuciones de prueba, carpetas del repositorio de pruebas |
| Modificación | cualquier campo, descripción, criterios de aceptación, prioridad, asignación, etiquetas, versión, sprint |
| Flujo | transiciones de estado, cierre, reapertura |
| Vínculos | vincular o desvincular incidencias, asociar casos a historias o a suites |
| Gestor de pruebas | cambiar el tipo de un test, subir o reemplazar la definición Gherkin, mover un test de carpeta, asociar a un plan o ciclo |
| Resultados | subir resultados de ejecución, adjuntar evidencias, capturas, videos o logs |
| Otros | comentarios, registros de tiempo, menciones a personas |

**Leer nunca requiere autorización**: consultar incidencias, buscar por consulta, listar proyectos, leer campos y metadatos, descargar una historia con sus criterios. Leer es el modo por defecto del agente.

## La ficha de operación

La autorización **no** se pide con una pregunta suelta en el chat. Se pide con una ficha que el usuario aprueba o rechaza, y que contiene:

```yaml
autorizacion_requerida:
  operacion: "crear casos de prueba"          # verbo exacto, una sola operación
  sistema: "gestor de pruebas"                # gestor de proyectos | gestor de pruebas
  destino: "proyecto ABC / carpeta X"         # proyecto, tablero, carpeta o ciclo
  ambiente: "productivo del cliente"          # declararlo SIEMPRE cuando lo sea
  alcance:
    elementos: 14                             # conteo exacto, obligatorio
    detalle: "14 casos nuevos, 0 actualizaciones, 3 omitidos por ya existir"
  muestra: |                                  # obligatoria en lotes: 1 o 2 elementos completos
    Resumen: ...
    Vínculo: ...
  efectos_colaterales:
    - "notifica a los observadores de la historia"
    - "los casos aparecen en el tablero del equipo"
  reversibilidad: "los casos creados solo puede borrarlos un humano con permisos"
```

**Sin conteo no hay ficha.** "Voy a crear varios casos" o "voy a subir los resultados" no son autorizaciones pedidas: son avisos. El usuario debe poder dimensionar el daño antes de aprobar.

## Reglas de la compuerta

1. **Por lote y por operación, nunca general.** Aprobar la creación de casos no autoriza a transicionar estados. Aprobar un lote no autoriza el siguiente. No existe el "autorizado para todo lo del ALM".
2. **No se hereda entre sesiones.** Una autorización de ayer no vale hoy. Al retomar un flujo interrumpido, se vuelve a pedir para lo que falte.
3. **Fallo a mitad de lote**: se detiene de inmediato, se reporta qué alcanzó a escribirse y qué no, y **se vuelve a pedir autorización** para continuar o para revertir. Nunca se sigue "porque ya estaba aprobado".
4. **Ambiente productivo del cliente**: la ficha lo declara explícitamente. Si el agente no sabe si el destino es productivo, lo pregunta antes de armar la ficha.
5. **Verificaciones de capacidad también son escritura.** Probar "si el agente puede crear un caso" crea un caso. Pasa por la ficha, se hace sobre un elemento desechable declarado como tal, y se limpia o se reporta para que un humano lo limpie.
6. **Registro obligatorio**: cada escritura ejecutada se anota en la bitácora de sesión (`[[calidad-pipeline-state-tracking]]`) con la operación, quién autorizó, cuándo, y el resultado real — incluidos los identificadores creados, que son lo que permite deshacer.
7. **Idempotencia antes de la ficha**: se consulta qué existe ya y el conteo de la ficha distingue nuevos de existentes. Un lote que duplicaría elementos se corrige antes de pedir autorización, no después.

## Restricciones

- **NUNCA** escribir en el ALM para "probar si funciona", "ver si tengo permisos" o "dejarlo listo". Toda escritura es intencional y autorizada.
- **NUNCA** interpretar una instrucción general del usuario ("automatiza el ciclo", "encárgate de la trazabilidad") como autorización de escritura. La autorización es específica de la operación y del lote.
- **NUNCA** borrar elementos del ALM del cliente. Lo obsoleto se marca o se comenta; borrar es decisión humana ejecutada por humanos (regla heredada de `[[calidad-alm-mcp-integration]]`).
- **NUNCA** editar un caso que ya tiene ejecuciones registradas para "alinearlo": se crea uno nuevo y se referencia (extensión al ALM de la regla anti-cheating de brownfield).
- Si el usuario rechaza la autorización, el flujo **no se bloquea**: se entrega el artefacto equivalente (archivo de importación, markdown listo para pegar, reporte) y se registra la decisión. La entrega continúa por la vía manual.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | toda operación que alteró estado en el ALM fue precedida por una ficha de operación aprobada explícitamente por el usuario en la misma sesión | Bloqueado: se escribió en el ALM del cliente sin autorización explícita. El daño en el ALM de un cliente no se deshace con un undo: notifica a terceros, altera métricas y deja rastro. |
| 2 | la ficha de autorización declaró operación, sistema destino, proyecto/ambiente, conteo exacto de elementos afectados y efectos colaterales previsibles | Bloqueado: se pidió autorización sin conteo o sin alcance. 'Voy a crear varios casos' no es una autorización pedida. |
| 3 | cada escritura ejecutada quedó registrada en la bitácora de sesión con quién autorizó, cuándo y el resultado real de la operación | Bloqueado: hay escrituras en el ALM sin registro de autorización. Sin traza no se puede auditar qué tocó el agente en el sistema del cliente. |

## Cross-links

`[[calidad-alm-mcp-integration]]`, `[[calidad-alm-test-publishing-cycle]]`, `[[calidad-pipeline-state-tracking]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-test-evidence-and-traceability]]`.
