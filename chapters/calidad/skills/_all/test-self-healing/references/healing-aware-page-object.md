# Healing-Aware Page Object

Patrón de Page Object que **inyecta** la estrategia de healing por dependency injection en lugar de acoplarla al POM. Beneficio: los mismos POMs pueden ejecutarse en modo healing (CI nocturno) o en modo determinista (suite `@regression-strict`) sin duplicar código.

## Motivación

Si el POM hardcodea `ResilientLocator`, la suite de regresión estricta no puede detectar cuándo el primary locator se rompió — porque siempre se cura. Necesitamos poder **deshabilitar el healing** en suites donde una falla del primary es señal valiosa (regression de selectors, contract, security).

## Snippet TypeScript

```typescript
import { Page, Locator } from '@playwright/test';

interface HealingStrategy {
  resolve(strategies: Array<() => Locator>, testId: string): Promise<Locator>;
}

class MultiLocatorHealing implements HealingStrategy {
  async resolve(strategies: Array<() => Locator>, testId: string): Promise<Locator> {
    for (const [i, strategy] of strategies.entries()) {
      const loc = strategy();
      if ((await loc.count()) > 0) {
        if (i > 0) {
          console.log(JSON.stringify({
            event: 'healing',
            test_id: testId,
            strategy_idx: i,
          }));
        }
        return loc;
      }
    }
    throw new Error(`All locator strategies exhausted for ${testId}`);
  }
}

class NoHealing implements HealingStrategy {
  async resolve(strategies: Array<() => Locator>, testId: string): Promise<Locator> {
    const primary = strategies[0]();
    if ((await primary.count()) === 0) {
      throw new Error(
        `Primary locator failed for ${testId} (healing disabled by strategy). ` +
        'This is a regression signal, not a flake.'
      );
    }
    return primary;
  }
}

class UsersPage {
  constructor(
    private page: Page,
    private healing: HealingStrategy = new MultiLocatorHealing(),
  ) {}

  private emailStrategies = () => [
    () => this.page.getByTestId('email-input'),
    () => this.page.getByRole('textbox', { name: 'Email' }),
    () => this.page.getByLabel('Email'),
  ];

  async fillEmail(value: string) {
    const loc = await this.healing.resolve(this.emailStrategies(), 'users.email');
    await loc.fill(value);
  }
}
```

## Uso por tipo de suite

```typescript
// Suite CI nocturno (healing habilitado)
const users = new UsersPage(page, new MultiLocatorHealing());

// Suite @regression-strict (healing deshabilitado)
const usersStrict = new UsersPage(page, new NoHealing());

// Suite @security / @contract (healing deshabilitado obligatoriamente)
const usersSec = new UsersPage(page, new NoHealing());
```

## Reglas

- El POM **nunca** instancia su propia estrategia de healing — siempre vía constructor.
- El default puede ser `MultiLocatorHealing` pero los suites estrictos **deben** pasar `NoHealing` explícito.
- La decisión de qué estrategia inyectar se toma en el orquestador (`[[calidad-test-execution-orchestration]]`) basándose en los tags del suite.
- Si se introduce una tercera estrategia (ej. `VisualHealing`), debe implementar la misma interfaz `HealingStrategy` para no romper los POMs existentes.
- El patrón aplica análogo en Appium (Java) — definir `HealingStrategy` como interfaz y inyectar en cada Page Object del Screenplay.

## Beneficios concretos

- Tests `@regression-strict` fallan cuando el primary locator se rompe → señal temprana de cambio de SUT.
- Tests CI nocturnos siguen verdes mientras el equipo investiga → no bloquean entregas.
- Switch de estrategia es una línea, no requiere reescribir POMs.
- La evidencia (`[[calidad-test-evidence-and-traceability]]`) registra qué estrategia se usó por run.
