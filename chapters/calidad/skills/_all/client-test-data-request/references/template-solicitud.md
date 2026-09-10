# Solicitud de datos de prueba a {{meta.cliente}} — {{meta.segmento}}

**Fecha:** {{meta.fecha}}
**Solicita:** {{meta.solicita}}
**Ambiente:** **{{meta.ambiente}}** (NO producción)

## Cómo leer este documento

Esta es una lista de **usuarios y productos de prueba** que necesitamos habilitar en el
ambiente. Está escrita para quien administra usuarios y productos; **no hace falta conocer
las historias de usuario (HU)**.

Cada fila describe **un sujeto concreto y la condición que debe cumplir**. La columna **HU**
indica a qué historia sirve cada dato, solo como referencia de trazabilidad.

### Notas generales

<!-- slot:notas -->

### Referencia de HU

<!-- slot:historias -->

---

<!-- slot:familias -->

---

# Resumen para quien habilita

<!-- slot:resumen -->

### Puntos a confirmar

Si algo no se puede montar en el ambiente, indíquenlo para buscar una alternativa:

<!-- slot:confirmar -->

---

# Auditoría: cada HU tiene datos para ejecutar sus casos

Cruce de los criterios de aceptación (CA) de cada HU contra los datos pedidos. Se genera con
la herramienta, no a mano: es lo que garantiza que no falte un caso base.

<!-- slot:auditoria -->

## Datos que NO se piden

Se derivan de otro dato ya pedido, o son responsabilidad de otro rol:

<!-- slot:fuera -->

<!-- slot:cierre -->
