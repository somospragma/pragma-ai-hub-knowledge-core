<!-- keywords: data masking, tokenization, pii, pci, sensitive data, jackson serializer, annotations, java -->
# Data Masking and Tokenization - Java

## Purpose

Self-contained reference for PII/PCI data masking and tokenization in Java. Covers fundamental concepts, implementation patterns with configurable strategies, annotations, and Jackson serializers for automatic sensitive data protection.

## Scope of Application

- When implementing logging that may contain sensitive data.
- When partially hidden data needs to be displayed to users.
- To comply with GDPR, PCI-DSS, or privacy regulations.
- When designing APIs that return sensitive data.
- When developing Java services that handle sensitive data.
- When automatic masking in DTOs is needed.
- To configure secure serialization with Jackson.

## Fundamental Concepts

### Masking Types

| Type | Description | Example |
|------|-------------|---------|
| Truncation | Show only part of the data | `****1234` |
| Substitution | Replace with fixed characters | `XXX-XX-1234` |
| Shuffling | Rearrange characters | `john@email.com` → `nhoj@liame.moc` |
| Nulling | Replace with null/empty | `null` |
| Hashing | Irreversible hash | `a1b2c3d4...` |
| Tokenization | Replace with reversible token | `tok_abc123` |

### Data Requiring Masking

```
┌─────────────────────────────────────────────────────────────┐
│                    SENSITIVE DATA                            │
├─────────────────────────────────────────────────────────────┤
│  PCI (Payment Card Industry)                                │
│  ├── PAN: Show only last 4 digits                          │
│  ├── CVV: Never show or store                              │
│  └── Exp date: Can be shown in full                        │
├─────────────────────────────────────────────────────────────┤
│  PII (Personally Identifiable Information)                  │
│  ├── Email: user***@domain.com                             │
│  ├── Phone: ***-***-1234                                   │
│  ├── SSN/ID: ***-**-1234                                   │
│  └── Address: Street ***, City                             │
├─────────────────────────────────────────────────────────────┤
│  PHI (Protected Health Information)                         │
│  ├── Diagnoses: Always mask                                │
│  └── Medical record numbers: Tokenize                      │
└─────────────────────────────────────────────────────────────┘
```

### API Masking Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    MASKING FLOW                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Request arrives with sensitive data                     │
│         │                                                    │
│         ▼                                                    │
│  2. Data is processed internally without masking            │
│         │                                                    │
│         ▼                                                    │
│  3. Before logging: apply masking for logs                  │
│         │                                                    │
│         ▼                                                    │
│  4. Before response: apply masking based on role            │
│         │                                                    │
│         ▼                                                    │
│  5. Client receives data masked according to access level   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Strategies by Data Type

| Data | Strategy | Result |
|------|----------|--------|
| PAN | Truncation | `************1234` |
| Email | Partial | `j***n@domain.com` |
| Phone | Truncation | `***-***-5678` |
| SSN | Truncation | `***-**-1234` |
| Name | Optional | Context-dependent |

## Main Content

### Dependencies

```groovy
dependencies {
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.0'
}
```

### Implementation

```java
// Masking service
@Service
public class DataMaskingService {
    
    private static final Map<DataType, MaskingStrategy> STRATEGIES = Map.of(
        DataType.PAN, new PanMaskingStrategy(),
        DataType.EMAIL, new EmailMaskingStrategy(),
        DataType.PHONE, new PhoneMaskingStrategy(),
        DataType.SSN, new SsnMaskingStrategy()
    );
    
    public String mask(String value, DataType type) {
        if (value == null || value.isBlank()) {
            return value;
        }
        return STRATEGIES.getOrDefault(type, new DefaultMaskingStrategy())
            .mask(value);
    }
    
    public <T> T maskObject(T object) {
        for (Field field : object.getClass().getDeclaredFields()) {
            Masked annotation = field.getAnnotation(Masked.class);
            if (annotation != null) {
                field.setAccessible(true);
                try {
                    String value = (String) field.get(object);
                    field.set(object, mask(value, annotation.type()));
                } catch (IllegalAccessException e) {
                    // Log error
                }
            }
        }
        return object;
    }
}
```

```java
// Masking strategies
public class PanMaskingStrategy implements MaskingStrategy {
    @Override
    public String mask(String pan) {
        if (pan.length() < 4) return "****";
        return "*".repeat(pan.length() - 4) + pan.substring(pan.length() - 4);
    }
}

public class EmailMaskingStrategy implements MaskingStrategy {
    @Override
    public String mask(String email) {
        int atIndex = email.indexOf('@');
        if (atIndex <= 1) return "***@" + email.substring(atIndex + 1);
        String local = email.substring(0, atIndex);
        String domain = email.substring(atIndex);
        return local.charAt(0) + "***" + local.charAt(local.length() - 1) + domain;
    }
}

public class PhoneMaskingStrategy implements MaskingStrategy {
    @Override
    public String mask(String phone) {
        String digits = phone.replaceAll("\\D", "");
        if (digits.length() < 4) return "****";
        return "***-***-" + digits.substring(digits.length() - 4);
    }
}
```

```java
// Annotation for maskable fields
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Masked {
    DataType type();
    boolean inLogs() default true;
    boolean inResponse() default false;
}

// DTO with masking
public class CustomerDto {
    private String id;
    private String name;
    
    @Masked(type = DataType.EMAIL, inResponse = true)
    private String email;
    
    @Masked(type = DataType.PHONE, inResponse = true)
    private String phone;
    
    @Masked(type = DataType.PAN, inLogs = true, inResponse = true)
    private String cardNumber;
}
```

### Configuration

```yaml
masking:
  enabled: true
  default-mask-char: '*'
  types:
    pan:
      show-last: 4
    email:
      show-first: 1
      show-last: 1
```

## Important Rules

- Never store sensitive data unmasked in logs.
- Apply masking at the point closest to the output.
- Use tokenization when reversibility is needed.
- Document what data is masked and how.
- Validate that masking does not break functionality.
- Consider context: different levels for different users.
- Implement tests to verify correct masking.
- Use annotations to declare maskable fields.
- Implement separate strategies per data type.
- Consider context (logs vs response) when masking.

## Example

```java
@Service
public class CustomerService {
    private final DataMaskingService maskingService;
    
    public CustomerDto getCustomerMasked(String id) {
        Customer customer = repository.findById(id);
        CustomerDto dto = mapper.toDto(customer);
        return maskingService.maskObject(dto);
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
