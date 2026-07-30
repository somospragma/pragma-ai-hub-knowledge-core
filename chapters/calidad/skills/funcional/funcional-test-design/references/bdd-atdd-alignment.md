
# Alineación con la estrategia de desarrollo (BDD / ATDD / TDD)

El diseño de casos no vive en el vacío: se acopla a cómo el equipo desarrolla. Preguntar SIEMPRE cuál es la práctica del equipo antes de elegir el formato final — no asumir.

## Qué cambia según la práctica

| Práctica del equipo | Qué son los casos de alto nivel | Implicación para el diseño |
|---|---|---|
| **BDD** (Behaviour-Driven Development) | Los ejemplos ejecutables del comportamiento: el MISMO Gherkin que la automatización consumirá | Gherkin en español disciplinado (Dado=contexto, Cuando=UN evento, Entonces=resultado observable); los escenarios se escriben ANTES del desarrollo (salen del example map de [[calidad-funcional-story-refinement]]); lenguaje ubicuo del dominio (los términos del PO, no jerga técnica) |
| **ATDD** (Acceptance-TDD) | Los criterios de aceptación convertidos en pruebas acordadas ANTES de codificar | El set de casos se cierra con PO+dev+QA antes del sprint (Tres Amigos); el "done" de la HU es que estos casos pasen; formato Gherkin o tabla según tooling |
| **TDD** (Test-Driven Development) | TDD es práctica de diseño de código (unitaria) del developer — NO la reemplaza el QA | El diseño funcional NO duplica lo unitario: se enfoca en comportamiento de negocio observable; coordinar la frontera (qué valida dev en unitarias vs qué valida QA) en la estrategia |
| **Tradicional / sin práctica declarada** | Casos en formato paso-a-paso ejecutables por un humano | Formato "paso | resultado esperado" (mapea nativo a Azure Test Plans); Gherkin sigue siendo válido si el equipo lo lee bien |

## Reglas de disciplina Gherkin (cuando aplica BDD/ATDD)

1. **Un Cuando por escenario** — un solo evento disparador. Varios Cuando = varios escenarios o un flujo mal partido.
2. **Declarativo, no imperativo**: "Cuando el cliente confirma la transferencia" y no la secuencia de clicks. El paso imperativo pertenece a la capa de automatización (step definitions / POM).
3. **Dado sin acciones del usuario** — es estado del mundo, idealmente sembrable por datos (`[[calidad-test-data-management]]`).
4. **Entonces sin nuevas acciones** — solo verificaciones.
5. Los escenarios diseñados aquí son los que los stacks de automatización implementan: Karate/Appium los toman casi literales como `.feature`; Playwright los mapea a specs. Diseñar una vez, automatizar después — no re-diseñar en cada stack.

## Frontera con lo unitario (evitar doble cobertura)

La pirámide manda: reglas puras de cálculo (redondeos, fórmulas) se cubren en unitarias del dev; el diseño funcional cubre el comportamiento integrado y observable. Si un CA es 100% cálculo puro, el caso funcional verifica UN ejemplo representativo end-to-end y anota "cobertura exhaustiva de la fórmula: unitarias" — la matriz de trazabilidad lo registra así en vez de duplicar 20 filas de BVA que el dev ya cubre. Esta frontera se pacta en `[[calidad-funcional-test-strategy]]`.
