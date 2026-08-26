---
id: calidad-chapter-entry-point
version: 1.0.0
scope: chapter
type: steering
chapter: calidad
description: "Punto de entrada del Chapter Calidad. Protocolo de lectura con permiso de parar, cómo resolver una referencia cruzada que no existe con ese nombre, y las compuertas obligatorias con la pregunta concreta que cada una exige contestar antes de seguir."
tags: [entry-point, navegacion, compuertas, enforcement, mandatory]
enforcement: mandatory
---

# Punto de Entrada del Chapter Calidad

## Rol

Este documento es lo primero que se lee y lo único que hay que tener presente
todo el tiempo. Todo lo demás se abre cuando toca y no antes.

El costo de una sesión de certificación **no está en escribir**: está en
descubrir. Leer de más se paga en cada turno; leer de menos se paga en corridas
que no aportan información. Este documento existe para acertar en las dos cosas.

## Protocolo de lectura

Lee en este orden y **para en cuanto tengas lo que necesitas**. Que un documento
esté disponible no es razón para abrirlo.

| # | Qué | Cuándo |
|---|---|---|
| 1 | Este documento y el resto del steering | Siempre. Ya está cargado: no lo releas |
| 2 | `.evidence/pipeline-state.json` y la bitácora | Siempre, si el `output_path` ya tiene evidencia |
| 3 | El inventario del repositorio (`.evidence/repo-capability-map.md`, `.evidence/archetype-inventory.md`) | En brownfield, antes de tocar nada |
| 4 | El workflow que corresponda al intent | Al empezar la tarea, no antes |
| 5 | El skill de la compuerta que estés cruzando | En el momento de cruzarla |
| 6 | Los `references/` de ese skill | Solo el que resuelve la duda concreta |

**Un archivo ya leído no se relee.** Si necesitas algo que ya viste y no lo
recuerdas, el problema es que la sesión creció demasiado: anota el estado en la
traza y córtala, no vuelvas a abrir medio repositorio.

## Cómo resolver una referencia entre dobles corchetes

Una referencia entre dobles corchetes es el identificador del asset **en la fuente del chapter**. La CLI lo
instala con un nombre derivado de su título, así que el `id` casi nunca es el
nombre de la carpeta. `[[calidad-failure-triage-and-classification]]` vive en
`failure-triage-and-classification-clasificacion-de-fallos-y-analisis-de-causa-ra`.

Cuando una referencia no exista con ese nombre, busca su fila en el resolvedor
que corresponda. No es un enlace roto del documento: es una traducción que falta.

| Si la referencia empieza por… | Ábrela en |
|---|---|
| `calidad-` | `[[calidad-asset-resolver]]` |
| cualquier otra cosa (es conocimiento de la cuenta) | el resolvedor de la cuenta, `<cliente>-<chapter>-asset-resolver` |

**Que no encuentres una compuerta obligatoria no reduce lo que exige.** Si de
verdad no está instalada, dilo con esas palabras y detente; no la sustituyas por
tu criterio.

## Enrutamiento

Cualquier solicitud de **generar pruebas**, sea cual sea el framework, entra por
`[[calidad-route-test-generation]]`. Es el único punto de entrada de generación
y decide stack, modo y cadena de workflows. No elijas el framework por tu cuenta.

## Compuertas: la pregunta que hay que contestar antes de seguir

Cada fila es un momento en el que **no se avanza sin contestar la pregunta**.
Contestarla deja rastro en la respuesta; una exhortación a "tener cuidado" no.
El documento de la derecha es donde está el procedimiento completo.

| Momento | Pregunta que hay que contestar | Documento |
|---|---|---|
| Abrir sesión sobre un `output_path` con evidencia | ¿Dónde quedó el proceso y cuál es su `next_action`? | `[[calidad-pipeline-state-tracking]]` |
| Antes del primer archivo | ¿Está cada insumo obligatorio presente y leído completo, con su fila en la tabla de extracción? | `[[calidad-mandatory-inputs-protocol]]` |
| Brownfield, antes de escribir | ¿Qué resuelve ya el repositorio, y dónde mide calidad? | `[[calidad-repo-capability-discovery]]` |
| Antes de convertir un texto en localizador o aserción | ¿Este texto es estático, de formato invariante, volátil o dato controlado? | `[[calidad-data-volatility-and-assertion-anchoring]]` |
| Antes de cualquier ejecución | ¿El preflight está verde y el comando salió del repositorio? | `[[calidad-execution-preflight]]` |
| Ante un fallo, antes de teorizar | ¿De qué instante es la evidencia que estoy mirando, y es anterior o posterior al hecho que quiero afirmar? | `[[calidad-failure-triage-and-classification]]` |
| Antes de llamar algo intermitente | ¿Cuántas veces de cuántas? ¿Y qué pasa en el caso en que NO debería ocurrir? | `[[calidad-failure-triage-and-classification]]` |
| Antes de declarar bloqueo de ambiente | ¿Puedo demostrar, desde el reporte, que ninguna sesión llegó a tocar la aplicación? | `[[calidad-environment-blocker-evidence]]` |
| Antes de corregir un test que falla | ¿El triage dice que es defecto del arnés y no del sistema bajo prueba? | `[[calidad-test-self-correction-loop]]` |
| Antes de añadir un reintento | ¿Este reintento muta el estado del sistema bajo prueba? | `[[calidad-test-self-healing]]` |
| Antes de escribir cualquier cosa en el ALM del cliente | ¿Tengo autorización explícita, previa, específica y con conteo? | `[[calidad-alm-write-authorization-gate]]` |
| Antes de retirar escenarios de un feature | ¿Sobrevive al menos un escenario con la etiqueta que forma el gate? | `[[calidad-smoke-gate-policy]]` |
| Al cerrar la entrega | ¿El bloque de cierre está completo y la cobertura reportada es la real por plataforma? | `[[calidad-delivery-gate-contract]]` |

## Lo que nunca debes hacer

- **Nunca formules una segunda hipótesis sin haber mirado la evidencia de la
  primera**, y nunca trates como evidencia una captura o un volcado **posterior**
  al hecho que quieres afirmar. Una evidencia tardía no refuta nada.
- **Nunca trates dos evidencias coincidentes como confirmación sin comprobar que
  no fallan por la misma causa.** Dos capturas tardías por la misma razón no se
  corroboran entre sí: comparten el sesgo.
- **Nunca uses "intermitente", "flaky" o "transitorio" sin poder decir cuántas
  veces de cuántas.** Son conclusiones cuantitativas, no impresiones.
- **Nunca concluyas que algo no existe a partir de una búsqueda cuyo código de
  salida no comprobaste.** Una salida vacía puede ser "no hay resultados" o puede
  ser "el comando no corrió".
- **Nunca releas un documento que ya está en el contexto de esta sesión.** Si el
  contexto ya no lo tiene, corta la sesión y arranca desde la traza.
- **Nunca sigas adelante sin contestar la pregunta de la compuerta que estás
  cruzando**, ni des una compuerta por cumplida porque el documento "dice algo
  parecido a lo que ya ibas a hacer".
