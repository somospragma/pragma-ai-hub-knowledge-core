<!-- keywords: rest api, api design, http methods, status codes, pagination, filtering, resource naming, controllers, dto, spring boot, java -->
# REST API Design Standards — Java Implementation

## Purpose

Document the design standards for REST APIs and implementation in Java with Spring Boot, including resource naming, HTTP methods, status codes, pagination, filtering, OpenAPI documentation, controllers, and DTOs.

## Scope of Application

- When designing new REST APIs
- When consistency between services is required
- To review existing APIs against standards
- When documenting APIs with OpenAPI/Swagger
- When implementing REST controllers with Spring Boot

## Main content

### Resource naming

```
✓ CORRECT                     ✗ INCORRECT
/customers                    /getCustomers
/customers/{id}               /customer/{id}
/customers/{id}/orders        /customers/{id}/getOrders
/orders/{id}/items            /orderItems
```

### HTTP Methods

| Method | Usage | Idempotent | Body |
|--------|-------|------------|------|
| GET | Retrieve resource(s) | Yes | No |
| POST | Create resource | No | Yes |
| PUT | Replace resource | Yes | Yes |
| PATCH | Partial update | No | Yes |
| DELETE | Delete resource | Yes | No |

### Status codes

```
2xx - Success
├── 200 OK - Successful request
├── 201 Created - Resource created
├── 202 Accepted - Asynchronous processing accepted
└── 204 No Content - Success without content (DELETE)

4xx - Client Error
├── 400 Bad Request - Malformed request
├── 401 Unauthorized - Not authenticated
├── 403 Forbidden - Not authorized
├── 404 Not Found - Resource does not exist
├── 409 Conflict - State conflict
├── 422 Unprocessable Entity - Validation failed
└── 429 Too Many Requests - Rate limit exceeded

5xx - Server Error
├── 500 Internal Server Error - Unexpected error
├── 502 Bad Gateway - Upstream service error
├── 503 Service Unavailable - Service not available
└── 504 Gateway Timeout - Upstream service timeout
```

### Response structure

```json
// Single resource
{
  "id": "cust-123",
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2024-01-15T10:30:00Z",
  "_links": {
    "self": { "href": "/customers/cust-123" },
    "orders": { "href": "/customers/cust-123/orders" }
  }
}

// Collection with pagination
{
  "data": [
    { "id": "cust-123", "name": "John Doe" },
    { "id": "cust-124", "name": "Jane Doe" }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 150,
    "totalPages": 8
  },
  "_links": {
    "self": { "href": "/customers?page=1&pageSize=20" },
    "next": { "href": "/customers?page=2&pageSize=20" },
    "last": { "href": "/customers?page=8&pageSize=20" }
  }
}
```

### OpenAPI Specification

```yaml
openapi: 3.0.3
info:
  title: Customer API
  version: 1.0.0
  description: API for customer management

servers:
  - url: https://api.example.com/v1

paths:
  /customers:
    get:
      summary: List customers
      operationId: listCustomers
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: size
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: Successful operation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomerList'
    post:
      summary: Create customer
      operationId: createCustomer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateCustomerRequest'
      responses:
        '201':
          description: Customer created
          headers:
            Location:
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Customer'

components:
  schemas:
    Customer:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
          format: email
        status:
          type: string
          enum: [ACTIVE, INACTIVE]
        createdAt:
          type: string
          format: date-time
```

### Java Technology Stack

- **Framework:** Spring Boot with Spring Web MVC
- **REST Annotations:** `@RestController`, `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`
- **DTOs:** Java Records (Java 16+)
- **Validation:** Jakarta Bean Validation (`@Valid`, `@NotBlank`, `@Email`, `@Size`, `@Pattern`, `@Min`, `@Max`)
- **Documentation:** OpenAPI with `springdoc-openapi` (`@Tag`, `@Operation`, `@ApiResponse`)

### REST Controller — Spring Boot

```java
@RestController
@RequestMapping("/api/v1/customers")
@Tag(name = "Customers", description = "Customer management API")
public class CustomerController {

    private final CustomerService customerService;

    @GetMapping
    @Operation(summary = "List customers", description = "Returns paginated list of customers")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Successful operation"),
        @ApiResponse(responseCode = "400", description = "Invalid parameters")
    })
    public ResponseEntity<PagedResponse<CustomerDto>> listCustomers(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String sort) {

        Page<CustomerDto> customers = customerService.findAll(
            PageRequest.of(page, size, parseSort(sort)),
            status
        );

        return ResponseEntity.ok(PagedResponse.of(customers));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get customer by ID")
    public ResponseEntity<CustomerDto> getCustomer(
            @PathVariable @NotBlank String id) {

        return customerService.findById(id)
            .map(ResponseEntity::ok)
            .orElseThrow(() -> new ResourceNotFoundException("Customer", id));
    }

    @PostMapping
    @Operation(summary = "Create customer")
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<CustomerDto> createCustomer(
            @Valid @RequestBody CreateCustomerRequest request) {

        CustomerDto created = customerService.create(request);

        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
            .path("/{id}")
            .buildAndExpand(created.getId())
            .toUri();

        return ResponseEntity.created(location).body(created);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update customer")
    public ResponseEntity<CustomerDto> updateCustomer(
            @PathVariable String id,
            @Valid @RequestBody UpdateCustomerRequest request) {

        CustomerDto updated = customerService.update(id, request);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete customer")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public ResponseEntity<Void> deleteCustomer(@PathVariable String id) {
        customerService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

### DTOs with validation (Java Records)

```java
public record CreateCustomerRequest(
    @NotBlank(message = "Name is required")
    @Size(max = 100, message = "Name must not exceed 100 characters")
    String name,

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    String email,

    @Pattern(regexp = "^\\+?[1-9]\\d{1,14}$", message = "Invalid phone format")
    String phone
) {}

public record CustomerDto(
    String id,
    String name,
    String email,
    String phone,
    String status,
    Instant createdAt,
    Links links
) {
    public record Links(
        Link self,
        Link orders
    ) {}
}
```

### Resource creation flow

```
POST /api/v1/customers
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com"
}

Response:
HTTP/1.1 201 Created
Location: /api/v1/customers/cust-123
Content-Type: application/json

{
  "id": "cust-123",
  "name": "John Doe",
  "email": "john@example.com",
  "status": "ACTIVE",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

## Important Rules

- Use plural nouns for resources
- Keep URLs lowercase with hyphens
- Version APIs in the URL (/v1/)
- Use appropriate HTTP codes for each situation
- Implement pagination for collections
- Document all APIs with OpenAPI
- Include correlation headers (X-Request-ID)

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
