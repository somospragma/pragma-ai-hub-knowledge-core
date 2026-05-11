---
id: backend-skill-java-webflux-seguridad
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Seguridad — Java WebFlux (Reactivo)

## Propósito

Documentar las prácticas de seguridad obligatorias para microservicios reactivos: Spring Security Reactive con `SecurityWebFilterChain`, mTLS con WebClient, uso de Secrets Manager, cumplimiento PCI-DSS, audit logging reactivo para SOC2, y enmascaramiento de datos sensibles.

---

## 1. Spring Security Reactive (SecurityWebFilterChain)

### Dependencias

```groovy
implementation 'org.springframework.boot:spring-boot-starter-security'
```

### Configuración de Seguridad Reactiva

En WebFlux se usa `SecurityWebFilterChain` en lugar de `SecurityFilterChain`:

```java
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Bean
    public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
        return http
            .csrf(ServerHttpSecurity.CsrfSpec::disable)
            .authorizeExchange(exchanges -> exchanges
                .pathMatchers("/actuator/health/**").permitAll()
                .pathMatchers("/api/v1/public/**").permitAll()
                .pathMatchers("/api/v1/**").authenticated()
                .anyExchange().denyAll()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtDecoder(reactiveJwtDecoder()))
            )
            .build();
    }

    @Bean
    public ReactiveJwtDecoder reactiveJwtDecoder() {
        return ReactiveJwtDecoders.fromIssuerLocation("https://auth.pragma.com/realms/services");
    }
}
```

### Acceso al Usuario Autenticado (Reactivo)

En WebFlux NO existe `SecurityContextHolder.getContext()`. Se usa `ReactiveSecurityContextHolder`:

```java
@Component
public class SecurityUtils {

    public Mono<String> getCurrentUserId() {
        return ReactiveSecurityContextHolder.getContext()
            .map(SecurityContext::getAuthentication)
            .map(Authentication::getName);
    }

    public Mono<Set<String>> getCurrentUserRoles() {
        return ReactiveSecurityContextHolder.getContext()
            .map(SecurityContext::getAuthentication)
            .map(auth -> auth.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toSet()));
    }
}
```

### WebFilter de Seguridad Personalizado

En WebFlux se usa `WebFilter` en lugar de `OncePerRequestFilter`:

```java
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class ApiKeyWebFilter implements WebFilter {

    @Value("${security.api-key}")
    private String expectedApiKey;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String apiKey = exchange.getRequest().getHeaders().getFirst("X-API-Key");
        if (apiKey == null || !apiKey.equals(expectedApiKey)) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        return chain.filter(exchange);
    }
}
```

---

## 2. mTLS entre Servicios (WebClient)

### Configuración del SSLContext para WebClient

```java
@Configuration
public class MtlsConfig {
    @Value("${mtls.keystore.path}") private String keystorePath;
    @Value("${mtls.keystore.password}") private String keystorePassword;
    @Value("${mtls.truststore.path}") private String truststorePath;

    @Bean
    public WebClient mtlsWebClient() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        keyStore.load(new FileInputStream(keystorePath), keystorePassword.toCharArray());

        KeyStore trustStore = KeyStore.getInstance("PKCS12");
        trustStore.load(new FileInputStream(truststorePath), keystorePassword.toCharArray());

        KeyManagerFactory kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
        kmf.init(keyStore, keystorePassword.toCharArray());

        TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init(trustStore);

        SslContext sslContext = SslContextBuilder.forClient()
            .keyManager(kmf)
            .trustManager(tmf)
            .build();

        HttpClient httpClient = HttpClient.create()
            .secure(spec -> spec.sslContext(sslContext));

        return WebClient.builder()
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }
}
```

### Configuración (application.yml)

```yaml
mtls:
  keystore:
    path: ${KEYSTORE_PATH:/certs/keystore.p12}
    password: ${KEYSTORE_PASSWORD}
  truststore:
    path: ${TRUSTSTORE_PATH:/certs/truststore.p12}
  allowed-clients:
    - service-a
    - service-b
```

---

## 3. AWS Secrets Manager (Reactivo)

### Dependencias

```groovy
implementation 'software.amazon.awssdk:secretsmanager'
implementation 'software.amazon.awssdk:netty-nio-client'
implementation 'com.github.ben-manes.caffeine:caffeine'
```

