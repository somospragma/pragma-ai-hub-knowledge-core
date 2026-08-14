# Cadena de Evidencia para Declarar un Defecto del SUT

Declarar un defecto del SUT es una afirmación sobre el producto del cliente que llega a su equipo de desarrollo y consume tiempo ajeno. Un falso positivo cuesta credibilidad al chapter; y un falso positivo repetido hace que los defectos reales dejen de atenderse.

Verificado en campo: se reportó un defecto del SUT en una corrida donde **la aplicación nunca se abrió** y la sesión apuntaba a un destino distinto del que se había levantado. El árbol de decisión (`bug-vs-test-design-decision-tree.md`) clasificaba bien, pero **no exigía que la evidencia existiera**.

Esta reference cierra ese hueco: son las precondiciones que deben cumplirse **antes** de entrar al árbol con el nodo "bug del SUT".

## Las seis precondiciones

Acumulativas. Si falta una, **no se puede clasificar `bug_sut`**; el fallo sigue en triage.

| # | Precondición | Cómo se demuestra |
|---|---|---|
| 1 | **Preflight verde en la corrida que produjo el fallo** | `.evidence/preflight.json` de esa corrida, con todas las sondas en `pass` (`[[calidad-execution-preflight]]`). Sin esto no está demostrado que la corrida llegara a tocar el SUT |
| 2 | **Evidencia capturada en el instante del fallo** | Captura de pantalla y volcado de la jerarquía o del DOM tomados en el fallo, no reconstruidos después ni de una corrida distinta |
| 3 | **Fallo determinista** | Protocolo de re-ejecución de `re-run-protocol-for-determinism.md` con el mismo error en todas las repeticiones |
| 4 | **Descartes de causa técnica documentados** | Ver la lista de abajo: cada descarte con su evidencia. Un descarte sin evidencia no cuenta |
| 5 | **Contraste multiplataforma** | Si la historia cubre varias plataformas: ¿falla igual en las demás? Un fallo en una sola plataforma apunta a implementación específica antes que a defecto funcional (`[[calidad-cross-platform-learning-propagation]]`) |
| 6 | **Cita textual del criterio de aceptación incumplido** | El texto literal del criterio, no una paráfrasis. Si no hay criterio que lo respalde, no es defecto: es una expectativa del agente |

**Reproducción manual**: se ejecuta el mismo paso a mano y se describe el resultado. Si no fue posible, se declara explícitamente por qué. Es lo primero que va a pedir el equipo de desarrollo.

## Los descartes obligatorios (precondición 4)

La regla inversa, tan importante como las seis anteriores:

> **"No encontré el elemento" nunca es, por sí solo, un defecto del SUT.**

Es primero un fallo de localizador, de espera, de contexto, de datos o de ambiente. Antes de clasificar como defecto hay que descartar, **cada uno con su evidencia**:

1. **Localizador** — el identificador existe en la jerarquía capturada. Si no existe en la captura, el problema es el localizador o la pantalla no es la esperada, no el SUT.
2. **Ancla volátil** — el localizador o la aserción no dependen de contenido que cambia entre registros (`[[calidad-data-volatility-and-assertion-anchoring]]`).
3. **Espera** — el elemento no aparece más tarde; el fallo no es de sincronización.
4. **Contexto** — en aplicaciones híbridas, el contexto activo es el correcto.
5. **Visibilidad real** — el elemento no está presente pero oculto, deshabilitado o tapado por otro.
6. **Estado y datos** — el escenario partió del estado que declara su precondición y los datos de prueba son los acordados (`[[calidad-test-data-management]]`).
7. **Pantalla correcta** — la captura demuestra que el flujo llegó a donde debía. Un flujo que se desvió falla en el sitio equivocado.

## Salida obligatoria

Cuando las seis precondiciones se cumplen, el triage emite el **bloque de reporte de defecto** listo para el ALM, que es lo que después consume `[[calidad-alm-test-publishing-cycle]]`:

```markdown
## Defecto del SUT — <identificador de la historia>

**Criterio de aceptación incumplido** (textual): "<cita>"
**Comportamiento esperado:** <lo que el criterio exige>
**Comportamiento observado:** <lo que hace la aplicación>
**Determinismo:** N/N repeticiones con el mismo error
**Plataformas afectadas:** <en cuáles falla y en cuáles no>
**Reproducción manual:** <pasos y resultado, o razón por la que no se pudo>
**Preflight:** verde — <ruta de la evidencia>
**Evidencia:** <captura del fallo, volcado de jerarquía, log>
**Descartes realizados:** <lista con su evidencia>
**Escenario afectado:** <identificador del test> — permanece en rojo hasta corrección
```

## Qué pasa después

- El test **permanece fallando**. No se modifica, no se marca como omitido, no se ajusta la aserción para que pase. Es la regla anti-cheating del chapter: el test está correcto y el SUT no.
- El defecto no entra a `[[calidad-test-self-correction-loop]]`.
- El escenario **no** va a quarantine por esta causa: quarantine es para inestabilidad, no para defectos confirmados. Un defecto confirmado es un rojo legítimo con su reporte asociado.
- La publicación del defecto en el ALM pasa por `[[calidad-alm-write-authorization-gate]]`.

## Restricción final

**NUNCA** declarar un defecto del SUT con la cadena incompleta, ni siquiera "provisionalmente" o "para que el cliente lo revise". Un reporte con evidencia parcial es indistinguible de uno falso para quien lo recibe.
