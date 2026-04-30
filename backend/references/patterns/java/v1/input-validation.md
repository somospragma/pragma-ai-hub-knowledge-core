<!-- keywords: input validation, bean validation, jakarta validation, sanitization, security, java -->
# Input Validation Patterns — Java Implementation

## Purpose

Define the principles and strategies for input validation and implementation in Java with Bean Validation (Jakarta Validation), including sanitization and security considerations.

## Scope of Application

- When implementing DTO and request validation
- When sanitizing user input
- When preventing code injection
- When validating specific formats (email, phone, etc.)
- When implementing custom validation

## Main content

### Validation Principles

```
┌─────────────────────────────────────────────────────────────┐
│                 VALIDATION PRINCIPLES                        │
├─────────────────────────────────────────────────────────────┤
│  1. VALIDATE EARLY - At the system boundary (controllers)   │
│  2. WHITELIST > BLACKLIST - Define what is allowed           │
│  3. FAIL FAST - Immediately reject invalid data             │
│  4. CLEAR MESSAGES - Indicate which field failed            │
└─────────────────────────────────────────────────────────────┘
```

### Validation Types

| Type | Description | Example |
|------|-------------|---------|
| Presence | Required field | `@NotNull`, `@NotBlank` |
| Format | Specific pattern | Email, phone, UUID |
| Range | Min/max values | `@Min(1)`, `@Max(100)` |
| Length | String size | `@Size(min=1, max=50)` |
| Type | Correct data type | Number, date, boolean |
| Business | Domain rules | Sufficient balance |

### Validation Layers

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: SYNTACTIC (Controller/DTO)                        │
│  - Correct format, required fields, data types              │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: SEMANTIC (Service/Domain)                         │
│  - Business rules, consistency, valid references            │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: PERSISTENCE (Repository/DB)                       │
│  - DB constraints, uniqueness, referential integrity        │
└─────────────────────────────────────────────────────────────┘
```

### Input Sanitization

```
┌─────────────────────────────────────────────────────────────┐
│  HTML:  Escape characters, tag whitelist                    │
│  SQL:   Use prepared statements (ALWAYS)                    │
│  LOGS:  Remove control characters, eliminate newlines       │
│  PATHS: Validate against path traversal (../)              │
└─────────────────────────────────────────────────────────────┘
```

## Libraries and dependencies

```groovy
// build.gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    implementation 'org.owasp.encoder:encoder:1.2.3'
}
```

```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
    <dependency>
        <groupId>org.owasp.encoder</groupId>
        <artifactId>encoder</artifactId>
        <version>1.2.3</version>
    </dependency>
</dependencies>
```

## Step by Step / Guidelines

### DTOs with Bean Validation

```java
@Data
public class OrderRequest {
    
    @NotNull(message = "Customer ID is required")
    @Pattern(regexp = "^[a-zA-Z0-9-]{1,50}$", message = "Invalid customer ID format")
    private String customerId;
    
    @NotEmpty(message = "Items cannot be empty")
    @Size(min = 1, max = 100, message = "Order must have 1-100 items")
    @Valid
    private List<OrderItemRequest> items;
    
    @NotNull(message = "Currency is required")
    @Pattern(regexp = "^[A-Z]{3}$", message = "Currency must be 3-letter ISO code")
    private String currency;
    
    @Email(message = "Invalid email format")
    private String notificationEmail;
    
    @ValidPhoneNumber
    private String phoneNumber;
    
    @Future(message = "Delivery date must be in the future")
    private LocalDate deliveryDate;
}

@Data
public class OrderItemRequest {
    
    @NotBlank(message = "Product ID is required")
    @Size(max = 50)
    private String productId;
    
    @NotNull
    @Min(value = 1, message = "Quantity must be at least 1")
    @Max(value = 1000, message = "Quantity cannot exceed 1000")
    private Integer quantity;
    
