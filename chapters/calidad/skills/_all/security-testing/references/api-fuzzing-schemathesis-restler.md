# API Fuzzing — Schemathesis vs RESTler

Dos herramientas de fuzzing dirigido por contrato OpenAPI con enfoques distintos. Se eligen según si el flujo a probar es stateless o stateful.

## Comparación rápida

| Aspecto                         | Schemathesis                            | RESTler                                  |
|---------------------------------|-----------------------------------------|------------------------------------------|
| Lenguaje                        | Python                                  | Python (compiler en F#/.NET)             |
| Tipo de fuzzing                 | Property-based, stateless por endpoint  | Stateful, encadena requests              |
| Curva de aprendizaje            | Baja                                    | Media-alta                               |
| Setup                           | `pip install schemathesis`              | Build con `dotnet` + Python              |
| Integración CI                  | Trivial (un comando)                    | Requiere fase compile + test             |
| Ideal para                      | Validación de contrato y robustez       | Descubrir vulnerabilidades en flujos     |
| Reporte                         | Junit, Allure, terminal                 | Bugs bucket + replay scripts             |
| Autoría                         | Schemathesis.io / community             | Microsoft Research                       |

## Schemathesis

Property-based testing dirigido por el OpenAPI. Genera payloads que cumplen el esquema y verifica que la respuesta también lo cumpla (o sea un 4xx esperado).

Instalación y uso básico:

```bash
pip install schemathesis
schemathesis run https://api-staging.example.com/openapi.json \
  --checks all \
  --hypothesis-max-examples 200 \
  --report
```

Checks incluidos con `--checks all`:

- `not_a_server_error` — ningún 5xx ante input válido por contrato.
- `status_code_conformance` — códigos de respuesta declarados en el spec.
- `content_type_conformance` — Content-Type acorde al spec.
- `response_schema_conformance` — el cuerpo cumple el `schema` declarado.
- `response_headers_conformance` — headers obligatorios presentes.

Con autenticación:

```bash
schemathesis run https://api-staging.example.com/openapi.json \
  --header "Authorization: Bearer ${API_TOKEN}" \
  --checks all
```

Hooks personalizados (Python) permiten datos válidos por dominio (ej. RUT chileno válido):

```python
import schemathesis
from schemathesis import GenerationConfig

@schemathesis.register_string_format("rut_cl")
def rut_cl_strategy():
    from hypothesis import strategies as st
    return st.sampled_from(["12.345.678-5", "23.456.789-K"])
```

Pipeline (GitHub Actions):

```yaml
- name: Schemathesis
  run: |
    pip install schemathesis
    schemathesis run "$OPENAPI_URL" \
      --header "Authorization: Bearer $API_TOKEN" \
      --checks all \
      --junit-xml schemathesis-report.xml
```

## RESTler

Fuzzing stateful: analiza el OpenAPI, deduce dependencias entre endpoints (un `POST /users` retorna un `id` que `GET /users/{id}` consume) y construye secuencias largas. Encuentra bugs que sólo aparecen tras combinar varios requests (auth obligatoria, transiciones de estado, locks).

Flujo de uso:

```bash
# 1. Compile: convierte el OpenAPI en una gramática RESTler
restler compile --api_spec openapi.json

# 2. Test: smoke test sobre cada endpoint
restler test --grammar_file Compile/grammar.py --dictionary_file Compile/dict.json \
  --settings Compile/engine_settings.json --no_ssl

# 3. Fuzz-lean: fuzzing rápido, secuencias cortas
restler fuzz-lean --grammar_file Compile/grammar.py --dictionary_file Compile/dict.json \
  --settings Compile/engine_settings.json --no_ssl

# 4. Fuzz: fuzzing prolongado (nightly)
restler fuzz --grammar_file Compile/grammar.py --dictionary_file Compile/dict.json \
  --settings Compile/engine_settings.json --time_budget 4 --no_ssl
```

Bugs bucket: cada hallazgo queda en `RestlerResults/.../bug_buckets/` con el script de replay exacto. Útil para reproducir y reportar.

## Cuándo usar cada uno

| Escenario                                                                                   | Herramienta            |
|---------------------------------------------------------------------------------------------|------------------------|
| API REST con endpoints mayormente independientes (CRUD simple)                              | Schemathesis           |
| Cada PR debe validar conformidad de contrato                                                | Schemathesis (lean)    |
| API con flujos transaccionales: signup → login → operación → logout                         | RESTler                |
| Buscar bugs profundos que requieren secuencias largas                                       | RESTler (fuzz nightly) |
| Cliente quiere "ver" tests legibles                                                         | Schemathesis           |
| Cliente quiere replay scripts auditables de cada bug                                        | RESTler                |

En la práctica, **se complementan**: Schemathesis en cada PR + RESTler en pipeline nightly.

## Snippet de pipeline combinado

```yaml
jobs:
  contract-fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Schemathesis on PR
        if: github.event_name == 'pull_request'
        run: |
          pip install schemathesis
          schemathesis run "$OPENAPI_URL" --checks all --hypothesis-max-examples 50

  stateful-fuzz:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
      - name: RESTler fuzz nightly
        run: |
          ./restler/Restler compile --api_spec openapi.json
          ./restler/Restler fuzz --grammar_file Compile/grammar.py \
            --dictionary_file Compile/dict.json --time_budget 2
      - uses: actions/upload-artifact@v4
        with:
          name: restler-bugs
          path: RestlerResults/**/bug_buckets/
```

Encadena los reportes con `[[calidad-test-evidence-and-traceability]]`.
