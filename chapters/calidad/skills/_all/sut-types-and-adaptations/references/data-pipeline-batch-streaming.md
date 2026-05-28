# Data Pipelines — Batch y Streaming

## Patrones canónicos

- **Data quality** como contrato: no es opcional. Cada dataset productivo tiene expectativas explícitas (no-nulls, ranges, uniqueness, freshness, referential integrity).
- **Transformaciones SQL idempotentes**: la re-ejecución del mismo modelo dbt produce el mismo resultado (uso de `unique_key`, materializations `incremental`).
- **Schema evolution**: agregar columnas es FORWARD-compatible; eliminar o renombrar requiere coordinar con consumers downstream.
- **Data lineage**: cada tabla declara su upstream y downstream. Validar con `dbt docs` o herramientas de lineage (OpenLineage, DataHub).
- **Late-arriving data**: ventanas con tolerancia y watermarks (Flink, Spark Structured Streaming).
- **Backfills**: re-procesamiento histórico debe ser predecible — los tests cubren al menos un backfill end-to-end.
- **Consumer lag SLA**: para streaming, el lag (segundos detrás del head) tiene SLA; alertas y tests sobre el lag.

## Framework primario

- **Great Expectations**: tests declarativos sobre datasets (parquet, CSV, tablas SQL). Genera "data docs" como evidencia.
- **dbt tests** (`unique`, `not_null`, `accepted_values`, `relationships`) + tests custom en SQL/Python.
- **Flink Test Harness** (`StreamTaskTestHarness`, `KeyedOneInputStreamOperatorTestHarness`) para operators de streaming.

## Complementarios

- **Pytest fixtures custom** para cargar samples deterministas en S3/GCS/ADLS local (con minio o moto).
- **Airflow DAG tests**: `airflow dags test`, `pytest-airflow`, validar dependencias y orden de tasks.
- **Schema Registry validation** en streams (ver `event-driven-messaging.md`).
- **k6 NO aplica**: los batch pipelines no reciben HTTP load. La carga se simula con datasets sintéticos de tamaño real (Faker, dbt-faker, synthetic-data libraries).

## Patrón canónico: Great Expectations sobre output de un job

```python
import great_expectations as gx

context = gx.get_context()
batch = context.sources.add_pandas("orders").read_csv("s3://datalake/orders/dt=2026-05-27/*.csv")

batch.expect_column_values_to_not_be_null("order_id")
batch.expect_column_values_to_be_unique("order_id")
batch.expect_column_values_to_be_between("amount", min_value=0, max_value=1e7)
batch.expect_column_values_to_match_regex("currency", r"^[A-Z]{3}$")
```

## Consumer lag SLA (streaming)

- Definir SLA: p. ej. lag < 60s en P95, < 5 min en P99.
- Monitorear con Kafka exporter + Prometheus, o Flink metrics.
- Test de regresión: simular un burst de 10x throughput y validar que el lag converge en < SLA tras el burst.

## Antipatrones

- Tratar pipelines como apps HTTP y meter k6 — no hay endpoint que cargar.
- Probar solo con datasets de muestra (10 rows) — los bugs aparecen con volumen real (skew, OOM, partition explosion).
- Olvidar el backfill — el primer reprocesamiento histórico falla en producción sin tests.
- No versionar las expectativas (Great Expectations suite) — los cambios silenciosos rompen alertas.
- Ignorar late-arriving data — los reportes diarios se construyen incompletos sin watermark explícito.