    @NotNull
    @DecimalMin(value = "0.01", message = "Price must be positive")
    @DecimalMax(value = "999999.99", message = "Price exceeds maximum")
    @Digits(integer = 6, fraction = 2)
    private BigDecimal unitPrice;
}
```

### Custom validator

```java
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = PhoneNumberValidator.class)
public @interface ValidPhoneNumber {
    String message() default "Invalid phone number";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class PhoneNumberValidator implements ConstraintValidator<ValidPhoneNumber, String> {
    
    private static final Pattern PHONE_PATTERN = 
        Pattern.compile("^\\+?[1-9]\\d{1,14}$");
    
    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.isBlank()) {
            return true; // Use @NotNull for required
        }
        return PHONE_PATTERN.matcher(value).matches();
    }
}
```

### Validation exception handler

```java
@RestControllerAdvice
public class ValidationExceptionHandler {
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleValidationErrors(
            MethodArgumentNotValidException ex) {
        
        List<Map<String, String>> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(error -> Map.of(
                "field", error.getField(),
                "message", error.getDefaultMessage()
            ))
            .toList();
        
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setType(URI.create("https://api.company.com/errors/validation-error"));
        problem.setTitle("Validation Error");
        problem.setDetail("Request validation failed");
        problem.setProperty("errors", errors);
        
        return ResponseEntity.badRequest().body(problem);
    }
    
    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ProblemDetail> handleConstraintViolation(
            ConstraintViolationException ex) {
        
        List<Map<String, String>> errors = ex.getConstraintViolations().stream()
            .map(violation -> Map.of(
                "field", violation.getPropertyPath().toString(),
                "message", violation.getMessage()
            ))
            .toList();
        
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setTitle("Validation Error");
        problem.setProperty("errors", errors);
        
        return ResponseEntity.badRequest().body(problem);
    }
}
```

### Input sanitization

```java
@Component
public class InputSanitizer {
    
    public String sanitizeHtml(String input) {
        if (input == null) return null;
        return Encode.forHtml(input);
    }
    
    public String sanitizeForLog(String input) {
        if (input == null) return null;
        return input.replaceAll("[\\r\\n]", " ")
                   .replaceAll("[^\\p{Print}]", "");
    }
    
    public String sanitizeForJson(String input) {
        if (input == null) return null;
        return Encode.forJavaScript(input);
    }
}
```

### Validation in Controller

```java
@RestController
@RequestMapping("/api/v1/orders")
@Validated
public class OrderController {
    
    private final OrderService orderService;
    
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            @Valid @RequestBody OrderRequest request) {
        OrderResponse response = orderService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<OrderResponse> getOrder(
            @PathVariable @Pattern(regexp = "^[a-zA-Z0-9-]{1,50}$") String id) {
        return ResponseEntity.ok(orderService.findById(id));
    }
}
```

## Configuration

### Custom validation messages

```properties
# ValidationMessages.properties
javax.validation.constraints.NotNull.message=Field is required
javax.validation.constraints.Size.message=Size must be between {min} and {max}
javax.validation.constraints.Email.message=Invalid email format
```

## Mocks and fixtures

### Validation test

```java
@WebMvcTest(OrderController.class)
class OrderControllerValidationTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Test
    void shouldReturnValidationError() throws Exception {
        String invalidRequest = """
            {
                "customerId": "",
                "items": [],
                "currency": "INVALID"
            }
            """;
        
        mockMvc.perform(post("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidRequest))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.title").value("Validation Error"))
            .andExpect(jsonPath("$.errors").isArray());
    }
}
```

## Important Rules

1. **Validate Early**: Validate at the system boundary (controllers)
2. **Whitelist**: Prefer whitelist validation over blacklist
3. **Sanitization**: Sanitize according to usage context (HTML, SQL, logs)
4. **Messages**: Provide clear and safe error messages
5. **Types**: Use strong types and schema validation
6. **Limits**: Set size limits on all fields
7. **Encoding**: Validate and normalize encoding (UTF-8)

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
