# Lo que no se pide: derivables, y de otro dueño

## Por qué importa recortar

Cada fila de una solicitud de datos cuesta trabajo de alguien en el cliente, y una solicitud
inflada se atiende peor que una corta: la que trae treinta ítems de los cuales seis sobran
se retrasa entera mientras alguien decide qué hacer con los seis.

Hay dos motivos para que un dato no entre, y son distintos.

## Derivable: se produce usando otro dato ya pedido

Un dato es derivable cuando **existe un camino desde otro dato de la lista hasta él**, y ese
camino lo puede recorrer quien prueba, sin permisos ni intervención de nadie.

| Se pidió | Lo que NO hace falta pedir | Por qué |
|---|---|---|
| Un usuario con clave válida | Un usuario "recién autenticado" | Se autentica el que ya se pidió |
| Un usuario con clave válida | Un usuario "con conexión previa registrada" | Aparece cuando entra por segunda vez |
| Un usuario con segundo factor operativo | Un usuario "en zona reconocida" | Es el estado en el que queda al recorrer el flujo |
| Una cuenta que admite movimientos | Una cuenta "con saldo por debajo del mínimo" | Se deja el saldo ahí operando |

La prueba de que es derivable: **se puede escribir la precondición del caso** —"partiendo de
A1, autenticar"— sin pedirle nada a nadie. Si para llegar hace falta un permiso, un proceso
nocturno o un tercero, **no es derivable**: es un dato, y se pide.

En la fuente de datos esto es el campo `derivado_de`. Un ítem con ese campo poblado **no
puede estar en la solicitud**: el verificador lo rechaza y el renderizador no emite. Su
lugar es el bloque de exclusiones, que existe para que nadie gaste tiempo consiguiéndolo.

## De otro dueño: se resuelve, pero por otro canal

El segundo motivo no es que el dato sobre, sino que el destinatario no es quien lo tiene.
Un contrato de servicio, un parámetro de una consola de administración, una regla de negocio
sin definir, un temporizador de configuración, un binario firmado. Todo eso hace falta para
probar y nada de eso se le pide a quien administra usuarios y productos.

La diferencia práctica: **un derivable desaparece del proceso; un dato de otro dueño cambia
de canal**. El segundo sigue vivo, con su dueño, en el registro que le corresponde — la duda
de refinamiento, la pregunta al arquitecto, la tarea de desarrollo. Perderlo por sacarlo de
la solicitud es el fallo simétrico al de meterlo.

## El bloque de exclusiones no es opcional

Termina el documento y hace un trabajo concreto: **corta la pregunta antes de que se haga**.
Sin él, quien recibe la solicitud ve que falta el usuario recién autenticado, no sabe si es
un olvido, y escribe un correo. Con él, lee que se deriva de A1 y sigue.

Cada línea dice qué es y por qué no se pide: derivado de tal ítem, o resuelto por tal rol.
Nunca sin motivo.
