---
id: calidad-karate-brownfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [karate]
description: Extiende un proyecto Karate existente con nuevos features sin regenerar infraestructura.
tags: [karate, brownfield, conventions]
---

# Karate Brownfield

## Cuándo aplicar

Cuando el usuario tiene un **proyecto Karate ya inicializado** (al menos `karate-config.js` + un `.feature`) y solicita agregar pruebas para uno o más endpoints nuevos. Decisión brownfield vs greenfield en `[[calidad-brownfield-vs-greenfield]]`.

Si el usuario no provee archivos del proyecto, no asumas: solicítalos o usa `[[calidad-karate-greenfield]]` previo acuerdo.

## Lectura obligatoria antes de tocar el proyecto

El conocimiento técnico del stack vive en el bundle **greenfield** del mismo stack; brownfield no lo duplica, lo consume. **Abrir antes de generar** y declarar cuáles se leyeron (traza en `[[calidad-pipeline-state-tracking]]`):

| Reference | Para qué |
|---|---|
| [[calidad-karate-greenfield]] (`references/feature-design-dsl.md`) | Tipos de escenario, tags y estilo |
| [[calidad-karate-greenfield]] (`references/contract-testing-match-patterns.md`) | Notación `match`, `#type` vs `##type` |
| [[calidad-karate-greenfield]] (`references/negative-coverage-formula.md`) | Cobertura defendible por endpoint |
| `references/convention-detection.md` · `references/client-specific-conventions.md` | Convenciones del proyecto (propias de este skill) |

**Cómo se aplica en brownfield**: estas references aportan el **conocimiento técnico** (cómo estructurar un feature, cómo reusar bodies y helpers, cómo aseverar con precisión, cómo diagnosticar un fallo). Las **convenciones del proyecto del cliente siempre mandan** sobre las del chapter (naming, tags, idioma, estilo, versiones). Nunca se importan las convenciones del greenfield a un proyecto existente.

**Diagnóstico sin imposición**: si al analizar el proyecto detectas un defecto conocido del stack (p. ej. aserciones laxas del tipo `#notnull` donde el contrato permite validar el schema completo, URLs de ambiente hardcodeadas en los `.feature` en vez de `karate-config.js`, escenarios que dependen del orden porque comparten estado, login repetido por escenario en vez de `callonce`, o el runner con tags fijos que anulan el filtro de la línea de comandos), **repórtalo al usuario con su evidencia y el fix sugerido — no lo apliques por tu cuenta**. Corregirlo sin permiso viola la regla de no tocar infraestructura ajena; callarlo deja al cliente con un falso verde que ya conocemos.

## Instrucción

1. **Recolectar inputs** — Usa `[[calidad-mandatory-inputs-protocol]]` y la lista de `references/mandatory-inputs-brownfield.md`. Inputs mínimos: `spec`, archivos de proyecto existente (`karate-config.js` + ≥1 `.feature`), `ticket_id`, `Body_Mode` (A = JSON externo, B = inline), `Scenario_Prefix` (opcional, se autodetecta del proyecto). Si el proyecto impone convenciones cliente-específicas (ver `references/client-specific-conventions.md`), `user_story` y `firma` pasan a OBLIGATORIO.
2. **Analizar proyecto existente y extraer convenciones** — Aplica el algoritmo de `references/convention-detection.md`: `features_dir`, `bodies_dir`, `package_name`, `base_url_var` (no asumir `baseUrl`), `header_style`, `body_loading_style`, `scenario_naming_pattern`, variables de `karate-config.js`.
3. **Detectar convenciones cliente-específicas y aplicarlas** — Si el proyecto impone convenciones cliente-específicas (naming con prefix de ticket, headers transversales obligatorios cross-endpoint, estilo step-by-step, etc.), aplica las reglas documentadas en `references/client-specific-conventions.md`. Las convenciones cliente-específicas **sobrescriben** las convenciones autodetectadas cuando hay conflicto.
4. **Generar SOLO `.feature` y body JSON** — Calcula escenarios con `[[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)`. Ubica los archivos en los directorios detectados, no inventes paths nuevos. Respeta `header_style`, `body_loading_style`, naming y tags del proyecto.
5. **Validar** — Cumple `[[calidad-karate-greenfield]] (consultar `references/file-location-constraint.md` en su subfolder)` (revisa que el `pom.xml` existente ya tenga el `<testResources>` correcto; si no, repórtalo pero no lo modifiques sin permiso). Recorre el DoD aplicable en `[[calidad-extend-karate-brownfield]]`.
6. **No generar infraestructura** — Cero archivos `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`. El proyecto ya los tiene.

## Salidas

- Uno o más `{resource}.feature` en `features_dir` detectado.
- Cero o más `{resource}-body.json` (u otro naming detectado) en `bodies_dir` cuando `Body_Mode = A`.

## Restricciones

- **NUNCA** regenerar `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, ni schemas existentes.
- **Respetar 100%** las convenciones detectadas. No "mejorar" estilo si difiere del proyecto.
- Si los inputs obligatorios faltan (especialmente `user_story` o `firma` cuando el proyecto impone convenciones cliente-específicas), detente y solicítalos.
- No mezclar convenciones cliente-específicas de un proyecto con proyectos de otros clientes ni viceversa.
- Reportar entregables con `[[calidad-streaming-files-protocol]]` y trazabilidad por `[[calidad-test-evidence-and-traceability]]`.
