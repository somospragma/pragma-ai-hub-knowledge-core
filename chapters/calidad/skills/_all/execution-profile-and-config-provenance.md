---
id: calidad-execution-profile-and-config-provenance
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "El interruptor único que decide contra qué aplicativo corre la suite y de dónde salen sus datos, por qué el perfil y el destino de ejecución son ejes distintos, cómo entra la configuración desde la canalización, y la única barrera que de verdad protege: la que mira contra qué corrió. Consultar al montar la ejecución de una suite que se construye contra simulado y se valida contra real."
tags: [perfiles, configuracion, ambientes, procedencia, pipeline, datos, simulado, gate, universal]
---

# Perfil de Ejecución y Procedencia de la Configuración

## Problema que resuelve

El fallo que este asset existe para impedir es uno solo: **la suite en verde
contra el aplicativo equivocado, o con los datos equivocados, sin que nada
avise.**

Aparece siempre que la automatización se construye antes que el desarrollo —
contra un aplicativo simulado— y luego tiene que validar el real. Y aparece
también sin simulados, en cuanto una variable puede venir de tres sitios y nadie
declaró cuál manda.

## Cuándo aplicar

Al montar la ejecución de cualquier suite que corra contra más de un ambiente o
más de un juego de datos, y al integrarla en una canalización. Complementa a
`[[calidad-execution-preflight]]`, que demuestra que la corrida **toca** un SUT;
esto decide **cuál** y lo comprueba después.

## 1. Un interruptor, obligatorio y sin valor por defecto

```
--profile local | dev | qa
```

Decide **las dos cosas a la vez**: a qué apunta la corrida y de dónde salen sus
datos. Con dos interruptores separados sería expresable «perfil real con datos
del simulado», que es exactamente la combinación que nunca debe ocurrir.

**Sin valor por defecto, a propósito.** Una canalización que se olvide de
declararlo falla de inmediato nombrando los perfiles válidos, en vez de caer en
el simulado y reportar verde contra nada.

En un entorno de integración continua, el runner además **rechaza cualquier
perfil simulado**: la canalización nunca ejecuta contra un aplicativo que no es
el que se está certificando.

## 2. El perfil y el destino de ejecución son ejes ortogonales

Se confunden porque suenan parecido, y la confusión sale cara.

| Eje | Pregunta que responde | Valores |
|---|---|---|
| **Perfil** | ¿contra qué aplicativo y con qué datos? | simulado / integración / certificación |
| **Destino** | ¿dónde corre el navegador o el dispositivo? | propio / granja |

Se puede correr el perfil de certificación en un dispositivo propio, y el perfil
simulado en la granja. Un nombre como «modo local» para el segundo eje invita
a leerlo como el primero — **el nombre del eje dice qué decide**.

Y un simulado, en front, no es interceptar tráfico: es **apuntar a otra URL** en
web e **instalar otra aplicación** en móvil. El flujo de la prueba es idéntico.
Las variables admiten sufijo de perfil con caída a la variable sin sufijo, de
modo que en local se declaran ambas y basta cambiar de perfil, mientras la
canalización declara la de su ambiente a secas.

> El identificador de paquete también se resuelve por perfil: una compilación
> simulada suele publicarse con otro identificador para poder convivir con la
> real en el mismo dispositivo.

## 3. El dato sigue al perfil, y el escenario no se entera

El mismo escenario, el mismo step, el mismo nombre de dato. **Promover de
simulado a real no toca el `.feature`** — que es lo que mantiene alineado lo que
corre en local con lo que corre en la canalización.

Y la excepción se declara en vez de recordarse:

| Etiqueta | Qué significa |
|---|---|
| *(por defecto)* | El escenario necesita un sujeto real del catálogo |
| `@datos:sinteticos` | Funciona con datos inventados **también contra el aplicativo real** |

La segunda es mayoría y suele olvidarse: los negativos, las validaciones de
formato y los límites no necesitan un sujeto real. Declararlo la convierte en
una propiedad del escenario en lugar de una excepción que alguien recuerda.

## 4. El ciclo de vida se ata al perfil, no a una lista de exclusión

Un escenario en construcción **corre solo con el perfil simulado**. No hace falta
una lista de exclusión en la canalización: la regla vive en el runner y aplica
igual desde cualquier sitio.

