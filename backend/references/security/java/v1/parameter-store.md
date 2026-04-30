<!-- keywords: parameter store, aws ssm, configuration management, encryption, caching, dynamic config, spring cloud aws, java -->
# AWS Parameter Store Patterns - Java

## Purpose

Self-contained reference for configuration management with AWS Systems Manager Parameter Store in Java. Covers parameter hierarchy concepts, encryption, caching strategies, dynamic update patterns, and implementation with AWS SDK v2, reactive patterns, and Spring Cloud AWS.

## Scope of Application

- When implementing centralized configuration management.
- When hierarchical configuration per environment is required.
- To implement feature flags or dynamic configuration.
- When designing caching patterns for parameters.
- When developing in Java with Spring WebFlux.
- When integrating with Spring Cloud AWS.

## Fundamental Concepts

### Parameter Store vs Secrets Manager

| Feature | Parameter Store | Secrets Manager |
|---------|-----------------|-----------------|
| Cost | Free (Standard) | $0.40/secret/month |
| Automatic rotation | No | Yes |
| Maximum size | 8KB (Advanced) | 64KB |
| Versioning | Yes | Yes |
| Encryption | Optional (KMS) | Always (KMS) |
| Use case | Configuration | Credentials |

### Parameter Hierarchy

```
/myapp/
├── common/
│   ├── log-level          → INFO
│   ├── feature-flags      → {"newUI": true}
│   └── api-timeout        → 30
├── dev/
│   ├── database/
│   │   ├── host           → dev-db.example.com
│   │   └── port           → 5432
│   └── cache/
│       └── ttl            → 300
├── staging/
│   ├── database/
│   │   ├── host           → staging-db.example.com
│   │   └── port           → 5432
│   └── cache/
│       └── ttl            → 600
└── prod/
    ├── database/
    │   ├── host           → prod-db.example.com (SecureString)
    │   └── port           → 5432
    └── cache/
        └── ttl            → 3600
```

### Parameter Configuration (CloudFormation)

```yaml
Resources:
  LogLevelParameter:
    Type: AWS::SSM::Parameter
    Properties:
      Name: /myapp/prod/log-level
      Type: String
      Value: INFO
      Description: Application log level
      Tags:
        Environment: prod
        Application: myapp

  DatabaseHostParameter:
    Type: AWS::SSM::Parameter
    Properties:
      Name: /myapp/prod/database/host
      Type: SecureString
      Value: !Sub '{{resolve:secretsmanager:${DatabaseSecret}:SecretString:host}}'
      KeyId: !Ref ParameterKmsKey
      Description: Database host (encrypted)

  FeatureFlagsParameter:
    Type: AWS::SSM::Parameter
    Properties:
      Name: /myapp/prod/feature-flags
      Type: String
      Value: '{"newUI": true, "betaFeatures": false}'
      Description: Feature flags configuration
```

### Dynamic Configuration Flow

```
1. Application starts and loads configuration
2. Parameters are cached locally
3. Every 5 minutes, configuration refresh
4. If parameter changes, application uses new value
5. Feature flags are evaluated in real time
```

## Main Content

### Dependencies

```xml
<dependencies>
    <dependency>
        <groupId>software.amazon.awssdk</groupId>
        <artifactId>ssm</artifactId>
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
public class ParameterStoreConfig {
    
    @Bean
    public SsmAsyncClient ssmAsyncClient() {
        return SsmAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .httpClientBuilder(NettyNioAsyncHttpClient.builder()
                .maxConcurrency(50)
                .connectionTimeout(Duration.ofSeconds(5)))
            .build();
    }
}
```

### Implementation

