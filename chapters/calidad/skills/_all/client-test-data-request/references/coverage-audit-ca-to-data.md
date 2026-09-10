# La auditoría criterio → dato: lo que ninguna relectura encuentra

## El fallo que la motiva, medido

Una solicitud de datos revisada, enumerada uno a uno y con la audiencia correcta pidió dos
usuarios administradores: uno que representa dos empresas y otro más. Ninguno de los dos
representaba **una sola** empresa, que es la condición por defecto de media docena de
criterios de aceptación repartidos entre tres historias.

Nadie lo vio releyendo. Se vio cuando alguien preguntó explícitamente si cada criterio tenía
con qué ejecutarse, y la respuesta obligó a rehacer la sección de usuarios.

La lección no es "revisar mejor". Es que **este cruce no es una revisión: es un join**, y un
join lo hace una herramienta. Pedirle a quien acaba de escribir el documento que verifique
su propia cobertura es pedirle que encuentre lo que no se le ocurrió.

## Qué comprueba

`scripts/check-data-coverage.py` cruza `.evidence/ca-inventory.json` contra
`.evidence/data-request.json` y falla si encuentra cualquiera de estas siete:

| # | Comprobación | Qué significa que falle |
|---|---|---|
| 1 | Ningún criterio sin dato ni justificación | Hay un caso que no se va a poder ejecutar, y se descubre el día de la ejecución |
| 2 | Ningún dato huérfano | O sobra, o hay un criterio que nadie trazó |
| 3 | Ningún derivable en la solicitud | Se está pidiendo trabajo que no hace falta |
| 4 | Ningún dato de otro dueño pedido al cliente | El destinatario tiene que separar lo suyo, y lo ajeno se queda sin canal |
| 5 | Todo dato con sujeto, condición y responsable | Un dato sin condición exigida no es un requisito, es una intención |
| 6 | Toda historia citada existe en el inventario | Caza erratas de identificador antes de que viajen al cliente |
| 7 | Todo dato documentado dice cómo se obtiene | Un "lo montamos nosotros" sin el cómo no lo monta nadie |

La comprobación 1 admite dos salidas, no una: el criterio tiene dato, **o** está en el bloque
de exclusiones con su motivo. Lo que no admite es el silencio.

## El criterio sin dato no siempre es un dato que falta

Cuando la comprobación 1 falla, hay tres desenlaces legítimos y uno ilegítimo:

- **Falta un dato** → se añade a la solicitud. Es el caso del usuario monoempresa.
- **Lo cubre otro rol** → entra al bloque de exclusiones con su responsable, y **su pregunta
  se enruta** por el canal de ese rol. No basta con sacarlo de aquí.
- **El criterio no es verificable** tal como está escrito → es un hallazgo del análisis y va
  a las dudas de la historia, no a la solicitud.
- **Se afloja el criterio para que el dato que hay alcance** → esto es anti-cheating y está
  prohibido por `[[calidad-test-self-correction-loop]]`. El dato se consigue o el caso se
  declara no ejecutable; no se reescribe el criterio para que cuadre.

## Por qué es una dependencia y no un paso

El renderizador **no emite** si la auditoría no pasa. No es una comprobación que se ejecuta
al final y produce un aviso: es la condición de existencia del documento.

Es deliberado, y es la capa 1 de `[[calidad-deterministic-work-to-tooling]]`: nadie olvida
un artefacto del que depende la salida que necesita. La versión anterior de esta regla —una
línea que decía "audita la cobertura antes de emitir"— existió y no se cumplió; hizo falta
que alguien lo pidiera, dos veces, y la segunda después del fallo.

## Lo que la herramienta no decide

Enumerar criterios y cruzarlos es determinista. Lo que sigue exigiendo juicio, y por eso el
inventario deja el campo `verificable` en nulo:

- Si un criterio se puede convertir en aserción sin preguntarle a una persona.
- Si un dato es derivable de otro, o solo lo parece.
- Cuál es la condición exacta que debe cumplir un sujeto para que el criterio se pueda probar.

Eso lo escribe el agente y lo revisa alguien con contexto limpio
(`[[calidad-fresh-context-verification]]`), no el script.
