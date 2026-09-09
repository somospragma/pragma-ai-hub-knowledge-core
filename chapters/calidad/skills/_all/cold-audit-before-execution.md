---
id: calidad-cold-audit-before-execution
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Antes de la primera corrida de un escenario, recorrer el código en frío y escribir la secuencia de interacciones que hará sobre el dispositivo o el navegador, paso a paso. La mayoría de los fallos de una corrida se ven leyendo el código, y una corrida cuesta órdenes de magnitud más que leerlo."
tags: [ejecucion, auditoria, pre-corrida, costo, precision, brownfield, universal, mandatory]
enforcement: mandatory
verification:
  - check: "existe .evidence/cold-audit/<escenario>.md antes de su primera corrida, con la secuencia de interacciones y el punto declarado como más frágil"
    failure_message: "Bloqueado: se iba a ejecutar sin haber leído lo que el código hará paso a paso. Una corrida cuesta minutos de dispositivo y presupuesto; leer el código no cuesta ninguno de los dos."
  - check: "la auditoría se repitió tras cada corrección antes de volver a correr"
    failure_message: "Bloqueado: se corrigió y se volvió a correr sin releer. Corregir sin auditar es lo que produce cadenas de intentos que fallan por motivos distintos cada vez."
---

# Auditoría en Frío Antes de Ejecutar

## Problema que resuelve

El agente escribe un escenario y lo lanza para ver qué pasa. La corrida falla, corrige lo que el error señala, vuelve a lanzar, falla por otra cosa. Cada vuelta cuesta minutos de dispositivo, presupuesto de modelo y —lo peor— contexto: la salida de cada corrida se queda ocupando espacio durante el resto de la sesión.

Casi todos esos fallos eran visibles **leyendo el código antes de correrlo**: un gesto a ciegas sin ancla, una espera fija que nadie va a satisfacer, un selector que asume un tipo de nodo, un paso que abre un menú que el paso anterior ya cerró.

Verificado en campo: en una certificación de tres plataformas, ocho escenarios que llevaban días fallando de uno en uno salieron **verdes en una sola tanda** después de una auditoría en frío que cazó cuatro errores sin gastar una corrida. Fue el mejor retorno de toda la entrega.

## Cuándo aplicar

Antes de la **primera** corrida de cada escenario, y de nuevo **después de cada corrección**, antes de volver a correr. Sin excepción por urgencia: la auditoría cuesta menos que la corrida que evita.

## Instrucción

### 1. Recorrer la cadena completa, no el step que se acaba de escribir

Se sigue el escenario de punta a punta —Given, When, Then— entrando a cada step, a cada método de la pantalla o página, y a cada helper que invoquen. Lo que se audita es **la cadena que se va a ejecutar**, no el archivo que se acaba de tocar.

### 2. La secuencia la emite una herramienta; el criterio lo pone el agente

Recorrer la cadena y listar las interacciones es trabajo **determinista**: misma entrada, misma salida, sin juicio. Por tanto no lo hace el razonamiento del agente cada vez, sino una herramienta del proyecto que recorre los steps estáticamente y **imprime la secuencia**. Si el proyecto no la tiene, se construye una vez según `[[calidad-deterministic-work-to-tooling]]` — es de las que antes se amortizan, porque se invoca en cada escenario de cada historia.

Lo que la herramienta imprime es **la lista de lo que va a ocurrir en la pantalla**, en orden, con la estrategia de localización y la espera de cada paso. No un resumen de lo que hace el código.

```
1. login(usuario)                     -> espera Home            [espera explícita 60 s]
2. buscarTarjeta('5771')              -> hasta 6 gestos A CIEGAS   sin ancla de sección
3. abrirMenuContextual()              -> localiza por tipo Botón    el nodo real es contenedor
4. esperarModalDeBloqueo(8 s)         -> 8 s incondicionales        se pagan en el camino feliz
5. asertar(textoEsperado)             -> el texto es transitorio    se lee después de que desaparece
```

### 3. Declarar el punto más frágil antes de correr

Esto **sí es del agente**: la herramienta lista, el criterio decide. De esa lista, se nombra **cuál paso es el que más probablemente falle y por qué**. Esa declaración es la que convierte la auditoría en un acto de diseño y no en un trámite: obliga a mirar la cadena con criterio, y deja constancia para comparar contra lo que realmente falle.

### 4. Corregir lo obvio antes de gastar la corrida

Los cinco patrones que esta auditoría caza casi siempre, y que no requieren ver la aplicación para detectarse:

1. **Gestos o desplazamientos sin ancla** — se repite un gesto un número fijo de veces esperando que el elemento aparezca, sin verificar contra qué sección se está moviendo. Ver `[[calidad-test-self-healing]]`.
2. **Esperas fijas por elementos que pueden no existir** — el escenario paga el techo completo cuando el elemento opcional no aparece. Ver `[[calidad-wait-cost-and-timeout-design]]`.
3. **Suposiciones sobre el tipo de nodo** — se localiza por tipo (botón, campo, texto) sin haberlo verificado contra el árbol real. Ver `[[calidad-ui-locator-map-contract]]`.
4. **Lectura tardía de algo transitorio** — el resultado se valida en el Then cuando ya desapareció; debe capturarse en el instante del When.
5. **Reinvención de un paso que ya existe estable** — hay un escenario verde que toca esa misma pantalla con otro mecanismo. Ver `[[calidad-cross-platform-learning-propagation]]`.

### 5. Verificar que la cadena al menos enlaza

La auditoría se acompaña de las comprobaciones estáticas que no tocan el sistema bajo prueba: compilación, análisis de estilo y ensayo en seco del runner. Son baratas, no requieren ambiente y atrapan lo que ninguna lectura atrapa: steps sin implementar, ambigüedades, tablas de ejemplos mal formadas.

Un escenario **no se entrega como listo para correr** si no compila, no enlaza sus steps y no pasó esta auditoría.

## Restricciones

- La auditoría **no sustituye** a la corrida: demuestra que vale la pena gastarla.
- **Nunca** se ajustan parámetros de un gesto o de una espera "a ver si ahora sí" sin haber releído la cadena. Ese es exactamente el ciclo que este asset existe para cortar.
- La auditoría se hace **sobre el código que se va a ejecutar**, no sobre el que se recuerda haber escrito: si hubo correcciones de por medio, se relee.
- Su salida se persiste junto a la traza de la entrega, no se deja sólo en la conversación.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | existe .evidence/cold-audit/<escenario>.md antes de su primera corrida, con la secuencia de interacciones y el punto declarado como más frágil | Bloqueado: se iba a ejecutar sin haber leído lo que el código hará paso a paso. Una corrida cuesta minutos de dispositivo y presupuesto; leer el código no cuesta ninguno de los dos. |
| 2 | la auditoría se repitió tras cada corrección antes de volver a correr | Bloqueado: se corrigió y se volvió a correr sin releer. Corregir sin auditar es lo que produce cadenas de intentos que fallan por motivos distintos cada vez. |

## Cross-links

`[[calidad-test-self-correction-loop]]`, `[[calidad-wait-cost-and-timeout-design]]`, `[[calidad-test-self-healing]]`, `[[calidad-cross-platform-learning-propagation]]`, `[[calidad-ui-locator-map-contract]]`, `[[calidad-smoke-gate-policy]]`, `[[calidad-human-fix-request-protocol]]`, `[[calidad-static-analysis-on-the-test-repo]]`, `[[calidad-deterministic-work-to-tooling]]`.
