---
id: calidad-data-volatility-and-assertion-anchoring
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Clasificación obligatoria de todo texto antes de convertirlo en localizador o aserción: etiqueta estática, formato invariante, contenido volátil o dato controlado. Evita suites que fallan por datos y no por defectos, y fija cómo corregir el ancla con la evidencia de la primera ejecución."
tags: [selectores, aserciones, volatilidad, datos, figma, ui, api, determinismo, universal, all-stacks, mandatory]
enforcement: mandatory
verification:
  - check: "todo texto usado como localizador o como valor esperado fue clasificado y la clasificación quedó registrada"
    failure_message: "Bloqueado: hay localizadores o aserciones sobre texto sin clasificar. Anclar en contenido volátil produce una suite que falla por datos y no por defectos."
  - check: "ninguna aserción compara por valor literal un contenido clasificado como volátil"
    failure_message: "Bloqueado: hay aserciones sobre contenido que cambia en cada registro. Ese test va a fallar mañana sin que el SUT haya cambiado."
---

# Data Volatility and Assertion Anchoring — Qué Texto Sirve de Ancla

## Problema que resuelve

Al derivar localizadores y aserciones de una fuente de diseño, de una captura o de una respuesta de ejemplo, es fácil tomar por estable un texto que por naturaleza cambia en cada registro. El resultado es una suite que **falla por datos y no por defectos**: cada corrida enciende alarmas que nadie puede accionar, y el equipo termina ignorando el rojo.

Verificado en campo: se generaron localizadores desde el diseño usando como ancla el nombre de un elemento de negocio que es distinto en cada registro. Lo que sí se repetía en todos —el símbolo de moneda, el rótulo de la pantalla, el formato de la fecha— estaba a la vista y no se usó.

La regla que resume todo: **el contenido de una maqueta es una muestra, no un dato.**

## Cuándo aplicar

Siempre que un texto vaya a convertirse en localizador o en valor esperado, en cualquier stack:

- Al construir el `[[calidad-ui-locator-map-contract]]` o derivar pantallas desde una fuente de diseño (`[[calidad-figma-mcp-integration]]`).
- Al escribir aserciones de UI en Playwright o Appium.
- Al escribir aserciones sobre respuestas en Karate: los `examples` del spec también son muestras.
- Al corregir un test que falla, antes de tocar la espera o el localizador (`[[calidad-test-self-correction-loop]]`).

## Las cuatro clases

| Clase | Qué es | Cómo se usa |
|---|---|---|
| **Etiqueta estática** | Rótulos, títulos, encabezados, textos de botón, nombres de sección: pertenecen a la interfaz, no al dato | Sirve como ancla **y** como aserción por valor |
| **Formato invariante** | Símbolo de moneda, separadores, máscara de fecha, patrón de identificador, unidades, prefijos | Se ancla por patrón y se afirma por expresión regular, **nunca** por valor concreto |
| **Contenido volátil** | Nombre del comercio o del producto, descripción, monto, fecha del registro, saldo, folio | **Nunca** se ancla ni se afirma por valor. Se afirma existencia, formato, cantidad o relación |
| **Dato controlado** | Valor que el propio test creó, sembró o seleccionó del catálogo de datos | Se puede afirmar por valor, porque el test lo controla y es reproducible |

Ante la duda, **volátil**. Reclasificar hacia arriba con evidencia es barato; descubrir la volatilidad en producción cuesta una corrida roja y un diagnóstico.

## Anclas que desaparecen: la segunda pregunta, sobre el tiempo

Las cuatro clases responden **qué** es el texto. Falta responder **cuánto dura**,
y es una pregunta distinta: una etiqueta estática perfectamente clasificada sigue
sin poder aserarse si la aplicación la retira sola a los tres segundos.

**Un mensaje que la aplicación muestra y retira por su cuenta —banner, snackbar,
toast, mensaje de validación temporal— no se puede aserar en un step posterior al
que lo provoca.** Para cuando el `Then` mira, ya no está. Esto rompe una
suposición que atraviesa todo el diseño de pasos Gherkin: que un `Then` puede
consultar la pantalla que dejó el `When`.

**El desenlace se captura en el instante en que ocurre** —dentro del mismo step
que ejecuta la acción— y se guarda en el World. El step de aserción comprueba lo
guardado, no la pantalla.

### Cómo se reconoce

| Síntoma | Qué parece | Qué es |
|---|---|---|
| Pasa en local y falla en la granja | Problema de entorno | El tiempo entre la acción y la consulta es mayor en la granja |
| Pasa en un dispositivo y falla en otro | Dispositivo defectuoso | El dispositivo lento llega tarde a mirar |
| El elemento "no existe" pero el selector es correcto | Locator roto | Se está preguntando después |

