<!-- keywords: rfc7807, error handling, problem details, http error, rest api errors, spring boot error, exception handler, java -->
# RFC 7807 Error Handling — Java Implementation

## Purpose

Implement the RFC 7807 standard (Problem Details for HTTP APIs) for error handling in Java applications with Spring Boot, providing a consistent structure for error responses in REST APIs.

## Scope of Application

- When designing error responses for REST APIs
- When implementing global exception handling in Spring Boot
- When creating consistent error responses across services
- When integrating bean validation with RFC 7807 responses
- When documenting API error codes in OpenAPI

## Main content

### RFC 7807 Structure

The standard defines a consistent JSON structure for communicating errors:

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "The request contains invalid fields",
  "instance": "/api/v1/customers",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ],
  "traceId": "abc-123-def"
}
```

### Standard fields

| Field | Required | Description |
|-------|-----------|-------------|
| type | Yes | URI that identifies the error type |
| title | Yes | Human-readable summary of the problem |
| status | Yes | HTTP code |
| detail | No | Specific explanation of this occurrence |
| instance | No | URI of the problem instance |

### Common error types

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Categories                              │
├─────────────────────────────────────────────────────────────────┤
│  4xx - Client Errors                                             │
│  ├── 400 validation-error      → Invalid data                   │
│  ├── 401 unauthorized          → Not authenticated              │
│  ├── 403 forbidden             → Not authorized                 │
│  ├── 404 resource-not-found    → Resource does not exist        │
│  └── 409 conflict              → State conflict                 │
├─────────────────────────────────────────────────────────────────┤
│  5xx - Server Errors                                             │
│  ├── 500 internal-error        → Unexpected error               │
│  └── 503 service-unavailable   → Service not available          │
└─────────────────────────────────────────────────────────────────┘
```

### Error handling flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Request    │────▶│  Validation  │────▶│   Process    │
└──────────────┘     └──────┬───────┘     └──────┬───────┘
                           │                     │
                     Error │               Error │
                           ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐
                    │ ProblemDetail│     │ ProblemDetail│
                    │   (400)      │     │   (500)      │
                    └──────────────┘     └──────────────┘
```

### Dependencies

```groovy
// build.gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    implementation 'com.fasterxml.jackson.core:jackson-databind'
}
```

```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
</dependencies>
```

### RFC 7807 Error Model

```java
public record ProblemDetail(
    @JsonProperty("type") String type,
    @JsonProperty("title") String title,
    @JsonProperty("status") int status,
    @JsonProperty("detail") String detail,
    @JsonProperty("instance") String instance,
    @JsonProperty("traceId") String traceId,
    @JsonProperty("timestamp") Instant timestamp,
    @JsonProperty("errors") List<FieldError> errors
) {
    public record FieldError(String field, String message) {}
    
    public static ProblemDetailBuilder builder() {
        return new ProblemDetailBuilder();
    }
}
```

### ProblemDetail Builder

```java
public class ProblemDetailBuilder {
    private String type;
    private String title;
    private int status;
    private String detail;
    private String instance;
    private List<ProblemDetail.FieldError> errors = new ArrayList<>();
    
    public ProblemDetailBuilder type(ErrorType errorType) {
        this.type = errorType.getTypeUri();
        this.title = errorType.getTitle();
        this.status = errorType.getStatus();
        return this;
    }
    
    public ProblemDetailBuilder detail(String detail) {
        this.detail = detail;
        return this;
    }
    
    public ProblemDetailBuilder instance(String instance) {
        this.instance = instance;
        return this;
    }
    
    public ProblemDetailBuilder addError(String field, String message) {
        this.errors.add(new ProblemDetail.FieldError(field, message));
        return this;
    }
    
    public ProblemDetail build() {
        return new ProblemDetail(
            type, title, status, detail, instance,
            MDC.get("traceId"),
            Instant.now(),
            errors.isEmpty() ? null : errors
        );
    }
}
```

### Error Types

```java
public enum ErrorType {
    VALIDATION_ERROR("validation-error", "Validation Error", 400),
    RESOURCE_NOT_FOUND("resource-not-found", "Resource Not Found", 404),
    CONFLICT("conflict", "Resource Conflict", 409),
    UNAUTHORIZED("unauthorized", "Unauthorized", 401),
    FORBIDDEN("forbidden", "Forbidden", 403),
    INTERNAL_ERROR("internal-error", "Internal Server Error", 500),
    SERVICE_UNAVAILABLE("service-unavailable", "Service Unavailable", 503);
    
    private final String code;
    private final String title;
    private final int status;
    
    ErrorType(String code, String title, int status) {
        this.code = code;
        this.title = title;
        this.status = status;
    }
    
    public String getTypeUri() {
        return "https://api.example.com/errors/" + code;
    }
    
    public String getTitle() { return title; }
    public int getStatus() { return status; }
}
```

### Global Exception Handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleValidation(
            MethodArgumentNotValidException ex,
            HttpServletRequest request) {
        
        ProblemDetailBuilder builder = ProblemDetail.builder()
            .type(ErrorType.VALIDATION_ERROR)
            .detail("Request validation failed")
            .instance(request.getRequestURI());
        
        ex.getBindingResult().getFieldErrors().forEach(error ->
            builder.addError(error.getField(), error.getDefaultMessage()));
        
        return ResponseEntity.badRequest()
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(builder.build());
    }
    
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleNotFound(
            ResourceNotFoundException ex,
            HttpServletRequest request) {
        
        ProblemDetail problem = ProblemDetail.builder()
            .type(ErrorType.RESOURCE_NOT_FOUND)
            .detail(ex.getMessage())
            .instance(request.getRequestURI())
            .build();
        
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> handleGeneric(
            Exception ex,
            HttpServletRequest request) {
        
        log.error("Unexpected error", ex);
        
        ProblemDetail problem = ProblemDetail.builder()
            .type(ErrorType.INTERNAL_ERROR)
            .detail("An unexpected error occurred")
            .instance(request.getRequestURI())
            .build();
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }
}
```

### Custom Exception

```java
public class ResourceNotFoundException extends RuntimeException {
    private final String resourceType;
    private final String resourceId;
    
    public ResourceNotFoundException(String resourceType, String resourceId) {
        super(String.format("%s with id '%s' not found", resourceType, resourceId));
        this.resourceType = resourceType;
        this.resourceId = resourceId;
    }
    
    public String getResourceType() { return resourceType; }
    public String getResourceId() { return resourceId; }
}
```

## Important Rules

- Always use Content-Type: `application/problem+json` (`MediaType.APPLICATION_PROBLEM_JSON`)
- Include traceId from MDC for log correlation
- Do not expose internal details or stack traces in production
- Use consistent URIs for error types
- Document all error types in OpenAPI
- Differentiate client errors (4xx) vs server errors (5xx)
- Include specific field errors for validation
- Map all known exceptions to specific types

## Example

```java
@RestController
@RequestMapping("/api/v1/customers")
public class CustomerController {
    
    @PostMapping
    public ResponseEntity<Customer> createCustomer(
            @Valid @RequestBody CreateCustomerRequest request) {
        // If validation fails, GlobalExceptionHandler handles the error
        Customer customer = customerService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(customer);
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<Customer> getCustomer(@PathVariable String id) {
        return customerService.findById(id)
            .map(ResponseEntity::ok)
            .orElseThrow(() -> new ResourceNotFoundException("Customer", id));
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
