# Output Parsers

Snippets concretos para parsear el output de cada framework al esquema definido en `result-schema-common.md`. Cada bloque muestra: input crudo del framework → comando/parser → output normalizado.

## Karate — JUnit XML + summary JSON

### Input

`target/karate-reports/karate-summary-json.txt`:

```json
{
  "scenariosTotal": 12,
  "scenariosPassed": 10,
  "scenariosFailed": 2,
  "featuresTotal": 3,
  "elapsedTime": 8421.0,
  "efficiency": 0.84
}
```

`target/surefire-reports/TEST-users.UsersRunner.xml` (extracto):

```xml
<testsuite name="users.UsersRunner" tests="12" failures="2" time="8.421">
  <testcase classname="users.feature" name="create new user" time="0.234"/>
  <testcase classname="users.feature" name="get user by id" time="0.187">
    <failure type="AssertionError" message="path: response.id, actual: null, expected: '123'">
      ... stack trace ...
    </failure>
  </testcase>
</testsuite>
```

### Parser

```bash
# Totals desde summary JSON
jq '{
  framework: "karate",
  totals: {
    total: .scenariosTotal,
    passed: .scenariosPassed,
    failed: .scenariosFailed,
    skipped: 0
  },
  duration_ms: (.elapsedTime | floor)
}' target/karate-reports/karate-summary-json.txt

# Tests desde JUnit XML (con xq de yq)
xq -r '.testsuite.testcase[] | {
  id: ("\(.["@classname"])::\(.["@name"])"),
  status: (if .failure then "failed_deterministic" else "passed" end),
  duration_ms: ((.["@time"] | tonumber) * 1000 | floor),
  error: (if .failure then {
    type: .failure["@type"],
    message: .failure["@message"],
    stack: .failure["#text"]
  } else null end)
}' target/surefire-reports/TEST-*.xml
```

### Output normalizado (ejemplo)

```json
{
  "framework": "karate",
  "run_id": "...",
  "status": "failed",
  "totals": { "total": 12, "passed": 10, "failed": 2, "skipped": 0 },
  "tests": [
    {
      "id": "users.feature::create new user",
      "status": "passed",
      "duration_ms": 234
    },
    {
      "id": "users.feature::get user by id",
      "status": "failed_deterministic",
      "duration_ms": 187,
      "error": {
        "type": "AssertionError",
        "message": "path: response.id, actual: null, expected: '123'",
        "stack": "..."
      }
    }
  ]
}
```

## Playwright — JSON reporter

### Input

`results.json` (estructura del JSON reporter de Playwright):

