# Multi-Locator Fallback Pattern

Patrón de implementación para resolver un elemento UI / API recurso evaluando una cadena de estrategias en orden de prioridad. La primera estrategia que retorna un resultado válido se devuelve; si ninguna funciona, se lanza error explícito (no silencioso).

El log de healing se emite cuando se resuelve con cualquier estrategia con índice `> 0` — es decir, cuando el primary falló y se cayó al fallback.

## Snippet completo TypeScript (Playwright)

```typescript
import { Page, Locator } from '@playwright/test';

type LocatorStrategy = () => Locator;

class ResilientLocator {
  constructor(
    private page: Page,
    private strategies: Array<LocatorStrategy>,
    private testId: string = 'unknown',
  ) {}

  async resolve(): Promise<Locator> {
    for (const [i, strategy] of this.strategies.entries()) {
      const loc = strategy();
      if ((await loc.count()) > 0) {
        if (i > 0) {
          console.log(
            JSON.stringify({
              event: 'healing',
              framework: 'playwright',
              test_id: this.testId,
              strategy_idx: i,
              total_strategies: this.strategies.length,
              timestamp: new Date().toISOString(),
            }),
          );
        }
        return loc;
      }
    }
    throw new Error(
      `All locator strategies exhausted for test=${this.testId}`,
    );
  }
}

// Uso en un Page Object
export class LoginPage {
  readonly emailInput: ResilientLocator;

  constructor(private page: Page) {
    this.emailInput = new ResilientLocator(
      page,
      [
        () => this.page.getByTestId('email-input'),
        () => this.page.getByRole('textbox', { name: 'Email' }),
        () => this.page.getByLabel('Email'),
        () => this.page.getByPlaceholder('correo electrónico'),
      ],
      'login.email',
    );
  }

  async fillEmail(value: string) {
    const loc = await this.emailInput.resolve();
    await loc.fill(value);
  }
}
```

## Equivalente Java / Appium

```java
import io.appium.java_client.AppiumBy;
import io.appium.java_client.AppiumDriver;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import java.util.List;

public class ResilientAppiumLocator {
    private final AppiumDriver driver;
    private final List<By> strategies;
    private final String testId;

    public ResilientAppiumLocator(AppiumDriver driver, List<By> strategies, String testId) {
        this.driver = driver;
        this.strategies = strategies;
        this.testId = testId;
    }

    public WebElement resolve() {
        for (int i = 0; i < strategies.size(); i++) {
            try {
                WebElement el = driver.findElement(strategies.get(i));
                if (i > 0) {
                    System.out.println(String.format(
                        "{\"event\":\"healing\",\"framework\":\"appium\",\"test_id\":\"%s\",\"strategy_idx\":%d}",
                        testId, i
                    ));
                }
                return el;
            } catch (Exception ignored) { }
        }
        throw new RuntimeException("All locator strategies exhausted for test=" + testId);
    }
}

// Uso
ResilientAppiumLocator emailField = new ResilientAppiumLocator(
    driver,
    List.of(
        AppiumBy.accessibilityId("email-input"),
        AppiumBy.id("com.app:id/email"),
        AppiumBy.xpath("//android.widget.EditText[@hint='Email']")
    ),
    "login.email"
);
emailField.resolve().sendKeys("user@example.com");
```

## Equivalente Karate (schema drift tolerance)

```gherkin
Feature: items listing con tolerancia controlada

  Scenario: shape opcional
    Given url baseUrl + '/items'
    When method get
    Then status 200
    # id es requerido (#notnull); description es opcional (##string)
    And match each $.items contains { id: '#notnull', description: '##string' }
    # Si description aparece pero no es string -> falla. Si no aparece -> pasa (drift tolerado).
```

## Reglas de uso

- El primary locator (índice `0`) **debe** ser el más estable según convención del chapter (`getByTestId` web, `accessibilityId` mobile, `#notnull` o `#number` para campos requeridos en Karate).
- El xpath o CSS bruto solo puede aparecer como **último elemento** de la cadena, nunca primario.
- El `testId` del `ResilientLocator` se propaga al log para correlacionar con dashboard de healing.
- Si la cadena se agota, error explícito (`throw`) — nunca devolver `null` ni continuar.
