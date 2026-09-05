---
id: calidad-wait-cost-and-timeout-design
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Los cinco temporizadores disfrazados que dominan el reloj de una suite E2E — espera opcional con techo largo, predicado usado como espera, sondeo en serie, pausa ciega y umbral escrito a mano — cómo inventariarlos, y por qué el timeout de un step tiene que superar sus esperas internas. Consultar al escribir cualquier espera y ante una suite lenta o intermitente."
tags: [esperas, timeouts, rendimiento, flakiness, e2e, mobile, web, granja, brownfield, universal]
---

# Wait Cost and Timeout Design — Los Temporizadores que Nadie Declaró

## Problema que resuelve

En una suite E2E el reloj no se va donde uno cree. Medido sobre una corrida real
de un escenario móvil cross-device:

| Tramo | Tiempo | % |
|---|---:|---:|
| Creación de sesiones | 45,9 s | 14 % |
| Precondición de negocio | 177,1 s | 54 % |
| Navegación y preparación | 67,0 s | 20 % |
| **Lo que la historia certifica** | **27,6 s** | **8 %** |
| Teardown | 9,2 s | 3 % |

**89 % es montaje.** Y buena parte de ese montaje no es trabajo: son esperas que
se pagan completas sin que nadie las haya pedido. En la misma suite aparecieron
30 segundos exactos, en cada corrida y en las dos plataformas, esperando un
elemento que nunca iba a existir.

Ninguno de estos costes se ve leyendo el código: **todos parecen una espera
prudente.** Se ven midiendo, y por eso este asset es la contraparte en tiempo de
ejecución de `[[calidad-measure-before-proposing]]`.

## Cuándo aplicar

- Al escribir cualquier espera, en cualquier stack.
- Cuando una suite heredada va lenta y hay que decir por qué con números.
- Cuando un escenario pasa en local y falla en la granja, o pasa en un
  dispositivo y falla en otro.
- Antes de proponer paralelismo o reducción de alcance para "que la suite corra
  en menos tiempo": puede que el tiempo no esté donde se supone.

## Los cinco temporizadores disfrazados

### 1. La espera opcional con techo largo

Un elemento que **puede** aparecer, esperado con un techo generoso:

```
esperarQueAparezca(cerrarModal, 15 s).sino(seguir)
```

Cuando el elemento aparece, el techo es un techo. Cuando **no** aparece —que es
el caso normal para lo opcional— el techo deja de ser un límite y se convierte en
**la duración**. Es coste fijo del camino feliz, pagado en cada corrida.

Es el peor de los cinco porque se escribe con la mejor intención y nunca falla:
la suite queda en verde, sólo que lenta.

**Corrección**: una espera opcional corre **contra el desenlace alternativo**, no
contra el reloj. Se espera *o bien el modal, o bien el elemento del paso
siguiente*, y termina en cuanto se resuelve cualquiera de los dos. Si no hay
desenlace alternativo que observar, el techo se ajusta al instante en que ese
elemento aparecería —segundos, no decenas.

### 2. El predicado usado como espera

Un método que se llama `esAlgo()` y devuelve un booleano es un **predicado**.
Invocarlo y descartar el resultado lo convierte en una espera cuyo peor caso es
el techo completo:

```
await pantalla.esModalVisible(30000);   // el booleano no lo lee nadie
```

Dos fallos superpuestos, y el segundo es peor: el `false` que nadie lee era justo
la señal de que algo no cuadraba. En el caso medido, además, el selector
consultado ya no correspondía a esa fase del flujo, así que **nunca** iba a
casar: 30 segundos por plataforma, en cada corrida, esperando algo imposible, sin
un solo mensaje.

**Cómo se caza**: buscar toda llamada `await …esAlgo(NNNN);` como sentencia
suelta. Cada aparición es un temporizador disfrazado de verificación.

### 3. El sondeo en serie de una lista de candidatos