Promover es **quitar la etiqueta**, y el criterio es verificable — corrió verde
con el perfil real. El gate informa cuántos escenarios siguen en construcción,
para que la deuda sea visible en vez de silenciosa.

## 5. Tres barreras, y la que vale mira el resultado

| # | Barrera | Qué comprueba | Qué deja pasar |
|---|---|---|---|
| 1 | **Intención** | el perfil se declaró y es válido | un perfil correcto mal configurado |
| 2 | **Configuración** | la URL o el artefacto del perfil existen, y si faltan **el error nombra la variable buscada** | una variable presente con el valor de otro ambiente |
| 3 | **Resultado** | contra qué corrió de verdad | — |

**La tercera es la única que protege**, porque no confía en que nadie se
equivocó: mira lo que ocurrió. En web, recoger los hosts que la corrida contactó
y contrastarlos con el perfil. En móvil, verificar qué aplicación se instaló.

Y falla **en las dos direcciones**: un perfil real que tocó una dirección local,
y un perfil simulado que salió a un host externo — el segundo arriesga dejar
datos en un ambiente compartido.

Declarar sus límites es parte de tenerla: un escenario que no llama a red no
aporta nada que contrastar y **no debe fallar por ello**, porque asumir lo peor
produce falsos negativos. Y en móvil la barrera es más débil que en web: si
alguien publica el artefacto simulado con el identificador del real, desde el
arnés no hay forma de detectarlo. Escribirlo evita confiar de más en ella.

## 6. La configuración entra por una lista versionada, no por el YAML

El patrón habitual —un bloque de variables por cada paso que ejecuta pruebas,
mapeadas una a una— tiene un problema que no es de estilo: **una variable
ausente no rompe la canalización.** La prueba corre sin ella y el fallo aparece
más tarde disfrazado de otra cosa. Y como la lista está repetida en tantos
sitios como pasos haya, basta olvidarla en uno.

No es hipotético: en un arquetipo real, los bloques inyectaban tres variables
que **ningún archivo del repositorio leía**, mientras las que el código sí leía
no las inyectaba nadie. Dos listas que tienen que coincidir, y nada que
compruebe que coinciden.

**La configuración entra por un archivo versionado de marcadores**, que la
canalización sustituye antes de ejecutar nada. Se versiona porque **lo que
contiene es la lista, no los valores**: añadir una variable es añadir su línea y
darla de alta donde vivan los valores, y la línea se revisa en el PR como
cualquier otro cambio.

En el YAML queda solo lo que es propio de *correr en la canalización* y no
describe ningún ambiente — incluido, deliberadamente, **el interruptor que
autoriza a escribir en el ALM**: ese permiso tiene que ser una decisión de la
canalización, no de un archivo de configuración
(`[[calidad-alm-write-authorization-gate]]`).

### Procedencia antes que especificidad

Cuando una variable puede venir de varios sitios y además tener variante por
ambiente, hay que ordenar por dos criterios a la vez. **Manda la procedencia; la
especificidad desempata dentro de ella.**

| # | Procedencia | Típicamente |
|---|---|---|
| 1 | entorno del proceso | lo que exporta alguien para probar algo puntual |
| 2 | canalización | el archivo ya sustituido |
| 3 | repositorio | el archivo local de quien desarrolla |

Al revés —que la más específica gane siempre— una variante de ambiente olvidada
en el archivo local de alguien le ganaría a la que inyecta la canalización, y la
corrida iría a otro ambiente sin que nada avise. Es justo el fallo silencioso
que todo esto viene a cerrar.

### Un marcador sin sustituir es una variable ausente, no un valor

Si la variable no existe donde viven los valores, la tarea deja el marcador
literal. **El cargador tiene que reconocer esa forma y descartar el valor**,
cayendo a la siguiente procedencia.

Sin eso, la variable vale la cadena del marcador y el síntoma es un error de
conexión que no menciona la configuración, mandando a investigar al sitio
equivocado.

> **Trampa de sintaxis, comprobada:** los cargadores de archivos de entorno
> tratan `#` como inicio de comentario. Un marcador sin comillas se parsea como
> **cadena vacía** — la variable llega vacía, no ausente, y ningún mecanismo se
> entera, porque no queda marcador que detectar. Van entrecomillados.