```json
{
  "stats": {
    "startTime": "2026-05-28T10:00:00.000Z",
    "duration": 12345,
    "expected": 47,
    "unexpected": 2,
    "skipped": 1
  },
  "suites": [
    {
      "file": "users.spec.ts",
      "specs": [
        {
          "title": "create user successfully",
          "tests": [
            {
              "results": [
                {
                  "status": "passed",
                  "duration": 234,
                  "retry": 0,
                  "attachments": []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Parser

```bash
jq '{
  framework: "playwright",
  started_at: .stats.startTime,
  duration_ms: .stats.duration,
  totals: {
    total: (.stats.expected + .stats.unexpected + .stats.skipped),
    passed: .stats.expected,
    failed: .stats.unexpected,
    skipped: .stats.skipped
  },
  tests: [
    .suites[] | .specs[] as $spec |
    $spec.tests[] | .results[-1] as $r |
    {
      id: ("\($spec.file // "unknown")::\($spec.title)"),
      status: (
        if $r.status == "passed" and $r.retry > 0 then "failed_flaky"
        elif $r.status == "passed" then "passed"
        elif $r.status == "skipped" then "skipped"
        elif $r.status == "timedOut" then "errored"
        else "failed_deterministic"
        end
      ),
      duration_ms: $r.duration,
      error: ($r.error // null),
      evidence: [$r.attachments[]?.path // empty]
    }
  ]
}' results.json
```

## K6 — handleSummary JSON

### Input

`results/summary.json` (output de `handleSummary`):

```json
{
  "state": {
    "testRunDurationMs": 60000
  },
  "metrics": {
    "http_req_duration": {
      "values": {
        "avg": 123.4,
        "p(95)": 450.0,
        "p(99)": 890.0
      }
    },
    "http_req_failed": {
      "values": { "rate": 0.012, "passes": 12, "fails": 988 }
    },
    "checks": {
      "values": { "passes": 9876, "fails": 12, "rate": 0.998 }
    }
  },
  "root_group": {
    "checks": [
      {
        "name": "status is 200",
        "passes": 988,
        "fails": 12
      }
    ]
  }
}
```

### Parser

```bash
jq '{
  framework: "k6",
  duration_ms: .state.testRunDurationMs,
  totals: {
    total: (.metrics.checks.values.passes + .metrics.checks.values.fails),
    passed: .metrics.checks.values.passes,
    failed: .metrics.checks.values.fails,
    skipped: 0
  },
  thresholds: {
    passed: (.metrics.http_req_failed.values.rate < 0.05),
    details: {
      p95: .metrics.http_req_duration.values["p(95)"],
      p99: .metrics.http_req_duration.values["p(99)"],
      error_rate: .metrics.http_req_failed.values.rate
    }
  },
  tests: [
    .root_group.checks[] | {
      id: ("k6::check::\(.name)"),
      status: (if .fails == 0 then "passed" else "failed_deterministic" end),
      duration_ms: 0,
      error: (if .fails > 0 then {
        type: "CheckFailed",
        message: ("\(.fails) of \(.passes + .fails) iterations failed check"),
        stack: ""
      } else null end)
    }
  ]
}' results/summary.json
```

## Appium / Serenity — results.json

### Input

`target/site/serenity/results.json` (estructura simplificada):

```json
{
  "results": {
    "total": 20,
    "success": 18,
    "failure": 1,
    "error": 1,
    "skipped": 0
  },
  "tags": [],
  "scenarios": [
    {
      "name": "user logs in successfully",
      "story": "LoginStory",
      "result": "SUCCESS",
      "duration": 4321,
      "tags": ["@smoke"]
    },
    {
      "name": "user sees error on bad creds",
      "story": "LoginStory",
      "result": "FAILURE",
      "duration": 5500,
      "tags": ["@regression"],
      "testFailureCause": {
        "errorType": "AssertionError",
        "message": "Expected error banner to be visible",
        "stackTrace": "..."
      },
      "screenshots": ["screenshots/login-error.png"]
    }
  ]
}
```

### Parser

```bash
jq '{
  framework: "appium",
  duration_ms: ([.scenarios[].duration] | add),
  totals: {
    total: .results.total,
    passed: .results.success,
    failed: .results.failure,
    skipped: .results.skipped
  },
  tests: [
    .scenarios[] | {
      id: ("\(.story)::\(.name)"),
      status: (
        if .result == "SUCCESS" then "passed"
        elif .result == "FAILURE" then "failed_deterministic"
        elif .result == "ERROR" then "errored"
        elif .result == "SKIPPED" then "skipped"
        else "errored"
        end
      ),
      duration_ms: .duration,
      tags: (.tags // []),
      error: (.testFailureCause // null | if . then {
        type: .errorType,
        message: .message,
        stack: .stackTrace
      } else null end),
      evidence: (.screenshots // [])
    }
  ]
}' target/site/serenity/results.json
```

## Convenciones de los parsers

- **jq** es la herramienta canónica; **xq** (de `yq`) para XML.
- Los parsers son **idempotentes**: ejecutar 2 veces sobre el mismo input produce el mismo output.
- **Nunca** modificar el archivo de input; siempre escribir el output normalizado a un archivo nuevo (`normalized.json` por convención).
- El `run_id` y `started_at` cuando no estén disponibles en el output del framework, los genera el orquestador antes de invocar al parser.
- Si el output del framework está corrupto o incompleto (job killed, timeout), el parser debe emitir un esquema mínimo con `status: "errored"` y dejar `tests: []`.
