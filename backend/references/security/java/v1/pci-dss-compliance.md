<!-- keywords: pci-dss, compliance, cardholder data, pan tokenization, encryption, log sanitization, card validation, java -->
# PCI-DSS Compliance - Java

## Purpose

Self-contained reference for PCI-DSS compliance in Java. Covers cardholder data handling concepts, encryption, access control, audit logging, and implementation with Spring Boot including PAN tokenization, log sanitization, and card data validation.

## Scope of Application

- When developing systems that process, store, or transmit card data.
- When PCI-DSS level 1, 2, 3, or 4 certification is required.
- To implement security controls in financial applications.
- When designing architectures that handle PAN, CVV, or sensitive authentication data.
- When developing payment services in Java.
- To configure PCI-compliant log sanitization filters.

## Fundamental Concepts

### PCI-DSS Requirements Relevant to Development

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| 3.4 | Render PAN unreadable wherever stored | Encryption, truncation, tokenization |
| 3.5 | Protect encryption keys | KMS, HSM, rotation |
| 4.1 | Encrypt data transmission | TLS 1.2+, mTLS |
| 6.5 | Secure development | Validation, sanitization |
| 8.2 | Strong authentication | MFA, secure tokens |
| 10.2 | Audit logging | Immutable logs |

### Card Data Handling

```
┌─────────────────────────────────────────────────────────────┐
│                      CARD DATA                              │
├─────────────────────────────────────────────────────────────┤
│  PAN (Primary Account Number)                               │
│  ├── Can be stored encrypted or tokenized                  │
│  ├── Show only last 4 digits                               │
│  └── Never in logs                                          │
├─────────────────────────────────────────────────────────────┤
│  CVV/CVC                                                    │
│  ├── NEVER store after authorization                       │
│  └── Only in memory during processing                       │
├─────────────────────────────────────────────────────────────┤
│  Expiration date                                            │
│  └── Can be stored encrypted                               │
└─────────────────────────────────────────────────────────────┘
```

### Tokenized Payment Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  TOKENIZATION FLOW                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Customer enters data in secure frontend (PCI iframe)    │
│         │                                                    │
│         ▼                                                    │
│  2. Frontend sends data directly to processor               │
│         │                                                    │
│         ▼                                                    │
│  3. Processor returns card token                            │
│         │                                                    │
│         ▼                                                    │
│  4. Backend receives only the token (never the PAN)         │
│         │                                                    │
│         ▼                                                    │
│  5. Backend stores token for recurring payments             │
│         │                                                    │
│         ▼                                                    │
│  6. For charges, backend sends token to processor           │
│         │                                                    │
│         ▼                                                    │
│  7. Processor detokenizes and processes the payment         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### PAN Validation (Luhn Algorithm)

```
Algorithm steps:
1. From the rightmost digit, double every second digit
2. If the result of doubling is > 9, subtract 9
3. Sum all digits
4. If the sum is divisible by 10, the number is valid
```

### Data Protection Strategies

| Strategy | Description | Recommended Use |
|----------|-------------|-----------------|
| Encryption | Reversible transformation with key | Secure storage |
| Tokenization | Replacement with non-sensitive value | Reduce PCI scope |
| Truncation | Show only part of the data | Display |
| Hashing | Irreversible transformation | Verification |

## Main Content

### Dependencies

```groovy
// build.gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'software.amazon.awssdk:kms:2.x.x'
    implementation 'jakarta.validation:jakarta.validation-api:3.0.0'
}

### Implementation

```java
// PAN tokenization service
@Service
public class CardTokenizationService {
    
    private final KmsClient kmsClient;
    private final TokenRepository tokenRepository;
    private final String kmsKeyId;
    
    public CardTokenizationService(
        KmsClient kmsClient,
        TokenRepository tokenRepository,
        @Value("${kms.key-id}") String kmsKeyId
    ) {
        this.kmsClient = kmsClient;
        this.tokenRepository = tokenRepository;
        this.kmsKeyId = kmsKeyId;
    }
    
