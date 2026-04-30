<!-- keywords: bian, banking, service domain, control record, behavior qualifier, banking architecture, api design, ddd, java, spring -->
# Reference: BIAN Framework for Banking Services — Java Spring

## Purpose

Self-contained reference for applying the BIAN (Banking Industry Architecture Network) framework version 13.0 in the design and development of banking microservices with Java Spring Boot. This document covers all conceptual foundations (BIAN hierarchy, Service Domains, Control Records, Behavior Qualifiers, operations, API design, DDD mapping) as well as the concrete Java implementation patterns (models, interfaces, controllers, DTOs, OpenAPI, dependencies). No other BIAN reference file is required.

## Scope of Application

- Java 17+ microservices with Spring Boot 3.x implementing BIAN Service Domains.
- Compatible with any architectural pattern: hexagonal, onion, or simple.
- Reference version: **BIAN Service Landscape 13.0** (June 2025). Do not use versions 12.0 or 14.0 unless explicitly indicated.

---

## Part I — BIAN Conceptual Foundations

### 1. BIAN Core Concepts

BIAN organizes banking functionality in a hierarchy:

```
Business Area (12)
  └── Business Domain (intermediate grouping)
        └── Service Domain (~340 in SL 13.0)
              ├── Control Record (CR)
              ├── Behavior Qualifiers (BQ)
              └── Service Operations
```

**Key definitions:**

| Concept | Definition | Code Analogy |
|---------|-----------|--------------|
| Business Area | Top-level grouping of banking capabilities | High-level module or bounded context |
| Service Domain | Discrete functional unit with single responsibility | Microservice |
| Control Record (CR) | Primary instance managed by the Service Domain | Aggregate Root |
| Behavior Qualifier (BQ) | Specific aspect or sub-function of the CR | Child entity of the aggregate |
| Service Operation | Action that can be executed on a CR or BQ | Service method / endpoint |

### 2. BIAN 13.0 Business Areas

BIAN 13.0 defines 12 Business Areas. Each groups multiple Service Domains:

| # | Business Area | Description | Example Service Domains |
|---|--------------|-------------|------------------------|
| 1 | Reference Data | Master and reference data | Party Reference Data, Product Directory, Location Data Management |
| 2 | Sales & Service | Commercial management and customer service | Customer Offer, Customer Case Management, Customer Relationship Management |
| 3 | Operations & Execution | Transaction processing and operations | Payment Execution, Card Transaction, Clearing, Settlement |
| 4 | Risk & Compliance | Risk management and regulatory compliance | Credit Risk, Fraud Detection, Regulatory Compliance, KYC |
| 5 | Finance & Risk Management | Financial control and corporate risk management | Financial Accounting, Position Management, Market Risk |
| 6 | Products | Banking product management | Current Account, Savings Account, Loan, Mortgage |
| 7 | Channels | Service channels | Branch Operations, E-Branch Operations, Contact Center |
| 8 | Payments | Payment processing | Payment Order, Payment Initiation, ACH Operations |
| 9 | Trade & Securities | Capital markets operations | Securities Trading, Trade Confirmation, Custody |
| 10 | Credit | Credit management | Credit Facility, Credit Administration, Collections |
| 11 | Corporate Services | Internal corporate services | Human Resources, Procurement, Facilities Management |
| 12 | Business Support | Business support | Business Architecture, IT Standards, Platform Operations |

> **Note:** The full list of Service Domains (~340) is available on the official BIAN portal. See the Tools and Resources section for the complete catalog URL.

### 3. Functional Patterns (Asset Types)

Each Service Domain implements exactly one Functional Pattern that determines its behavior:

