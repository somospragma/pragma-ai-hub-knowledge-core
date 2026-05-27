# Estrategias de Datos de Prueba por Nivel

La estrategia óptima depende del nivel de prueba. Mezclar estrategias (ej. usar fixtures de e2e en pruebas unitarias) introduce acoplamiento y fragilidad.

## Matriz por nivel

| Nivel        | Estrategia recomendada                      | Volumen   | Cleanup                 | Reproducibilidad        |
|--------------|---------------------------------------------|-----------|-------------------------|-------------------------|
| Unit         | Mocks + factories simples in-memory         | 1-10      | GC (sin estado)         | Total (seed fijo)       |
| Integration  | DB efímera (testcontainers) + seeders       | 10-1.000  | Drop schema / rollback  | Total                   |
| E2E (UI/API) | Builders + cleanup por entidad o admin API  | 5-100     | API admin / DELETE      | Alta (con seeds)        |
| Performance  | Datasets sintéticos masivos pre-generados   | 10K-10M   | Truncate batch o ignore | Alta (mismo dataset)    |
| Security     | Datasets dirigidos + payloads adversariales | 1-100     | API admin               | Total                   |

## Detalle por nivel

### Unit

- **Estrategia**: factories puras en memoria. No tocan red ni disco.
- **Patrón**: Test Data Builder con valores por defecto razonables (`UserBuilder().build()` produce un User válido).
- **Cleanup**: ninguno; cada test crea sus instancias y la JVM/Node las descarta.
- **Tradeoff**: súper rápido y aislado, pero no detecta problemas de persistencia o serialización.

### Integration

- **Estrategia**: Testcontainers (Postgres, Mongo, Kafka) con esquema cargado por migración. Seeders cargan estado conocido al inicio de cada test.
- **Patrón**: `@BeforeEach` con `@Sql` (Spring) o `db.seed(usersFixture)` (Node). `@AfterEach` con rollback transaccional o `truncate`.
- **Cleanup**: `@Transactional` (Spring), `BEGIN/ROLLBACK` (Node), o drop/recreate schema por suite.
- **Tradeoff**: más realista, pero 10-100x más lento que unit. Usa testcontainers para evitar shared state.

### E2E (UI / API)

- **Estrategia**: dos opciones:
  - **A. Pre-seed por API admin**: la suite crea usuarios/datos vía un endpoint administrativo y los borra al final.
  - **B. Datasets pre-cargados en ambiente QA**: hay 100 usuarios fijos identificados por convención (`qa-user-001@example.com`). La suite los reutiliza sin cleanup.
- **Patrón A**: `Setup.feature` (Karate), `globalSetup` (Playwright). Tag `@cleanup-needed` para saber cuáles necesitan tear-down.
- **Patrón B**: ledger de usuarios documentado en el repo (sólo IDs, nunca credenciales). Riesgo: si un test contamina al usuario X, los siguientes fallan.
- **Cleanup**: por API admin (preferido) o por job nightly que resetea el ambiente.
- **Tradeoff**: A es más limpio pero más lento; B es más rápido pero requiere coordinación con el equipo del ambiente.

### Performance (k6)

- **Estrategia**: datasets sintéticos masivos pre-generados (JSON, CSV) cargados una vez por VU vía `SharedArray`. Nunca generar datos pesados on-the-fly por iteración.
- **Patrón**: dataset de 10K-1M usuarios serializado en disco, cargado en `setup()`, indexado por `__VU` y `__ITER`.
- **Cleanup**: depende de si la prueba es destructiva. Para read-heavy, ninguno. Para write-heavy, truncate batch al final.
- **Tradeoff**: requiere espacio (mitigar con git LFS / S3). Ver `data-for-perf-testing.md`.

### Security

- **Estrategia**: datasets pequeños y dirigidos: un user normal, un user admin, un user de otro tenant (para BOLA), payloads adversariales (XSS, SQLi, SSRF).
- **Patrón**: catálogo de payloads en `fixtures/payloads/` versionado.
- **Cleanup**: por API admin, especialmente si los payloads tocan tablas reales.

## Decisión rápida

```
¿es unit test?           → Builder/Factory in-memory.
¿integration con DB?     → Testcontainers + seeder + rollback.
¿e2e?                    → Builder + API admin para crear/destruir.
¿performance?            → Dataset sintético pre-generado + SharedArray.
¿security?               → Dataset dirigido + payloads adversariales.
```

## Anti-patrones

- **Reusar datos productivos**: ilegal en LATAM sin anonimización (Ley 1581, LGPD, etc.).
- **Hardcodear IDs entre tests**: acopla orden de ejecución y rompe paralelismo.
- **Generar datos distintos en cada corrida sin loguear el seed**: bugs irreproducibles.
- **Cleanup parcial**: deja residuos que contaminan corridas siguientes.
- **Compartir fixtures entre niveles**: cambios en el fixture de unit rompen e2e silenciosamente.
