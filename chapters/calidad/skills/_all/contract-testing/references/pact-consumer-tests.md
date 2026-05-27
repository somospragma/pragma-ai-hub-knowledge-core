# Pact Consumer Tests — Snippets por Lenguaje

El consumer escribe tests con un mock provider (provido por Pact). Cada test interactúa con el mock, y Pact registra las interacciones en un archivo JSON (el pact).

## TypeScript / Node.js (@pact-foundation/pact v12)

```bash
npm i -D @pact-foundation/pact
```

```typescript
// tests/contracts/users-api.pact.test.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';
import { fetchUser } from '../../src/clients/users-client';

const { like, integer, string } = MatchersV3;

const provider = new PactV3({
  consumer: 'web-app',
  provider: 'users-service',
  dir: path.resolve(process.cwd(), 'pacts'),
  logLevel: 'info',
});

describe('Users API contract', () => {
  it('GET /users/:id returns user when exists', async () => {
    provider
      .given('user with id 42 exists')
      .uponReceiving('a request for user 42')
      .withRequest({
        method: 'GET',
        path: '/users/42',
        headers: { Authorization: like('Bearer token') },
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: like({
          id: integer(42),
          name: string('Alice'),
          email: string('alice@example.com'),
        }),
      });

    await provider.executeTest(async (mockServer) => {
      const user = await fetchUser(mockServer.url, 42);
      expect(user.id).toBe(42);
      expect(user.name).toBe('Alice');
    });
  });

  it('GET /users/:id returns 404 when not found', async () => {
    provider
      .given('no user with id 999 exists')
      .uponReceiving('a request for missing user 999')
      .withRequest({ method: 'GET', path: '/users/999' })
      .willRespondWith({
        status: 404,
        body: like({ error: 'User not found' }),
      });

    await provider.executeTest(async (mockServer) => {
      await expect(fetchUser(mockServer.url, 999)).rejects.toThrow();
    });
  });
});
```

Al correr el test, Pact genera `pacts/web-app-users-service.json`.

## Java (pact-jvm-consumer-junit5)

```xml
<dependency>
    <groupId>au.com.dius.pact.consumer</groupId>
    <artifactId>junit5</artifactId>
    <version>4.6.9</version>
    <scope>test</scope>
</dependency>
```

```java
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "users-service")
class UsersApiContractTest {

    @Pact(consumer = "web-app")
    public V4Pact getUserPact(PactDslWithProvider builder) {
        return builder
            .given("user with id 42 exists")
            .uponReceiving("a request for user 42")
                .path("/users/42")
                .method("GET")
            .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(new PactDslJsonBody()
                    .integerType("id", 42)
                    .stringType("name", "Alice")
                    .stringType("email", "alice@example.com"))
            .toPact(V4Pact.class);
    }

    @Test
    @PactTestFor(pactMethod = "getUserPact")
    void getUserReturnsExpected(MockServer mockServer) {
        UsersClient client = new UsersClient(mockServer.getUrl());
        User user = client.fetchUser(42);

        assertEquals(42, user.getId());
        assertEquals("Alice", user.getName());
    }
}
```

## Python (pact-python v2)

```bash
pip install pact-python
```

```python
import pytest
from pact import Consumer, Provider

pact = Consumer('web-app').has_pact_with(
    Provider('users-service'),
    pact_dir='./pacts'
)

@pytest.fixture(scope='session', autouse=True)
def setup_pact():
    pact.start_service()
    yield
    pact.stop_service()

def test_get_user_exists():
    expected = {'id': 42, 'name': 'Alice', 'email': 'alice@example.com'}

    (pact
        .given('user with id 42 exists')
        .upon_receiving('a request for user 42')
        .with_request('GET', '/users/42')
        .will_respond_with(200, body=expected))

    with pact:
        from src.clients.users_client import fetch_user
        result = fetch_user(pact.uri, 42)
        assert result['id'] == 42
```

## .NET (PactNet)

```bash
dotnet add package PactNet --version 5.0.0
```

```csharp
public class UsersApiContractTests
{
    private readonly IPactBuilderV4 _pact;

    public UsersApiContractTests()
    {
        var config = new PactConfig { PactDir = "../../../pacts" };
        var pact = Pact.V4("web-app", "users-service", config);
        _pact = pact.WithHttpInteractions();
    }

    [Fact]
    public async Task GetUser_WhenExists_ReturnsUser()
    {
        _pact
            .UponReceiving("a request for user 42")
                .Given("user with id 42 exists")
                .WithRequest(HttpMethod.Get, "/users/42")
            .WillRespond()
                .WithStatus(HttpStatusCode.OK)
                .WithJsonBody(new
                {
                    id = 42,
                    name = "Alice",
                    email = "alice@example.com"
                });

        await _pact.VerifyAsync(async ctx =>
        {
            var client = new UsersClient(ctx.MockServerUri);
            var user = await client.FetchUserAsync(42);
            Assert.Equal(42, user.Id);
        });
    }
}
```

## Publicar pacts al broker

```bash
# después de que los tests pasen
pact-broker publish ./pacts \
  --consumer-app-version $(git rev-parse HEAD) \
  --branch $(git rev-parse --abbrev-ref HEAD) \
  --broker-base-url https://pactflow.cliente.io \
  --broker-token $PACT_BROKER_TOKEN
```

En CI (GitHub Actions):
```yaml
- name: Publish pacts
  if: success()
  run: |
    npx @pact-foundation/pact-cli publish ./pacts \
      --consumer-app-version=${{ github.sha }} \
      --branch=${{ github.ref_name }} \
      --broker-base-url=${{ secrets.PACT_BROKER_URL }} \
      --broker-token=${{ secrets.PACT_BROKER_TOKEN }}
```

## Buenas prácticas

- Una interacción por test — facilita debugging.
- Usar `MatchersV3.like()` y `integer()`/`string()` para no acoplarse a valores específicos (solo a tipos/estructura).
- `given()` describe el state del provider que se necesita — debe coincidir con un state handler en el provider verification.
- NUNCA hardcodear timestamps, UUIDs, o IDs generados — usar matchers (`uuid()`, `iso8601DateTime()`).
- Tests Pact viven en `tests/contracts/` separados de tests funcionales — corren rápido y sin red.

## Anti-patterns

- Pact tests que llaman al provider real (defeats the purpose — usar mock).
- Pacts gigantes con 50 interacciones — split en múltiples test files.
- Verificar comportamiento de negocio en el pact test (eso es para test funcional/integration).
- Olvidar publicar el pact en CI — el provider verifica versiones obsoletas.