| Functional Pattern | Purpose | Example Service Domain |
|-------------------|---------|----------------------|
| **Direct** | Direct and supervise activities | Corporate Strategy, Business Direction |
| **Manage** | Manage a resource or capability continuously | Customer Relationship Management, Employee Management |
| **Administer** | Administer a regulatory or normative framework | Regulatory Compliance, Legal Compliance |
| **Design** | Design products, processes, or services | Product Design, Service Design |
| **Develop** | Develop capabilities or assets | Software Development, Staff Development |
| **Process** | Process discrete transactions or requests | Payment Execution, Card Transaction |
| **Operate** | Operate infrastructure or platforms | Platform Operations, IT Operations |
| **Fulfill** | Fulfill a contracted product or service | Current Account, Savings Account, Loan |
| **Transact** | Execute financial transactions | Securities Trading, Foreign Exchange |
| **Enroll** | Register or enroll participants | Customer Enrollment, Product Enrollment |
| **Agree Terms** | Negotiate and agree on terms | Service Agreement, Customer Agreement |
| **Allocate** | Allocate resources or capabilities | Resource Allocation, Budget Allocation |
| **Analyze** | Analyze information to generate insights | Customer Behavior Analysis, Market Analysis |
| **Assess** | Evaluate and qualify | Credit Assessment, Risk Assessment |
| **Catalog** | Catalog and organize information | Product Catalog, Service Catalog |
| **Monitor** | Monitor activities or conditions | Fraud Monitoring, Compliance Monitoring |
| **Track** | Track status and progress | Case Tracking, Delivery Tracking |

**Rule:** When creating a new Service Domain, first identify which Functional Pattern applies. This defines the available operations and the Control Record structure.

### 4. Service Operations

BIAN defines a standard set of operations applied to Control Records (CR) and Behavior Qualifiers (BQ):

#### Operations on Control Record (CR)

| Operation | When to Use | Example |
|-----------|------------|---------|
| **Initiate** | Create a new CR instance | Open an account, start a loan |
| **Update** | Modify attributes of an existing CR | Update account data |
| **Retrieve** | Query the state of a CR | Get account details |
| **Control** | Change the operational state of the CR (suspend, reactivate, close) | Suspend an account for fraud |
| **Execute** | Execute an automated action on the CR | Execute a scheduled payment |
| **Request** | Request an action requiring approval or intervention | Request credit limit increase |
| **Grant** | Grant an authorization or permission | Approve a credit application |
| **Register** | Register information or a participant | Register a new customer |
| **Notify** | Send a notification about a CR event | Notify payment due date |
| **Capture** | Capture information external to the system | Capture data from a scanned document |

#### Operations on Behavior Qualifier (BQ)

The same operations apply at the BQ level, but in the context of a specific aspect of the CR:

```
CR: Current Account (Initiate, Update, Retrieve, Control)
  └── BQ: Deposits And Withdrawals (Initiate, Retrieve)
  └── BQ: Service Fees (Retrieve, Update)
  └── BQ: Interest (Retrieve, Update)
  └── BQ: Account Sweep (Initiate, Update, Retrieve, Control)
```

**Rule:** Not all operations apply to every CR/BQ. Select only the operations that make sense for the domain.

### 5. BIAN API Design

API URLs must follow the BIAN convention:

#### URL Pattern

```
/{service-domain}/{cr-reference-id}/{behavior-qualifier}/{bq-reference-id}/{operation}
```

#### HTTP Method Mapping

| BIAN Operation | HTTP Method | URL Example |
|----------------|-------------|-------------|
| Initiate (CR) | POST | `/current-account/initiate` |
| Retrieve (CR) | GET | `/current-account/{cr-id}/retrieve` |
| Update (CR) | PUT | `/current-account/{cr-id}/update` |
| Control (CR) | PUT | `/current-account/{cr-id}/control` |
| Execute (CR) | PUT | `/current-account/{cr-id}/execute` |
| Request (CR) | POST | `/current-account/{cr-id}/request` |
| Initiate (BQ) | POST | `/current-account/{cr-id}/deposits-and-withdrawals/initiate` |
| Retrieve (BQ) | GET | `/current-account/{cr-id}/deposits-and-withdrawals/{bq-id}/retrieve` |

#### URL Naming Conventions

- Use **kebab-case** for Service Domain and BQ names: `current-account`, `deposits-and-withdrawals`
- Reference IDs use the `-id` suffix: `cr-reference-id`, `bq-reference-id`
- The operation goes at the end of the URL as a noun: `/initiate`, `/retrieve`, `/update`

### 6. Canonical Data Model

BIAN defines standard data models. When implementing, follow these naming conventions:

#### Entity Naming

