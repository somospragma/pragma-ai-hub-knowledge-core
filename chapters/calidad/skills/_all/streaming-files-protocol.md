---
id: calidad-streaming-files-protocol
version: 2.1.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Define el orden de scaffold de un proyecto de pruebas por valor entregado (tests primero, utilitarios después, infraestructura al final)."
tags: [scaffold, prioritization, value-delivery, generation, enforcement, mandatory]
enforcement: mandatory
verification:
  - check: "emit [ok] <ruta> por cada archivo persistido (una línea de log por archivo, no reporte global)"
    failure_message: "Bloqueado: la trazabilidad por archivo emitido falta. Sin log por archivo no hay manifiesto auditable."
  - check: "orden estricto respetado: tests → utilitarios/abstracciones → infraestructura"
    failure_message: "Bloqueado: el orden de scaffold se violó (infraestructura emitida antes que tests). Eso esconde valor detrás de boilerplate."
  - check: "directorio padre verificado antes de escribir; scaffold idempotente (no duplicar ni sobrescribir trabajo manual)"
    failure_message: "Bloqueado: archivo escrito sin verificar directorio padre o scaffold no idempotente."
---

# Orden de scaffold por valor entregado

## Cuándo aplicar

Aplica este skill **siempre** que armes un proyecto de pruebas en cualquier framework del Chapter Calidad (Karate, Playwright, K6, Appium, serenity-wdio), tanto en greenfield como en brownfield, ya sea de forma manual o asistida. Es el paso 6 de `[[calidad-route-test-generation]]`.

Su propósito es asegurar que **el activo entregable de mayor valor —los tests— se materialice primero**, y que el boilerplate regenerable quede para el final. En brownfield, el orden aplica sobre los archivos **nuevos** de la sesión; la infraestructura existente no se toca.

## Alias

Anteriormente llamado **streaming-files-protocol**. El nombre y el id (`calidad-streaming-files-protocol`) se mantienen por compatibilidad de links; el contenido se reformuló para reflejar que se trata de un principio de orden de scaffold por valor entregado, no de un protocolo de runtime.

## Principio

Los tests son el activo entregable de mayor valor: representan el conocimiento extraído del spec, la firma y el negocio. La infraestructura (pom, package.json, configs, scripts) es regenerable a partir de plantillas estándar.

Por eso el scaffold —manual o asistido— sigue este orden estricto:

1. **Tests** → primero, porque son lo que justifica el proyecto.
2. **Utilities / abstracciones** → después, porque dan estructura a los tests pero pueden recrearse.
3. **Infraestructura** → al final, porque es boilerplate regenerable.

Esto garantiza que, si el trabajo se interrumpe a la mitad por cualquier razón (cambio de prioridad, revisión temprana, decisión de cambiar de framework), lo entregado ya tenga valor real y no sea sólo "estructura sin contenido".

## Orden de scaffold (estricto)

### 1. PRIMERO — Archivos de prueba

Los artefactos de mayor valor: el conocimiento extraído del spec y la firma materializado en escenarios concretos.

| Framework  | Archivos                                       |
|------------|------------------------------------------------|
| Karate     | `*.feature`                                    |
| Playwright | `tests/**/*.spec.ts` (o `*.test.ts`)           |
| K6         | `tests/*.js` (uno por escenario load/stress/spike/soak) |
| Appium     | `*.feature` (Cucumber) y `tests/**/*Test.java` |
| serenity-wdio | `features/**/*.feature` (por canal: web, mobile, api) |

### 2. LUEGO — Utilitarios compartidos y modelos

Refactorizaciones, helpers y abstracciones que dan estructura a los tests, pero que pueden recrearse si se pierden.

| Framework  | Archivos                                                                          |
|------------|-----------------------------------------------------------------------------------|
| Karate     | Bodies JSON (`bodies/*.json`), feature helpers (`helpers/*.feature`)              |
| Playwright | Page Objects (`pages/*.ts`), fixtures (`fixtures/*.ts`), utils                    |
| K6         | `utils.js`, `config.js`, `payloads/*.js`, módulos de auth                          |
| Appium     | Tasks, Questions, UI elements, Screenplay actors                                  |
| serenity-wdio | Tasks, Interactions, Questions, UI Mapping (`PageElement`/selectores string), `support/parameter.config.ts` |

### 3. POR ÚLTIMO — Infraestructura

Configuración, build, documentación y scripts. Son los más fáciles de regenerar y los más voluminosos; por eso van al final.

| Framework  | Archivos                                                                                            |
|------------|-----------------------------------------------------------------------------------------------------|
| Karate     | `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, `README.md`, scripts de run    |
| Playwright | `package.json`, `playwright.config.ts`, `tsconfig.json`, `README.md`, scripts npm                    |
| K6         | `package.json` (si aplica), `README.md`, scripts de ejecución, dashboards (opcional)                 |
| Appium     | `build.gradle`, `serenity.conf`, `serenity.properties`, `README.md`, scripts gradle                  |
| serenity-wdio | `package.json`, `tsconfig.json`, `configs/wdio.*.conf.ts`, `wdio.shared.conf.ts`, `scripts/run.mjs`, `.env.*`, `README.md` |

## Disciplina

1. **Un archivo, una escritura.** Cada archivo queda persistido apenas se genera; nada se acumula "para entregar al final".
2. **Verificar el directorio padre** antes de escribir; si no existe, crearlo recursivamente.
3. **Trazabilidad por archivo emitido**: una línea de log por archivo (`[ok] tests/users.feature`), no un único reporte global.
4. **Idempotencia**: re-ejecutar el scaffold no debe duplicar tests ni sobrescribir trabajo manual posterior.

## Restricciones

- **NUNCA** generar primero `pom.xml` o `package.json` "para tener la estructura"; eso bloquea valor real detrás de boilerplate.
- **NUNCA** mezclar el orden entre frameworks: el orden es estricto por categoría (prueba → utilitario → infraestructura).
- Encadena con `[[calidad-test-evidence-and-traceability]]` para configurar los reportes después de escribir la infraestructura.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | emit [ok] <ruta> por cada archivo persistido (una línea de log por archivo, no reporte global) | Bloqueado: la trazabilidad por archivo emitido falta. Sin log por archivo no hay manifiesto auditable. |
| 2 | orden estricto respetado: tests → utilitarios/abstracciones → infraestructura | Bloqueado: el orden de scaffold se violó (infraestructura emitida antes que tests). Eso esconde valor detrás de boilerplate. |
| 3 | directorio padre verificado antes de escribir; scaffold idempotente (no duplicar ni sobrescribir trabajo manual) | Bloqueado: archivo escrito sin verificar directorio padre o scaffold no idempotente. |
