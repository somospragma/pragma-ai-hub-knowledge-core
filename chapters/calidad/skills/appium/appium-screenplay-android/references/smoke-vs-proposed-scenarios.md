
# Escenarios `@smoke` vs `@proposed`

## Regla

- Siempre se generan **2 escenarios `@android @smoke`** ejecutables, independientes de los inputs:
  1. Flujo base de login sin localizadores finales.
  2. Validación de carga y DOM de la aplicación.
- Si los inputs traen `user_story` o `test_cases` (≥1 item), se agregan **escenarios `@android @proposed`** aspiracionales, uno por item.

`LoginRunner` filtra por `@smoke` por default (constante `FILTER_TAGS_PROPERTY_NAME=@smoke`). `@proposed` es opt-in.

## `@smoke` (siempre, sin localizadores reales)

```gherkin
@android @smoke
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
# default: solo @smoke
./gradlew clean test aggregate -p .

# opt-in: solo aspiracionales
./gradlew clean test aggregate -Dcucumber.filter.tags=@proposed

# ambos
./gradlew clean test aggregate -Dcucumber.filter.tags='@smoke or @proposed'
```

Ver `[[calidad-appium-run-and-tags]]` para más combinaciones.