| BIAN Concept | Naming Convention | Example |
|-------------|-------------------|---------|
| Control Record | `{ServiceDomain}Facility` or `{ServiceDomain}Fulfillment` | `CurrentAccountFacility` |
| Behavior Qualifier | Descriptive name of the aspect | `DepositsAndWithdrawals`, `ServiceFees` |
| Reference | `{entity}Reference` | `currentAccountFacilityReference` |
| Status | `{entity}Status` | `accountStatus` |
| Type | `{entity}Type` | `transactionType` |
| Date | `{description}Date` or `{description}DateTime` | `valueDate`, `transactionDateTime` |
| Amount | `{description}Amount` with separate currency | `transactionAmount` + `transactionCurrency` |

#### Standard Control Record Structure

```
ControlRecord:
  ├── {cr}Reference          (unique identifier)
  ├── customerReference      (customer reference)
  ├── {cr}Type               (type/classification)
  ├── {cr}Status             (current status)
  ├── {cr}Currency           (currency, if applicable)
  ├── dateOfOpening          (creation date)
  ├── configuration          (specific configuration)
  └── behaviorQualifiers[]   (list of associated BQs)
```

#### Standard Behavior Qualifier Structure

```
BehaviorQualifier:
  ├── {bq}Reference          (unique identifier)
  ├── {bq}Type               (type/classification)
  ├── {bq}Status             (status)
  ├── {bq}Amount             (amount, if applicable)
  ├── {bq}Currency           (currency, if applicable)
  ├── {bq}DateTime           (event date/time)
  └── {bq}Description        (description)
```

### 7. BIAN to DDD Mapping

For implementing Service Domains using DDD patterns:

| BIAN Concept | DDD Concept | Notes |
|-------------|-------------|-------|
| Business Area | Subdomain | Strategic grouping |
| Service Domain | Bounded Context | One microservice = one Service Domain |
| Control Record | Aggregate Root | Transactional consistency root |
| Behavior Qualifier | Entity (within the Aggregate) | Child entity of the aggregate |
| Service Operation | Application Service / Use Case | Orchestrates the logic |
| Canonical Data Model | Value Objects + Entities | Domain models |
| BIAN Events | Domain Events | Communication between bounded contexts |
| Functional Pattern | Determines the Aggregate type | Fulfill = long-lived Aggregate |

**Mapping rules:**

1. One Service Domain = one Bounded Context = one microservice
2. The Control Record is always the Aggregate Root
3. BQs are entities within the aggregate, accessible only through the CR
4. Service Operations are implemented as Use Cases or Application Services
5. Events between Service Domains are implemented as Domain Events
6. The Functional Pattern guides aggregate design:
   - **Fulfill**: Long-lived aggregate (account, loan)
   - **Process**: Short-lived transactional aggregate (payment, transfer)
   - **Manage**: Continuous management aggregate (customer relationship)

### 8. cross Example (Language-Agnostic)

#### Case: Current Account Service Domain

```
Service Domain: Current Account
Functional Pattern: Fulfill
Business Area: Products

Control Record: CurrentAccountFacility
  ├── currentAccountFacilityReference: string (UUID)
  ├── customerReference: string
  ├── accountType: "Checking" | "Savings"
  ├── accountCurrency: string (ISO 4217)
  ├── accountStatus: "Active" | "Dormant" | "Suspended" | "Closed"
  ├── dateOfOpening: date
  │
  ├── BQ: DepositsAndWithdrawals
  │     ├── depositsAndWithdrawalsReference: string
  │     ├── transactionType: "Deposit" | "Withdrawal" | "Transfer"
  │     ├── transactionAmount: decimal
  │     ├── transactionCurrency: string
  │     ├── valueDate: datetime
  │     └── transactionStatus: "Initiated" | "Completed" | "Failed"
  │
  ├── BQ: ServiceFees
  │     ├── serviceFeeReference: string
  │     ├── feeType: string
  │     ├── feeAmount: decimal
  │     └── applicationDate: date
  │
  └── BQ: Interest
        ├── interestReference: string
        ├── interestRate: decimal
        ├── interestType: "Fixed" | "Variable"
        └── accrualDate: date

Operations:
  CR: Initiate, Update, Retrieve, Control
  BQ DepositsAndWithdrawals: Initiate, Retrieve
  BQ ServiceFees: Retrieve, Update
  BQ Interest: Retrieve, Update

API Endpoints:
  POST   /current-account/initiate
  GET    /current-account/{cr-id}/retrieve
  PUT    /current-account/{cr-id}/update
  PUT    /current-account/{cr-id}/control
  POST   /current-account/{cr-id}/deposits-and-withdrawals/initiate
  GET    /current-account/{cr-id}/deposits-and-withdrawals/{bq-id}/retrieve
  GET    /current-account/{cr-id}/service-fees/{bq-id}/retrieve
  PUT    /current-account/{cr-id}/interest/{bq-id}/update
```

