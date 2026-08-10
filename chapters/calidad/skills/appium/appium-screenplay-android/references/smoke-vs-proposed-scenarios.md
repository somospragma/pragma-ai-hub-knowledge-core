
# Escenarios `@smoke` vs `@proposed`

## Regla

- **Exactamente UNO** de los escenarios lleva `@smoke-gate`: es el gate 1:1 del chapter (`[[calidad-smoke-gate-policy]]`) y debe ser el flujo crítico end-to-end más representativo. Verificar el conteo antes de correr: `grep -rc "@smoke-gate" src/test/resources/features/` == 1.
- Se generan **2 escenarios `@android @smoke`** ejecutables, independientes de los inputs (uno de ellos, el más end-to-end, lleva además `@smoke-gate`):
  1. Flujo base de login sin localizadores finales.
  2. Validación de carga y DOM de la aplicación.
- Si los inputs traen `user_story` o `test_cases` (≥1 item), se agregan **escenarios `@android @proposed`** aspiracionales, uno por item.

**Los tags NO se hardcodean en el runner.** Un solo runner por proyecto, sin `@ConfigurationParameter(FILTER_TAGS_PROPERTY_NAME, ...)`: el filtro llega por CLI (`-Dcucumber.filter.tags`). Un tag fijo en el runner **sobreescribe** el de la línea de comandos y hace que "correr el smoke" ejecute otra cosa — causa raíz verificada en campo (el usuario mandaba `@smoke` y corrían todos). Ver `[[calidad-appium-run-and-tags]]`.

## `@smoke` (siempre, sin localizadores reales)

```gherkin
@android @smoke @smoke-gate
Scenario: Flujo base de login sin localizadores finales
  Given el usuario abre la app movil
  When ejecuta el flujo base de login sin localizadores definitivos
  Then la app responde al flujo base

@android @smoke
Scenario: Validacion de carga y DOM de la aplicacion
  Given el usuario abre la app movil
  When la aplicacion termina de cargar
  Then la pantalla principal es visible y la app responde
```

Estos escenarios deben pasar sin selectores reales (ver ``deferred-locators-strategy.md``).

## `@proposed` (condicional, opt-in)

- Tags: `@android @proposed`
- Title: primeros 80 caracteres del item de `test_cases`/`user_story` (newlines → espacios).
- Steps: stubs compartidos con marker `# TODO: implementar steps para este escenario`.
- No invocan step definitions concretas: documentan intención.

Ejemplo:

```gherkin
@android @proposed
Scenario: Login con credenciales invalidas muestra mensaje de error
  Given el usuario abre la app movil
  When intenta el escenario propuesto
  Then queda pendiente la implementacion real
  # TODO: implementar steps para este escenario
```

## Ejecución

```bash
# GATE 1:1 — exactamente un escenario (esto es lo primero que se ejecuta)
./gradlew clean test aggregate -Dcucumber.filter.tags=@smoke-gate

# suite smoke
./gradlew clean test aggregate -Dcucumber.filter.tags=@smoke

# opt-in: solo aspiracionales
./gradlew clean test aggregate -Dcucumber.filter.tags=@proposed

# ambos
./gradlew clean test aggregate -Dcucumber.filter.tags='@smoke or @proposed'
```

Si el conteo ejecutado no coincide con el filtro pedido, el problema está en el runner (tag hardcodeado), en un runner duplicado o en un default de `build.gradle` — no se sigue adelante hasta corregirlo.

Ver `[[calidad-appium-run-and-tags]]` para más combinaciones.
