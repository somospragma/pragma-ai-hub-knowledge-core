---
id: calidad-human-fix-request-protocol
version: 1.2.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Dónde entra la persona una vez que lo determinista ya lo resuelven herramientas del proyecto: el juicio que ninguna herramienta da, la ficha de corrección de formato fijo, el canal visual, y cuándo la corrida la lanza el QA. Reemplaza el ciclo de correr-fallar-parchar por uno de corregir con diagnóstico."
tags: [ejecucion, human-in-the-loop, triage, costo, evidencia, capturas, precision, universal, mandatory]
enforcement: mandatory
verification:
  - check: "ninguna corrida volcó su salida cruda al razonamiento: se consumió el veredicto acotado que emite la herramienta del proyecto"
    failure_message: "Bloqueado: se leyó el registro completo de una corrida. Lo determinista lo resuelve la herramienta y devuelve un veredicto; el registro queda en disco."
  - check: "cada corrección aplicada tiene su ficha en .evidence/fix-requests/ con los seis campos, y el agente la auditó contra el código antes de aplicarla"
    failure_message: "Bloqueado: se corrigió sin ficha, o se aplicó una ficha sin auditarla. Obedecer un diagnóstico sin verificarlo cambia un desperdicio por otro."
  - check: "cuando la evidencia textual no explicó el fallo, se pidió la captura a la persona en vez de seguir iterando"
    failure_message: "Bloqueado: se siguió iterando a ciegas sobre algo que sólo se resuelve viendo la pantalla. Pedirla cuesta un turno; adivinarla cuesta la tanda entera."
---

# Protocolo de Corrección Dirigida por la Persona

## Problema que resuelve

El ciclo por defecto de un agente frente a una prueba que falla es **volver a correrla**. Ejecutar le resulta barato de iniciar, así que sustituye pensar por intentar: ajusta un parámetro, relanza, mira, ajusta otro. Verificado en campo: una certificación de cincuenta casos consumió **214 corridas para 53 escenarios en verde** —cuatro corridas por cada uno— y la mitad del presupuesto de la entrega se fue en ese ciclo.

Hay dos costos encadenados. El obvio es la corrida. El que no se ve es que **la salida de cada corrida se queda en el contexto** y se reenvía en cada paso posterior de la sesión, así que las corridas de la mañana se siguen pagando por la tarde.

Y hay un tercero, de calidad: iterar sustituye al diagnóstico. En la misma entrega, un problema cuya causa era un desplazamiento demasiado brusco sobre una lista larga costó del orden de setecientos créditos en intentos, y se resolvió en uno solo cuando la persona describió el gesto manual correcto.

## Cuándo aplicar

En toda entrega donde la ejecución toque un dispositivo real, una granja, un sistema bajo prueba o la red. Es el modelo por defecto de estabilización; los modos alternos se declaran en la estrategia y se justifican.

## Instrucción

### 1. Primero la herramienta; la persona, donde hay juicio

**El orden importa y es el que corrige el error más común de este protocolo.** Antes de decidir qué hace la persona, se decide qué hace una herramienta: todo lo determinista y repetido —ejecutar, resumir, triar por patrón, empaquetar la evidencia, auditar en frío, medir cobertura— se resuelve con herramientas del proyecto según `[[calidad-deterministic-work-to-tooling]]`. Pasarle a una persona trabajo determinista lo mueve de sitio; no lo elimina, y convierte al QA en el cuello de botella.

Lo que queda para la persona es **lo que ninguna herramienta puede dar**:

| Aporte de la persona | Por qué no se automatiza |
|---|---|
| **Leer la pantalla** | La herramienta extrae texto, árbol y geometría; interpretar lo que se ve cuando eso no basta sigue siendo humano (ver punto 4) |
| **Aprobar la cobertura** al cerrar la fase de insumos | Es una decisión de alcance, no un recuento |
| **Autorizar escrituras** — gestor de pruebas, datos del cliente, transacciones con costo | `[[calidad-alm-write-authorization-gate]]` |
| **Decidir ante una contradicción** entre historia y diseño | No hay fuente de verdad que resolverla mecánicamente |
| **Confirmar un defecto del producto** | Exige la cadena de evidencia y criterio, no un patrón |

Y la corrida propiamente dicha **la lanza el QA cuando lanzarla tiene costo o riesgo propio**: dispositivo físico ocupado, granja de pago, transacción con cobro real, escritura ya autorizada, o un flujo entre dos dispositivos. En el resto de los casos la lanza el agente invocando la herramienta, que devuelve un veredicto acotado y cuesta lo mismo que cualquier otra llamada.

**La frontera real no es quién presiona ejecutar: es qué entra al razonamiento.** Una corrida cuya salida se consume como veredicto de dos kilobytes es barata la lance quien la lance; una cuyo registro entero entra al contexto es cara aunque la haya lanzado una persona y la pegue en la conversación.

### 2. Se trabaja por lotes, nunca escenario por escenario

Si el repositorio provee un ejecutor por etiquetas o multiplataforma —lo habitual en un arquetipo maduro; comprobarlo con `[[calidad-repo-capability-discovery]]`— **se usa**. Correr de a un escenario paga de nuevo, en cada corrida, el login, la navegación y las precondiciones.

