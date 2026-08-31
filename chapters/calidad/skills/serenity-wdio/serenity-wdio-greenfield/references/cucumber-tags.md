# Tags de Cucumber (Serenity WDIO Greenfield)

Todo `.feature` generado debe estar etiquetado con al menos un tag de canal y un tag de suite para permitir ejecucion selectiva via `--tags`.

## Convencion de tags

| Categoria | Tags validos | Donde aplica |
|---|---|---|
| Canal / plataforma | `@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop` | nivel Feature |
| Suite | `@smoke`, `@regression` | Feature o Scenario |
| Tipo | `@happy-path`, `@negative`, `@edge-case` | Scenario |
| Dominio | `@login`, `@form`, `@health-check`, etc. | Feature o Scenario |
| Estado | `@wip`, `@skip`, `@flaky` | Scenario (excluir con `not`) |

## Reglas

- Tags de canal y suite global van a nivel Feature.
- Tags de tipo y dominio especifico van a nivel Scenario.
- `@smoke` es un subconjunto de `@regression`; no etiquetar como `@smoke` lo que no sea critico.
- Escenarios `@wip` o `@skip` se excluyen con `--tags="not @wip and not @skip"`.

## Ejemplo de feature etiquetado

```gherkin
@web @form @regression
Feature: Gestion de formulario Practice Form

  @smoke @happy-path
  Scenario: Registro exitoso de estudiante
    ...

  @negative
  Scenario: Registro con datos invalidos
    ...
```

## Seleccion por tags

El orquestador `scripts/run.mjs` acepta `--tags=...` o `TAGS=...` y los reenvia a WebdriverIO como `--cucumberOpts.tags=<expr>`. La sintaxis admite `and`, `or`, `not` y agrupacion con parentesis.

```bash
node ./scripts/run.mjs --mode=web --tags=@smoke
node ./scripts/run.mjs --mode=api --tags="@regression and not @wip"
node ./scripts/run.mjs --mode=movil --platform=android --tags="(@smoke or @happy-path) and not @flaky"
```
