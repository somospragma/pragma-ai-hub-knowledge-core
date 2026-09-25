# Cucumber/Gherkin — Patrones de features

## Patrón del proyecto (Web)

```gherkin
Feature: <Descripción del módulo funcional>

  @<tag>
  Scenario Outline: <Nombre del escenario en español>
    Given que <actor> <precondición>
    When <actor> <acción principal>
    And <actor> <acción secundaria>
    Then <actor> debería <resultado esperado>

    Examples:
      | actor   | dataset          |
      | Pepito  | datos_ejemplo    |
```

## Patrón del proyecto (Mobile)

```gherkin
Feature: <Descripción del módulo funcional>

  Scenario: <Nombre del escenario>
    Given the user named <actor> opens the application
    When he logs in with username "<usuario>" and password "<clave>"
    Then he should see the home screen
```

## Patrón del proyecto (API)

```gherkin
Feature: <Descripción del módulo de API>

  Scenario: <Nombre del escenario>
    Given que <actor> consume el servicio API
    When <actor> consulta el endpoint "<ruta>"
    Then <actor> debería recibir un código <código>
```

## Tags obligatorios (convención del proyecto)

Todo `.feature` debe tener al menos un tag de canal y uno de suite a nivel Feature:

```gherkin
@web @form @regression
Feature: Gestión de formulario Practice Form

  @smoke @happy-path
  Scenario: Registro exitoso de estudiante
    ...

  @negative
  Scenario: Registro con datos inválidos
    ...
```

| Categoría | Tags válidos | Nivel |
|---|---|---|
| Canal / plataforma | `@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop` | Feature |
| Suite | `@smoke`, `@regression` | Feature o Scenario |
| Tipo | `@happy-path`, `@negative`, `@edge-case` | Scenario |
| Dominio | `@login`, `@form`, `@health-check`, etc. | Feature o Scenario |
| Estado | `@wip`, `@skip`, `@flaky` | Scenario |

## Mapeo Gherkin a Screenplay

| Elemento Gherkin | Elemento Screenplay | Ubicación |
|---|---|---|
| `Given` | Task de precondición / navegación | `Tasks/` |
| `When` | Task de acción principal | `Tasks/` |
| `Then` | Task de verificación o Question + Ensure | `Tasks/` o `Questions/` |
| `And` | Composición dentro de Task existente | `Tasks/` |
| Actor en step | `actorCalled('Nombre')` | `parameter.config.ts` |

## Checklist de calidad (features)

- [ ] El `.feature` no contiene detalles técnicos (selectores, IDs, XPath)
- [ ] Cada escenario tiene una sola responsabilidad
- [ ] Los nombres de actores usan mayúscula inicial
- [ ] El archivo tiene al menos un tag de canal y uno de suite a nivel Feature
- [ ] El archivo está en la carpeta correcta según el contexto (web/mobile/api)
- [ ] Los escenarios marcados como `@wip` se excluyen por defecto