```java
@Service
@Slf4j
public class ReactiveParameterService {
    
    private final SsmAsyncClient ssmClient;
    private final Cache<String, CachedParameter> cache;
    private final String environment;
    
    public ReactiveParameterService(SsmAsyncClient ssmClient) {
        this.ssmClient = ssmClient;
        this.cache = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofMinutes(5))
            .maximumSize(500)
            .build();
        this.environment = System.getenv("ENVIRONMENT");
    }
    
    public Mono<String> getParameter(String name) {
        String fullPath = buildPath(name);
        
        CachedParameter cached = cache.getIfPresent(fullPath);
        if (cached != null && !cached.isExpired()) {
            return Mono.just(cached.getValue());
        }
        
        return fetchParameter(fullPath)
            .doOnNext(value -> cache.put(fullPath, new CachedParameter(value)));
    }
    
    public <T> Mono<T> getParameterAs(String name, Class<T> type) {
        return getParameter(name)
            .map(value -> convertValue(value, type));
    }
    
    public Flux<Parameter> getParametersByPath(String path) {
        String fullPath = buildPath(path);
        
        return Mono.fromFuture(() -> ssmClient.getParametersByPath(
                GetParametersByPathRequest.builder()
                    .path(fullPath)
                    .recursive(true)
                    .withDecryption(true)
                    .build()))
            .flatMapMany(response -> Flux.fromIterable(response.parameters()));
    }
    
    private Mono<String> fetchParameter(String path) {
        return Mono.fromFuture(() -> ssmClient.getParameter(
                GetParameterRequest.builder()
                    .name(path)
                    .withDecryption(true)
                    .build()))
            .map(response -> response.parameter().value())
            .doOnError(e -> log.error("Failed to fetch parameter: {}", path, e));
    }
    
    private String buildPath(String name) {
        if (name.startsWith("/")) {
            return name;
        }
        return String.format("/myapp/%s/%s", environment, name);
    }
}
```

### Dynamic Configuration with Refresh

```java
@Component
public class DynamicConfiguration {
    
    private final ReactiveParameterService parameterService;
    private final AtomicReference<AppConfig> currentConfig = new AtomicReference<>();
    
    @PostConstruct
    public void init() {
        refreshConfig().block();
        scheduleRefresh();
    }
    
    public Mono<Void> refreshConfig() {
        return parameterService.getParametersByPath("/config")
            .collectMap(
                p -> extractKey(p.name()),
                Parameter::value
            )
            .map(this::buildConfig)
            .doOnNext(currentConfig::set)
            .then();
    }
    
    private void scheduleRefresh() {
        Flux.interval(Duration.ofMinutes(5))
            .flatMap(tick -> refreshConfig())
            .subscribe();
    }
    
    public AppConfig getConfig() {
        return currentConfig.get();
    }
    
    private AppConfig buildConfig(Map<String, String> params) {
        return AppConfig.builder()
            .logLevel(params.getOrDefault("log-level", "INFO"))
            .apiTimeout(Integer.parseInt(params.getOrDefault("api-timeout", "30")))
            .featureFlags(parseFeatureFlags(params.get("feature-flags")))
            .build();
    }
}
```

### Spring Cloud AWS Integration

```java
@Configuration
@EnableConfigurationProperties
public class SpringCloudParameterConfig {
    
    // application.yml
    // spring:
    //   cloud:
    //     aws:
    //       parameterstore:
    //         enabled: true
    //         prefix: /myapp
    //         profile-separator: /
    
    @ConfigurationProperties(prefix = "app")
    public record AppProperties(
        String logLevel,
        int apiTimeout,
        DatabaseProperties database,
        CacheProperties cache
    ) {}
    
    public record DatabaseProperties(String host, int port) {}
    public record CacheProperties(int ttl) {}
}
```

## Important Rules

- Use parameter hierarchies for logical organization.
- Implement caching to reduce latency and costs (Caffeine for local caching).
- Use SecureString for sensitive values.
- Do not store complete credentials; use Secrets Manager.
- Implement periodic refresh for dynamic configuration.
- Use tags for organization and access control.
- Limit IAM permissions by parameter path.
- Use `withDecryption(true)` for SecureString.
- Organize parameters by environment using hierarchies.

## Example

```java
@RestController
@RequiredArgsConstructor
public class ConfigController {
    
    private final DynamicConfiguration config;
    
    @GetMapping("/config")
    public AppConfig getConfig() {
        return config.getConfig();
    }
    
    @GetMapping("/features/{feature}")
    public boolean isFeatureEnabled(@PathVariable String feature) {
        return config.getConfig().featureFlags().getOrDefault(feature, false);
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
