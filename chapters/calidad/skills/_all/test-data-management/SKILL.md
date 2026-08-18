---
id: calidad-test-data-management
version: 1.2.0
scope: chapter
type: skill
chapter: calidad
description: "Estrategia de gestión de datos de prueba: builders, factories, anonimización, seeding, cleanup, datos sintéticos."
tags: [test-data, builders, factory, anonymization, hipaa, ccpa, ley-1581, lgpd, faker, synthetic-data]
---

# Test Data Management — Datos de Prueba Reproducibles y Conformes

## Cuándo aplicar

Aplica este skill **cada vez que se diseñe una suite que requiera datos consistentes, reproducibles y conformes a normativa** — es decir, prácticamente toda suite no trivial.

Es especialmente crítico en clientes regulados de LATAM y Estados Unidos:

| Jurisdicción | Marco principal |
|---|---|
| Estados Unidos | HIPAA (salud), CCPA/CPRA (California), SOX (financiero público), GLBA (financiero), FedRAMP (gobierno) |
| Brasil | LGPD (Lei 13.709) |
| Colombia | Ley 1581 / Decreto 1377 |
| México | LFPDPPP |
| Argentina | Ley 25.326 |
| Chile | Ley 19.628 / Ley 21.719 (2024) |
| Perú | Ley 29.733 |
| Otras LATAM (Centroamérica, Caribe, Uruguay, Bolivia, Ecuador, Paraguay, Venezuela) | Aplicar marco análogo local + estándares internacionales (ISO 27001, SOC 2, PCI-DSS) como mínimo común |

Estos marcos prohíben usar datos productivos en ambientes de prueba sin anonimización. Este skill define la estrategia para evitar esa exposición y al mismo tiempo garantizar **reproducibilidad** (mismo seed → mismo dataset → mismos resultados).

Activa este skill en paralelo con `[[calidad-karate-greenfield]]`, `[[calidad-karate-brownfield]]`, `[[calidad-playwright-greenfield]]`, `[[calidad-k6-greenfield]]` o `[[calidad-appium-screenplay-android]]`. Coordina con `[[calidad-mandatory-inputs-protocol]]` para obtener catálogo de datasets disponibles del cliente.

## Instrucción

0. **Confirmar disponibilidad de datos PRIMERO y respetar la precedencia de fuentes** — La pregunta del `[[calidad-sut-readiness-gate]]` (¿existen datos de prueba o catálogo del cliente?) se hace AL INICIO, no como último recurso. Precedencia estricta:
   1. **Data real / catálogo del cliente** (con anonimización cuando aplique).
   2. **`examples` del spec y valores de la firma** — son parte del contrato; se usan tal cual.
   3. **Sintética determinista** (Faker + seed fijo, pasos 2-4) para todo lo que 1 y 2 no cubran.

   **PROHIBIDO el camino observado en pruebas de campo**: "inventar" datos con criterio del agente cuando el spec no trae examples. Un dato improvisado sin seed no es reproducible entre corridas — rompe el determinismo que es el objetivo de toda esta capacidad. Si falta un dato y ninguna fuente lo provee, se genera con Faker + seed (reproducible) o se pregunta; nunca se improvisa.

   Si NO hay datos (`data_strategy: synthetic`), la ausencia NO detiene la construcción de la suite: si hay mock de servicios (`[[calidad-service-virtualization-mockoon]]`), el mismo seed y locale alimentan sus data buckets para que test y mock sean coherentes end-to-end. El switchover a datos reales es parte del plan de certificación, no un cambio de código.
