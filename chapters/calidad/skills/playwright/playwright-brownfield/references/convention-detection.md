
# Detección de convenciones

## Campos a extraer

| Campo                    | Fuente                                       | Ejemplo                                                  |
|--------------------------|----------------------------------------------|----------------------------------------------------------|
| `tests_dir`              | `playwright.config.ts` → `testDir`           | `./tests`, `./e2e`                                       |
| `pages_dir`              | Imports en specs                              | `pages/`, `src/page-objects/`                            |
| `fixtures_dir`           | Imports en specs                              | `fixtures/`, `src/fixtures/`                             |
| `test_file_pattern`      | Listado de specs                              | `*.spec.ts` vs `*.test.ts`                               |
| `page_object_style`      | Sample de un Page Object                      | `class` con propiedades readonly vs `function` factory   |
| `selector_strategy`      | Frecuencia de APIs en Page Objects            | predominantemente `getByRole` vs `getByTestId` vs CSS    |
| `import_style`           | Imports en specs y Page Objects               | `@pages/...` (alias) vs `../../pages/...` (relativo)     |
| `path_aliases`           | `tsconfig.json` → `compilerOptions.paths`     | `{ "@pages/*": ["pages/*"], ... }`                       |
| `base_url`               | `playwright.config.ts` → `use.baseURL`        | `process.env.BASE_URL`, literal string                   |
| `auth_pattern`           | Presencia de `auth.setup.ts` y `storageState` | `storageState` \| `fixture` \| `none`                    |
| `existing_page_objects[]`| Listado `pages/*.ts`                          | `[UsersPage, OrdersPage, NavigationBar]`                 |
| `existing_tests[]`       | Listado de specs                              | `[users.spec.ts, orders.spec.ts]`                        |
| `existing_fixtures[]`    | Listado `fixtures/*.ts`                       | `[base.fixture.ts, auth.setup.ts]`                       |

## Algoritmo

1. Leer `playwright.config.ts` → `testDir`, `use.baseURL`, projects, dependencies, storageState.
2. Leer `tsconfig.json` → `compilerOptions.paths` para resolver aliases.
3. Leer `package.json` → versiones de `@playwright/test`, `@axe-core/playwright`, scripts.
4. Tomar 2-3 specs y 2-3 Page Objects representativos: contar frecuencia de cada `getBy*` API; observar estilo de imports; observar estructura de clase.
5. Listar archivos en `pages/`, `fixtures/`, `tests/` para llenar los arrays `existing_*`.
6. Si se ve `auth.setup.ts` + `storageState` en config → `auth_pattern: storageState`. Si solo se ve un fixture nombrado `authenticated` → `auth_pattern: fixture`. Sin login alguno → `auth_pattern: none`.

## Salida sugerida

```json
{
  "tests_dir": "./tests",
  "pages_dir": "pages",
  "fixtures_dir": "fixtures",
  "test_file_pattern": "*.spec.ts",
  "page_object_style": "class",
  "selector_strategy": "getByRole",
  "import_style": "alias",
  "path_aliases": { "@pages/*": ["pages/*"], "@fixtures/*": ["fixtures/*"] },
  "base_url": "process.env.BASE_URL",
  "auth_pattern": "storageState",
  "existing_page_objects": ["UsersPage", "OrdersPage", "NavigationBar"],
  "existing_tests": ["users.spec.ts", "orders.spec.ts"],
  "existing_fixtures": ["base.fixture.ts", "auth.setup.ts"]
}
```
