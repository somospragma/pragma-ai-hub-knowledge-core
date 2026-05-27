---
id: generate-karate-greenfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Flujo completo para generar un proyecto Karate desde cero a partir de un spec OpenAPI/Swagger/WSDL.
tags: [karate, greenfield, workflow, openapi]
---

# Workflow — Generar proyecto Karate greenfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` y `[[calidad-brownfield-vs-greenfield]]` identifican un escenario greenfield para Karate: el usuario provee spec, no provee archivos de un proyecto existente, y solicita pruebas funcionales/contract de APIs.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `spec` | Sí | OpenAPI 3.x, Swagger 2.0 o WSDL. |
| `project_name` | Sí | En kebab-case. |
| `output_path` | Sí | Carpeta destino. |
| `base_url` | No | Si se omite, se extrae del spec. |
| `user_story` | No | Tag `@user-story:HUT-XXX`. |
| `firma` | No | Documento técnico complementario. |

Recolectar inputs siguiendo `[[calidad-mandatory-inputs-protocol]]`.

## Pasos

### 1. Validar el spec
Aplica `[[calidad-spec-validation]]`. OpenAPI > 200 chars, WSDL > 100 chars, debe parsear sin errores. Si falla, detente y reporta error específico.

### 2. Extraer service info
Service name kebab-case desde `info.title` (fallback: filename). `base_url` desde `servers[0].url` / `schemes+host+basePath` / `soap:address`. Variable de URL: camelCase + `Url`.

### 3. Inventario de endpoints y schemas
Para cada path×method: required headers, body fields, response codes, enums, formatos. Convierte `components.schemas` o `definitions` a la notación match (`[[karate-greenfield/references/contract-testing-match-patterns.md]]`).

### 4. Decidir cobertura por endpoint
Aplica `[[karate-negative-coverage-formula]]`. Declara el número objetivo de escenarios por endpoint ANTES de generar.

### 5. Generar features
Invoca `[[karate-greenfield]]` paso 5. Usa los tipos y tags de `references/feature-design-dsl.md`. Si hay señales de cifrado, añade los escenarios de `references/encrypted-payloads.md`. Aplica `[[calidad-route-test-generation]]` para mapear endpoint → archivos.

### 6. Generar schemas `-match.json`
Uno por schema utilizado en respuestas. Respeta `#type` vs `##type`.

### 7. Generar infraestructura
`pom.xml`, `karate-config.js`, `logback-test.xml`, `TestRunner.java` según `references/project-structure.md`. Versiones exactas: `karate-junit5` 1.4.1, `maven-surefire-plugin` 3.2.2. Bloque `<testResources>` obligatorio (`[[karate-feature-file-location-constraint]]`).

### 8. Asegurar resource files y validar DoD
Detecta referencias a `classpath:resources/files/*` y crea archivos por defecto. Recorre el checklist de finalización antes de entregar. Entrega con `[[calidad-streaming-files-protocol]]` y registra trazabilidad por `[[calidad-test-evidence-and-traceability]]`.

## Criterios de finalización (DoD — 14 items)

1. Todos los archivos no-Java en `src/test/java/` (cero en `src/test/resources/`).
2. Fórmula real de cobertura mínima aplicada por endpoint (no piso fijo de 5 si el endpoint es complejo).
3. Happy path valida status AND significado de negocio (no sólo `status 200`).
4. Contract tests con notación correcta (`#type` requerido, `##type` opcional, sin `##[] #type`).
5. Cobertura exhaustiva de required fields: `absent + null + invalid-type` por campo.
6. Cobertura exhaustiva de headers: `missing` + `invalid-format` (si aplica) por header.
7. Escenarios de cifrado si aplica: `valid + invalid-key + plaintext-body + missing-encryption-header`.
8. `pom.xml` con `karate-junit5` 1.4.1, `maven-surefire-plugin` 3.2.2 y `<testResources>` excluyendo `**/*.java`.
9. `karate-config.js` retorna `config` con `baseUrl`, `ssl`, `connectTimeout`, `readTimeout`.
10. `TestRunner.java` usa `.relativeTo(getClass())` y package `com.testing`.
11. Sin auth inline si el spec no declara `security`.
12. Todos los paths relativos en `Given path` (sin protocolo/host).
13. Field names en bodies coinciden exactamente con el spec.
14. Sin lógica condicional (`if`) en aserciones; `Examples` sin celdas vacías. Comando `mvn test` provisto en la entrega.