0.5. **Evaluar SUFICIENCIA, no solo existencia** — Que haya datos no significa que sirvan: los que existen son los que necesitaron las pruebas anteriores. Una vez planificados los escenarios y **antes** de emitir la estrategia, derivar de ellos la matriz de datos requeridos —entidad, **estado que exige**, si existe en el ambiente, quién lo gestiona y para cuándo— y comunicar al QA en el chat, de forma explícita y accionable, lo que falta gestionar. Contra mocks el dato faltante se sintetiza y se declara como sintético; **contra software ya desarrollado es un bloqueo con fecha**, porque conseguirlo puede exigir trámite o intervención de otro equipo. Procedimiento completo, plantilla del mensaje y validación cruzada contra el catálogo en `references/data-sufficiency-gate.md`.
1. **Definir alcance** — ¿el dato es para unit, integration, e2e o performance? La estrategia cambia drásticamente. Matriz en `references/test-data-strategies.md`.
2. **Elegir estrategia** — `synthetic` (generado on-the-fly, default) vs `anonymized prod-like` (snapshot prod pasado por pipeline de anonimización, sólo cuando volumen/realismo lo exija). Anonimización detallada en `references/anonymization-pii.md`.
3. **Diseñar el patrón de construcción** — Object Mother, Test Data Builder o Factory según contexto. Snippets canónicos por lenguaje en `references/builder-factory-objectmother-patterns.md`.
4. **Integrar Faker con seeds deterministas** — Elegir locales según jurisdicción del cliente dentro del alcance del Chapter: `en_US`, `es_CO`, `es_MX`, `es_AR`, `es_CL`, `es_PE`, `pt_BR`, y `es` genérico para Centroamérica + Caribe + otros donde no haya locale dedicado. Seed fijo en CI. Reglas y anti-patrones en `references/synthetic-data-faker.md`.
5. **Seeding y cleanup transaccional** — Por framework: Karate `Setup.feature`, k6 `setup()/teardown()`, Playwright `globalSetup/globalTeardown`, Spring `@Transactional` rollback. Patrones en `references/seeding-cleanup-transactional.md`.
6. **Anonimizar por columna** — Reglas por tipo de dato: cédulas, RUT, teléfono, email, dirección, tarjeta (Luhn-valid pero fake), IBAN. Ver `references/anonymization-pii.md`.
7. **Catalogar datasets versionados** — Naming, almacenamiento (git LFS, DVC, S3 con tags), regeneración cuando cambia el esquema. Estrategia en `references/datasets-versioning.md`. Para perf, consideraciones específicas en `references/data-for-perf-testing.md`.

## Restricciones

- **NUNCA** usar datos productivos sin anonimización en ningún ambiente que no sea producción. Es una violación legal en LATAM y Estados Unidos bajo los marcos listados arriba y un riesgo reputacional grave.
- **NUNCA** commitear datasets que contengan PII real, ni siquiera "para que sea más fácil reproducir un bug". Si un dataset llegó a la rama, debe purgarse del historial (`git filter-repo`) y se debe notificar al cliente.
- **SIEMPRE** documentar la política de retención de los datasets sintéticos/anonimizados: por defecto se rotan cada release.
- **SIEMPRE** usar seed fijo en CI (`FAKER_SEED=12345`) para garantizar reproducibilidad. Local puede usar seed aleatorio sólo si se loguea el seed usado para poder reproducir.
- **NUNCA** mezclar cleanup transaccional con cleanup por API admin en la misma suite sin documentarlo: confunde la traza.
- Encadena con `[[calidad-test-evidence-and-traceability]]` para que el `seed`, el ID del dataset y la versión queden registrados en cada reporte.
- Sigue `[[calidad-mandatory-inputs-protocol]]` para confirmar al inicio: ¿hay catálogo de datasets del cliente? ¿qué framework de anonimización usa? ¿qué políticas de retención aplican?
- Con `data_strategy: synthetic` + mock de servicios: las aserciones de los tests validan contrato y reglas de negocio (formato, presencia, eco del request), NUNCA valores literales que solo existen en el dataset sintético del mock — de lo contrario el switchover a datos reales rompe la suite.
- Si el cliente requiere snapshot prod-like, exige el dataset anonimizado por el equipo de datos del cliente; **no** anonimices tú dumps productivos.

## Cross-links

- `references/test-data-strategies.md`
- `references/builder-factory-objectmother-patterns.md`
- `references/anonymization-pii.md`
- `references/synthetic-data-faker.md`
- `references/seeding-cleanup-transactional.md`
- `references/datasets-versioning.md`
- `references/data-for-perf-testing.md`
