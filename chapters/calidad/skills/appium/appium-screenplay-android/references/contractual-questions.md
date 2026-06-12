# Contractual Questions — Validación no superficial (Appium / Screenplay)

## Principio

Una Question como `ElementIsDisplayed.of(...)` o `WebElementQuestion.the(...).is(visible())` confirma que el elemento existe en el árbol nativo, pero NO confirma que el dato del dominio que la app debía mostrar coincida con el contrato funcional. Una pantalla puede renderizar el componente vacío, con datos del usuario equivocado, o con un formato distinto al esperado, y aún así pasar el `seeThat(...is displayed...)`.

**Regla obligatoria**: cada `.feature` de Appium que valide datos del dominio debe expresar el contrato funcional con Questions específicas (cantidad esperada, formato esperado, texto del dominio, transición post-acción), además de la existencia estructural del elemento.

Aplica al workflow `[[generate-appium-screenplay-android]]` paso 6 ("Generar escenarios") y se audita como parte del DoD (`[[calidad-delivery-gate-contract]]`).

## Anti-pattern frecuente

```java
// MAL — pasa aunque la lista esté vacía
actor.should(seeThat(theElement(TransactionsList.CONTAINER).is(displayed())));
```

El escenario no falla si:

- El backend responde `[]` y la lista renderiza vacía.
- La paginación está rota (sólo se renderizan 5 de 100).
- El monto viene sin formato (`1234` en vez de `$1,234.56`).
- El primer row corresponde a otro usuario por bug de tenancy.

## Patrón correcto

```java
// BIEN — codifica el contrato funcional
actor.should(
  seeThat("rows visible",        TransactionsList.rowCount(),           equalTo(20)),
  seeThat("first row money fmt", TransactionsList.firstRowAmountText(), matchesPattern("^\\$[\\d,]+\\.\\d{2}$")),
  seeThat("pagination text",     TransactionsList.paginationText(),     matchesPattern("Página \\d+ de \\d+"))
);
```

Cada `seeThat` es una Question independiente que declara una propiedad del contrato. El escenario falla cuando:

- Cambia la cantidad de rows (regresión de paginación o filtro).
- Cambia el formato monetario.
- Desaparece el indicador de paginación.

## Tabla — tipo de pantalla → Questions contractuales mínimas

| Tipo de pantalla        | Questions contractuales mínimas                                                                                                               |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| Listado paginado        | `rowCount()` con valor esperado; `firstRowDomainText()` con regex de formato; `paginationText()` regex `Página \\d+ de \\d+`.                  |
| Detalle                 | Campos clave con valor del dominio (no sólo "displayed"); incluir IDs/labels del registro abierto.                                            |
| Formulario              | Mensaje de éxito específico (texto exacto) tras submit válido; mensajes de error por campo en submit inválido.                                |
| Login                   | Transición a `HomeScreen` esperada (Question `CurrentScreen.is()`), avatar / nombre de usuario visible con el valor logueado.                 |
| Filtros                 | `resultCount()` igual al esperado tras aplicar filtro; empty state explícito con filtro inválido.                                             |
| Listado scrolleable     | `firstVisibleItem()` y `lastVisibleItem()` con valor esperado tras scroll; no "al menos un item visible".                                     |
| Modal / Dialog          | Foco trapped en el modal; cierre por gesto back y por botón; el body del modal contiene los campos del registro abierto.                     |
| Wizard / multi-step     | `currentStepIndicator()` con valor esperado; navegación adelante/atrás preserva datos previos.                                                |
| Empty state             | Mensaje exacto cuando el backend responde `[]`; CTA correcto (no "crear" si la pantalla es read-only).                                       |
| Error state             | Mensaje del backend renderizado tal cual; retry visible si aplica; layout no colapsa.                                                         |

## Estructura de Questions del dominio

Las Questions del contrato viven en `src/main/java/co/com/pragma/questions/`:

```java
public class TransactionsList {

  public static Question<Integer> rowCount() {
    return actor -> Target.the("transaction rows")
        .locatedBy(AppiumBy.id("co.example:id/transaction_row"))
        .resolveAllFor(actor)
        .size();
  }

  public static Question<String> firstRowAmountText() {
    return actor -> Text.of(Target.the("first row amount")
        .locatedBy(AppiumBy.xpath("(//android.widget.TextView[@resource-id='co.example:id/amount'])[1]")))
        .answeredBy(actor);
  }

  public static Question<String> paginationText() {
    return actor -> Text.of(Target.the("pagination indicator")
        .locatedBy(AppiumBy.accessibilityId("pagination-text")))
        .answeredBy(actor);
  }
}
```

## Reglas Appium-específicas

- Las Questions de contrato se evalúan SOLO en step `@main-step`; en setup/auth/cleanup se usan Questions estructurales (existencia, displayed). Ver `[step-isolation-appium](./step-isolation-appium.md)`.
- Una Question es contractual cuando devuelve un valor del dominio (`Integer`, `String` con regex, enum) y se compara con un matcher específico. Si devuelve `Boolean` desde `displayed()`, es estructural.
- NO mezclar visibilidad estructural con contrato en un solo `seeThat`: separar en varias `seeThat(...)` consecutivas mejora la trazabilidad del fallo.
- Cuando la app es localizada (i18n), las regex se parametrizan vía utility o se cargan desde `models/` para no hardcodear strings de idioma en las Questions.
- Anti-pattern adicional: usar `Thread.sleep(...)` entre Question y aserción. Usar `WaitUntil.the(target, isVisible()).forNoMoreThan(N).seconds()` antes de la Question contractual.

## Cross-links

`[step-isolation-appium](./step-isolation-appium.md)`, `[screenplay-layers](./screenplay-layers.md)`, `[gherkin-syntax-rules](./gherkin-syntax-rules.md)`, `[[appium-screenplay-android]]`, `[[calidad-delivery-gate-contract]]`.