---

## Part II — Java Spring Implementation

### 9. Control Record Model

The Control Record is implemented as the main domain entity. Regardless of the chosen architecture, the model structure is the same:

```java
// Control Record: CurrentAccountFacility
public class CurrentAccountFacility {

    private String currentAccountFacilityReference;
    private String customerReference;
    private String bankBranchLocationReference;
    private String accountType;
    private String accountCurrency;
    private LocalDate dateOfOpening;
    private String accountStatus;
    private AccountConfiguration accountConfiguration;

    // Behavior Qualifiers as collections
    private List<DepositsAndWithdrawals> depositsAndWithdrawals;
    private List<ServiceFee> serviceFees;
    private List<Interest> interestArrangements;

    // Constructor, getters, setters or use Lombok/Records per project convention
}
```

### 10. Behavior Qualifier Models

Each BQ is a separate entity with its own reference:

```java
// BQ: DepositsAndWithdrawals
public class DepositsAndWithdrawals {

    private String depositsAndWithdrawalsReference;
    private String transactionType;
    private BigDecimal transactionAmount;
    private String transactionCurrency;
    private LocalDateTime valueDate;
    private String transactionDescription;
    private String payerReference;
    private String payeeReference;
    private String transactionStatus;
}

// BQ: ServiceFee
public class ServiceFee {

    private String serviceFeeReference;
    private String feeType;
    private BigDecimal feeAmount;
    private String feeCurrency;
    private LocalDate applicationDate;
    private String feeStatus;
}

// BQ: Interest
public class Interest {

    private String interestReference;
    private BigDecimal interestRate;
    private String interestType;
    private LocalDate accrualDate;
    private BigDecimal accruedAmount;
    private String interestCurrency;
}
```

### 11. Service Operations Interface

Define an interface exposing the BIAN operations of the Service Domain:

```java
// Service Domain interface: Current Account
public interface CurrentAccountServiceDomain {

    // --- CR Operations ---

    CurrentAccountFacility initiate(InitiateCurrentAccountRequest request);

    CurrentAccountFacility update(String crReferenceId, UpdateCurrentAccountRequest request);

    CurrentAccountFacility retrieve(String crReferenceId);

    ControlRecordStatus control(String crReferenceId, ControlAction action);

    // --- BQ: Deposits And Withdrawals ---

    DepositsAndWithdrawals initiateDepositsAndWithdrawals(
        String crReferenceId,
        InitiateDepositRequest request
    );

    DepositsAndWithdrawals retrieveDepositsAndWithdrawals(
        String crReferenceId,
        String bqReferenceId
    );

    // --- BQ: Service Fees ---

    ServiceFee retrieveServiceFee(String crReferenceId, String bqReferenceId);

    ServiceFee updateServiceFee(
        String crReferenceId,
        String bqReferenceId,
        UpdateServiceFeeRequest request
    );

    // --- BQ: Interest ---

    Interest retrieveInterest(String crReferenceId, String bqReferenceId);

    Interest updateInterest(
        String crReferenceId,
        String bqReferenceId,
        UpdateInterestRequest request
    );
}
```

### 12. Request/Response DTOs

DTOs follow BIAN naming with operation prefix:

```java
// Request for Initiate CR
public class InitiateCurrentAccountRequest {

    private String customerReference;
    private String accountType;
    private String accountCurrency;
    private AccountConfiguration accountConfiguration;
}

// Request for Initiate BQ
public class InitiateDepositRequest {

    private String transactionType;
    private BigDecimal transactionAmount;
    private String transactionCurrency;
    private LocalDateTime valueDate;
    private String transactionDescription;
    private String payerReference;
    private String payeeReference;
}

// Generic Control response
public class ControlRecordStatus {

    private String controlRecordReference;
    private String controlAction;
    private String previousStatus;
    private String newStatus;
    private LocalDateTime effectiveDate;
}

// Control action enum
public enum ControlAction {
    SUSPEND,
    REACTIVATE,
    CLOSE,
    BLOCK,
    UNBLOCK
}
```

