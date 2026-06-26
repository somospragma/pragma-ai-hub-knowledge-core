---
id: calidad-karate-greenfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [karate]
description: Genera proyecto Karate completo desde un spec OpenAPI/Swagger/WSDL.
tags: [karate, greenfield, openapi, swagger, wsdl, contract-testing]
---

# Karate Greenfield

## Cuándo aplicar

Cuando el usuario solicita generar un proyecto Karate **desde cero** a partir de un spec OpenAPI 3.x, Swagger 2.0 o WSDL, y no existe un proyecto previo donde extender pruebas. Si el usuario provee archivos de un proyecto Karate existente, usar `[[calidad-karate-brownfield]]` en su lugar (ver `[[calidad-brownfield-vs-greenfield]]`).

Antes de activar este skill, valida el spec con `[[calidad-spec-validation]]` y confirma intent con `[[calidad-intent-detection]]`. Recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`.

## Instrucción

1. **Validar spec** — Verifica que el archivo sea OpenAPI 3.x (>200 chars), Swagger 2.0 (>200 chars) o WSDL (>100 chars) y que parsee correctamente. Si falla, detente y reporta el error específico.
2. **Extraer service info** — Obtén `base_url` desde `servers[0].url` (OpenAPI 3.x), `schemes + host + basePath` (Swagger 2.0) o `soap:address location` (WSDL). El `service_name` se deriva en kebab-case desde `info.title` (fallback: nombre del archivo). La variable de URL se nombra en camelCase + sufijo `Url` (ej: `transferenciaUrl`).
3. **Inventario de endpoints** — Lista paths, métodos, tags, response codes, required headers y body fields. Detecta enums y campos con formato (UUID, email, date-time) — son insumo de la fórmula de cobertura.
4. **Extraer schemas** — Convierte `components.schemas` (OpenAPI) o `definitions` (Swagger 2.0) a archivos `{resource}-match.json` con la notación Karate (ver ``references/contract-testing-match-patterns.md``).
5. **Generar features primero** — Crea los `.feature` ANTES que cualquier otro artefacto: son lo más caro en tiempo de generación y queremos progreso visible si hay timeout. Aplica los tipos de escenario y tags definidos en `references/feature-design-dsl.md` y calcula el mínimo real con ``references/negative-coverage-formula.md``. Si detectas señales de cifrado, añade los escenarios de `references/encrypted-payloads.md`.
6. **Generar `-match.json`** — Un archivo por schema usado en respuestas. Respeta `#type` vs `##type` (requerido vs opcional).
7. **Generar infraestructura** — `pom.xml`, `karate-config.js`, `logback-test.xml`, `TestRunner.java` según `references/project-structure.md`. Versiones exactas: `karate-junit5` 1.4.1, `maven-surefire-plugin` 3.2.2.
8. **Asegurar resource files y validar DoD** — Si algún feature referencia `classpath:resources/files/*.{jpg,png,pdf,csv,txt,xml,json}`, crea archivos por defecto (PNG/JPG 1x1, PDF mínimo, CSV/TXT/XML vacíos válidos). Antes de entregar, recorre el checklist DoD de 14 items del workflow `[[calidad-generate-karate-greenfield]]`.

## Salidas

Estructura Maven completa:

```
{project_name}/
├── pom.xml
└── src/test/java/
    ├── karate-config.js
    ├── logback-test.xml
    ├── schemas/
    │   └── {resource}-match.json
    ├── resources/files/
    └── com/testing/
        ├── TestRunner.java
        └── features/
            └── {resource}.feature
```

Detalle completo de cada archivo en `references/project-structure.md`.

**Fuente autoritativa de archivos a copiar** — las plantillas inmutables viven en `references/templates/`:

- `pom.xml.tpl` — pom.xml completo con `1.0.0-SNAPSHOT`, `karate-junit5` 1.4.1, surefire 3.2.2 con `<include>**/TestRunner.java</include>`, y `<testResources>` excluyendo `**/*.java`.
- `karate-config.js.tpl` — config con retorno explícito del objeto, sin `karate.configure()`.
- `TestRunner.java.tpl` — runner con `.relativeTo(getClass())`, sin paths hardcodeados.
- `feature.tpl` — feature con comentario `# cobertura:` obligatorio en primera línea (ver `references/cobertura-comment-enforcement.md`) y bloques por cada escenario mínimo (`@happy-path`, `@contract`, `@data-driven`, y un negativo separado por cada required field / header).
- `body.json.tpl` — body JSON externo (Body Mode A).

Copiar textualmente. Solo rellenar `{{slots}}` declarados.

## Restricciones

- Las plantillas en `references/templates/` son **inmutables**: copiar textualmente, solo rellenar `{{slots}}` declarados. No parafrasear, no omitir secciones, no reordenar bloques.
- Cada `.feature` generada DEBE incluir el comentario `# cobertura: <N>` en la cabecera, donde `<N>` es el `effective_minimum` calculado con ``references/negative-coverage-formula.md``. Detalle en `references/cobertura-comment-enforcement.md`. Este número es consumido por `[[calidad-delivery-gate-contract]]`.
- **TODOS** los `.feature`, `.json`, `.js`, `.xml` van dentro de `src/test/java/`. NUNCA en `src/test/resources/`. Causa raíz y diagnóstico en ``references/file-location-constraint.md``.
- No inventes endpoints, campos, headers, enums, códigos de error ni esquemas de autenticación que no estén en el spec.
- No uses esquemas de autenticación inline si el spec no declara `security`.
- No hardcodees payloads cifrados literales: usa `karate.call('classpath:helpers/encrypt.feature', {...})`.
- No apliques convenciones cliente-específicas aquí — esas se detectan y se aplican sólo en brownfield (ver `karate-brownfield/references/client-specific-conventions.md`).
- **Step isolation obligatorio** cuando el flow tiene setup/auth/main/cleanup: separar en `Background:` + escenarios `@auth`/`@main`/`@cleanup` con tags por step. La cobertura sólo cuenta `@main`. Detalle en `references/step-isolation-karate.md`.
- No reportes "todo verde" sin haber recorrido el DoD de `[[calidad-generate-karate-greenfield]]`.
- Antes de generar, recorre `[[calidad-pre-generation-protocol]]`. Al cerrar, recorre `[[calidad-post-generation-protocol]]` y valida `[[calidad-delivery-gate-contract]]`.
- Entrega los archivos usando `[[calidad-streaming-files-protocol]]` y enlaza la traza según `[[calidad-test-evidence-and-traceability]]`.
