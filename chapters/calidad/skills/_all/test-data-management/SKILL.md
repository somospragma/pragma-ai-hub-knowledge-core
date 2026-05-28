---
id: calidad-test-data-management
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Estrategia de gestión de datos de prueba: builders, factories, anonimización, seeding, cleanup, datos sintéticos."
tags: [test-data, builders, factory, anonymization, gdpr, ley-1581, faker, synthetic-data]
---

# Test Data Management — Datos de Prueba Reproducibles y Conformes

## Cuándo aplicar

Aplica este skill **cada vez que se diseñe una suite que requiera datos consistentes, reproducibles y conformes a normativa** — es decir, prácticamente toda suite no trivial.

Es especialmente crítico en cualquier cliente sujeto a regulación de protección de datos personales — sin presunción de jurisdicción específica:

| Jurisdicción         | Marco principal                                                |
|----------------------|----------------------------------------------------------------|
| UE / Reino Unido     | GDPR / UK-GDPR                                                 |
| Estados Unidos       | HIPAA (salud), CCPA/CPRA (California), SOX (financiero), GLBA  |
| Canadá               | PIPEDA                                                         |
| China                | PIPL                                                           |
| Brasil               | LGPD (Lei 13.709)                                              |
| Colombia             | Ley 1581 / Decreto 1377                                        |
| México               | LFPDPPP                                                        |
| Argentina            | Ley 25.326                                                     |
| Chile                | Ley 19.628 / Ley 21.719 (2024)                                 |
| Perú                 | Ley 29.733                                                     |
| Cualquier otra       | Aplicar marco análogo local + GDPR como mínimo común si hay usuarios EU |

Estos marcos prohíben usar datos productivos en ambientes de prueba sin anonimización. Este skill define la estrategia para evitar esa exposición y al mismo tiempo garantizar **reproducibilidad** (mismo seed → mismo dataset → mismos resultados).

Activa este skill en paralelo con `[[karate-greenfield]]`, `[[karate-brownfield]]`, `[[playwright-greenfield]]`, `[[k6-greenfield]]` o `[[appium-screenplay-android]]`. Coordina con `[[calidad-mandatory-inputs-protocol]]` para obtener catálogo de datasets disponibles del cliente.

## Instrucción

1. **Definir alcance** — ¿el dato es para unit, integration, e2e o performance? La estrategia cambia drásticamente. Matriz en `references/test-data-strategies.md`.
2. **Elegir estrategia** — `synthetic` (generado on-the-fly, default) vs `anonymized prod-like` (snapshot prod pasado por pipeline de anonimización, sólo cuando volumen/realismo lo exija). Anonimización detallada en `references/anonymization-pii.md`.
3. **Diseñar el patrón de construcción** — Object Mother, Test Data Builder o Factory según contexto. Snippets canónicos por lenguaje en `references/builder-factory-objectmother-patterns.md`.
4. **Integrar Faker con seeds deterministas** — Elegir locales según jurisdicción del cliente: por ejemplo `en_US`, `en_GB`, `de_DE`, `fr_FR`, `pt_BR`, `es_CO`, `es_MX`, `es_CL`, `es_AR`, `ja_JP`, `zh_CN`, etc. Seed fijo en CI. Reglas y anti-patrones en `references/synthetic-data-faker.md`.
5. **Seeding y cleanup transaccional** — Por framework: Karate `Setup.feature`, k6 `setup()/teardown()`, Playwright `globalSetup/globalTeardown`, Spring `@Transactional` rollback. Patrones en `references/seeding-cleanup-transactional.md`.
6. **Anonimizar por columna** — Reglas por tipo de dato: cédulas, RUT, teléfono, email, dirección, tarjeta (Luhn-valid pero fake), IBAN. Ver `references/anonymization-pii.md`.
7. **Catalogar datasets versionados** — Naming, almacenamiento (git LFS, DVC, S3 con tags), regeneración cuando cambia el esquema. Estrategia en `references/datasets-versioning.md`. Para perf, consideraciones específicas en `references/data-for-perf-testing.md`.

## Restricciones

- **NUNCA** usar datos productivos sin anonimización en ningún ambiente que no sea producción. Es una violación legal en prácticamente toda jurisdicción con marco de protección de datos personales y un riesgo reputacional grave.
- **NUNCA** commitear datasets que contengan PII real, ni siquiera "para que sea más fácil reproducir un bug". Si un dataset llegó a la rama, debe purgarse del historial (`git filter-repo`) y se debe notificar al cliente.
- **SIEMPRE** documentar la política de retención de los datasets sintéticos/anonimizados: por defecto se rotan cada release.
- **SIEMPRE** usar seed fijo en CI (`FAKER_SEED=12345`) para garantizar reproducibilidad. Local puede usar seed aleatorio sólo si se loguea el seed usado para poder reproducir.
- **NUNCA** mezclar cleanup transaccional con cleanup por API admin en la misma suite sin documentarlo: confunde la traza.
- Encadena con `[[calidad-test-evidence-and-traceability]]` para que el `seed`, el ID del dataset y la versión queden registrados en cada reporte.
- Sigue `[[calidad-mandatory-inputs-protocol]]` para confirmar al inicio: ¿hay catálogo de datasets del cliente? ¿qué framework de anonimización usa? ¿qué políticas de retención aplican?
- Si el cliente requiere snapshot prod-like, exige el dataset anonimizado por el equipo de datos del cliente; **no** anonimices tú dumps productivos.

## Cross-links

- `references/test-data-strategies.md`
- `references/builder-factory-objectmother-patterns.md`
- `references/anonymization-pii.md`
- `references/synthetic-data-faker.md`
- `references/seeding-cleanup-transactional.md`
- `references/datasets-versioning.md`
- `references/data-for-perf-testing.md`
