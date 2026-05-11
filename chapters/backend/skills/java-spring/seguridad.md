---
id: backend-skill-java-spring-seguridad
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Seguridad — Java Spring

## Propósito

Documentar las prácticas de seguridad obligatorias: mTLS entre servicios, uso de Secrets Manager y Parameter Store, cumplimiento PCI-DSS, audit logging para SOC2, y enmascaramiento de datos sensibles en logs.

---

## 1. mTLS entre Servicios

### Configuración del SSLContext

```java
@Configuration
public class MtlsConfig {
    @Value("${mtls.keystore.path}") private String keystorePath;
    @Value("${mtls.keystore.password}") private String keystorePassword;
    @Value("${mtls.truststore.path}") private String truststorePath;

    @Bean
    public SSLContext sslContext() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        keyStore.load(new FileInputStream(keystorePath), keystorePassword.toCharArray());

        KeyStore trustStore = KeyStore.getInstance("PKCS12");
        trustStore.load(new FileInputStream(truststorePath), keystorePassword.toCharArray());

        return SSLContextBuilder.create()
            .loadKeyMaterial(keyStore, keystorePassword.toCharArray())
            .loadTrustMaterial(trustStore, null)
            .build();
    }

    @Bean
    public RestClient restClient(SSLContext sslContext) {
        HttpClient httpClient = HttpClient.create()
            .secure(spec -> spec.sslContext(sslContext));
        return RestClient.builder()
            .requestFactory(new ReactorClientHttpRequestFactory(httpClient))
            .build();
    }
}
```

### Validación de Certificado del Cliente

```java
@Component
public class ClientCertificateValidator {
    private final Set<String> allowedCNs;

    public ClientCertificateValidator(@Value("${mtls.allowed-clients}") List<String> allowed) {
        this.allowedCNs = new HashSet<>(allowed);
    }

    public void validate(X509Certificate cert) {
        String cn = extractCN(cert.getSubjectX500Principal().getName());
        if (!allowedCNs.contains(cn)) {
            throw new SecurityException("Cliente no autorizado: " + cn);
        }
        if (cert.getNotAfter().before(new Date())) {
            throw new SecurityException("Certificado expirado");
        }
    }

    private String extractCN(String dn) {
        return Arrays.stream(dn.split(","))
            .filter(s -> s.trim().startsWith("CN="))
            .map(s -> s.trim().substring(3))
            .findFirst()
            .orElseThrow(() -> new SecurityException("CN no encontrado"));
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

## 2. AWS Secrets Manager

### Dependencias

```groovy
implementation 'software.amazon.awssdk:secretsmanager'
implementation 'com.github.ben-manes.caffeine:caffeine'
```

### Servicio de Secretos con Caché

```java
@Service
@RequiredArgsConstructor
public class SecretsService {
    private final SecretsManagerClient client;
    private final ObjectMapper objectMapper;
    private final Cache<String, String> cache = Caffeine.newBuilder()
        .expireAfterWrite(Duration.ofMinutes(60))
        .maximumSize(100)
        .build();

    public String getSecret(String secretId) {
        return cache.get(secretId, this::fetchSecret);
    }

    public <T> T getSecretAs(String secretId, Class<T> type) {
        String json = getSecret(secretId);
        try {
            return objectMapper.readValue(json, type);
        } catch (JsonProcessingException e) {
            throw new SecretParseException("Error parseando secreto", e);
        }
    }

    private String fetchSecret(String secretId) {
        GetSecretValueResponse response = client.getSecretValue(
            GetSecretValueRequest.builder().secretId(secretId).build());
        return response.secretString();
    }
}
```

### Modelo de Credenciales

```java
public record DatabaseCredentials(
    String username, String password, String host, int port, String dbname
) {
    public String toJdbcUrl() {
        return String.format("jdbc:postgresql://%s:%d/%s", host, port, dbname);
    }
}
```

---

## 3. AWS Parameter Store

### Servicio de Parámetros

```java
@Service
public class ParameterService {
    private final SsmClient ssmClient;
    private final Cache<String, String> cache;
    private final String environment;