### Servicio de Secretos Reactivo con Caché

```java
@Service
@RequiredArgsConstructor
public class ReactiveSecretsService {
    private final SecretsManagerAsyncClient secretsClient;
    private final ObjectMapper objectMapper;
    private final Cache<String, String> cache = Caffeine.newBuilder()
        .expireAfterWrite(Duration.ofMinutes(60))
        .maximumSize(100)
        .build();

    public Mono<String> getSecret(String secretId) {
        String cached = cache.getIfPresent(secretId);
        if (cached != null) {
            return Mono.just(cached);
        }
        return Mono.fromFuture(() -> secretsClient.getSecretValue(
                GetSecretValueRequest.builder().secretId(secretId).build()))
            .map(GetSecretValueResponse::secretString)
            .doOnNext(value -> cache.put(secretId, value));
    }

    public <T> Mono<T> getSecretAs(String secretId, Class<T> type) {
        return getSecret(secretId)
            .flatMap(json -> {
                try {
                    return Mono.just(objectMapper.readValue(json, type));
                } catch (JsonProcessingException e) {
                    return Mono.error(new SecretParseException("Error parseando secreto", e));
                }
            });
    }
}
```

### Configuración del Cliente Async

```java
@Configuration
public class SecretsManagerConfig {
    @Bean
    public SecretsManagerAsyncClient secretsManagerAsyncClient() {
        return SecretsManagerAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }
}
```

---

## 4. AWS Parameter Store (Reactivo)

```java
@Service
public class ReactiveParameterService {
    private final SsmAsyncClient ssmAsyncClient;
    private final Cache<String, String> cache;
    private final String environment;

    public ReactiveParameterService(SsmAsyncClient ssmAsyncClient) {
        this.ssmAsyncClient = ssmAsyncClient;
        this.cache = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofMinutes(5))
            .maximumSize(500)
            .build();
        this.environment = System.getenv("ENVIRONMENT");
    }

    public Mono<String> getParameter(String name) {
        String fullPath = String.format("/myapp/%s/%s", environment, name);
        String cached = cache.getIfPresent(fullPath);
        if (cached != null) {
            return Mono.just(cached);
        }
        return Mono.fromFuture(() -> ssmAsyncClient.getParameter(
                GetParameterRequest.builder()
                    .name(fullPath)
                    .withDecryption(true)
                    .build()))
            .map(response -> response.parameter().value())
            .doOnNext(value -> cache.put(fullPath, value));
    }
}
```

---

## 5. Cumplimiento PCI-DSS (Reactivo)

### Tokenización de PAN

```java
@Service
@RequiredArgsConstructor
public class ReactiveCardTokenizationService {
    private final KmsAsyncClient kmsAsyncClient;
    private final ITokenRepository tokenRepository;
    @Value("${kms.key-id}") private String kmsKeyId;

    public Mono<String> tokenize(String pan) {
        return Mono.fromCallable(() -> validatePan(pan))
            .then(encryptWithKms(pan))
            .flatMap(encryptedPan -> {
                String token = "tok_" + UUID.randomUUID().toString().replace("-", "");
                return tokenRepository.save(new TokenMapping(token, encryptedPan))
                    .thenReturn(token);
            });
    }

    private Mono<String> encryptWithKms(String data) {
        EncryptRequest request = EncryptRequest.builder()
            .keyId(kmsKeyId)
            .plaintext(SdkBytes.fromUtf8String(data))
            .encryptionContext(Map.of("purpose", "pan-encryption"))
            .build();
        return Mono.fromFuture(() -> kmsAsyncClient.encrypt(request))
            .map(response -> Base64.getEncoder().encodeToString(
                response.ciphertextBlob().asByteArray()));
    }

    private Void validatePan(String pan) {
        if (!LuhnValidator.isValid(pan)) {
            throw new InvalidPanException("PAN inválido");
        }
        return null;
    }
}
```

### Validador Luhn

```java
public class LuhnValidator {
    public static boolean isValid(String pan) {
        if (pan == null || pan.isEmpty()) return false;
        String digits = pan.replaceAll("\\D", "");
        if (digits.length() < 13 || digits.length() > 19) return false;

        int sum = 0;
        boolean alternate = false;
        for (int i = digits.length() - 1; i >= 0; i--) {
            int digit = Character.getNumericValue(digits.charAt(i));
            if (alternate) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            sum += digit;
            alternate = !alternate;
        }
        return sum % 10 == 0;
    }
}
```

