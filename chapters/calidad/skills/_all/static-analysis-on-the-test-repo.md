---
id: calidad-static-analysis-on-the-test-repo
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Qué hacer cuando el repositorio de pruebas —no el SUT— pasa por el análisis estático y la puerta de calidad del cliente: cobertura declarada en vez de cero, vulnerabilidades transitivas, cuándo el arreglo que sugiere la regla cambia el comportamiento, y por qué un error de análisis no es un archivo limpio. Consultar antes de la primera integración de un repositorio de pruebas en la canalización del cliente."
tags: [analisis-estatico, sonarqube, checkmarx, quality-gate, dependencias, cobertura, pipeline, brownfield, universal]
---

# Análisis Estático sobre el Propio Repositorio de Pruebas

> **Esto no va del SUT.** El análisis de seguridad y calidad **de la aplicación
> bajo prueba** vive en `[[calidad-security-testing]]` y
> `[[calidad-cicd-integration]]`. Aquí el sujeto analizado es **el repositorio de
> automatización**, que en la canalización del cliente pasa por la misma puerta
> que el código de producto — y falla la primera vez.

## Cuándo aplicar

Antes de la primera integración de un repositorio de pruebas en la canalización
del cliente, y cada vez que la puerta de calidad lo rechace. Es una fase del
`[[calidad-delivery-gate-contract]]`, no un extra: un arquetipo que no integra no
se entrega.

## Por qué existe

Un repositorio de pruebas nuevo se somete a la misma puerta que el producto —
cero incidencias nuevas, cero puntos calientes sin revisar, umbral de
vulnerabilidades— y **la primera pasada las falla todas**. Medido en un
arquetipo real: 177 incidencias, 7 puntos calientes y 5 vulnerabilidades.

Casi nada de eso es deuda del arquetipo. Es la diferencia entre lo que un
analizador espera de un repositorio y lo que un repositorio de pruebas es, más
un herramental de desarrollo que cambia cada semana por su cuenta. Presupuestar
esta fase evita que la entrega se atasque en la última semana.

## 1. La cobertura se declara excluida, no se deja en cero

Un repositorio de pruebas **es** las pruebas. Pedirle cobertura de unitarias es
un error de categoría: el número saldría de escribir pruebas de las pruebas. Su
verificación es ejecutarlo contra la aplicación real.

Pero **dejarlo implícito es dejar una mina**: un 0 % se lee como regresión, y en
cuanto alguien añada una condición de cobertura a la puerta, el build cae por
algo que nunca tuvo sentido medir. Se declara la exclusión total de cobertura,
con el motivo escrito al lado.

Esto no dice que no haya nada que comprobar. Dice **dónde** se comprueba:

| Qué | Dónde se verifica |
|---|---|
| Que un locator resuelve, que un step existe, que un tipo cuadra | La primera ejecución, y el compilador |
| La lógica cuyo fallo **no se nota** — precedencia de configuración, resolución de datos por perfil | Una autocomprobación pequeña y dedicada (`[[calidad-execution-profile-and-config-provenance]]`) |
| Que la suite prueba lo que dice | Ejecutarla contra el SUT |

Y si el proyecto **sí** mide cobertura sobre parte del árbol, hay que mirar
dónde antes de escribir una prueba unitaria: un objeto de pantalla suele estar
excluido —es casi todo selectores y llamadas al driver, y mockearlo entero
prueba el mock—, mientras la lógica que decide algo sí cuenta. Escribir pruebas
en la zona excluida es esfuerzo que no aparece en ninguna métrica y que la
primera ejecución ya cubría.

## 2. Vulnerabilidades: casi todas son transitivas y de herramental

Lo que el análisis de composición encuentra en un repositorio de pruebas suele
estar en dependencias **de desarrollo** —el runner, el driver, el linter— de un
repositorio que **no publica ningún artefacto**. Eso no las hace inocuas, pero sí
cambia la conversación.

Reglas de trabajo:

- **Actualizar aguas arriba a menudo no resuelve nada.** Si la versión más
  reciente del paquete de arriba sigue declarando la versión vulnerable, subirlo
  no cambia el árbol. Ahí se fija la versión con el mecanismo de sustitución del
  gestor de paquetes.
- **Una sustitución fuerza una versión que el paquete de arriba no declaró**, así
  que **cada una se verifica ejecutando** —que la librería carga y expone lo que
  se usa, que la suite pasa entera—, no leyendo el manifiesto.
- **Es deuda con fecha.** Cuando el paquete de arriba actualice, sobra. Antes de
  quitar una, comprobar qué versión resuelve ya el árbol; no borrarla y confiar.
- **Cuando no hay versión corregida, sacar el paquete del árbol** —subiendo al
  que dejó de usarlo— antes que silenciarlo con una exención. Una exención
  caduca sin que nadie se entere; una dependencia que ya no está, no vuelve.
- **La puerta se abrirá sola.** Un aviso publicado entre un escaneo y el
  siguiente vuelve a poner en rojo una rama que nadie tocó, y la base de datos
  del escáner comercial va por delante de la del gestor de paquetes, así que la
  comprobación local no sirve de red. Se corrige cada hallazgo cuando aparece.
- **Ajustar el alcance del análisis a las dependencias de producción es una
  decisión de la política de seguridad del cliente**, no del repositorio. Se
  plantea a quien la administra, con el dato: cuántas dependencias de producción
  hay y qué publica el repositorio.

## 3. El arreglo que sugiere la regla es una sugerencia, no una especificación