### 13. REST Controller

The controller implements BIAN URLs. This example is agnostic to the service layer (works with hexagonal, onion, or simple):

```java
@RestController
@RequestMapping("/current-account")
public class CurrentAccountController {

    private final CurrentAccountServiceDomain serviceDomain;

    public CurrentAccountController(CurrentAccountServiceDomain serviceDomain) {
        this.serviceDomain = serviceDomain;
    }

    // --- CR Operations ---

    @PostMapping("/initiate")
    public ResponseEntity<CurrentAccountFacility> initiate(
            @Valid @RequestBody InitiateCurrentAccountRequest request) {
        CurrentAccountFacility facility = serviceDomain.initiate(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(facility);
    }

    @GetMapping("/{cr-reference-id}/retrieve")
    public ResponseEntity<CurrentAccountFacility> retrieve(
            @PathVariable("cr-reference-id") String crReferenceId) {
        return ResponseEntity.ok(serviceDomain.retrieve(crReferenceId));
    }

    @PutMapping("/{cr-reference-id}/update")
    public ResponseEntity<CurrentAccountFacility> update(
            @PathVariable("cr-reference-id") String crReferenceId,
            @Valid @RequestBody UpdateCurrentAccountRequest request) {
        return ResponseEntity.ok(serviceDomain.update(crReferenceId, request));
    }

    @PutMapping("/{cr-reference-id}/control")
    public ResponseEntity<ControlRecordStatus> control(
            @PathVariable("cr-reference-id") String crReferenceId,
            @RequestBody ControlAction action) {
        return ResponseEntity.ok(serviceDomain.control(crReferenceId, action));
    }

    // --- BQ: Deposits And Withdrawals ---

    @PostMapping("/{cr-reference-id}/deposits-and-withdrawals/initiate")
    public ResponseEntity<DepositsAndWithdrawals> initiateDeposit(
            @PathVariable("cr-reference-id") String crReferenceId,
            @Valid @RequestBody InitiateDepositRequest request) {
        DepositsAndWithdrawals result =
            serviceDomain.initiateDepositsAndWithdrawals(crReferenceId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(result);
    }

    @GetMapping("/{cr-reference-id}/deposits-and-withdrawals/{bq-reference-id}/retrieve")
    public ResponseEntity<DepositsAndWithdrawals> retrieveDeposit(
            @PathVariable("cr-reference-id") String crReferenceId,
            @PathVariable("bq-reference-id") String bqReferenceId) {
        return ResponseEntity.ok(
            serviceDomain.retrieveDepositsAndWithdrawals(crReferenceId, bqReferenceId)
        );
    }

    // --- BQ: Service Fees ---

    @GetMapping("/{cr-reference-id}/service-fees/{bq-reference-id}/retrieve")
    public ResponseEntity<ServiceFee> retrieveServiceFee(
            @PathVariable("cr-reference-id") String crReferenceId,
            @PathVariable("bq-reference-id") String bqReferenceId) {
        return ResponseEntity.ok(
            serviceDomain.retrieveServiceFee(crReferenceId, bqReferenceId)
        );
    }
}
```

### 14. Implementation by Architectural Pattern

The `CurrentAccountServiceDomain` interface is implemented differently depending on the chosen architecture:

#### Hexagonal Architecture

```java
// Input port (domain)
public interface CurrentAccountServiceDomain { /* ... BIAN operations ... */ }

// Domain service implements the port
@Service
public class CurrentAccountService implements CurrentAccountServiceDomain {

    private final CurrentAccountRepository repository; // Output port

    @Override
    public CurrentAccountFacility initiate(InitiateCurrentAccountRequest request) {
        CurrentAccountFacility facility = CurrentAccountFacility.builder()
            .currentAccountFacilityReference(UUID.randomUUID().toString())
            .customerReference(request.getCustomerReference())
            .accountType(request.getAccountType())
            .accountCurrency(request.getAccountCurrency())
            .accountStatus("Active")
            .dateOfOpening(LocalDate.now())
            .build();

        return repository.save(facility);
    }

    // ... remaining operations
}

// Output port (domain)
public interface CurrentAccountRepository {
    CurrentAccountFacility save(CurrentAccountFacility facility);
    Optional<CurrentAccountFacility> findByReference(String reference);
}

// Output adapter (infrastructure)
@Repository
public class JpaCurrentAccountRepository implements CurrentAccountRepository {
    // JPA implementation
}
```

