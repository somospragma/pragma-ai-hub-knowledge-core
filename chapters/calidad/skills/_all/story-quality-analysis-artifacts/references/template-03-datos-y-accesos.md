# Datos y accesos — {{hu}} · {{titulo}}

Fecha: {{fecha}} · Épica: {{epica}}
Fuente: `{{fuente}}`

## Alcance de este documento

Panorama **completo** de lo que Calidad necesita para correr los casos de esta historia. No
solo lo que se le pide al cliente: también lo que hay que gestionar con arquitectura, con
negocio, con desarrollo, y lo que monta el propio equipo.

Es un error frecuente y caro reducir este documento a "lo que pedimos al banco": lo que se
queda fuera se queda **sin dueño**, y aparece el día de la ejecución.

Cada ítem lleva su responsable, del catálogo de `[[calidad-responsibility-routing-of-blockers]]`:

| Responsable | Qué le corresponde |
|---|---|
| **cliente-datos** | Usuarios, productos y estados que solo el cliente puede habilitar en el ambiente. Van a la solicitud formal (`[[calidad-client-test-data-request]]`) |
| **arquitecto** | Contratos de servicio, endpoints, mecanismos técnicos, ambientes |
| **po-negocio** | Reglas de negocio, textos exactos, parámetros de consola de administración. Van al refinamiento, vía `01-dudas.md` |
| **dev-pragma** | Mocks, fixtures, temporizadores de configuración, builds, dispositivos |
| **qa** | Lo que el propio equipo provisiona: perfiles, usuarios derivados, estados alcanzables operando |

## Prioridad 1 — Bloquean la ejecución

| # | Ítem | Estado exigido, no solo la entidad | Responsable | Para cuándo |
|---|---|---|---|---|
| P1.1 |  |  |  |  |

La columna del estado exigido es la que hace el trabajo. "Una tarjeta" no es un requisito;
"una tarjeta con al menos un movimiento en tránsito" sí (`[[calidad-test-data-management]]`).

## Prioridad 2 — Necesarios para verificar

| # | Ítem | Estado exigido | Responsable | Para cuándo |
|---|---|---|---|---|

## Prioridad 3 — Los levanta el equipo

| # | Ítem | Cómo se levanta | Responsable |
|---|---|---|---|

## Prioridad 4 — Herramientas y entorno

| # | Ítem | Detalle | Responsable |
|---|---|---|---|

## Lo que NO hace falta pedir

Derivable de otro ítem ya pedido, o cubierto por otro que ya está en la lista. Se declara
para que nadie gaste tiempo consiguiéndolo (`[[calidad-client-test-data-request]]`).

| Ítem | Se obtiene de | Cómo |
|---|---|---|

## Trazabilidad a la solicitud al cliente

Los ítems de responsable **cliente-datos** de este documento tienen que aparecer en
`.evidence/data-request.json`. El cruce lo comprueba `check-data-coverage.py`; si un
criterio de esta historia queda sin dato, la solicitud no se emite.

| Ítem de aquí | ID en la solicitud |
|---|---|