**La prueba que los separa**: si la traza de comandos muestra el elemento
**encontrado** en algún momento de la corrida, el selector está bien y el
problema es *cuándo* se pregunta. Un locator roto nunca lo encuentra.

### El corolario que costó un defecto falso

Una evidencia recogida en el teardown es evidencia legítima del **final** del
escenario y no prueba nada sobre un estado intermedio. En la sesión que originó
esta sección se concluyó que la aplicación no mostraba un mensaje de error de
validación, y se abrió un defecto: la aserción consultaba un banner ya
desvanecido, y el volcado de jerarquía —tomado aún más tarde— mostraba la
pantalla ya sin él. **Dos evidencias coincidentes, ambas tardías por la misma
razón.** El vídeo de la sesión mostraba el mensaje apareciendo.

Antes de afirmar que algo no se mostró: **¿de qué instante es esta evidencia, y
es anterior o posterior al hecho que quiero afirmar?** Ver
`[[calidad-failure-triage-and-classification]]`.

## Instrucción

1. **Clasificar antes de escribir.** Para cada texto candidato a localizador o a valor esperado, asignar clase y dejarla registrada junto al locator map o al plan de escenarios.
2. **Anclar según la clase.** El elemento volátil se localiza por su **etiqueta adyacente**, por su posición dentro de un contenedor identificado, o por su formato; nunca por su contenido. Si el elemento no tiene ancla estable, eso es un hallazgo de instrumentación: se solicita un identificador estable al equipo de desarrollo (`[[calidad-ui-locator-map-contract]]`), no se inventa un ancla frágil.
3. **Afirmar según la clase.**

   | Clase | Aserción correcta |
   |---|---|
   | Etiqueta estática | el texto es exactamente el esperado |
   | Formato invariante | el valor cumple el patrón; el símbolo o la unidad están presentes |
   | Contenido volátil | el campo existe, no está vacío, cumple su formato, y su relación con otros campos se sostiene |
   | Dato controlado | el valor es exactamente el que el test sembró |

4. **Corregir con la evidencia real.** Tras la primera ejecución, las capturas y los volcados del reporte son la **fuente autorizada** para reclasificar. Si un texto supuesto estable aparece distinto entre corridas, se reclasifica como volátil y se corrige el ancla.

   Esto es una corrección legítima dentro de `[[calidad-test-self-correction-loop]]` y **no es cheating**: no se debilita la aserción para que pase, se corrige el ancla para que verifique lo correcto. La diferencia se declara en el registro de correcciones: *qué se afirmaba antes, qué se afirma ahora, y por qué lo nuevo verifica lo mismo o más*.

5. **Registrar** la clasificación y sus cambios junto al locator map, para que la siguiente sesión no la vuelva a deducir.

## Restricciones

- **NUNCA** tomar el contenido de una maqueta como dato real: los nombres y valores de una maqueta son de relleno.
- **NUNCA** debilitar una aserción a "el elemento existe" para esquivar la volatilidad cuando el criterio de aceptación exige verificar el valor. Si el criterio exige un valor, el test debe controlarlo: se siembra el dato o se usa el catálogo (`[[calidad-test-data-management]]`).
- **NUNCA** usar un índice de posición como ancla en listas ordenadas por datos: el orden es contenido volátil.
- **NUNCA** reclasificar hacia "estable" por conveniencia sin evidencia de al menos dos corridas.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | todo texto usado como localizador o como valor esperado fue clasificado y la clasificación quedó registrada | Bloqueado: hay localizadores o aserciones sobre texto sin clasificar. Anclar en contenido volátil produce una suite que falla por datos y no por defectos. |
| 2 | ninguna aserción compara por valor literal un contenido clasificado como volátil | Bloqueado: hay aserciones sobre contenido que cambia en cada registro. Ese test va a fallar mañana sin que el SUT haya cambiado. |
| 3 | ningún mensaje que la aplicación retira sola se asere en un step posterior al que lo provoca | Bloqueado: hay aserciones sobre anclas transitorias. Ese test pasa en el dispositivo rápido y falla en el lento, y el diagnóstico apuntará al entorno en vez de al diseño del step. |

## Cross-links

`[[calidad-ui-locator-map-contract]]`, `[[calidad-figma-mcp-integration]]`, `[[calidad-test-data-management]]`, `[[calidad-test-self-correction-loop]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-visual-regression]]`, `[[calidad-sut-readiness-gate]]`.