#### Simple Architecture

```java
// Direct service without ports
@Service
public class CurrentAccountService implements CurrentAccountServiceDomain {

    private final CurrentAccountJpaRepository repository; // Direct dependency

    @Override
    public CurrentAccountFacility initiate(InitiateCurrentAccountRequest request) {
        CurrentAccountEntity entity = new CurrentAccountEntity();
        entity.setReference(UUID.randomUUID().toString());
        entity.setCustomerReference(request.getCustomerReference());
        entity.setAccountType(request.getAccountType());
        entity.setStatus("Active");

        CurrentAccountEntity saved = repository.save(entity);
        return toFacility(saved);
    }

    // ... remaining operations
}
```

### 15. OpenAPI Specification

Document the API following BIAN conventions:

```yaml
openapi: 3.0.3
info:
  title: Current Account Service Domain
  version: 13.0.0
  description: >
    BIAN Service Domain: Current Account.
    Functional Pattern: Fulfill.
    Handles the fulfillment of a current account product.

servers:
  - url: https://api.company.com
    description: Production

paths:
  /current-account/initiate:
    post:
      operationId: initiateCurrentAccount
      summary: Initiate a new current account facility
      tags:
        - CR - Current Account Facility
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InitiateCurrentAccountRequest'
      responses:
        '201':
          description: Current account initiated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CurrentAccountFacility'

  /current-account/{cr-reference-id}/retrieve:
    get:
      operationId: retrieveCurrentAccount
      summary: Retrieve current account facility details
      tags:
        - CR - Current Account Facility
      parameters:
        - name: cr-reference-id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Current account details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CurrentAccountFacility'

  /current-account/{cr-reference-id}/deposits-and-withdrawals/initiate:
    post:
      operationId: initiateDepositsAndWithdrawals
      summary: Initiate a deposit or withdrawal transaction
      tags:
        - BQ - Deposits And Withdrawals
      parameters:
        - name: cr-reference-id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InitiateDepositRequest'
      responses:
        '201':
          description: Transaction initiated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DepositsAndWithdrawals'
```

### 16. Maven/Gradle Dependencies

```groovy
// build.gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'

    // Lombok (optional, per project convention)
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'

    // OpenAPI documentation
    implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.3.0'
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
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springdoc</groupId>
        <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
        <version>2.3.0</version>
    </dependency>
</dependencies>
```

---

## Verification Checklist

### BIAN Conceptual

- [ ] The Service Domain is identified in the BIAN 13.0 catalog
- [ ] The correct Functional Pattern for the Service Domain has been identified
- [ ] The Control Record has a unique Reference as identifier
- [ ] Behavior Qualifiers are correctly identified as sub-functions of the CR
- [ ] Only the applicable Service Operations have been implemented
- [ ] API URLs follow the BIAN convention: `/{service-domain}/{cr-id}/{bq}/{bq-id}/{operation}`
- [ ] Field names follow BIAN naming: `{entity}Reference`, `{entity}Status`, `{entity}Type`
- [ ] The DDD mapping is correct: CR = Aggregate Root, BQ = Entity
- [ ] Amounts always have an associated currency field (ISO 4217)
- [ ] Events between Service Domains are defined as Domain Events

### Java Implementation

- [ ] The Control Record is implemented as a Java class with all required BIAN fields
- [ ] Behavior Qualifiers are separate classes with their own `Reference`
- [ ] The Service Domain interface exposes only the applicable BIAN operations
- [ ] Request DTOs use the operation prefix: `Initiate...Request`, `Update...Request`
- [ ] The REST controller uses BIAN URLs: `/{sd}/{cr-id}/{bq}/{bq-id}/{operation}`
- [ ] Path variables use kebab-case: `cr-reference-id`, `bq-reference-id`
- [ ] Amounts use `BigDecimal`, never `double` or `float`
- [ ] Dates use `LocalDate` or `LocalDateTime` from `java.time`
- [ ] The API is documented with OpenAPI 3.0 following BIAN conventions
- [ ] The service implementation is independent of the chosen architectural pattern

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
