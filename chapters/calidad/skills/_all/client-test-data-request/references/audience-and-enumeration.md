# La audiencia decide la forma: quien habilita el dato no conoce la historia

## El error que produce la mayoría del reproceso

La solicitud de datos la escribe alguien que acaba de leer trece historias, y la recibe
alguien que no ha leído ninguna y que no las va a leer. Entre esas dos personas hay un
salto que no se cruza con buena voluntad: se cruza cambiando la forma del documento.

Verificado en campo, la primera versión de una solicitud decía cosas como *"cuentas que
cubran cada fila de la tabla de estatus de la HU"*. Es correcta, es trazable, y es
inservible: quien administra el ambiente no tiene la tabla, no sabe cuál es la HU, y no
puede preguntar sin frenar la entrega varios días. La corrección costó un turno entero y
la reescritura completa del documento.

## Las cinco reglas de forma

### 1. Un sujeto por fila, enumerado uno a uno

No se agrupa por referencia a un documento que la audiencia no tiene. Si la tabla de
estados del sistema de origen tiene catorce filas, la solicitud tiene **catorce ítems**,
cada uno con su estado escrito. Aunque sean treinta. La redundancia es el precio de que el
documento se pueda ejecutar sin consultar nada más.

> Mal: "una cuenta por cada estado de la tabla de la historia".
> Bien: catorce filas, de `Cuenta ACTIVA` a `Cuenta con un estado distinto a todos los anteriores`.

### 2. Se pide el estado exigido, no el identificador

Quien administra el ambiente sabe conseguir *"una cuenta con saldo menor al mínimo de la
operación"*. No sabe qué quería decir *"la cuenta 3"*. El identificador concreto lo
devuelve la persona que habilita; la condición la pone quien prueba.

### 3. Cada fila dice para qué sirve

Una fila sin propósito se interpreta ancha o se descarta por rara. La columna que explica
para qué se usa es lo que permite a quien habilita **proponer una alternativa** cuando la
condición exacta no es montable, en vez de contestar que no se puede.

### 4. Nada que no sea del destinatario

Un contrato de servicio es del arquitecto. Una regla de negocio es del PO. Un temporizador
en un archivo de configuración es del desarrollador. Nada de eso entra en la solicitud de
datos, aunque haga falta para probar: mezclarlo hace que el destinatario tenga que separar
lo suyo de lo ajeno, y que lo ajeno se quede sin dueño porque nadie lo enrutó.
El enrutamiento está en `[[calidad-responsibility-routing-of-blockers]]`.

### 5. Lo que resuelve el propio equipo se documenta, no se pide

Hay una categoría intermedia que no es ni del cliente ni descartable: lo que el equipo de
pruebas puede provisionar por su cuenta. Un usuario secundario que se crea desde el
administrador, un perfil que se configura, un estado que se alcanza usando el producto.

Eso **aparece en el documento marcado como propio**, con cómo se obtiene, y no se pide.
Aparece porque quien lea la solicitud tiene que poder ver que ese caso está cubierto; si se
omite, alguien lo va a echar en falta y va a preguntar. En la fuente de datos son ítems con
`documentar: true`, y el renderizador los saca en un bloque aparte de la familia.

## El ambiente se declara en la primera línea, siempre

Una solicitud de datos de prueba que no dice a qué ambiente se refiere es una solicitud que
alguien puede ejecutar en producción. Va en la cabecera, con la negación explícita.

## Lo que la forma no arregla

Ninguna de estas reglas sustituye a la auditoría. Un documento perfectamente enumerado, con
condiciones exactas y ambiente declarado, puede seguir olvidando el caso base — ocurrió: se
pidieron dos usuarios multiempresa y ninguno monoempresa, que era el caso por defecto de
media docena de criterios. Eso lo caza el cruce contra los criterios, no la redacción.
Ver `coverage-audit-ca-to-data.md`.
