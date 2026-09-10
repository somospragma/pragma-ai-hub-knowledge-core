# El destino es un ticket, y eso cambia el markdown

## Por qué está aquí

La solicitud no se entrega como archivo: se sube al gestor de incidencias del cliente, donde
queda enlazada a las historias que la necesitan. Ese renderizador no es el de un repositorio,
y las diferencias no son cosméticas — un documento que se ve bien en el editor puede llegar
partido en dos al ticket.

## Reglas que el renderizador aplica

| Regla | Por qué |
|---|---|
| **La cabecera va en líneas de clave en negrita**, una por línea, no en una sola con separadores | Los separadores intermedios se comen el salto y la cabecera queda en un párrafo ilegible |
| **Las citas llevan la barra vertical también en la línea en blanco** (`>` sola entre párrafos) | Sin ella la cita se parte y el segundo párrafo sale como texto normal |
| **Los identificadores viajan como enlace completo**, no como texto suelto | Quien lee la solicitud en el ticket tiene que poder abrir la historia; el identificador solo no es navegable |
| **Las viñetas usan asterisco** | Es la forma que el gestor renderiza sin ambigüedad en listas anidadas |
| **El identificador de cada fila va en negrita** | La tabla se lee por identificador y es la columna que se cita en el resto del documento |
| **Sin HTML, sin notas al pie, sin listas de definición** | No sobreviven a la conversión |
| **Las tablas no se alinean con espacios** | El ancho no se conserva; alinear solo engorda el documento fuente |

## Lo que sigue viviendo en el repositorio

El markdown emitido se conserva en `.evidence/` aunque su destino sea el ticket: es la
evidencia de qué se pidió y cuándo, y es lo que la siguiente sesión lee para saber qué está
pendiente de llegar. El ticket es el canal, no el sistema de registro.

## La subida es una escritura en el ALM

Crear el ticket, adjuntar el contenido y **vincularlo a cada historia** son escrituras, y
pasan por la ficha de `[[calidad-alm-write-authorization-gate]]`: autorización explícita,
previa, específica y con conteo. Verificado en campo, la vinculación de una solicitud a sus
trece historias fueron doce enlaces creados en una operación autorizada — y el borrado de un
enlace es otra escritura, que exige su propia autorización.

Qué tipo de enlace usa cada cuenta y con qué credencial es conocimiento de cuenta, no del
chapter: se consulta en el mapa de capacidades del ALM de esa cuenta.