El agente entrega un lote etiquetado. La persona corre el lote y revisa un reporte. El agente recibe las fichas de los que fallaron y los corrige todos en un turno.

### 3. La ficha de corrección

El diagnóstico humano entra **en un archivo con formato fijo**, no en la conversación. La conversación lleva el puntero: "lote 1, fichas 3 y 7".

```markdown
# FIX-3 · <escenario> · <plataforma>

**Falló en:** <el step exacto>
**Lo que vi en pantalla:** <una o dos líneas: dónde quedó y qué se veía>
**Causa (mi diagnóstico):** <qué lo provoca>
**La corrección:** <qué hacer, en términos de comportamiento observable>
**Homólogo estable:** <escenario ya verde que resuelve esto, si existe>
**Confianza:** alta | media | baja
```

Seis campos. El límite es una pantalla: si la ficha crece, es que hay dos problemas y van dos fichas.

### 4. El canal visual: qué aporta la persona y cuándo se le pide

El agente **no puede abrir imágenes con sus herramientas de archivo**. El mecanismo completo —por qué, y las tres vías que sí funcionan— vive en `[[calidad-test-evidence-and-traceability]]`, que es el asset dueño de la evidencia. Aquí sólo lo que le toca a este protocolo:

- **El campo "lo que vi en pantalla" de la ficha es la vía dos.** Una línea de la persona describiendo dónde quedó la pantalla y qué se veía entrega en texto lo que el agente no puede mirar. Por eso es obligatorio y no opcional.
- **La vía tres se dispara aquí.** Si el paquete de evidencia y la ficha no explican el fallo, el agente **pide la captura con una pregunta concreta** —"¿en qué pantalla quedó y qué se ve en la parte superior?"— en lugar de seguir intentando. Pedirla cuesta un turno; adivinarla cuesta la tanda.

### 5. Auditar la ficha antes de aplicarla

Una ficha es un diagnóstico humano, no una orden. El agente **contrasta lo que dice contra el código** y objeta si no cuadra: "la ficha dice que el selector no coincide, pero el step no llega ahí porque el anterior sale por excepción".

Obedecer sin verificar convierte un desperdicio en otro: en vez de gastar corridas adivinando, se gastan corrigiendo lo que no era. Cuando el campo de confianza dice media o baja, la verificación es obligatoria antes de tocar nada.

### 6. Los verdes falsos no puede cazarlos la persona

Si la persona sólo ve pasa o falla, un escenario que pasa por la razón equivocada se archiva como bueno. La defensa **no puede ser que el agente lea la traza** —ya no la lee— sino que la comprobación baje al propio escenario: la aserción exige la señal sustantiva y falla si no puede demostrarla.

Un escenario que no puede demostrar su señal no reporta verde: reporta *pasa sin verificar*, y no se archiva. Ver `[[calidad-test-self-healing]]` para los guardarraíles anti-complacencia.

## Restricciones

- **Prohibido** pegar registros, volcados o diseños completos en la conversación: van a archivo y se pasa la ruta. Un volcado pegado puede agotar la ventana de contexto de una sola vez.
- **Prohibido** relanzar un escenario "para ver si ahora sí", lo lance quien lo lance. Tras dos fallos manda el diagnóstico de fondo de `[[calidad-test-self-correction-loop]]`.
- La ficha **no lleva el registro adjunto**. Si el agente necesita más, lo pide una vez y de forma acotada.
- El modo de diagnóstico —donde el agente sí abre la evidencia completa— es excepcional, se usa **una vez por escenario** y exige declarar la hipótesis antes de abrirla. Ver `[[calidad-test-self-correction-loop]]`.
- Nada de esto releva de las autorizaciones de escritura: `[[calidad-alm-write-authorization-gate]]` sigue vigente.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | ninguna corrida volcó su salida cruda al razonamiento: se consumió el veredicto acotado que emite la herramienta del proyecto | Bloqueado: se leyó el registro completo de una corrida. Lo determinista lo resuelve la herramienta y devuelve un veredicto; el registro queda en disco. |
| 2 | cada corrección aplicada tiene su ficha en .evidence/fix-requests/ con los seis campos, y el agente la auditó contra el código antes de aplicarla | Bloqueado: se corrigió sin ficha, o se aplicó una ficha sin auditarla. Obedecer un diagnóstico sin verificarlo cambia un desperdicio por otro. |
| 3 | cuando la evidencia textual no explicó el fallo, se pidió la captura a la persona en vez de seguir iterando | Bloqueado: se siguió iterando a ciegas sobre algo que sólo se resuelve viendo la pantalla. Pedirla cuesta un turno; adivinarla cuesta la tanda entera. |

## Cross-links

`[[calidad-deterministic-work-to-tooling]]`, `[[calidad-test-self-correction-loop]]`, `[[calidad-cold-audit-before-execution]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-test-execution-orchestration]]`, `[[calidad-repo-capability-discovery]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-pipeline-state-tracking]]`, `[[calidad-test-self-healing]]`, `[[calidad-alm-write-authorization-gate]]`.