Un helper que prueba tres selectores posibles, uno detrás de otro, con techo
propio cada uno. En local la diferencia se disimula; contra un dispositivo remoto
cada sonda es una ida y vuelta por red, y **el coste es N veces la latencia** —
creciendo cada vez que alguien añade un fallback, que es justo lo que el
self-healing anima a hacer (`[[calidad-test-self-healing]]`).

Con esperas opcionales encadenadas el daño va más allá del tiempo: **la función
deja de cumplir su propósito**. Un descartador de modales que prueba tres
candidatos en serie durante 24 segundos mira justo antes de que aparezca el que
busca, y el error que se ve después no menciona modales por ningún lado.

**Corrección**: la lista se sondea **en paralelo**, quedándose con el candidato
de menor índice que exista, para conservar el orden de prioridad — que es lo que
hace significativa la telemetría de healing.

### 4. La pausa ciega donde hay condición observable

Una pausa fija es correcta sólo cuando **no existe** condición observable. En la
suite medida había pausas tras una llamada de API de bloqueo, tras un tap de
confirmación y en el sondeo de un código de un solo uso — y en los tres casos la
condición existía: el estado del recurso, la pantalla resultante, la presencia
del código.

Regla adicional sobre el mismo presupuesto: **granularidad**. Cinco esperas de
3 s y quince de 1 s cuestan lo mismo en el peor caso, pero la segunda sale en
cuanto la condición se cumple.

### 5. El umbral temporal escrito a mano

«Al menos 20 segundos de vigencia restante para leer ocho dígitos» es una
**suposición sobre la velocidad del dispositivo**. En una granja el dispositivo
cambia en cada corrida: la misma lectura que sobra en local se pasa de largo en
remoto, y la operación empieza con margen aparente y termina fuera de plazo.

**Corrección**: cuando una espera depende de cuánto tarda una operación, se
**mide la operación** y se deriva el umbral de lo medido más un colchón. Medir
sale más barato que adivinar dos veces.

> Y un aviso al reparar cualquiera de los cinco: **al arreglar una comprobación
> rota hay que esperar fallos nuevos.** No son regresiones — son los fallos que
> la comprobación rota estaba tapando. En el caso medido, reparar la lectura de
> un contador puso en rojo un escenario que llevaba semanas en verde por suerte.

## El timeout del step es un tope de seguridad, no la duración esperada

Un step que declara `timeout: 15 s` y por dentro espera `15 s` se queda **sin
voz**: el arnés lo mata justo cuando la espera interna vence, así que el error
explicativo que el propio código iba a lanzar nunca se ejecuta. Lo que llega al
reporte es *«la función excedió 15000 milisegundos»*, que no dice nada, y la
captura se toma tarde, cuando cualquier mensaje transitorio ya desapareció
(`[[calidad-data-volatility-and-assertion-anchoring]]`).

**Regla: `timeout del step > suma de las esperas internas + margen`.** El tope
del arnés existe para que un cuelgue no bloquee la suite, no para marcar el
plazo. Cuando coinciden, el arnés se calla justo cuando más falta hace.

Corolario sobre los mensajes: un error que informa mal del tiempo esperado
desvía el diagnóstico. Si el ciclo de espera reporta el plazo de su último
intento interno en vez del total, invita a buscar un selector roto cuando el
problema es de ritmo.

## Cómo se inventaría, en vez de descubrirlos de a uno

El barrido se emite **una vez y completo**, no cada vez que uno estorba:

| Qué buscar | Qué es | Veredicto |
|---|---|---|
| `await …esAlgo(NNNN);` como sentencia suelta | predicado usado como espera | siempre defecto |
| espera con `.sino/.catch` inline | espera opcional | defecto **si** el elemento normalmente no está |
| ciclos de espera con intervalo ≥ 1 s | granularidad gruesa | revisar |
| pausas fijas | pausa ciega | defecto si hay condición observable |
| constantes de tiempo comparadas contra una vigencia | umbral a mano | medir |

