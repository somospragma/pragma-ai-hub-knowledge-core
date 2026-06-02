---
id: calidad-streaming-files-protocol
version: 2.0.0
scope: chapter
type: skill
chapter: calidad
description: Define el orden de scaffold de un proyecto de pruebas por valor entregado (tests primero, utilitarios después, infraestructura al final).
tags: [scaffold, prioritization, value-delivery, generation]
---

# Orden de scaffold por valor entregado

## Cuándo aplicar

Aplica este skill **siempre** que armes un proyecto de pruebas en cualquier framework del Chapter Calidad (Karate, Playwright, K6, Appium), tanto en greenfield como en brownfield, ya sea de forma manual o asistida. Es el paso 6 de `[[calidad-route-test-generation]]`.

Su propósito es asegurar que **el activo entregable de mayor valor —los tests— se materialice primero**, y que el boilerplate regenerable quede para el final.

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

### 2. LUEGO — Utilitarios compartidos y modelos

Refactorizaciones, helpers y abstracciones que dan estructura a los tests, pero que pueden recrearse si se pierden.

| Framework  | Archivos                                                                          |
|------------|-----------------------------------------------------------------------------------|
| Karate     | Bodies JSON (`bodies/*.json`), feature helpers (`helpers/*.feature`)              |
| Playwright | Page Objects (`pages/*.ts`), fixtures (`fixtures/*.ts`), utils                    |
| K6         | `utils.js`, `config.js`, `payloads/*.js`, módulos de auth                          |
| Appium     | Tasks, Questions, UI elements, Screenplay actors                                  |

### 3. POR ÚLTIMO — Infraestructura

Configuración, build, documentación y scripts. Son los más fáciles de regenerar y los más voluminosos; por eso van al final.

| Framework  | Archivos                                                                                            |
|------------|-----------------------------------------------------------------------------------------------------|
| Karate     | `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, `README.md`, scripts de run    |
| Playwright | `package.json`, `playwright.config.ts`, `tsconfig.json`, `README.md`, scripts npm                    |
| K6         | `package.json` (si aplica), `README.md`, scripts de ejecución, dashboards (opcional)                 |
| Appium     | `build.gradle`, `serenity.conf`, `serenity.properties`, `README.md`, scripts gradle                  |

## Disciplina

1. **Un archivo, una escritura.** Cada archivo queda persistido apenas se genera; nada se acumula "para entregar al final".
2. **Verificar el directorio padre** antes de escribir; si no existe, crearlo recursivamente.
3. **Trazabilidad por archivo emitido**: una línea de log por archivo (`[ok] tests/users.feature`), no un único reporte global.
4. **Idempotencia**: re-ejecutar el scaffold no debe duplicar tests ni sobrescribir trabajo manual posterior.

## Restricciones

- **NUNCA** generar primero `pom.xml` o `package.json` "para tener la estructura"; eso bloquea valor real detrás de boilerplate.
- **NUNCA** mezclar el orden entre frameworks: el orden es estricto por categoría (prueba → utilitario → infraestructura).
- Encadena con `[[calidad-test-evidence-and-traceability]]` para configurar los reportes después de escribir la infraestructura.
