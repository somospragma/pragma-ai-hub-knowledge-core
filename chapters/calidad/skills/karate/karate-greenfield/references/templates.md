# Plantillas del proyecto generado

Cada seccion corresponde a un archivo que el agente debe materializar en la ruta indicada (relativa a la raiz del proyecto generado). Respeta los placeholders `{{...}}`.

## `README.md`

````markdown
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
````

## `STRATEGY.md`

```markdown
# STRATEGY.md — {{project_name}} (Karate)

Documento de estrategia previo a la generación de código. Debe estar aprobado explícitamente por el usuario antes de emitir el primer `.feature`. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- SUT: {{sut_name}} — {{sut_description}}
- Tipo: API REST / SOAP / GraphQL — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}}
- Stack tecnológico del SUT: {{sut_stack}}
- Tipo de relación: greenfield (proyecto Karate nuevo)
- Spec: {{spec_path}} ({{spec_format}}: OpenAPI 3.x / Swagger 2.0 / WSDL)
- Firma: {{firma}}

## 2. Volumen y SLAs

Karate cubre validación funcional y contract. Los SLAs de performance no se ejercitan aquí (eso es K6), pero sí los SLAs funcionales:

- Disponibilidad esperada del SUT durante la corrida (% uptime).
- Tiempo de respuesta máximo tolerable por endpoint para que un test no sea considerado timeout (no es SLA, es timeout técnico).
- Error rate aceptable en happy paths: 0%.
- Tasa de fallo aceptable en suite completa: 0% (todos los tests deben pasar determinísticamente).

| Métrica | Valor declarado |
|---|---|
| Disponibilidad SUT en corrida | {{availability}} |
| Timeout por request | {{request_timeout}} ms |
| Error rate happy paths | 0% |

## 3. Alcance funcional

- Endpoints en scope: {{endpoints_in_scope}}
- Endpoints fuera de scope: {{endpoints_out_of_scope}} (justificación: {{out_of_scope_reason}})
- Criterios de aceptación por endpoint: {{acceptance_criteria}}
- User story principal: {{user_story_id}} — {{user_story_summary}}

## 4. Dependencias externas

- Auth: {{auth_type}} ({{auth_endpoint}}). Si el spec NO declara `security`, no se emite `Authorization` (regla `[[calidad-mandatory-inputs-protocol]]`).
- Base URL: {{base_url}} (también disponible como variable `{{baseUrlVar}}` en `karate-config.js`).
- Servicios externos consumidos por el SUT (mockear o probar): {{external_services}}

## 5. Riesgos conocidos

- WAF en ambiente de prueba: {{waf_status}} — proveedor: {{waf_provider}}, allowlist coordinada: {{waf_allowlist}}
- Rate limits documentados: {{rate_limits}}
- Datos sensibles tratados: {{sensitive_data}}
- Restricciones regulatorias: {{regulatory_constraints}}

## 6. Próximos pasos

- Archivos a generar (alto nivel): `pom.xml`, `karate-config.js`, `TestRunner.java`, features bajo `src/test/java/com/testing/features/`, schemas `-match.json`.
- Comando de ejecución: `mvn test` (filtros opcionales por tag).
- Reporte ejecutivo: formato {{report_format}} (default `html`) generado por `[[calidad-generate-executive-report]]` al cierre.

## 7. Estrategia Karate

### 7.1 Cobertura por endpoint (effective_minimum)

Aplicar la fórmula `[negative-coverage-formula](negative-coverage-formula.md)`. Declarar antes de generar:

| Endpoint | Effective minimum | Required fields | Headers críticos | Cobertura cifrado | Risk |
|---|---|---|---|---|---|
| POST /pet | 10 | name, status | Content-Type | N/A | HIGH |
| GET /pet/findByStatus | 8 | (query) status | — | N/A | MEDIUM |
| GET /pet/{id} | 6 | (path) id | — | N/A | MEDIUM |

### 7.2 Risk map

`{ POST /pet: HIGH, GET /pet/findByStatus: MEDIUM, GET /pet/{id}: MEDIUM, DELETE /pet/{id}: HIGH }`

Reglas: HIGH eleva el `effective_minimum` calculado; CRITICAL agrega cobertura de cifrado obligatoria si la firma declara cifrado.

### 7.3 Conventions cliente (solo brownfield)

| Convention | Valor detectado | Fuente |
|---|---|---|
| Body_Mode | (n/a en greenfield) | — |
| Scenario_Prefix | (n/a en greenfield) | — |

En greenfield se aplican defaults del chapter (`Scenario:` literal, body en `request {...}` JSON inline).

### 7.4 Schemas de contrato

Listar schemas `-match.json` a generar (uno por schema respuesta):

- `pet-match.json` ← `Pet` schema del spec
- `order-match.json` ← `Order` schema
- `user-match.json` ← `User` schema

Notación: `#type` para required, `##type` para optional. Sin `##[] #type`.

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar features. Cambios posteriores requieren actualizar este documento y re-aprobar.
```

## `TestRunner.java`

```java
package com.testing;

import com.intuit.karate.junit5.Karate;

class TestRunner {

