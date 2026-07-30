
# Niveles, tipos y cuadrantes

## Niveles de prueba (quién cubre qué)

| Nivel | Dueño principal | Qué verifica | Stack del chapter |
|---|---|---|---|
| Unitario | Desarrollo (TDD) | Lógica pura, fórmulas, ramas de código | — (frontera pactada, no lo cubre QA) |
| Componente / API | QA + dev | Contratos, reglas de negocio expuestas, integraciones | Karate |
| Contract | QA + dev | Compatibilidad consumer/provider entre servicios | [[calidad-contract-testing]] |
| E2E UI web | QA | Flujos de usuario end-to-end en browser | Playwright |
| Mobile | QA | Flujos en app Android | Appium |
| Performance | QA + infra | Latencia, throughput, degradación bajo carga | K6 |

Principio de pirámide: cada comportamiento se verifica en el **nivel más bajo capaz de observarlo**. Un flujo cuya regla se puede validar por API no gana nada validándose solo por UI (más lento, más frágil); la UI verifica lo que solo la UI muestra.

## Cuadrantes ágiles (qué tipos de prueba existen y para qué)

| | Soportan al equipo | Critican el producto |
|---|---|---|
| **De cara al negocio** | Q2: funcionales de aceptación, ejemplos BDD, prototipos | Q3: exploratorio, UAT, usabilidad |
| **De cara a la tecnología** | Q1: unitarias, componente | Q4: performance, seguridad, accesibilidad, resiliencia |

Uso práctico: la estrategia debe tener respuesta para los 4 cuadrantes — aunque la respuesta sea "Q3 exploratorio: 2 charters por sprint" o "Q4 seguridad: solo escaneo pasivo, pentest fuera de alcance". Cuadrante sin mención = hueco no decidido.

Los tipos del Q4 se resuelven con las capas transversales del chapter ([[calidad-transversal-capabilities]]): seguridad, accesibilidad, visual, SEO, performance — la estrategia declara cuáles aplican y con qué profundidad.

## Formato del documento de estrategia (standalone)

```markdown
# Estrategia de pruebas — {producto/iniciativa}
1. Contexto y alcance (qué producto, qué releases, qué queda fuera)
2. Enfoque por niveles (tabla nivel → dueño → herramienta → cobertura objetivo)
3. Tipos y capas transversales (qué aplica, con qué profundidad, qué no y por qué)
4. Enfoque risk-based (resumen del risk map; dónde va el esfuerzo y qué recibe menos)
5. Práctica del equipo y frontera con dev (BDD/ATDD, pacto de lo unitario)
6. Datos y ambientes (estrategia de datos, ambientes por nivel, camino mock->real si aplica)
7. Automatización (qué stacks se activan, criterio de qué se automatiza vs manual/exploratorio)
8. Supuestos y decisiones de riesgo aceptadas
```

Extensión objetivo: 2-4 páginas. Una estrategia que nadie lee no gobierna nada — el detalle operativo vive en el plan ([[calidad-funcional-test-plan]]), no aquí.