    public String tokenize(String pan) {
        validatePan(pan);
        
        // Generate unique token
        String token = generateSecureToken();
        
        // Encrypt PAN with KMS
        String encryptedPan = encryptWithKms(pan);
        
        // Store token -> encrypted PAN mapping
        tokenRepository.save(new TokenMapping(token, encryptedPan));
        
        return token;
    }
    
    public String detokenize(String token) {
        TokenMapping mapping = tokenRepository.findByToken(token)
            .orElseThrow(() -> new TokenNotFoundException(token));
        
        return decryptWithKms(mapping.getEncryptedPan());
    }
    
    private String encryptWithKms(String data) {
        EncryptRequest request = EncryptRequest.builder()
            .keyId(kmsKeyId)
            .plaintext(SdkBytes.fromUtf8String(data))
            .encryptionContext(Map.of("purpose", "pan-encryption"))
            .build();
        
        return Base64.getEncoder().encodeToString(
            kmsClient.encrypt(request).ciphertextBlob().asByteArray()
        );
    }
    
    private void validatePan(String pan) {
        if (!LuhnValidator.isValid(pan)) {
            throw new InvalidPanException("Invalid PAN");
        }
    }
    
    private String generateSecureToken() {
        return "tok_" + UUID.randomUUID().toString().replace("-", "");
    }
}
```

```java
// Log sanitization filter
@Component
public class PciLogSanitizer implements LogFilter {
    
    private static final Pattern PAN_PATTERN = 
        Pattern.compile("\\b(?:\\d{4}[- ]?){3}\\d{4}\\b");
    private static final Pattern CVV_PATTERN = 
        Pattern.compile("\\b\\d{3,4}\\b");
    
    @Override
    public String sanitize(String message) {
        String sanitized = PAN_PATTERN.matcher(message)
            .replaceAll("[PAN-REDACTED]");
        
        // Only sanitize CVV in specific contexts
        if (message.contains("cvv") || message.contains("cvc")) {
            sanitized = CVV_PATTERN.matcher(sanitized)
                .replaceAll("[CVV-REDACTED]");
        }
        
        return sanitized;
    }
}
```

```java
// DTO with PCI validation
public record CardDataDto(
    @NotNull
    @Pattern(regexp = "^[0-9]{13,19}$", message = "Invalid PAN")
    String pan,
    
    @NotNull
    @Pattern(regexp = "^(0[1-9]|1[0-2])/([0-9]{2})$")
    String expiryDate,
    
    @NotNull
    @Size(min = 3, max = 4)
    @JsonIgnore // Never serialize
    String cvv
) {
    public String getMaskedPan() {
        if (pan == null || pan.length() < 4) return "****";
        return "*".repeat(pan.length() - 4) + pan.substring(pan.length() - 4);
    }
}
```

```java
// Luhn validator
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

### Configuration

```yaml
# application.yml
kms:
  key-id: ${KMS_KEY_ID}

logging:
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
  # Configure sanitization filter
```

## Important Rules

- NEVER store CVV/CVC after authorization.
- NEVER log full PAN, even in debug mode.
- Use AES-256 or higher encryption for data at rest.
- Implement TLS 1.2+ for data in transit.
- Rotate encryption keys at least annually.
- Truncate PAN to first 6 and last 4 digits for display.
- Implement tokenization to reduce PCI scope.
- Maintain an inventory of all systems that handle card data.
- CVV must never be persisted or serialized.
- Use `@JsonIgnore` on sensitive DTO fields.
- Implement Luhn validation before processing PANs.

## Example

```java
// Tokenization service usage
@RestController
@RequestMapping("/api/payments")
public class PaymentController {
    
    private final CardTokenizationService tokenizationService;
    
    @PostMapping("/tokenize")
    public ResponseEntity<TokenResponse> tokenize(@Valid @RequestBody CardDataDto card) {
        String token = tokenizationService.tokenize(card.pan());
        return ResponseEntity.ok(new TokenResponse(token, card.getMaskedPan()));
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
