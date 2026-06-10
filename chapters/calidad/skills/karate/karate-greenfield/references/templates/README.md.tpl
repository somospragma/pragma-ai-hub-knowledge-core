# {{project_name}}

Proyecto de pruebas API con Karate generado a partir de `{{spec_source}}`.

## Prerequisitos

- **Java 11 o 17** (NO 12-16, NO 18+ — Karate 1.4.1 exige LTS).
- **Maven 3.6+**.
- **`jq`** opcional para parsear `karate-summary.json` en CI. Alternativa: `python -m json.tool`.

Verificación rápida:

```bash
java -version    # debe mostrar 11.x o 17.x
mvn -version     # debe mostrar 3.6+
jq --version     # opcional
```

## Quick start

```bash
./scripts/preflight.sh     # valida prereqs (Java, Maven, jq)
mvn test -f pom.xml

# Ver summary sin jq:
python -m json.tool target/karate-reports/karate-summary-json.txt 2>/dev/null | head
```

Filtros por tag:

```bash
mvn test -f pom.xml -Dkarate.options="--tags @smoke"
mvn test -f pom.xml -Dkarate.options="--tags @main"
mvn test -f pom.xml -Dkarate.options="--tags @contract"
```

Override de URL base:

```bash
mvn test -f pom.xml -Dkarate.env=staging
# karate-config.js mapea karate.env → baseUrl
```

## Estructura del proyecto

```
{{project_name}}/
├── pom.xml
├── README.md
├── scripts/preflight.sh
└── src/test/java/
    ├── karate-config.js
    ├── logback-test.xml
    ├── com/testing/
    │   ├── TestRunner.java
    │   └── features/
    │       └── {{resource}}.feature       # tag # cobertura: N obligatorio
    ├── schemas/
    │   └── {{resource}}-match.json
    └── resources/files/                   # assets para multipart/upload
```

## Evidencia

Tras cada `mvn test`:

- `target/karate-reports/karate-summary-json.txt` — summary nativo.
- `results/karate/{YYYY-MM-DD}/{ISO}-metadata.json` — metadata universal (schema cross-stack).
- `.evidence/execution-status.json` — sólo si hubo bloqueo de ambiente.

## Cobertura

Cada `.feature` declara `# cobertura: <N>` en primera línea (donde N = `effective_minimum` calculado por la fórmula de cobertura negativa). El delivery_gate audita que el conteo real de escenarios `@main` cumpla N.

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `UnsupportedClassVersionError` | JDK incompatible (>17). | Cambiar a JDK 11 o 17. |
| `mvn test` cuelga sin output | Surefire log buffering. | Agregar `-X` o `-e` para verbose. |
| Feature no se ejecuta | Tag exclusión activa en `TestRunner`. | Revisar `@tags("~@ignore")` en runner. |
| 403 sostenido | WAF/CDN bloquea CI. | Revisar `.evidence/execution-status.json` y escalar a infra. |
