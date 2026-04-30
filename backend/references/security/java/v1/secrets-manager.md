<!-- keywords: secrets manager, aws, secret rotation, caching, credentials, spring webflux, java -->
# AWS Secrets Manager Patterns - Java

## Purpose

Self-contained reference for secrets management with AWS Secrets Manager in Java. Covers automatic rotation concepts, caching, access patterns for Lambda and containers, and implementation with AWS SDK v2, reactive patterns, and Spring WebFlux.

## Scope of Application

- When implementing centralized secrets management.
- When automatic credential rotation is required.
- To optimize secret access in Lambda and containers.
- When designing caching patterns to reduce latency and costs.
- When developing in Java with Spring WebFlux.
- When configuring dynamic database connections.

## Fundamental Concepts

### Secrets Manager Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Secrets Manager                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Secret    │  │   Secret    │  │   Secret    │         │
│  │  (DB Creds) │  │ (API Keys)  │  │   (Certs)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────────────────────────────────────────┐       │
│  │              KMS Encryption                      │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Lambda  │    │   ECS    │    │   EC2    │
    │ (Cache)  │    │ (Sidecar)│    │ (Agent)  │
    └──────────┘    └──────────┘    └──────────┘
```

### Rotation Configuration (CloudFormation)

```yaml
Resources:
  DatabaseSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: prod/database/credentials
      Description: Database credentials with automatic rotation
      GenerateSecretString:
        SecretStringTemplate: '{"username": "admin"}'
        GenerateStringKey: password
        PasswordLength: 32
        ExcludeCharacters: '"@/\'
      KmsKeyId: !Ref SecretsKmsKey

  SecretRotationSchedule:
    Type: AWS::SecretsManager::RotationSchedule
    Properties:
      SecretId: !Ref DatabaseSecret
      RotationLambdaARN: !GetAtt RotationLambda.Arn
      RotationRules:
        AutomaticallyAfterDays: 30
        ScheduleExpression: rate(30 days)
```

### Secret Retrieval Flow

```
1. Application requests secret
2. Check local cache
3. If cache valid, return cached value
4. If cache expired, fetch from Secrets Manager
5. Secrets Manager decrypts with KMS
6. Return value and update cache
7. Application uses credentials
```

## Main Content

### Dependencies

```xml
<dependencies>
    <dependency>
        <groupId>software.amazon.awssdk</groupId>
        <artifactId>secretsmanager</artifactId>
    </dependency>
    <dependency>
        <groupId>software.amazon.awssdk</groupId>
        <artifactId>netty-nio-client</artifactId>
    </dependency>
    <dependency>
        <groupId>com.github.ben-manes.caffeine</groupId>
        <artifactId>caffeine</artifactId>
    </dependency>
</dependencies>
```

### Configuration

```java
@Configuration
public class SecretsManagerConfig {
    
    @Bean
    public SecretsManagerAsyncClient secretsManagerAsyncClient() {
        return SecretsManagerAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .httpClientBuilder(NettyNioAsyncHttpClient.builder()
                .maxConcurrency(50)
                .connectionTimeout(Duration.ofSeconds(5)))
            .build();
    }
    
    @Bean
    public SecretCache secretCache(SecretsManagerAsyncClient client) {
        return SecretCache.builder()
            .client(client)
            .cacheItemTTL(Duration.ofMinutes(60))
            .maxCacheSize(100)
            .build();
    }
}
```

### Implementation

```java
@Service
public class ReactiveSecretsService {
    
    private final SecretsManagerAsyncClient client;
    private final SecretCache cache;
    private final ObjectMapper objectMapper;
    
    public Mono<String> getSecret(String secretId) {
        return Mono.fromFuture(() -> 
            cache.getSecretString(secretId)
        ).onErrorResume(e -> {
            log.warn("Cache miss for secret: {}", secretId);
            return fetchSecretAsync(secretId);
        });
    }
    
    public <T> Mono<T> getSecretAs(String secretId, Class<T> type) {
        return getSecret(secretId)
            .map(json -> parseSecret(json, type));
    }
    