### Reglas PCI-DSS

- **NUNCA** almacenar CVV/CVC después de la autorización.
- **NUNCA** loguear PAN completo, ni en modo debug.
- Usar AES-256 o superior para datos en reposo.
- Implementar TLS 1.2+ para datos en tránsito.
- Rotar claves de encriptación al menos anualmente.
- Truncar PAN a primeros 6 y últimos 4 dígitos para display.

---

## 6. Audit Logging Reactivo para SOC2

### Modelo de Evento de Auditoría

```java
public record AuditEvent(
    String eventId,
    Instant timestamp,
    String eventType,
    String category,
    Actor actor,
    Resource resource,
    Action action,
    String correlationId
) {
    public record Actor(String userId, String userType, String ipAddress) {}
    public record Resource(String type, String id, String name) {}
    public record Action(String type, String status, String details) {}
}
```

### Servicio de Auditoría Reactivo

```java
@Service
@RequiredArgsConstructor
public class ReactiveAuditService {
    private final IAuditEventGateway auditGateway;
    private final ObjectMapper objectMapper;

    public Mono<Void> logEvent(AuditEvent event) {
        return auditGateway.save(event)
            .doOnSuccess(v -> log.info("audit_event: {}",
                serializeQuietly(event)))
            .doOnError(e -> log.error("Error registrando evento de auditoría", e))
            .onErrorResume(e -> Mono.empty())
            .then();
    }

    public Mono<Void> logWithContext(String eventType, String actionType, String resourceType) {
        return ReactiveSecurityContextHolder.getContext()
            .map(SecurityContext::getAuthentication)
            .flatMap(auth -> {
                AuditEvent event = new AuditEvent(
                    UUID.randomUUID().toString(),
                    Instant.now(),
                    eventType,
                    "DATA_ACCESS",
                    new AuditEvent.Actor(auth.getName(), "USER", null),
                    new AuditEvent.Resource(resourceType, null, null),
                    new AuditEvent.Action(actionType, "SUCCESS", null),
                    null
                );
                return logEvent(event);
            });
    }
}
```

---

## 7. Enmascaramiento de Datos Sensibles

### Estrategias de Enmascaramiento

```java
@Service
public class DataMaskingService {
    private static final Map<DataType, MaskingStrategy> STRATEGIES = Map.of(
        DataType.PAN, value -> "*".repeat(value.length() - 4) + value.substring(value.length() - 4),
        DataType.EMAIL, value -> {
            int at = value.indexOf('@');
            if (at <= 1) return "***@" + value.substring(at + 1);
            return value.charAt(0) + "***" + value.charAt(at - 1) + value.substring(at);
        },
        DataType.PHONE, value -> "***-***-" + value.substring(value.length() - 4)
    );

    public String mask(String value, DataType type) {
        if (value == null || value.isBlank()) return value;
        return STRATEGIES.getOrDefault(type, v -> "****").mask(value);
    }
}
```

### Sanitización de Logs PCI

```java
@Component
public class PciLogSanitizer {
    private static final Pattern PAN_PATTERN =
        Pattern.compile("\\b(?:\\d{4}[- ]?){3}\\d{4}\\b");

    public String sanitize(String message) {
        return PAN_PATTERN.matcher(message).replaceAll("[PAN-REDACTED]");
    }
}
```

---

## Reglas Generales de Seguridad

- Usar `SecurityWebFilterChain` (NO `SecurityFilterChain` de MVC).
- Usar `WebFilter` (NO `OncePerRequestFilter`).
- Usar `ReactiveSecurityContextHolder` (NO `SecurityContextHolder`).
- Usar certificados con validez máxima de 1 año.
- Implementar rotación automática de certificados.
- Almacenar claves privadas en Secrets Manager o HSM.
- Siempre usar caché para reducir latencia y costos en Secrets Manager.
- Usar clientes **async** de AWS SDK para mantener el pipeline reactivo.
- Retención mínima de 7 años para logs de auditoría (SOC2).
- Nunca incluir datos sensibles (PII, PAN) en logs de auditoría.
- **NUNCA** usar `.block()` en servicios de seguridad.
