---
id: calidad-measure-before-proposing
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Batería de mediciones sobre un repositorio de pruebas heredado antes de proponer cualquier cambio, y cómo cerrar una decisión de arquitectura con un banco de pruebas en vez de con una discusión. Consultar ANTES de emitir un diagnóstico o una propuesta sobre una suite que no escribiste."
tags: [medicion, brownfield, diagnostico, arquitectura, banco-de-pruebas, mandatory]
enforcement: mandatory
---

# Medir Antes de Proponer

## Cuándo aplicar

Antes de emitir cualquier diagnóstico o propuesta sobre una suite de pruebas que
no escribiste: por qué va lenta, qué hay que reescribir, qué conviene migrar.

## Instrucción

**La premisa de partida suele estar mal diagnosticada, y leer archivos no lo
revela.** Dos arquetipos consecutivos, dos premisas falsas:

- *"El orquestador es lento."* El costo real era **cero paralelismo** más
  autenticarse por interfaz en cada escenario.
- *"El problema es pedir un token por escenario."* Cierto, pero el multiplicador
  del token era **2,3x** y el del paralelismo **5,8x**. Y ninguno era el problema
  estructural, que era que **el 42,8% del Gherkin eran cabeceras copiadas**.

Ninguna de esas cifras se ve leyendo. Lo que hace falta no es criterio: es
**contar**.

### La batería

Siete preguntas, cada una con su medición. Se contestan **con números** antes de
escribir una sola línea de propuesta.

| Pregunta | Cómo se responde |
|---|---|
| ¿Cuánto se repite? | Líneas útiles distintas frente al total |
| ¿Qué se repite? | Las 20 líneas más frecuentes |
| ¿Hay paralelismo? | Buscar la configuración de hilos o workers del runner |
| ¿Se reutiliza el setup caro? | Llamadas de una sola vez frente a llamadas por escenario — **y dónde está la llamada**: en un bloque que se re-ejecuta, una sola vez es cero veces |
| ¿Cuánto código no compila? | Comparar las exclusiones del build con los archivos que hay |
| ¿Se puede arrancar desde cero? | Variables que la configuración **lee** frente a las que la plantilla **documenta** |
| ¿Hay secretos versionados? | Buscar credenciales, tokens y almacenes de claves en el árbol |

Las dos últimas rara vez se piden y son las que más caro salen: una suite que no
arranca en una máquina limpia bloquea a quien entra, y un secreto versionado hay
que **considerarlo comprometido y rotarlo**, no solo borrarlo.

### Un banco de pruebas cierra lo que una discusión no cierra

Cuando la decisión es de arquitectura —dos patrones, dos configuraciones— no se
discute: se mide. **Un stub local con latencia controlada y N escenarios** se
monta en media hora y produce una tabla que zanja el asunto, sin tocar ambientes
reales, sin credenciales y sin esperar una ventana de ejecución.

Compara **una variable a la vez** y publica la tabla con la propuesta: es lo que
permite que alguien la refute con otra medición en vez de con otra opinión.

### Verificar que tu propio cambio se aplicó

**Un reemplazo de texto que no coincide no falla: no hace nada.** Toda edición
por script lleva una comprobación de que el texto buscado existía antes, y otra
de que el resultado quedó como se esperaba. Sin eso, media sesión puede correr
sobre archivos intactos.

Lo mismo para una búsqueda: una salida vacía puede ser «no hay resultados» o
puede ser «el comando no corrió». Comprobar el código de salida
(`[[calidad-repo-capability-discovery]]`).

### Copiar programáticamente, nunca transcribir

Cuando haya que trasladar valores de un sitio a otro —selectores, cabeceras,
identificadores—, se hace **con un script**, no leyéndolos por pantalla.
Transcribir a mano truncó un selector a 130 caracteres y produjo 19 localizadores
mal en un arquetipo real.

Y tiene un efecto lateral que justifica la regla por sí solo: **al copiar con un
script se ven las anomalías**. Así apareció que un archivo canónico de cabeceras
llevaba un valor mal escrito, mientras los escenarios lo escribían bien 528
veces.

## Restricciones

- **NUNCA propongas una reescritura, una migración o un cambio de arquitectura
  sin haber contestado la batería con números.** Una propuesta sin cifras no se
  puede refutar y por eso no se puede confiar en ella.
- **NUNCA aceptes la premisa con la que llega el encargo.** «Esto es lento
  porque X» es una hipótesis del que la trae, no un dato.
- **NUNCA midas dos variables a la vez** en el banco de pruebas: la tabla deja
  de decir cuál de las dos produjo la diferencia.
- **NUNCA des por aplicada una edición por script sin comprobarlo.**

## Cross-links

- `[[calidad-repo-capability-discovery]]` — el barrido cualitativo: qué existe.
  Esta batería es el cuantitativo: cuánto cuesta.
- `[[calidad-automation-feasibility-assessment]]` — qué se puede automatizar.
- `[[calidad-failure-triage-and-classification]]` — medir antes de clasificar,
  la misma disciplina aplicada a un fallo.
