# OpenAPI Diff — Detección de Breaking Changes

Comparar versiones del spec OpenAPI para detectar cambios que rompan a los consumers. Es el equivalente schema-first al `can-i-deploy` de Pact.

## Herramientas

| Tool                              | Lenguaje | Pros                                        | Contras                            |
| --------------------------------- | -------- | ------------------------------------------- | ---------------------------------- |
| **oasdiff** (Tufin)               | Go       | Categorización rica, output JSON, CI-ready  | Configuración compleja             |
| **openapi-diff** (Tufin)          | Go       | Mismo origen, simpler CLI                   | Menos categorías                   |
| **openapi-changes** (pb33f)       | Go       | UI HTML interactivo, "what's changed" claro | Reciente, ecosistema menor         |
| **openapi-diff** (OpenAPITools)   | Java     | Maven plugin, integración Java              | Slower, menos mantenido            |

**Recomendación Pragma:** `oasdiff` para CI gates; `openapi-changes` para visualización stakeholders.

## Snippet CI — oasdiff

```yaml
# .github/workflows/openapi-diff.yml
name: OpenAPI breaking changes
on:
  pull_request:
    paths:
      - 'openapi/spec.yaml'

jobs:
  diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get base spec
        run: git show origin/main:openapi/spec.yaml > spec-base.yaml

      - name: Install oasdiff
        run: |
          curl -L https://github.com/Tufin/oasdiff/releases/latest/download/oasdiff_linux_amd64.tar.gz | tar xz
          sudo mv oasdiff /usr/local/bin/

      - name: Check breaking changes
        run: |
          oasdiff breaking spec-base.yaml openapi/spec.yaml \
            --format json > breaking-changes.json

          BREAKING_COUNT=$(jq 'length' breaking-changes.json)
          if [ "$BREAKING_COUNT" -gt 0 ]; then
            echo "Breaking changes detected:"
            cat breaking-changes.json | jq -r '.[] | "  - [\(.id)] \(.text)"'
            exit 1
          fi

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: openapi-diff
          path: breaking-changes.json
```

## Snippet Azure DevOps

```yaml
- script: |
    git show origin/main:openapi/spec.yaml > spec-base.yaml
    docker run --rm -v $(System.DefaultWorkingDirectory):/specs \
      tufin/oasdiff breaking /specs/spec-base.yaml /specs/openapi/spec.yaml \
      --fail-on ERR
  displayName: Gate - OpenAPI breaking changes
```

## Categorías de breaking changes detectadas

`oasdiff` clasifica cada cambio con un ID estable. Los más comunes:

| ID                                    | Severidad | Significado                                         |
| ------------------------------------- | --------- | --------------------------------------------------- |
| `api-removed`                         | ERROR     | Endpoint eliminado                                  |
| `api-path-removed-with-deprecation`   | INFO      | Eliminado tras deprecation window — OK              |
| `request-property-removed`            | ERROR     | Campo del request body removido                     |
| `response-property-removed`           | ERROR     | Campo del response removido                         |
| `request-property-became-required`    | ERROR     | Campo opcional ahora obligatorio                    |
| `request-property-type-changed`       | ERROR     | Tipo cambiado (ej. string -> integer)               |
| `response-property-became-optional`   | WARN      | Campo siempre presente ahora opcional               |
| `response-required-property-removed`  | ERROR     | Campo requerido removido del response              |
| `request-parameter-removed`           | ERROR     | Query/path/header parameter removido                |
| `request-parameter-enum-value-removed`| ERROR     | Valor de enum removido (consumers podian enviarlo) |
| `response-enum-value-removed`         | ERROR     | Valor de enum removido del response                 |
| `request-body-became-required`        | ERROR     | Body opcional ahora obligatorio                     |

Lista completa: https://github.com/Tufin/oasdiff/blob/main/BREAKING-CHANGES.md

## Workflow de deprecation (cómo NO romper consumers)

Para introducir un breaking change sin romper:

1. Marca el campo / endpoint como `deprecated: true` en el spec.
2. Agrega header `Deprecation: true` y `Sunset: <date>` en runtime.
3. Espera la "deprecation window" (típicamente 90-180 días).
4. Después del sunset, elimina — `oasdiff` lo marca como `api-path-removed-with-deprecation` (INFO, no ERROR).

```yaml
paths:
  /v1/users:
    get:
      deprecated: true
      x-sunset-date: "2026-12-31"
      ...
```

## Configuración avanzada — ignorar cambios esperados

A veces un breaking change es **intencional** (ej. versión major v2 de la API). Usar `--exclude-elements` o `severity-override.yaml`:

```yaml
# oasdiff-severity.yaml
- id: response-property-removed
  severity: WARN  # degradar a warning para esta release específica
```

```bash
oasdiff breaking spec-base.yaml spec-new.yaml --severity-levels oasdiff-severity.yaml
```

## Comparación con Pact

| Aspecto                          | OpenAPI diff           | Pact CDC                       |
| -------------------------------- | ---------------------- | ------------------------------ |
| Detección de breaking change     | General (todo consumer)| Per-consumer                   |
| Funciona con consumers externos  | Si                     | No (necesita pact del consumer)|
| Setup                            | Bajo (CLI + spec)      | Medio (broker + libs)          |
| Gate `can-i-deploy`              | Implícito (diff falla) | Explícito por consumer         |
| Requiere coordinación org        | No                     | Si                             |

## Anti-patterns

- Hacer diff contra el spec del commit anterior (`HEAD~1`) en lugar de `main` — pierdes cambios acumulados en el branch.
- Ignorar todos los warnings — algunos warnings son breaking según el contexto del consumer.
- Spec en múltiples archivos sin bundler — usar `swagger-cli bundle` o `redocly bundle` antes del diff.
- No versionar el spec — sin baseline no hay diff posible.
