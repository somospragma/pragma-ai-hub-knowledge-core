---
id: calidad-karate-runtime-traps
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: karate
description: "OBLIGATORIO. Comportamientos de Karate que producen cobertura falsa o suites lentas sin causa aparente: un escenario sin aserción pasa aunque el servicio devuelva 500, el Background se re-ejecuta por escenario, sin -T corre a un hilo, y las funciones del config pierden su clausura. Consultar antes de escribir el primer feature y al diagnosticar una suite Karate."
tags: [karate, aserciones, paralelismo, call-once, call-single, config, trampas, mandatory]
enforcement: mandatory
---

# Karate — Trampas de Runtime que No Fallan

## Cuándo aplicar

Antes de escribir el primer `.feature` de una suite Karate, y al diagnosticar una
suite existente que va lenta o que está verde y no debería.

Todas las de abajo tienen la misma forma: **no lanzan error**. Producen un verde
que no significa nada, o una lentitud sin causa visible.

## Instrucción

### 1. Un escenario sin aserción pasa aunque el servicio devuelva 500

**La más grave, y no tiene equivalente en Cucumber.** En Cucumber un step sin
aserción al menos ejecuta código; en Karate, un `When method GET` sin un
`Then status` posterior **completa el escenario con éxito sea cual sea la
respuesta**.

Un feature entero puede estar verde sin haber verificado nada. No es un
descuido teórico: es lo que produce cobertura reportada sobre servicios que
nunca se comprobaron.

**Todo escenario declara al menos un `status` o un `match`.** Esto es
verificable mecánicamente y por tanto va al gate, no a la buena voluntad — ver
más abajo.

### 2. Karate re-ejecuta el `Background` por cada `Scenario`

Una llamada cara en el `Background` —autenticarse, sembrar datos— **se paga una
vez por escenario**, no una vez por feature. Medido en un arquetipo real: 67
features invocaban el feature de token desde su `Background`, con 1.139
escenarios dentro. Resultado: **1.139 autenticaciones**.

| Qué usar | Cuándo |
|---|---|
| `call` | El resultado debe ser distinto en cada escenario |
| `callonce` | El resultado se reutiliza dentro del feature, **una vez por hilo** |
| `callSingle` | El resultado se reutiliza en toda la corrida, **una sola vez por JVM y seguro entre hilos** |

`callSingle` se declara en `karate-config.js`, no en el feature. Es lo que hace
viable compartir un setup caro con paralelismo.

### 3. Sin `-T`, Karate corre a un hilo — y no lo dice en el `--help`

Es el hallazgo que más veces se diagnostica al revés. Medido con un stub local
de latencia controlada y 20 escenarios:

| Patrón | Hilos | Llamadas caras | Tiempo |
|---|---:|---:|---:|
| `call` en `Background` | 1 | 20 | 8.964 ms |
| `callonce` | 1 | 1 | 3.871 ms |
| `call`, 5 hilos | 5 | 20 | 1.550 ms |
| `callonce`, 5 hilos | 5 | 1 | 1.128 ms |

**Reutilizar el setup multiplica por 2,3. El paralelismo multiplica por 5,8.**
La intuición apunta al setup repetido, y el multiplicador grande está en el
paralelismo. Los dos juntos, 7,9x.

Elegir el número de hilos se mira contra el **ambiente**, no contra el reloj:
límites de tasa y datos compartidos son el techo real.

### 4. Las funciones exportadas de `karate-config.js` pierden su clausura

Karate **recrea** cada función desde su texto fuente en un contexto JS nuevo.
Una función que cierra sobre una variable del config falla en ejecución con un
`ReferenceError` que nombra la variable, no la causa.

Todo lo que la función necesite se resuelve **dentro** de ella.

### 5. El reporte anterior se renombra en vez de reemplazarse

Salvo que se declare lo contrario, cada corrida conserva el reporte previo con
un sufijo de marca de tiempo, y el árbol se llena de copias. Importa más de lo
que parece cuando el publicador de resultados **lista un directorio**: sube lo
que encuentre, incluida una corrida vieja.

### 6. Al depurar, haz que el sistema diga lo que ve

Tres de estas trampas se encontraron devolviendo el estado observado en el
cuerpo de la respuesta, en vez de deducirlo del fallo. **Deducir costó tres
corridas; observar, una.** Aplica sobre todo a las cabeceras: en un mock pueden
llegar en minúsculas y como listas, y una comparación contra el nombre canónico
no casa nunca — con el síntoma de un `401` que parece fallo de autenticación y
no lo es.

## Lo que el gate debe hacer cumplir

Estas no se sostienen con disciplina; se verifican con un análisis estático del
Gherkin antes de ejecutar:

| Regla | Qué evita |
|---|---|
| `no-assertion` | Un escenario sin `status` ni `match`: pasa con un 500 |
| `missing-key` | Un escenario sin trazabilidad a requisito |
| `placeholder-key` | Un identificador sin sustituir: invisible para el ALM |
| `duplicate-key` | Dos escenarios con la misma key se pisan al publicar |
| `fixed-wait` | Esperas fijas; toda espera declara su condición observable |
| `xray-key-on-feature` | La key en el `Feature` — ver `[[calidad-alm-test-publishing-cycle]]` |

Un escenario compartido, que se invoca en vez de declarar casos, queda fuera de
las reglas de trazabilidad.

## Restricciones

- **NUNCA entregues un feature con un escenario sin `status` ni `match`.**
- **NUNCA pongas una llamada cara en el `Background` con `call`** sin haber
  contado cuántos escenarios tiene el feature.
- **NUNCA concluyas que una suite Karate es lenta sin comprobar primero si está
  corriendo a un hilo.** Es la causa más probable y la menos visible.
- **NUNCA declares un umbral de hilos mirando el reloj**: el techo lo pone el
  ambiente compartido.

## Cross-links

- `[[calidad-karate-greenfield]]` — construcción del arquetipo.
- `[[calidad-karate-brownfield]]` — extensión de una suite existente.
- `[[calidad-alm-test-publishing-cycle]]` — dónde va el identificador del ALM.
- `[[calidad-measure-before-proposing]]` — cómo se obtienen estas cifras en un
  repositorio heredado.
