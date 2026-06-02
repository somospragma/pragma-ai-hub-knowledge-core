# Seeding y Cleanup Transaccional por Framework

Cada framework tiene su mecanismo idiomático para preparar y limpiar datos. Mezclarlos sin documentar confunde la traza y deja residuos. Este documento estandariza los patrones por framework.

## Karate

### Patrón: `Setup.feature` + tags `@setup`/`@teardown`

`features/setup/Setup.feature`:

```gherkin
@setup
Feature: Setup global de datos

  Background:
    * url adminApiUrl
    * header X-Admin-Token = adminToken

  Scenario: crear usuario de prueba
    Given path 'admin/users'
    And request { email: '#(testEmail)', role: 'USER' }
    When method post
    Then status 201
    * def createdUserId = response.id
```

Invocación desde otra feature:

```gherkin
Feature: transferencias

  Background:
    * def setup = callonce read('classpath:features/setup/Setup.feature@setup') { testEmail: 'tx-tests@example.com' }
    * def userId = setup.createdUserId

  Scenario: usuario puede transferir
    Given path 'transfers'
    And request { from: '#(userId)', to: 'XYZ', amount: 100 }
    When method post
    Then status 201
```

`callonce` garantiza que el setup corre **una sola vez por feature** (no por scenario), reduciendo costo.

Teardown:

```gherkin
@teardown
Feature: Teardown global

  Scenario: borrar usuario de prueba
    Given url adminApiUrl
    And path 'admin/users', userId
    And header X-Admin-Token = adminToken
    When method delete
    Then status 204
```

Ejecutar con Karate hooks o como parte del runner:

```java
@AfterAll
static void teardown() {
  Runner.path("classpath:features/teardown/Teardown.feature").parallel(1);
}
```

## k6

### Patrón: `setup()` + `teardown()`

```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 50,
  duration: '2m',
};

export function setup() {
  // Se ejecuta una vez antes de la prueba
  const res = http.post(`${__ENV.ADMIN_URL}/users/bulk`, JSON.stringify({
    count: 1000,
    prefix: 'k6-perf-',
  }), { headers: { Authorization: `Bearer ${__ENV.ADMIN_TOKEN}` } });

  check(res, { 'bulk create 201': r => r.status === 201 });
  return { userIds: res.json('ids') }; // se pasa a default()
}

export default function (data) {
  const userId = data.userIds[__VU % data.userIds.length];
  http.get(`${__ENV.BASE_URL}/users/${userId}`);
}

export function teardown(data) {
  http.del(`${__ENV.ADMIN_URL}/users/bulk`, JSON.stringify({
    ids: data.userIds,
  }), { headers: { Authorization: `Bearer ${__ENV.ADMIN_TOKEN}` } });
}
```

Notas:
- `setup()` y `teardown()` corren en una VU dedicada, fuera del cómputo de carga.
- Si `teardown()` falla, los datos quedan: documentar y tener job nightly de limpieza.

## Playwright

### Patrón: `globalSetup` / `globalTeardown`

`playwright.config.ts`:

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  globalSetup: require.resolve('./tests/global-setup'),
  globalTeardown: require.resolve('./tests/global-teardown'),
  use: { baseURL: process.env.BASE_URL },
});
```

`tests/global-setup.ts`:

```typescript
import { request } from '@playwright/test';

export default async () => {
  const ctx = await request.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${process.env.ADMIN_TOKEN}` },
  });
  const res = await ctx.post(`${process.env.ADMIN_URL}/users`, {
    data: { email: 'pw-tests@example.com', role: 'USER' },
  });
  const { id } = await res.json();
  process.env.TEST_USER_ID = id;
  await ctx.dispose();
};
```

`tests/global-teardown.ts`:

```typescript
import { request } from '@playwright/test';

export default async () => {
  const ctx = await request.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${process.env.ADMIN_TOKEN}` },
  });
  await ctx.delete(`${process.env.ADMIN_URL}/users/${process.env.TEST_USER_ID}`);
  await ctx.dispose();
};
```

Para setup por archivo de test, usar `test.beforeAll` / `test.afterAll`.

## Spring (Java) — Integration tests

### Patrón: `@Transactional` con rollback automático

```java
@SpringBootTest
@Transactional
class TransferServiceIT {

  @Autowired UserRepository users;
  @Autowired TransferService service;

  @Test
  void transferReducesBalance() {
    // Setup
    User alice = users.save(UserMother.customerColombia());
    User bob = users.save(UserMother.customerMexico());

    // Test
    service.transfer(alice.getId(), bob.getId(), BigDecimal.TEN);

    // Assert
    assertEquals(BigDecimal.valueOf(90), users.findById(alice.getId()).getBalance());
    // No cleanup: Spring hace rollback al terminar el test.
  }
}
```

Beneficios:
- Cero código de cleanup.
- Aislamiento entre tests.
- Rápido (rollback < truncate).

Limitaciones:
- Solo aplica a integration tests sobre DB transaccional.
- Si la operación bajo prueba abre nueva transacción (`REQUIRES_NEW`), el rollback puede no cubrir lo creado dentro.
- No funciona si el test invoca servicios HTTP externos que persisten estado.

## Patrón Outbox para cleanup asíncrono

Cuando una operación dispara efectos asíncronos (mensaje a Kafka, evento webhook), el cleanup directo no alcanza: el procesador asíncrono puede crear datos después del teardown.

Solución: tag de correlación + job de cleanup que filtra por el tag.

```javascript
// Cada dato creado por la suite lleva un correlation id único
const corrId = `e2e-${Date.now()}-${randomUUID()}`;
await create({ email: `${corrId}@example.com`, metadata: { corrId } });

// Job nightly:
//   DELETE FROM users WHERE metadata->>'corrId' LIKE 'e2e-%';
//   DELETE FROM events WHERE metadata->>'corrId' LIKE 'e2e-%';
```

Documentar el patrón en el repo de la suite para que operaciones del cliente lo conozca.

## Decisión rápida

| Framework         | Mecanismo                                    |
|-------------------|----------------------------------------------|
| Karate            | `callonce` + `Setup.feature` + `@teardown`   |
| k6                | `setup()` + `teardown()`                     |
| Playwright        | `globalSetup` + `globalTeardown`             |
| Spring IT         | `@Transactional` (rollback automático)       |
| Cualquier e2e con efectos asíncronos | Tag de correlación + job nightly |

## Restricciones

- Nunca dejes datos huérfanos en ambientes compartidos: documenta y automatiza limpieza.
- Documenta en el README de la suite qué tipo de cleanup usa cada nivel.
- No mezcles rollback transaccional con limpieza por API admin en el mismo test: el orden de operaciones se vuelve frágil.
- Para fallas de teardown, registra alerta (no fail silencioso): los datos huérfanos crecen rápido.
- Encadena con `[[calidad-test-evidence-and-traceability]]` para que el reporte incluya correlation IDs.
