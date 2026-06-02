# Sharding y Paralelización por Framework

Cada framework tiene un modelo distinto de paralelización. Aplicar la estrategia incorrecta degrada el tiempo de ejecución o produce flakiness por contención de recursos.

## Playwright — `--shard=i/n` nativo

Playwright **divide automáticamente** la lista de specs entre N shards. Cada shard ejecuta una fracción independiente.

```bash
# Shard 1 de 4
npx playwright test --shard=1/4

# Shard 2 de 4 (en paralelo, otro runner)
npx playwright test --shard=2/4
```

**Reglas:**
- Combinar `--shard` con `workers` por shard: `--workers=4 --shard=1/4` ejecuta 4 specs en paralelo dentro del shard 1.
- En CI, total de workers efectivos = `workers * shards`. Calibrar contra capacidad del SUT.
- **Reportes**: cada shard genera su propio JUnit/HTML; se agregan post-execution con `npx playwright merge-reports`.

```bash
# Después de las jobs
npx playwright merge-reports --reporter=html ./all-blob-reports
```

## Karate — `karate.parallel` con threads

Karate paraleliza **scenarios** dentro de un mismo proceso JVM usando un pool de threads. NO shardea entre runners de forma nativa.

```bash
mvn test -Dtest=RegressionRunner -Dkarate.options="--threads 4"
```

```java
// RegressionRunner.java
@Test
void testParallel() {
    Results results = Runner.path("classpath:features")
        .tags("@regression")
        .parallel(4);  // 4 threads
    assertEquals(0, results.getFailCount());
}
```

**Para sharding entre runners** (cuando 1 sola JVM no es suficiente):
- Dividir por tags: runner A ejecuta `@regression-A`, runner B ejecuta `@regression-B`.
- Dividir por feature directory: runner A `--features=src/test/users`, runner B `--features=src/test/orders`.
- Combinar resultados con `karate-summary-json.txt` agregado en step posterior.

## K6 — NO shardear, distribuir VUs

K6 es la **herramienta de carga**: el objetivo es generar concurrencia controlada contra el SUT, NO acelerar la ejecución. Shardear el script entre runners **no tiene sentido funcional**.

**En su lugar:**

- **Un solo runner con N VUs**: simple y reproducible.
  ```bash
  k6 run --vus 100 --duration 10m load.js
  ```
- **Múltiples runners coordinados** (cuando un solo runner no genera carga suficiente — típico desde 5000+ VUs):
  - Cada runner genera una fracción de VUs (`--vus 1000` x 5 runners = 5000 VUs efectivos contra el SUT).
  - Coordinar inicio con scheduler externo o `k6 cloud` (Grafana Cloud k6).
  - **NO usar `parallel:matrix`** — desincroniza el inicio y rompe la curva de carga.

```yaml
# Coordinación cruda con startTime sincronizado
k6:load:distributed:
  parallel: 5
  script:
    - k6 run --vus 1000 --duration 10m --start-time=$START_TIME load.js
```

Para cargas >10k VUs, recomendar **Grafana Cloud k6** o **k6 operator en Kubernetes** (manejan el sharding automáticamente).

## Appium — Paralelo por device en grid

Appium paraleliza **por device físico/emulador**. Una sola JVM puede manejar múltiples sesiones Appium concurrentes si cada una apunta a un device distinto.

### Local (limitado)

```java
// TestNG parallel
@DataProvider(parallel = true)
public Object[][] devices() {
    return new Object[][] {
        {"Pixel_7_API_34"},
        {"Pixel_5_API_31"}
    };
}
```

Limitación: cada emulador consume ~4GB RAM. Realistic: 2-3 emuladores concurrentes por runner.

### Cloud (recomendado para paralelismo real)

**BrowserStack App Automate / Sauce Labs / AWS Device Farm** ejecutan sesiones concurrentes en su infraestructura. El paralelismo se limita por el plan contratado (típicamente 5-20 sesiones simultáneas).

```yaml
# pipeline matrix por device
strategy:
  matrix:
    device:
      - {name: 'Samsung Galaxy S23', os: '13'}
      - {name: 'Pixel 7', os: '14'}
      - {name: 'OnePlus 11', os: '14'}
```

Cada job inicia una sesión Appium contra el cloud apuntando al device de la matrix. El paralelismo efectivo = min(matrix size, plan concurrency).

## Tabla resumen

| Framework  | Estrategia nativa            | Sharding entre runners | Recomendación                        |
| ---------- | ---------------------------- | ---------------------- | ------------------------------------ |
| Playwright | `--shard=i/n` + workers      | Sí, nativo             | 4-8 shards x 4 workers               |
| Karate     | `--threads N`                | Manual (por tag/dir)   | 4-8 threads, 2-4 runners por tag     |
| K6         | NO aplica                    | NO recomendado         | 1 runner o Grafana Cloud k6          |
| Appium     | Paralelo por device          | Matrix por device      | Cloud provider (BrowserStack/Sauce)  |

## Anti-patterns

- Shardear K6 entre runners para acelerar — pierdes la curva de carga.
- Karate `--threads 16` en runner con 2 vCPU — context switching destruye performance.
- Playwright `--shard=10/10` con SUT que no soporta concurrencia — flakiness por race conditions.
- Appium en 10 emuladores en un solo runner — OOM garantizado.