No todos son defectos —un `.catch()` es correcto cuando el elemento **sí** suele
estar—, pero el inventario existe y se revisa por lote. Y se emite **antes** de
proponer nada: es la instancia en tiempo de ejecución de la batería de
`[[calidad-measure-before-proposing]]`.

## El coste por interacción, cuando la estrategia de localización es la causa

A veces las esperas están bien y el reloj se va igual. Medido sobre la traza de
un dispositivo remoto: cada búsqueda por expresión de ruta sobre el árbol de
accesibilidad tardaba entre 0,4 y 1,1 s, y un solo tap se descomponía en unas
nueve llamadas al driver — **5 a 6 segundos por interacción**. Un flujo de cinco
taps más el ingreso de un código dígito a dígito se come 46 s antes de llegar a
lo que certifica.

La causa es que ese tipo de selector obliga al motor a serializar el árbol
completo del dispositivo en cada consulta, mientras que un identificador de
accesibilidad o un predicado nativo resuelven contra el índice.

**Esto casi nunca se arregla en la sesión**: cambiar la estrategia de
localización de un arquetipo con cientos de selectores y varias historias ya
certificadas encima es una decisión del cliente
(`[[calidad-brownfield-vs-greenfield]]`). Lo que sí corresponde es **entregarla
cuantificada**: no «las expresiones de ruta son más lentas», sino «5–6 segundos
por interacción, N interacciones por escenario, tanto por pasada». Se mide, se
nombra el riesgo, y se entrega la decisión.

## Y la pregunta que borra más tiempo que las cinco anteriores juntas

Antes de optimizar una precondición cara, preguntar **qué consume el `Then` de
todo lo que hace el `Given`**. Un escenario que hereda la precondición de su
vecino suele estar pagando por un estado que no usa: «necesito la pantalla de
ingreso manual» y «necesito un código válido» son requisitos muy distintos, y el
mismo montaje los estaba satisfaciendo con el mismo martillo.

La respuesta se **verifica con un experimento corto**, no se asume: en el caso
medido la hipótesis parecía sólida, salió del texto del criterio de aceptación, y
era falsa — el experimento la descartó en menos de dos minutos. Asumirla habría
producido escenarios que pasan sin ejercitar lo que certifican, que es el peor
resultado posible. Ver `[[calidad-automation-feasibility-assessment]]`.

## Restricciones

- **NUNCA uses un techo largo para algo opcional.** Sobre algo que normalmente no
  aparece, el timeout **es** la duración.
- **NUNCA invoques un predicado descartando su resultado.** O se lee el booleano,
  o se llama a una espera de verdad.
- **NUNCA sondees una lista de candidatos en serie** contra un dispositivo o
  sesión remota.
- **NUNCA declares el timeout de un step igual a la espera que contiene.**
- **NUNCA fijes a mano un umbral que depende de cuánto tarda una operación** en un
  entorno donde la máquina cambia entre corridas.
- **NUNCA reescribas la estrategia de localización de un arquetipo heredado por
  cuenta propia**, por evidente que sea la ganancia: se mide, se cuantifica y se
  entrega la decisión.

## Cross-links

- `[[calidad-measure-before-proposing]]` — la batería sobre el repositorio; ésta
  es la del reloj de la corrida.
- `[[calidad-data-volatility-and-assertion-anchoring]]` — por qué el timeout del
  step decide si la evidencia llega a tiempo.
- `[[calidad-test-self-healing]]` — los fallbacks que este asset obliga a sondear
  en paralelo.
- `[[calidad-automation-feasibility-assessment]]` — qué consume el `Then` de la
  precondición.
- `[[calidad-session-reuse-and-isolation]]` — cuando la precondición cara es el
  login, la salida no es acelerarlo sino pagarlo una sola vez.
- `[[calidad-brownfield-vs-greenfield]]` — dónde termina lo que se puede cambiar.
- `[[calidad-failure-triage-and-classification]]` — «pasa en local y falla en la
  granja» es un síntoma, no una causa.