### La verificación corre antes de la suite, en cada job

Un comando que liste qué variables llegaron, **de dónde salió cada una**, y
cuáles faltan. Corre antes de la suite en cada job: una variable ausente cuesta
un minuto y no veinte. Y el archivo de marcadores hay que sustituirlo en cada
job, porque cada uno corre en un agente limpio.

Esa misma procedencia va **en el resumen de la corrida**: es lo que permite
contrastar por qué la misma petición devuelve un código desde una máquina y otro
desde el agente. De las direcciones se guarda el valor; de lo demás **solo si
llegó**, porque ahí hay claves y contraseñas y el resumen acaba publicado.

## 7. Qué merece una comprobación propia: ¿su fallo es silencioso?

Todo lo anterior son mecanismos que **al romperse dejan la suite en verde**. Esa
propiedad es la que decide si hace falta una comprobación dedicada, y es el único
criterio que hace falta:

> **Si romperlo hace que algo reviente, no necesita red**: la primera ejecución
> lo dice, o el compilador. **Si romperlo deja la suite en verde contra el sitio
> o los datos equivocados, sí.**

Aplicado a un repositorio de pruebas, ese criterio deja fuera casi todo —un
locator que no resuelve revienta, un step sin implementar revienta, un tipo mal
puesto no compila— y deja dentro dos cosas: **la precedencia entre procedencias**
y **la asimetría del respaldo simulado**. Ocho casos, no una capa de pruebas
unitarias por la puerta de atrás.

Tres propiedades que hacen que esa comprobación se siga creyendo a los dos meses:

1. **La lógica se expone como funciones puras.** La comprobación no lee el
   archivo de entorno, no lee los datos de prueba y no toca el proceso. Si
   dependiera del estado real diría cosas distintas en cada máquina, y una
   comprobación que a veces pasa por motivos ajenos deja de creerse.
2. **Cada caso declara qué se rompería**, y eso es lo que imprime al fallar. Un
   «esperado / obtenido» a secas obliga a reconstruir por qué importaba; el
   mensaje tiene que decir la consecuencia — *«un valor olvidado en el archivo de
   alguien mandaría la corrida a otro ambiente, en verde»*.
3. **Hay que verificar la verificación.** Al montarla se rompen a propósito los
   mecanismos que cubre y se comprueba que los detecta y devuelve error. Una
   comprobación que nadie ha visto fallar no prueba nada, y el ejercicio se
   repite cada vez que se añade un caso.

Su punto débil, que conviene tener presente al revisar un PR: **nada obliga
automáticamente a añadir el caso** cuando se añade un mecanismo silencioso nuevo.

## Restricciones

- **NUNCA des un valor por defecto al perfil.** Un olvido tiene que fallar, no
  caer en el simulado.
- **NUNCA separes en dos interruptores «contra qué apunta» y «de dónde salen los
  datos»**: la combinación prohibida deja de serlo.
- **NUNCA uses el mismo nombre para el eje del aplicativo y el del destino de
  ejecución.**
- **NUNCA confíes solo en las barreras de intención y de configuración.** La que
  protege es la que mira contra qué corrió de verdad.
- **NUNCA inyectes la configuración con una lista repetida por paso**: es una
  lista que nadie compara con la que el código lee.
- **NUNCA dejes que un marcador sin sustituir llegue como valor.**
- **NUNCA publiques el valor de un secreto en el resumen de procedencia** — solo
  si llegó.

## Cross-links

- `[[calidad-execution-preflight]]` — demuestra que la corrida toca un SUT; este
  asset decide cuál y lo verifica después.
- `[[calidad-test-data-management]]` — de dónde sale cada dato, y por qué el
  respaldo sintético es una clave aparte.
- `[[calidad-sut-readiness-gate]]` — cuándo un ambiente está listo para recibir
  la corrida.
- `[[calidad-alm-write-authorization-gate]]` — por qué el permiso de escribir en
  el ALM viaja en la canalización.
- `[[calidad-delivery-gate-contract]]` — qué merece una comprobación propia.
- `[[calidad-wait-cost-and-timeout-design]]` — el otro sitio donde un valor
  escrito a mano decide en silencio.
