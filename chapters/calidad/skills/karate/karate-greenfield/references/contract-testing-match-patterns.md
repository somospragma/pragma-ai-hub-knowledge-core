
# Patrones de match para contract testing

## Tabla de patrones

| Tipo | Patrón |
|---|---|
| String requerido | `#string` |
| String opcional | `##string` |
| Number requerido | `#number` |
| Number opcional | `##number` |
| Boolean requerido | `#boolean` |
| Boolean opcional | `##boolean` |
| Array requerido | `#[]` o `#[] #object` |
| Array opcional | `##[]` |
| Object requerido | `#object` |
| Object opcional | `##object` |
| Not null | `#notnull` |
| Null | `#null` |

## Reglas

- Un `#` = requerido. Doble `##` = opcional (la clave puede no existir, y si existe debe cumplir el tipo).
- **NUNCA** combinar opcional de array con tipo de items: `##[] #object` es inválido. Usa sólo `##[]`.
- Para objetos anidados opcionales, deja el `##object` o redirige a otro `-match.json` con `read('classpath:schemas/sub-match.json')`.
- Para arrays de objetos, define el shape de cada item: `'items': '#[] #object'` y opcionalmente `'items[0]': { ... }`.

## Ejemplo — `users-match.json`

```json
{
  "userId": "#uuid",
  "firstName": "#string",
  "lastName": "#string",
  "middleName": "##string",
  "age": "#number",
  "active": "#boolean",
  "createdAt": "#string",
  "deletedAt": "##null",
  "address": {
    "street": "#string",
    "zipCode": "##string"
  },
  "roles": "#[] #object",
  "metadata": "##object",
  "tags": "##[]"
}
```

Uso en feature:

```gherkin
@contract
Scenario: Get user - contract validation
  Given path '/users', userId
  When method get
  Then status 200
  And match response == read('classpath:schemas/users-match.json')
```