    public ParameterService(SsmClient ssmClient) {
        this.ssmClient = ssmClient;
        this.cache = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofMinutes(5))
            .maximumSize(500)
            .build();
        this.environment = System.getenv("ENVIRONMENT");
    }

    public String getParameter(String name) {
        String fullPath = String.format("/myapp/%s/%s", environment, name);
        return cache.get(fullPath, this::fetchParameter);
    }

    private String fetchParameter(String path) {
        GetParameterResponse response = ssmClient.getParameter(
            GetParameterRequest.builder()
                .name(path)
                .withDecryption(true)
                .build());
        return response.parameter().value();
    }
}
```

---

## 4. Cumplimiento PCI-DSS

### Tokenización de PAN

```java
@Service
@RequiredArgsConstructor
public class CardTokenizationService {
    private final KmsClient kmsClient;
    private final TokenRepository tokenRepository;
    @Value("${kms.key-id}") private String kmsKeyId;

    public String tokenize(String pan) {
        validatePan(pan);
        String token = "tok_" + UUID.randomUUID().toString().replace("-", "");
        String encryptedPan = encryptWithKms(pan);
        tokenRepository.save(new TokenMapping(token, encryptedPan));
        return token;
    }

    private String encryptWithKms(String data) {
        EncryptRequest request = EncryptRequest.builder()
            .keyId(kmsKeyId)
            .plaintext(SdkBytes.fromUtf8String(data))
            .encryptionContext(Map.of("purpose", "pan-encryption"))
            .build();
        return Base64.getEncoder().encodeToString(
            kmsClient.encrypt(request).ciphertextBlob().asByteArray());
    }

    private void validatePan(String pan) {
        if (!LuhnValidator.isValid(pan)) {
            throw new InvalidPanException("PAN inválido");
        }
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

### Reglas PCI-DSS

- **NUNCA** almacenar CVV/CVC después de la autorización.
- **NUNCA** loguear PAN completo, ni en modo debug.
- Usar AES-256 o superior para datos en reposo.
- Implementar TLS 1.2+ para datos en tránsito.
- Rotar claves de encriptación al menos anualmente.
- Truncar PAN a primeros 6 y últimos 4 dígitos para display.

---

## 5. Audit Logging para SOC2

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

### Servicio de Auditoría

```java
@Service
@RequiredArgsConstructor
public class AuditService {
    private final AuditEventRepository repository;
    private final ObjectMapper objectMapper;

    @Async
    public void logEvent(AuditEvent event) {
        try {
            repository.save(event);
            log.info("audit_event: {}", objectMapper.writeValueAsString(event));
        } catch (Exception e) {
            log.error("Error registrando evento de auditoría", e);
        }
    }
}
```

### Aspecto para Auditoría Automática

```java
@Aspect
@Component
@RequiredArgsConstructor
public class AuditAspect {
    private final AuditService auditService;

    @Around("@annotation(auditable)")
    public Object auditMethod(ProceedingJoinPoint joinPoint, Auditable auditable) throws Throwable {
        try {
            Object result = joinPoint.proceed();
            auditService.logEvent(buildEvent(auditable, "SUCCESS", null));
            return result;
        } catch (Exception e) {
            auditService.logEvent(buildEvent(auditable, "FAILURE", e.getMessage()));
            throw e;
        }
    }
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Auditable {
    String eventType();
    String actionType();
    String resourceType();
}
```

### Uso

```java
@Auditable(eventType = "DATA_ACCESS", actionType = "READ", resourceType = "CUSTOMER")
public Customer getCustomer(String customerId) {
    return customerRepository.findById(customerId);
}
```

---

## 6. Enmascaramiento de Datos Sensibles

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

### Anotación para Campos Enmascarables

```java
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Masked {
    DataType type();
    boolean inLogs() default true;
    boolean inResponse() default false;
}

public class CustomerDto {
    private String id;
    private String name;
    @Masked(type = DataType.EMAIL, inResponse = true) private String email;
    @Masked(type = DataType.PHONE, inResponse = true) private String phone;
    @Masked(type = DataType.PAN, inLogs = true, inResponse = true) private String cardNumber;
}
```

---

## Reglas Generales de Seguridad

- Usar certificados con validez máxima de 1 año.
- Implementar rotación automática de certificados.
- Almacenar claves privadas en Secrets Manager o HSM.
- Siempre usar caché para reducir latencia y costos en Secrets Manager.
- Usar SecureString para valores sensibles en Parameter Store.
- Retención mínima de 7 años para logs de auditoría (SOC2).
- Nunca incluir datos sensibles (PII, PAN) en logs de auditoría.
- Usar `@Async` para no bloquear operaciones principales con auditoría.
- Implementar retry queue para eventos de auditoría fallidos.
