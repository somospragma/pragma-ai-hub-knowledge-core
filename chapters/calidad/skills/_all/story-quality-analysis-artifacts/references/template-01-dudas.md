# Dudas y ambigüedades — {{hu}} · {{titulo}}

Fecha: {{fecha}} · Épica: {{epica}} · Estado: {{estado}}
Fuente: `{{fuente}}` · Arquitectura: `{{arquitectura}}`

Enfoque: **qué necesita Calidad para poder probar esta historia**. No es una crítica de la
historia: cada línea es una pregunta concreta con dueño, que alguien tiene que contestar
antes de que un caso se pueda ejecutar.

> Este archivo es el **único registro de dudas** de esta historia. No se crea un documento
> de dudas aparte ni se duplican aquí las de otra historia: ver `single-registry-rule.md`.

## Resumen de la historia en una línea

_Qué hace, sobre qué, y qué la condiciona. Una frase, para que quien retome no tenga que
abrir la historia._

## Bloqueantes: sin esto no se puede ejecutar

| # | Tema | Duda | Por qué bloquea a Calidad | Responsable |
|---|---|---|---|---|
| B1 |  |  |  |  |

Responsable, uno de: **cliente-datos** · **arquitecto** · **po-negocio** · **dev-pragma** · **qa**.
Catálogo y regla de enrutamiento en `[[calidad-responsibility-routing-of-blockers]]`.

## Condicionan el diseño de las pruebas

Sin respuesta se puede empezar, pero el caso puede quedar mal diseñado.

| # | Tema | Duda | Responsable |
|---|---|---|---|
| C1 |  |  |  |

## Supuestos de trabajo, a validar

Lo que se está dando por cierto para poder avanzar. Un supuesto que nadie confirma es una
duda disfrazada, y se paga cuando el caso falla y parece un defecto.

1.
2.

## Números que van a gobernar una espera o una aserción

Todo valor de la historia que se vaya a convertir en un temporizador, un umbral o una
comparación, con **las dos lecturas posibles** cuando las haya. Ni el valor por defecto que
menciona la historia ni lo que muestra la interfaz son fuentes válidas
(`[[calidad-funcional-story-analysis]]`).

| Valor | Dónde aparece | Lectura A | Lectura B | Confirmado por |
|---|---|---|---|---|

## Hallazgos confirmados

Lo que se resolvió al leer la historia íntegra y su arquitectura, con la duda que cierra.
Se anexa, no se reescribe lo de arriba: la duda queda visible junto a su respuesta.

- **Hallazgo** — … Resuelve B1, C2.
