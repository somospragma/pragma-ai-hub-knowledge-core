# Un hallazgo, un registro: por qué no se crean documentos paralelos

## El caso que lo motiva

En una sesión de análisis, el agente separó las dudas de negocio y de arquitectura en un
documento nuevo, `DUDAS-REFINAMIENTO.md`, con una numeración propia. Era una respuesta
razonable a la instrucción de sacar esas dudas de la solicitud de datos.

Y estaba mal, porque **esas dudas ya vivían** en el `01-dudas.md` de cada historia. El
documento nuevo era una copia con otra numeración de algo que ya existía. Deshacerlo —
borrarlo, verificar que nada se hubiera perdido, y de paso corregir la leyenda de roles en
trece archivos — costó un turno completo.

Lo que falló no fue el criterio del momento. Fue que ningún asset decía **dónde vive cada
tipo de hallazgo**, así que cuando llegó una instrucción de separación, el agente separó
creando, que es lo que uno hace cuando no sabe que el sitio ya existe.

## La tabla de registro

Cada tipo de hallazgo tiene exactamente un hogar. Si algo hay que sacar de un sitio, se
enruta al suyo; **no se crea uno nuevo**.

| Hallazgo | Vive en | No vive en |
|---|---|---|
| Duda, ambigüedad, vacío de la historia | `analisis/<HU>/01-dudas.md` | Un documento de dudas del lote, la solicitud de datos, el chat |
| Decisión de qué capa prueba qué criterio | `analisis/<HU>/02-estrategia-de-pruebas.md` | La estrategia general del proyecto |
| Dato, acceso o herramienta que hace falta | `analisis/<HU>/03-datos-y-accesos.md` | Solo la solicitud al cliente |
| Lo que se le pide al cliente | `.evidence/data-request.json` | Un markdown escrito a mano |
| Estado del proceso y siguiente acción | `.evidence/pipeline-state.json` | La memoria de la sesión |
| Qué pasó y qué corrigió el usuario | `.evidence/session-log.md`, append-only | Un resumen que se reescribe |
| Índice del lote | `analisis/README.md`, generado | Escrito a mano |

## Las tres reglas

### 1. Sacar algo de un sitio obliga a decir a cuál va

"Esto no va en la solicitud de datos" es media instrucción. La otra mitad es dónde sí va, y
sin ella el hallazgo se pierde o se duplica. Cuando algo cambia de registro, la línea que se
borra deja una referencia al sitio nuevo, no desaparece en silencio.

### 2. Lo transversal se apunta desde cada historia, no se centraliza

Una duda que afecta a cinco historias no crea un documento de dudas transversales: se
escribe en la historia donde más pesa y las otras cuatro la referencian. Centralizarla
parece más limpio y produce dos fuentes que hay que mantener en paralelo — y una de las dos
siempre se queda atrás.

### 3. La forma común es del generador, no de cada archivo

Cabecera, épica, fecha y leyenda de responsables son idénticas en todos los dossiers del
lote: las pone `scaffold-dossier.py` desde la plantilla. Cuando la leyenda cambia, cambia la
plantilla. Editarla a mano en cada archivo es lo que dejó, en el caso medido, archivos con
la leyenda vieja conviviendo con archivos con la nueva.

## Cómo se comprueba

La estructura la impone la herramienta: `scaffold-dossier.py` crea exactamente estas rutas y
regenera el índice. Un documento de análisis que no esté bajo `.evidence/analisis/<HU>/` es,
por construcción, un registro paralelo — y esa es toda la comprobación que hace falta.