    private Mono<String> fetchSecretAsync(String secretId) {
        GetSecretValueRequest request = GetSecretValueRequest.builder()
            .secretId(secretId)
            .build();
        
        return Mono.fromFuture(client.getSecretValue(request))
            .map(GetSecretValueResponse::secretString)
            .doOnNext(secret -> log.debug("Fetched secret: {}", secretId));
    }
    
    private <T> T parseSecret(String json, Class<T> type) {
        try {
            return objectMapper.readValue(json, type);
        } catch (JsonProcessingException e) {
            throw new SecretParseException("Failed to parse secret", e);
        }
    }
}
```

### Credentials Model

```java
public record DatabaseCredentials(
    String username,
    String password,
    String host,
    int port,
    String dbname
) {
    public String toJdbcUrl() {
        return String.format("jdbc:postgresql://%s:%d/%s", host, port, dbname);
    }
}

@Service
public class DatabaseConnectionService {
    
    private final ReactiveSecretsService secretsService;
    
    public Mono<ConnectionFactory> createConnectionFactory() {
        return secretsService.getSecretAs("prod/db/credentials", DatabaseCredentials.class)
            .map(creds -> ConnectionFactories.get(ConnectionFactoryOptions.builder()
                .option(DRIVER, "postgresql")
                .option(HOST, creds.host())
                .option(PORT, creds.port())
                .option(USER, creds.username())
                .option(PASSWORD, creds.password())
                .option(DATABASE, creds.dbname())
                .build()));
    }
}
```

### Automatic Rotation with Lambda

```java
public class SecretRotationHandler implements RequestHandler<SecretsManagerRotationEvent, String> {
    
    private final SecretsManagerClient client;
    private final DatabaseService databaseService;
    
    @Override
    public String handleRequest(SecretsManagerRotationEvent event, Context context) {
        String secretId = event.getSecretId();
        String step = event.getStep();
        
        return switch (step) {
            case "createSecret" -> createSecret(secretId, event.getClientRequestToken());
            case "setSecret" -> setSecret(secretId, event.getClientRequestToken());
            case "testSecret" -> testSecret(secretId, event.getClientRequestToken());
            case "finishSecret" -> finishSecret(secretId, event.getClientRequestToken());
            default -> throw new IllegalArgumentException("Unknown step: " + step);
        };
    }
    
    private String createSecret(String secretId, String token) {
        GetSecretValueResponse current = client.getSecretValue(
            GetSecretValueRequest.builder()
                .secretId(secretId)
                .versionStage("AWSCURRENT")
                .build());
        
        String newPassword = generateSecurePassword();
        
        DatabaseCredentials currentCreds = parseCredentials(current.secretString());
        DatabaseCredentials newCreds = new DatabaseCredentials(
            currentCreds.username(),
            newPassword,
            currentCreds.host(),
            currentCreds.port(),
            currentCreds.dbname()
        );
        
        client.putSecretValue(PutSecretValueRequest.builder()
            .secretId(secretId)
            .clientRequestToken(token)
            .secretString(toJson(newCreds))
            .versionStages(List.of("AWSPENDING"))
            .build());
        
        return "Created pending secret";
    }
}
```

## Important Rules

- Always use caching to reduce latency and costs.
- Implement automatic rotation for database credentials.
- Use KMS customer-managed keys for critical secrets.
- Do not hardcode secret ARNs; use environment variables.
- Implement retry with backoff for transient errors.
- Monitor secret access metrics in CloudWatch.
- Use VPC endpoints for private access to Secrets Manager.
- Use `Mono.fromFuture` for asynchronous operations.
- Verify that the secret exists before using it.

## Example

```java
@RestController
@RequiredArgsConstructor
public class UserController {
    
    private final ReactiveSecretsService secretsService;
    private final R2dbcEntityTemplate template;
    
    @GetMapping("/users/{id}")
    public Mono<User> getUser(@PathVariable String id) {
        return secretsService.getSecretAs("prod/db/credentials", DatabaseCredentials.class)
            .flatMap(creds -> {
                // Use credentials for query
                return template.selectOne(
                    Query.query(Criteria.where("id").is(id)),
                    User.class
                );
            });
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
