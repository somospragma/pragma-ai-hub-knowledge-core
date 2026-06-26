# Spring Cloud Contract (SCC) — Contratos Provider-Driven

A diferencia de Pact (consumer-driven), Spring Cloud Contract pone el contrato **en el repo del provider**. El provider genera automaticamente:
- Tests JUnit que verifican el contrato contra su API.
- Stubs WireMock que los consumers usan para sus tests.

## Cuándo usar SCC vs Pact

| Aspecto                            | Spring Cloud Contract       | Pact                        |
| ---------------------------------- | --------------------------- | --------------------------- |
| Stack del provider                 | Spring (Java/Kotlin/Groovy) | Cualquiera                  |
| Origen del contrato                | Provider                    | Consumer                    |
| Distribución de stubs              | Maven repo / Pact Broker    | Pact Broker                 |
| Consumer en otro stack             | Si (HTTP stubs)             | Si (Pact lib en su lang)    |
| `can-i-deploy` gate                | No nativo                   | Si                          |
| Curva                              | Media (DSL Groovy)          | Alta                        |
| Mejor caso                         | Provider Spring + consumers conocidos | Cross-org / cross-team |

**Recomendación Pragma:** SCC si el cliente es **Spring-heavy** y el provider es la fuente autoritativa del contrato. Pact si los consumers son los dueños del contrato.

## Setup en el provider (Maven + Spring Boot)

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-contract-verifier</artifactId>
    <version>4.1.4</version>
    <scope>test</scope>
</dependency>

<build>
    <plugins>
        <plugin>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-contract-maven-plugin</artifactId>
            <version>4.1.4</version>
            <extensions>true</extensions>
            <configuration>
                <baseClassForTests>com.cliente.users.BaseContractTest</baseClassForTests>
            </configuration>
        </plugin>
    </plugins>
</build>
```

## Contrato Groovy DSL

```groovy
// src/test/resources/contracts/shouldCreateUser.groovy
import org.springframework.cloud.contract.spec.Contract

Contract.make {
    description "should create user successfully"

    request {
        method POST()
        url "/users"
        headers {
            contentType applicationJson()
            header("Authorization", anyNonBlankString())
        }
        body([
            name: "Alice",
            email: $(consumer(regex(/[a-z]+@[a-z]+\.[a-z]+/)), producer("alice@example.com"))
        ])
    }

    response {
        status CREATED()
        headers {
            contentType applicationJson()
        }
        body([
            id: $(producer(42), consumer(anyPositiveInt())),
            name: "Alice",
            email: fromRequest().body('$.email'),
            createdAt: $(consumer(anyIso8601WithOffset()), producer("2026-01-15T10:30:00Z"))
        ])
    }
}
```

Alternativa YAML (más legible, menos expresiva):

```yaml
# src/test/resources/contracts/shouldGetUser.yaml
description: should get user by id
request:
  method: GET
  url: /users/42
response:
  status: 200
  headers:
    Content-Type: application/json
  body:
    id: 42
    name: "Alice"
    email: "alice@example.com"
  matchers:
    body:
      - path: $.id
        type: by_type
      - path: $.email
        type: by_regex
        value: "[a-z]+@[a-z]+\\.[a-z]+"
```

## Base class para tests generados

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
@AutoConfigureMockMvc
public abstract class BaseContractTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserRepository userRepository;

    @BeforeEach
    void setup() {
        RestAssuredMockMvc.mockMvc(mockMvc);

        when(userRepository.save(any()))
            .thenAnswer(inv -> {
                User u = inv.getArgument(0);
                u.setId(42L);
                return u;
            });

        when(userRepository.findById(42L))
            .thenReturn(Optional.of(new User(42L, "Alice", "alice@example.com")));
    }
}
```

SCC genera `ContractVerifierTest.java` automáticamente desde los `.groovy`/`.yaml`. Si los tests pasan, el provider cumple el contrato.

## Publicación de stubs

SCC empaqueta los stubs como `<artifactId>-stubs.jar` y los publica al Maven repo:

```bash
mvn install
# genera: target/users-service-1.0.0-stubs.jar
mvn deploy
# publica al Nexus/Artifactory del cliente
```

## Setup en el consumer

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-contract-stub-runner</artifactId>
    <scope>test</scope>
</dependency>
```

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureStubRunner(
    ids = "com.cliente:users-service:+:stubs:8080",
    stubsMode = StubRunnerProperties.StubsMode.REMOTE,
    repositoryRoot = "https://nexus.cliente.com/repository/maven-snapshots"
)
class WebAppUsersClientTest {

    @Autowired
    private UsersClient client;

    @Test
    void getUserReturnsExpected() {
        User user = client.fetchUser(42);
        assertEquals("Alice", user.getName());
    }
}
```

El stub runner descarga el JAR de stubs, levanta un WireMock en el puerto 8080, y el cliente le pega como si fuera el provider real.

## Integración con WireMock standalone

Los stubs SCC son compatibles WireMock — un consumer en cualquier stack (Node, Python, .NET) puede usarlos:

```bash
java -jar wiremock-standalone.jar --port 8080 --root-dir /path/to/extracted/stubs/META-INF/com.cliente/users-service
```

## Diferencias con Pact (resumen)

| Concepto              | SCC                              | Pact                             |
| --------------------- | -------------------------------- | -------------------------------- |
| Donde vive el contrato| Provider repo                    | Consumer repo                    |
| Quien lo escribe      | Provider team (o pair con consumer)| Consumer team                  |
| Stubs                 | WireMock                         | Pact mock server (custom)        |
| Distribución          | Maven artifact                   | Pact Broker                      |
| Verificación provider | Tests generados automáticamente  | Pact verifier                    |
| `can-i-deploy`        | No (manual con Nexus versioning) | Si nativo                        |
| Multi-lenguaje        | Si (WireMock-based)              | Si (libs por lang)               |

## Cross-link

- Si el cliente combina SCC con Pact, ver `references/cdc-vs-schema-first.md` para el modelo híbrido.
- Para validación funcional adicional, combinar con `[[calidad-karate-greenfield]]`.

## Anti-patterns

- Contratos con valores hardcodeados (sin matchers `by_type`/`by_regex`) — frágiles a datos.
- Base class con DB real en lugar de mocks — lento, frágil.
- No versionar los stubs en Maven (siempre `LATEST`) — consumers se rompen sin aviso.
- Usar SCC con provider non-Spring — pierdes el beneficio principal (generación automática de tests).