    @Karate.Test
    Karate all() {
        return Karate.run().relativeTo(getClass());
    }
}
```

## `body.json`

```json
{
  "{{field_name}}": "{{value}}"
}
```

## `feature`

```text
# cobertura: {{effective_minimum}}
Feature: {{endpoint_name}} API

  Background:
    * url baseUrl
    * def validBody = read('classpath:com/testing/bodies/{{endpoint_name}}.json')

  @happy-path
  Scenario: {{endpoint_name}} - happy path
    Given path '{{path}}'
    # Inject mandatory headers (one And header line per header in {{mandatory_headers}})
    And header X-Channel = 'web'
    And request validBody
    When method {{method}}
    Then status 200
    And match response.id == '#uuid'

  @contract
  Scenario: {{endpoint_name}} - contract validation
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request validBody
    When method {{method}}
    Then status 200
    And match response == {{schema_match}}

  @data-driven
  Scenario Outline: {{endpoint_name}} - data driven
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request karate.merge(validBody, { amount: <amount> })
    When method {{method}}
    Then status <expectedStatus>

    Examples:
      | amount  | expectedStatus |
      | 1       | 200            |
      | 999999  | 200            |
      | -1      | 400            |

  # ---------------------------------------------------------------------------
  # Negative scenarios — one block per required field in {{required_fields}}
  # Tags use the real field name; do NOT collapse multiple fields into one tag.
  # ---------------------------------------------------------------------------

  @negative @missing-field
  Scenario: {{endpoint_name}} - missing required field {{required_fields}}
    * def body = karate.merge(validBody, {})
    * remove body.{{required_fields}}
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request body
    When method {{method}}
    Then status 400

  @negative @null-field
  Scenario: {{endpoint_name}} - null required field {{required_fields}}
    * def body = karate.merge(validBody, { {{required_fields}}: null })
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request body
    When method {{method}}
    Then status 400

  @negative @invalid-type
  Scenario: {{endpoint_name}} - invalid type for {{required_fields}}
    * def body = karate.merge(validBody, { {{required_fields}}: 12345 })
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request body
    When method {{method}}
    Then status 400

  # ---------------------------------------------------------------------------
  # Negative scenarios — one block per mandatory header in {{mandatory_headers}}
  # ---------------------------------------------------------------------------

  @negative @missing-header
  Scenario: {{endpoint_name}} - missing mandatory header {{mandatory_headers}}
    Given path '{{path}}'
    And request validBody
    When method {{method}}
    Then status 400

  @negative @invalid-header-format
  Scenario: {{endpoint_name}} - invalid format for header {{mandatory_headers}}
    Given path '{{path}}'
    And header {{mandatory_headers}} = 'not-a-valid-format'
    And request validBody
    When method {{method}}
    Then status 400
```

## `karate-config.js`

```javascript
function fn() {
  var env = karate.env || '{{env}}';
  karate.log('karate.env =', env);

  var config = {
    baseUrl: '{{baseUrl}}',
    ssl: true,
    connectTimeout: 5000,
    readTimeout: 5000
  };

  if (env === 'dev') {
    config.baseUrl = '{{baseUrl}}';
  }
  if (env === 'qa') {
    config.baseUrl = '{{baseUrl}}';
  }
  if (env === 'staging') {
    config.baseUrl = '{{baseUrl}}';
  }
  if (env === 'prod') {
    config.baseUrl = '{{baseUrl}}';
  }

  return config;
}
```

## `pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.testing</groupId>
    <artifactId>{{project_name}}-tests</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>{{java_version}}</maven.compiler.source>
        <maven.compiler.target>{{java_version}}</maven.compiler.target>
        <karate.version>1.4.1</karate.version>
        <junit.jupiter.version>5.10.1</junit.jupiter.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>com.intuit.karate</groupId>
            <artifactId>karate-junit5</artifactId>
            <version>${karate.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>${junit.jupiter.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <testResources>
            <testResource>
                <directory>src/test/java</directory>
                <excludes>
                    <exclude>**/*.java</exclude>
                </excludes>
            </testResource>
        </testResources>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.2</version>
                <configuration>
                    <includes>
                        <include>**/TestRunner.java</include>
                    </includes>
                    <systemPropertyVariables>
                        <karate.env>${karate.env}</karate.env>
                    </systemPropertyVariables>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

## `preflight-karate.sh`

```bash
#!/usr/bin/env bash
set -e
echo "=== Karate pre-flight ==="
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | cut -d. -f1)
echo "Java major version: $JAVA_VERSION"
if [[ "$JAVA_VERSION" == "11" || "$JAVA_VERSION" == "17" ]]; then
  echo "[ok] Java $JAVA_VERSION compatible con Karate 1.4.1"
else
  echo "[fail] Java $JAVA_VERSION incompatible. Karate 1.4.1 requiere 11 o 17."
  echo "Sugerencia: export JAVA_HOME=\$(/usr/libexec/java_home -v 11) && export PATH=\$JAVA_HOME/bin:\$PATH"
  exit 1
fi
mvn -version > /dev/null 2>&1 || { echo "[fail] mvn no encontrado"; exit 1; }
echo "[ok] Maven disponible"
echo "=== preflight ok ==="
```