El caso más caro de esta fase no es la incidencia: es **corregirla como el
mensaje indica y cambiar el comportamiento sin querer**. Tres formas verificadas
en campo:

| La regla pide | Por qué el arreglo obvio está mal | Qué se hizo |
|---|---|---|
| Quitar la espera sobre algo que el tipo no declara como promesa | La librería devuelve un encadenable que **en ejecución sí lo es**; quitarla cambia el arnés a ciegas, sin dispositivo donde comprobarlo | Envolver en una función que devuelve una promesa de verdad: el tipo satisface la regla y no cambia nada de lo que ocurre |
| Usar la comparación sensible a configuración regional al ordenar | Ese orden alimenta archivos generados que CI compara **byte a byte**; cambiaría entre máquinas y rompería la comprobación sin que nada estuviera mal | Comparador explícito equivalente al que había |
| Sustituir el operador de alternativa por el de nulidad | Con el segundo, la **cadena vacía deja de caer** al siguiente valor — y ahí eso era el caso a cubrir | Se deja como está, con el motivo escrito |

La prueba de que un refactor no cambió nada **es un artefacto idéntico**: si el
cambio toca un generador, que su salida siga byte a byte igual es lo que lo
demuestra. Sin esa comprobación, «no cambia nada» es una opinión.

Y hay una decisión legítima que conviene no confundir con conveniencia:
**ignorar una regla que produce falsos positivos por el idioma en que se escribe
el código.** Una regla que busca un marcador en inglés dispara sobre palabras
españolas corrientes. La alternativa sería escribir peor español para complacer
al analizador. Se ignora **con el motivo escrito al lado de la exclusión** — no
en un mensaje de commit, donde nadie lo va a buscar.

## 4. El inventario exacto se pide al servidor, no se reproduce en local

Reproducir las reglas en local llega a una parte del total y no dice cuál falta.
El resto sale de **preguntarle al analizador por su API**, por la rama o el PR
concretos.

La razón es concreta: **una versión nueva del analizador trae familias de reglas
nuevas** que ningún análisis local trae por defecto —modernización de la
sintaxis del lenguaje, sobre todo—, y son mayoría en la primera pasada. Sin el
inventario del servidor, se corrige lo reproducible y la puerta sigue en rojo.

> **Un error de análisis no es «archivo sin problemas»: es «archivo sin
> revisar».** Es la trampa que deja un hallazgo vivo tras una corrección
> completa. Si el analizador local no puede parsear un archivo —porque la
> configuración del parser no lo incluye— no emite hallazgos sobre él, y esa
> ausencia se lee como limpieza. Contrastar el listado del servidor **archivo a
> archivo**, no solo por conteo de regla.

## 5. Las convenciones que salen de las correcciones se hacen cumplir

Toda corrección que deja una convención para el código nuevo —un prefijo de
importación, un envoltorio, un comparador explícito— **se cablea en el linter**,
no se escribe en un documento.

Escrita solo en un documento dura lo que tarde alguien en no leerlo, y el aviso
llega días después, en una canalización ajena, sin decir cuál de los archivos la
rompió. Cada regla nombra su reemplazo en el mensaje.

Dos detalles que se escapan al cablearlas:

- La restricción sobre importaciones **solo ve las declaraciones de importación**.
  Los ficheros que cargan módulos por llamada necesitan su propio selector, con
  la misma lista de nombres — no una copia, que deriva.
- El bloque de reglas suele aplicarse solo al lenguaje principal. Los pocos
  archivos del otro lenguaje del repositorio **el análisis de la canalización los
  mira igual**.

## 6. Lo que el repositorio no puede garantizar

El archivo de configuración del analizador **solo tiene efecto si el escáner lo
lee**. Cuando la canalización usa una plantilla compartida del área de DevOps,
esa plantilla puede pasar sus propias propiedades, que tienen precedencia. Es un
punto a acordar con quien la administra, y se reporta como tal en vez de
diagnosticarlo diez veces.

## Restricciones

- **NUNCA dejes la cobertura de un repositorio de pruebas implícita en cero.** Se
  declara excluida, con el motivo.
- **NUNCA silencies una vulnerabilidad con una exención** cuando se puede sacar
  el paquete del árbol.
- **NUNCA des por buena una sustitución de versión leyendo el manifiesto**: se
  verifica ejecutando.
- **NUNCA apliques el arreglo que sugiere una regla sin preguntarte qué cambia**,
  y sin una comprobación que demuestre que no cambió nada.
- **NUNCA leas un error de análisis como un archivo sin hallazgos.**
- **NUNCA dejes una convención nueva solo escrita en un documento** cuando el
  linter puede hacerla cumplir.
- **NUNCA escribas una prueba unitaria sin mirar en qué lado de las exclusiones
  de cobertura cae el archivo.**

## Cross-links

- `[[calidad-delivery-gate-contract]]` — pasar la puerta del cliente forma parte
  de la entrega, y el criterio de qué merece una comprobación vive ahí.
- `[[calidad-cicd-integration]]` — las puertas sobre el SUT, que son otra cosa.
- `[[calidad-security-testing]]` — SAST, SCA y DAST aplicados a la aplicación.
- `[[calidad-measure-before-proposing]]` — la batería sobre un repositorio
  heredado incluye buscar secretos versionados, que es lo primero que el análisis
  encuentra.
- `[[calidad-brownfield-vs-greenfield]]` — qué se puede corregir y qué se
  reporta.
