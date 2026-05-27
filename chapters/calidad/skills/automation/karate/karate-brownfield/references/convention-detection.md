
# Detección de convenciones en brownfield

## Qué detectar

| Convención | Cómo se infiere |
|---|---|
| `features_dir` | Path del primer `.feature` que se encuentre bajo `src/test/java/`. |
| `bodies_dir` | Path resuelto del primer `read('classpath:...json')` en un `.feature`. |
| `package_name` | Package del `TestRunner.java` (ej: `com.testing`, `com.cliente.qa`). |
| `base_url_var` | Variable de URL usada en los `Background` (ej: `baseUrl`, `mercantilUrl`, `apiUrl`). NO asumir `baseUrl`. |
| `background_pattern` | Líneas comunes en el `Background` (url, headers, defs, callonce). |
| `header_style` | `one-by-one` (`And header X-Name = 'value'`) o `configure-headers` (`* configure headers = {...}`). |
| `body_loading_style` | `external-json` (`read('classpath:...json')`) o `inline` (`* def body = { ... }` / `* set body.field = value`). |
| `scenario_naming_pattern` | Patrón observado en los `Scenario:` (prefijos, idioma, tags estándar). |
| `config_variables` | Variables expuestas por `karate-config.js` (URLs por env, timeouts, flags). |

## Algoritmo

1. Leer `karate-config.js` y extraer todas las propiedades del objeto `config`. Anotar nombres exactos.
2. Leer al menos un `.feature` existente. Idealmente uno por carpeta si hay varios módulos.
3. Para cada `.feature`:
   - Extraer `Background` y `Scenario`/`Scenario Outline`.
   - Clasificar `header_style` y `body_loading_style` según las líneas observadas.
   - Anotar tags utilizados (`@happyPath`, `@smoke`, `@regression`, etc.) y el patrón del título.
4. Leer `TestRunner.java` y registrar `package_name`.
5. Resolver paths `classpath:` relativos al package del runner — el resultado es el `features_dir` / `bodies_dir` real.
6. Consolidar las convenciones en un objeto y úsalo como contrato para los nuevos `.feature`.

## Regla de prioridad

Si el proyecto pertenece a un cliente con doc específica (ej: `[[karate-mercantil-conventions]]`), las reglas del cliente sobrescriben las convenciones autodetectadas en caso de conflicto. Esto evita "regresar" estilo cuando un proyecto fue construido contra una versión vieja del estándar Mercantil.
