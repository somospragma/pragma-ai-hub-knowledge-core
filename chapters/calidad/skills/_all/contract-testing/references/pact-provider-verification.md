# Pact Provider Verification — Snippets por Lenguaje

El provider descarga los pacts publicados por sus consumers y verifica que su API real cumple cada interacción.

## Java (pact-jvm-provider-junit5) — Spring Boot

```xml
<dependency>
    <groupId>au.com.dius.pact.provider</groupId>
    <artifactId>junit5spring</artifactId>
    <version>4.6.9</version>
    <scope>test</scope>
</dependency>
```

```java
@Provider("users-service")
@PactBroker(
    host = "${PACT_BROKER_HOST}",
    authentication = @PactBrokerAuth(token = "${PACT_BROKER_TOKEN}")
)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class UsersServiceProviderTest {

    @LocalServerPort
    private int port;

    @MockBean
    private UserRepository userRepository;

    @BeforeEach
    void setUp(PactVerificationContext context) {
        context.setTarget(new HttpTestTarget("localhost", port));
    }

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        context.verifyInteraction();
    }

    @State("user with id 42 exists")
    void userExists() {
        when(userRepository.findById(42L))
            .thenReturn(Optional.of(new User(42L, "Alice", "alice@example.com")));
    }

    @State("no user with id 999 exists")
    void userDoesNotExist() {
        when(userRepository.findById(999L))
            .thenReturn(Optional.empty());
    }
}
```

Para verificar con tag específico (ej. solo pacts de `prod`):

```java
@PactBroker(
    consumerVersionSelectors = {
        @VersionSelector(tag = "prod"),
        @VersionSelector(tag = "main", latest = "true")
    }
)
```

## TypeScript / Node.js (@pact-foundation/pact provider)

```typescript
// tests/provider/verify.test.ts
import { Verifier } from '@pact-foundation/pact';
import { server } from '../../src/server';

describe('Users Service provider verification', () => {
  let serverInstance: any;

  beforeAll(async () => {
    serverInstance = await server.listen(3001);
  });

  afterAll(async () => {
    await serverInstance.close();
  });

  it('validates contracts from broker', async () => {
    const opts = {
      provider: 'users-service',
      providerBaseUrl: 'http://localhost:3001',
      pactBrokerUrl: process.env.PACT_BROKER_URL,
      pactBrokerToken: process.env.PACT_BROKER_TOKEN,
      consumerVersionSelectors: [
        { mainBranch: true },
        { deployedOrReleased: true },
      ],
      providerVersion: process.env.GIT_SHA,
      providerVersionBranch: process.env.GIT_BRANCH,
      publishVerificationResult: true,
      stateHandlers: {
        'user with id 42 exists': async () => {
          await db.users.insert({ id: 42, name: 'Alice', email: 'alice@example.com' });
        },
        'no user with id 999 exists': async () => {
          await db.users.delete({ id: 999 });
        },
      },
    };

    await new Verifier(opts).verifyProvider();
  });
});
```

## State handlers — patrón canónico

Cada `given('state X')` del consumer debe tener un handler en el provider que **prepara el estado** antes de verificar la interacción.

Patrones comunes:
- **In-memory mock**: `MockBean` en Spring, `jest.mock` en Node. Rápido, sin DB.
- **Test database**: cleanup + seed antes de cada interacción. Más realista pero lento.
- **Fixtures pre-cargados**: DB con fixtures conocidos; el state handler valida que existan.

```java
// Patron con DB real
@State("user with id 42 exists")
void userExists() {
    jdbcTemplate.update("DELETE FROM users WHERE id = ?", 42);
    jdbcTemplate.update(
        "INSERT INTO users (id, name, email) VALUES (?, ?, ?)",
        42, "Alice", "alice@example.com"
    );
}
```

## Publicar resultado al broker

```bash
# JVM via maven plugin
mvn pact:verify \
  -Dpact.verifier.publishResults=true \
  -Dpact.provider.version=$(git rev-parse HEAD) \
  -Dpact.provider.branch=$(git rev-parse --abbrev-ref HEAD)
```

```typescript
// Node — ya configurado en publishVerificationResult: true
```

El broker registra el resultado y lo usa para `can-i-deploy`.

## Integración con Karate (no nativo)

Pact no tiene runner Karate oficial. Estrategia recomendada:

- Mantener **proyectos separados**: Karate para funcional, Pact verifier (Java JUnit5) para contratos.
- Compartir el mismo JAR del provider en ambos: Pact verifica el contrato, Karate verifica el comportamiento.
- En el pipeline, correr ambos jobs en paralelo contra el mismo build del provider.

```yaml
# pipeline
- job: PactVerify
  steps:
    - mvn -pl pact-verifier test
- job: KarateFunctional
  steps:
    - mvn -pl karate-tests test
```

No intentar reescribir el verifier en Karate — el match de Pact tiene reglas específicas (matchers V3/V4, generators) que Karate no replica nativamente.

## Buenas prácticas

- State handlers son **setup, no assertion** — no escribir lógica de validación allí.
- Database cleanup entre interactions evita test pollution.
- `publishVerificationResult: true` en CI principal; `false` en branches feature para no contaminar el broker.
- Usar `consumerVersionSelectors` para evitar verificar pacts obsoletos (ej. solo `mainBranch` y `deployedOrReleased`).

## Anti-patterns

- Verificar contra DB de producción (siempre staging o test container).
- State handlers con side effects no reversibles (envío de email, llamada a tercero).
- Skip de interactions sin razón documentada — el broker lo registra y can-i-deploy puede fallar.
- Cambiar el provider sin re-verificar — el contrato queda obsoleto silenciosamente.
