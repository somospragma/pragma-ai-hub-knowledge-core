---
id: calidad-fresh-context-verification
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Lo que ninguna puerta determinista puede comprobar lo revisa un verificador con contexto limpio, no quien acaba de hacer el trabajo. Qué se le manda, qué NO se le manda, en qué puntos de pausa se invoca y cómo se registra su veredicto."
tags: [verificacion, guardrails, anti-cheating, calidad-del-juicio, contexto, universal, mandatory]
enforcement: mandatory
verification:
  - check: "en cada punto de pausa que lo exige se registró el veredicto del verificador en .evidence/verification/, y quien verificó no fue quien produjo el trabajo en el mismo contexto"
    failure_message: "Bloqueado: la comprobación fue una autoevaluación. El mismo contexto que produjo el atajo no puede detectarlo: arrastra el sesgo que lo causó."
  - check: "al verificador se le entregó el artefacto y la pregunta, nunca la conversación que lo produjo"
    failure_message: "Bloqueado: se le pasó el hilo al verificador. Si recibe el razonamiento que llevó al resultado, hereda su sesgo y deja de ser una segunda opinión."
---

# Verificación con Contexto Limpio

## Problema que resuelve

Hay dos clases de comprobación. Una es mecánica —¿existe este archivo, devuelve este comando cero, aparece este campo?— y la resuelve una puerta determinista, que es barata e infalible. La otra exige juicio: **¿este criterio de aceptación se puede convertir en aserción? ¿esta ficha de corrección cuadra con lo que hace el código? ¿este verde demuestra lo que dice demostrar?**

Hoy esa segunda clase la resuelve **el mismo agente, en el mismo contexto, inmediatamente después de haber hecho el trabajo**. Es el diseño más débil posible: el contexto que produjo el atajo es el que tiene que detectarlo, y llega cargado con las razones por las que el atajo pareció buena idea.

La práctica convergente en sistemas que no fallan es una cadena de tres: **un generador que propone, un verificador con contexto fresco que revisa, y una puerta determinista que sólo deja pasar lo correcto.** Nosotros teníamos el primero y el tercero.

## Cuándo aplicar

En los puntos de pausa del recorrido, y sólo sobre lo que ninguna puerta puede comprobar. Si un script puede responder la pregunta, **no se invoca al verificador**: sale más caro y es menos fiable que el script.

## Instrucción

### 1. Los puntos de pausa y qué se verifica en cada uno

| Punto | Pregunta que se le hace | Por qué no la puede responder un script |
|---|---|---|
| **Cierre de insumos** | ¿Cada criterio de aceptación se puede convertir en aserción sin preguntarle a nadie? | Exige leer el criterio y juzgar si es observable |
| **Antes de la primera corrida** | ¿La secuencia de interacciones hace lo que el caso dice verificar? | Comparar intención contra mecánica |
| **Al aplicar una ficha de corrección** | ¿Lo que la ficha afirma cuadra con lo que hace el código? | Un diagnóstico humano puede ser correcto y aun así no aplicar |
| **Antes de archivar un verde** | ¿La aserción demuestra la señal sustantiva, o pasa por ausencia de algo que nunca llegó? | Es el patrón del verde falso |
| **Antes de declarar un defecto** | ¿La cadena de evidencia sostiene la afirmación? | Exige valorar suficiencia, no contar archivos |

### 2. Qué se le manda, y sobre todo qué no

**Se le manda**: el artefacto a revisar y la pregunta. Nada más.

**No se le manda la conversación que lo produjo.** Si recibe el hilo, hereda el razonamiento que llevó al resultado y deja de ser una segunda opinión: se convierte en un segundo voto del mismo votante. Esta restricción es la que hace que el mecanismo funcione, y es la más fácil de romper sin darse cuenta.

Tampoco se le manda la conclusión que se espera. Preguntar "¿confirmas que este criterio es verificable?" invita a confirmar; "¿este criterio se puede convertir en aserción, y si no, qué le falta?" pide un juicio.

### 3. Qué devuelve

Un veredicto corto y accionable, persistido en `.evidence/verification/<punto>.md`: qué revisó, qué encontró, y —si objeta— **qué falta concretamente**. Una objeción sin la pieza que falta no sirve más que un "no me convence".

### 4. Qué pasa con la objeción

La objeción **no es una orden**, igual que la ficha de corrección no lo es: se contrasta. Si el verificador objeta y el productor demuestra con evidencia que la objeción no aplica, se registra el desacuerdo y se sigue. Lo que no se puede es ignorarla en silencio.

### 5. Lo que este mecanismo no es

No es una segunda pasada del mismo agente diciéndose que sí. No es revisión de estilo. Y no sustituye a la puerta determinista: **si algo se puede comprobar contando archivos o mirando un código de salida, se comprueba así**, porque es más barato y no opina.

## Restricciones

- **NUNCA** entregar al verificador la conversación, el razonamiento previo ni la conclusión esperada.
- **NUNCA** usarlo para lo que una comprobación determinista resuelve. El verificador es caro; el script no.
- **NUNCA** dar por verificado un punto de pausa sin su registro. Un veredicto que no se escribió no ocurrió.
- **NUNCA** dejar que el verificador modifique el trabajo: revisa y objeta; corregir es del productor.
- Una objeción desestimada **se registra con su razón**. Desestimarla en silencio reproduce exactamente el problema que este asset existe para corregir.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | en cada punto de pausa que lo exige se registró el veredicto del verificador en .evidence/verification/, y quien verificó no fue quien produjo el trabajo en el mismo contexto | Bloqueado: la comprobación fue una autoevaluación. El mismo contexto que produjo el atajo no puede detectarlo: arrastra el sesgo que lo causó. |
| 2 | al verificador se le entregó el artefacto y la pregunta, nunca la conversación que lo produjo | Bloqueado: se le pasó el hilo al verificador. Si recibe el razonamiento que llevó al resultado, hereda su sesgo y deja de ser una segunda opinión. |

## Cross-links

`[[calidad-deterministic-work-to-tooling]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-cold-audit-before-execution]]`, `[[calidad-human-fix-request-protocol]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-test-self-healing]]`.
