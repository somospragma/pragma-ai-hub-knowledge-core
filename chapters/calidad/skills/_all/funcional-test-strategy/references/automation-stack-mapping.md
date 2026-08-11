
# Mapeo de la estrategia a los stacks de automatización del chapter

La estrategia decide QUÉ se automatiza y DÓNDE; los stacks ejecutan. Esta reference es el puente formal entre el stack funcional y los 4 de automatización.

## Matriz de decisión

| Decisión estratégica | Stack | Insumo que el stack exige | El diseño funcional aporta |
|---|---|---|---|
| Reglas de negocio expuestas por API, contratos | Karate | Spec OpenAPI/Swagger/WSDL (con response schemas si pre-desarrollo) | Casos Gherkin de alto nivel → `.feature` casi literales |
| SLAs de latencia/throughput, degradación | K6 | Spec + RNF/SLAs cuantificados | Los SLAs del plan/estrategia son los thresholds; escenarios de carga desde los flujos CRITICAL del risk map |
| Flujos de usuario web, estados visibles | Playwright | Fuente UI (URL viva / Figma) + locator map si pre-desarrollo | Casos de flujo → specs; matrices pairwise → projects/parámetros |
| Flujos en app Android | Appium | APK (o locator map + ejecución diferida) | Casos de flujo → features Screenplay |
| Capas transversales (a11y, seguridad, visual, SEO, contract) | vía [[calidad-transversal-capabilities]] | según capa | El risk map decide cuáles se activan con qué profundidad |
| Lo no automatizable / exploratorio / UAT | manual | — | Charters y casos paso-a-paso ([[calidad-funcional-test-design]]) |

## Reglas del puente

1. **Diseñar una vez, automatizar después**: los casos de alto nivel son la fuente; los stacks los implementan sin re-decidir el alcance. Si el stack descubre que un caso no es implementable, vuelve como hallazgo al diseño — no se descarta en silencio.
2. **Verificar viabilidad antes de comprometer**: estrategia que activa Karate sin spec disponible, o Playwright pre-desarrollo sin locator map, está prometiendo lo que `[[calidad-sut-readiness-gate]]` va a bloquear. La estrategia declara el estado de esos insumos y el camino (mock → real) cuando el desarrollo no existe.
3. **Trazabilidad continua**: HU → CA → caso de alto nivel (funcional) → test automatizado (tag `@user-story:`) → resultado → ALM. La cadena completa es auditable; el eslabón funcional es el que este stack agrega.
4. **Criterio de qué se automatiza** (default del chapter, ajustable por estrategia): CRITICAL y HIGH del risk map se automatizan; MEDIUM selectivo (repetitividad × estabilidad del feature); LOW manual o diferido. Automatizar lo inestable o lo de un solo uso es deuda, no avance.
5. **Los resultados vuelven**: la ejecución de los stacks (delivery gate, executive report) se publica al ALM vía `[[calidad-alm-mcp-integration]]` — estados de test cases, defectos, evidencia — cerrando el ciclo que la estrategia abrió.

## Entrada por el router

Cuando la estrategia dispara generación de automatización, se entra por `[[calidad-route-test-generation]]` con el intent y los insumos por stack; el STRATEGY.md operativo de cada stack (`[[calidad-pre-design-strategy-document]]`) referencia esta estrategia general como su marco (sección 1, Contexto).
