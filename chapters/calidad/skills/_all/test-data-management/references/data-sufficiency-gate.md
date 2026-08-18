# Suficiencia de datos: no alcanza con que "haya datos"

## Por qué "sí hay datos" no responde la pregunta

Preguntar *"¿hay datos de prueba en el ambiente?"* y recibir un sí es un dato casi inútil. Los datos existentes son los que necesitaron **las pruebas anteriores**. Los escenarios que se van a escribir necesitan estados concretos —una tarjeta con movimientos en tránsito, una cuenta sin saldo, un usuario con el segundo factor ya inscrito, un contrato vencido— y esos estados o existen o no existen, independientemente de que el catálogo esté lleno.

El fallo que produce saltarse esto es el más caro de todos: **la suite se pone roja por dato y parece un defecto**. Se investiga la aplicación, se escala al equipo de desarrollo, y varias horas después resulta que la entidad no estaba en el estado que el escenario asumía.

Y tiene un agravante de calendario: conseguir un dato en un ambiente de pruebas de un cliente no es instantáneo. Puede exigir un trámite, una carga en base de datos, la intervención de otro equipo o esperar a un proceso nocturno. Descubrirlo el día de la ejecución convierte un trámite de tres días en un bloqueo de la entrega.

## La matriz se deriva de los escenarios, no del catálogo

Se construye **después** de planificar los escenarios y **antes** de emitir la estrategia o escribir el primer archivo. Una fila por dato que algún escenario necesita:

| Escenario | Dato requerido | Estado que exige | Existe en el ambiente | Quién lo gestiona | Cuándo se necesita |
|---|---|---|---|---|---|
| Detalle de movimiento en tránsito | tarjeta de crédito | con al menos un movimiento en tránsito y su fecha de vencimiento | **no verificado** | QA de la célula | antes del primer smoke |
| Rechazo por saldo insuficiente | cuenta de ahorros | saldo menor al monto mínimo de la operación | sí, en el catálogo | — | — |
| Autenticación reforzada | usuario de prueba | con segundo factor inscrito y activo | **no** | equipo de canales | 3 días antes de la ejecución |

Tres columnas hacen el trabajo y son las que se suelen omitir:

- **Estado que exige**, no solo el tipo de entidad. "Una tarjeta" no es un requisito; "una tarjeta con movimientos en tránsito" sí.
- **Quién lo gestiona**, porque un dato sin dueño no se consigue.
- **Cuándo se necesita**, contado hacia atrás desde la ejecución, no desde hoy.

## Lo que se le dice al QA, y cuándo

En cuanto la matriz tiene una fila sin resolver, **se comunica en el chat de forma explícita y accionable**, sin esperar a la entrega. No es un aviso: es un pedido con fecha.

> Para automatizar estos escenarios necesito estos datos en el ambiente de pruebas:
>
> 1. **Tarjeta de crédito con al menos un movimiento en tránsito** y su fecha de vencimiento asociada — la necesito antes del primer smoke. Sin esto, los tres escenarios del detalle no se pueden ejecutar.
> 2. **Usuario con segundo factor inscrito y activo** — la inscripción la hace el equipo de canales y suele tardar; conviene pedirla ya.
> 3. **Cuenta con saldo menor al mínimo de la operación** — si no existe, sirve cualquier cuenta a la que se le pueda dejar el saldo por debajo del mínimo.
>
> De estos, el segundo depende de otro equipo. Los otros dos los puede resolver la célula.

Reglas de ese mensaje:

- **Se piden estados, no identificadores.** El QA sabe conseguir "una cuenta sin saldo"; no adivina qué quería decir "la cuenta 3".
- **Se dice qué escenarios quedan bloqueados** por cada dato. Convierte una lista de pedidos en una decisión de alcance.
- **Se separa lo que resuelve la célula de lo que depende de terceros.** Lo segundo se pide primero, aunque se necesite después.
- **Nunca se transcribe una credencial** en el mensaje ni en ningún artefacto: se marca como recibida.

## Mock y ejecución real no tienen el mismo contrato

La estrategia de datos depende de contra qué se ejecuta, y confundirlas produce entregas que aparentan cobertura que no existe.

| | Contra mocks (`execution_target: mock` o `hybrid`) | Contra software ya desarrollado (`real`) |
|---|---|---|
| Origen del dato | Se puede **sintetizar** para desbloquear el trabajo | Debe **existir en el ambiente**; no hay atajo |
| Qué valida la corrida | La mecánica de la suite y el contrato acordado, no el comportamiento real | El comportamiento real del producto |
| Si el dato falta | Se sintetiza y se **declara como sintético** | Es un **bloqueo con fecha**, se escala y se planifica |
| Al cierre | El delivery gate declara `pending_real_integration` y qué queda sin validar | La entrega no se cierra con datos inventados |

**El dato sintético es temporal por definición.** Se registra como tal en la evidencia junto con qué escenarios lo usan, para que la re-ejecución contra el ambiente real sepa exactamente qué revisar. Un dato sintético que sobrevive silenciosamente a la llegada del software real produce una suite verde que nunca ejercitó el producto.

**Contra software ya desarrollado, sintetizar es anti-cheating.** Inventar una entidad, o ablandar la aserción para que pase con la que hay, es exactamente el patrón que el chapter prohíbe: el test deja de verificar lo que dice verificar.

## Validación cruzada contra el catálogo

Todo valor que el usuario indique se cruza contra el catálogo de datos del proyecto antes de generar. Si no aparece, **se detiene y se pregunta**, listando lo disponible: *"no encontré la entidad X para el usuario Y; las disponibles son [...]. ¿Usamos una de estas o actualizamos el catálogo?"*.

Verificado en campo: los identificadores que indicó el usuario no coincidían con ninguna entrada del catálogo del proyecto y los steps existentes usaban otro valor. Generar sin cruzarlo habría producido una suite roja por dato.

Y al revés: **el catálogo del proyecto tampoco es autoridad final**. Puede estar desactualizado; quien sabe qué sigue vigente en el ambiente es el QA. El catálogo se usa para detectar la discrepancia, no para resolverla en silencio.

## Salida y enganche

La matriz se persiste con el resto de la evidencia de la corrida y se registra como fase del pipeline, de modo que al retomar la sesión no se reconstruya de memoria. Ninguna generación arranca con filas en estado desconocido: o el dato está confirmado, o está declarado como sintético con su alcance, o es un bloqueo comunicado con fecha y dueño.

## Cross-links

- `test-data-strategies.md` — estrategias por tipo de dato.
- `synthetic-data-faker.md` — cómo se sintetiza cuando corresponde.
- `datasets-versioning.md` — versionado del catálogo.
- `[[calidad-mandatory-inputs-protocol]]` — el checkpoint de datos que invoca esta matriz.
- `[[calidad-sut-readiness-gate]]` — resuelve `execution_target`, que decide qué columna de la tabla aplica.
- `[[calidad-automation-feasibility-assessment]]` — un dato imposible de obtener es una causa legítima de no automatizable.
- `[[calidad-delivery-gate-contract]]` — dónde se declara el dato sintético y lo que queda sin validar.
