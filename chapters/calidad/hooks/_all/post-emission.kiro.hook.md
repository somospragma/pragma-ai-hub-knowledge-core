---
id: calidad-post-emission-hook
version: 1.0.0
scope: chapter
type: hook
chapter: calidad
description: "Kiro hook que valida coherencia post-emisión (find paths, grep imports cruzados, compile dry-run) antes de permitir el cierre. Capa bonus para usuarios Kiro."
tags: [kiro, hook, post-emission, coherence, bonus]
trigger: agentStop
---

# Hook — Post-emission coherence (Kiro)

Trigger: agentStop después de batch de archivos.

Acciones por stack:
- Karate:
  - grep "# cobertura:" en *.feature → debe haber 1 por feature
  - find src/test/java/com/testing/features/ → debe contener los features
  - mvn compile (si modo full)
- Playwright:
  - grep "from.*fixtures/" tests/ → cada fixture debe ser importado
  - grep "from.*data/" tests/ → cada data file debe ser importado
  - grep "waitForTimeout" → debe ser 0
  - npx tsc --noEmit (si modo full)
- K6:
  - ls tests/*.js → debe haber 5 (smoke, load, stress, spike, soak)
  - grep "handleSummary" tests/*.js → debe estar en cada uno
  - k6 inspect tests/smoke-test.js (validación sintaxis)
- Appium:
  - find scripts/ → preflight.sh debe existir y ser ejecutable
  - test -x gradlew → wrapper ejecutable
  - ./gradlew compileJava (si modo full)

Si cualquier check falla → bloquear con mensaje y exigir corrección antes de continuar.

Mirror de la Capa 2 (workflow output-contract + scripts shippeable).
