---
id: calidad-karate-run-and-tags
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [karate]
description: Comandos Maven para ejecutar Karate por tag o environment y semántica de tags estándar.
tags: [karate, maven, tags, runtime, mvn]
---

# Ejecución Karate y semántica de tags

## Comandos `mvn test`

```bash
# Todos los tests
mvn test -f {project_path}/pom.xml

# Filtrar por tag
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags @happy-path"
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags @contract"
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags @negative"
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags @smoke"

# Excluir un tag
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags ~@slow"

# Combinaciones (AND con coma dentro del mismo --tags, OR con varios --tags)
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags @smoke,@regression"
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags @smoke --tags ~@slow"

# Environment (lo lee karate-config.js vía karate.env)
mvn test -f {project_path}/pom.xml -Dkarate.env=dev
mvn test -f {project_path}/pom.xml -Dkarate.env=qa
mvn test -f {project_path}/pom.xml -Dkarate.env=staging
mvn test -f {project_path}/pom.xml -Dkarate.env=prod

# Combinaciones tag + env
mvn test -f {project_path}/pom.xml -Dkarate.options="--tags @smoke" -Dkarate.env=qa
```

## Tabla de tags estándar

| Tag | Semántica |
|---|---|
| `@happy-path` | Camino feliz: request válido → respuesta correcta con significado de negocio. |
| `@contract` | Validación de contrato contra `-match.json`. |
| `@negative` | Cualquier escenario negativo. Se combina con sub-tags más específicos. |
| `@data-driven` | Escenarios `Scenario Outline` + `Examples`. |
| `@encrypted` | Escenarios con payload cifrado (JWE/JWS). |
| `@regression` | Suite de regresión que se ejecuta en pipeline de cada PR/release. |
| `@smoke` | Subconjunto rápido para validar despliegues. |
| `@missing-field` | Subtipo negativo: campo requerido ausente. |
| `@null-field` | Subtipo negativo: campo requerido con valor `null`. |
| `@invalid-type` | Subtipo negativo: campo requerido con tipo incorrecto. |
| `@missing-header` | Subtipo negativo: header obligatorio ausente. |
| `@invalid-header-format` | Subtipo negativo: header con formato inválido (UUID, enum). |
| `@bad-request` | Negativo genérico de body malformado (400/422). |
| `@plaintext-body-on-encrypted-contract` | Body plano cuando el contrato exige cifrado. |
| `@invalid-encryption` | Payload cifrado con llave/formato inválido. |
| `@user-story:HUT-XXX` | Trazabilidad a la historia de usuario. Reemplaza `HUT-XXX` por el id real. |

Convención: tags en kebab-case. Si un proyecto cliente impone otro estilo (p. ej. camelCase `@happyPath`), respetarlo — ver `client-specific-conventions.md` en `karate-brownfield`.
