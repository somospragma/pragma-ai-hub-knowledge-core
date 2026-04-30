<!-- keywords: soc2, audit logging, event traceability, log immutability, kinesis, dynamodb, compliance, java -->
# SOC2 Audit Logging - Java

## Purpose

Self-contained reference for SOC2-compliant audit logging in Java. Covers event traceability concepts, log immutability, retention, access tracking, and implementation with Spring Boot, Kinesis, and DynamoDB for immutable event storage.

## Scope of Application

- When implementing systems that require SOC2 certification.
- When complete operation traceability is needed.
- To design immutable logging systems.
- When implementing auditable access controls.
- When developing Java systems that require auditing with AOP aspects.

## Fundamental Concepts

### SOC2 Trust Principles Relevant to Auditing

| Principle | Audit Requirement |
|-----------|-------------------|
| Security | Access logging, configuration changes |
| Availability | Incident logs, response times |
| Integrity | Data change traceability |
| Confidentiality | Sensitive data access |
| Privacy | Consent, PII access |

### Audit Event Structure

```json
{
  "eventId": "uuid-v4",
  "timestamp": "2026-03-13T10:30:00.000Z",
  "eventType": "DATA_ACCESS",
  "eventCategory": "SECURITY",
  "actor": {
    "userId": "user-123",
    "userType": "EMPLOYEE",
    "ipAddress": "10.0.1.50",
    "userAgent": "Mozilla/5.0...",
    "sessionId": "sess-abc"
  },
  "resource": {
    "type": "CUSTOMER_RECORD",
    "id": "cust-456",
    "name": "customer-profile"
  },
  "action": {
    "type": "READ",
    "status": "SUCCESS",
    "details": "Viewed customer profile"
  },
  "context": {
    "correlationId": "corr-789",
    "requestId": "req-012",
    "service": "customer-service",
    "environment": "production"
  }
}
```

### Immutable Storage Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AUDIT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐                                           │
│  │  Application │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   DynamoDB   │───▶│   Kinesis    │───▶│   Firehose   │  │
│  │  (Immutable) │    │   Stream     │    │              │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│                                                  ▼          │
│                                          ┌──────────────┐  │
│                                          │  S3 Glacier  │  │
│                                          │ (7 years)    │  │
│                                          └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Event Types to Audit

| Category | Events |
|----------|--------|
| Authentication | Login, logout, MFA, password change |
| Authorization | Access denied, permission changes |
| Data | Read, create, modify, delete |
| Configuration | Settings changes, feature flags |
| System | Start, stop, critical errors |

### Data Retention

- Minimum 7 years for SOC2 compliance
- Use S3 Object Lock in COMPLIANCE mode
- Implement TTL in DynamoDB for operational data
- Archive to Glacier for long-term storage

## Main Content

### Dependencies

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-aop'
    implementation 'software.amazon.awssdk:kinesis:2.x.x'
    implementation 'software.amazon.awssdk:dynamodb:2.x.x'
}
```

### Implementation

```java
// Audit event model
@Document(collection = "audit_events")
public record AuditEvent(
    @Id String eventId,
    Instant timestamp,
    AuditEventType eventType,
    AuditCategory category,
    Actor actor,
    Resource resource,
    Action action,
    Context context,
    Map<String, Object> metadata
) {
    public static AuditEvent create(
        AuditEventType type,
        Actor actor,
        Resource resource,
        Action action,
        Context context
    ) {
        return new AuditEvent(
            UUID.randomUUID().toString(),
            Instant.now(),
            type,
            type.getCategory(),
            actor, resource, action, context,
            Map.of()
        );
    }
}

public record Actor(String userId, UserType userType, String ipAddress) {}
public record Resource(String type, String id, String name) {}
public record Action(ActionType type, ActionStatus status, String details) {}
```

```java
// Audit service
@Service
@Slf4j
public class AuditService {
    
    private final AuditEventRepository repository;
    private final KinesisClient kinesisClient;
    private final ObjectMapper objectMapper;
    
    @Async
    public void logEvent(AuditEvent event) {
        try {
            repository.save(event);
            sendToKinesis(event);
            log.info("audit_event: {}", objectMapper.writeValueAsString(event));
        } catch (Exception e) {
            log.error("Failed to log audit event, queuing for retry", e);
            queueForRetry(event);
        }
    }
    
    private void sendToKinesis(AuditEvent event) {
        PutRecordRequest request = PutRecordRequest.builder()
            .streamName("audit-events-stream")
            .partitionKey(event.actor().userId())
            .data(SdkBytes.fromUtf8String(
                objectMapper.writeValueAsString(event)))
            .build();
        kinesisClient.putRecord(request);
    }
}
```

```java
// Aspect for automatic auditing
@Aspect
@Component
public class AuditAspect {
    
    private final AuditService auditService;
    
    @Around("@annotation(auditable)")
    public Object auditMethod(ProceedingJoinPoint joinPoint, Auditable auditable) 
            throws Throwable {
        Actor actor = extractActor();
        Resource resource = extractResource(joinPoint, auditable);
        
        try {
            Object result = joinPoint.proceed();
            auditService.logEvent(AuditEvent.create(
                auditable.eventType(), actor, resource,
                new Action(auditable.actionType(), ActionStatus.SUCCESS, null),
                createContext()
            ));
            return result;
        } catch (Exception e) {
            auditService.logEvent(AuditEvent.create(
                auditable.eventType(), actor, resource,
                new Action(auditable.actionType(), ActionStatus.FAILURE, e.getMessage()),
                createContext()
            ));
            throw e;
        }
    }
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Auditable {
    AuditEventType eventType();
    ActionType actionType();
    String resourceType();
}
```

### Configuration

```yaml
audit:
  stream-name: audit-events-stream
  table-name: audit-events
  retention-years: 7
```

## Important Rules

- All audit events must be immutable.
- Minimum 7-year retention for SOC2 compliance.
- Always include: who, what, when, where, result.
- Never include sensitive data (PII, PAN) in audit logs.
- Implement alerts for critical security events.
- Protect logs against modification or deletion.
- Synchronize clocks with NTP for accurate timestamps.
- Use `@Async` to avoid blocking main operations.
- Implement retry queue for failed events.
- Never lose audit events.

## Example

```java
@Auditable(eventType = DATA_ACCESS, actionType = READ, resourceType = "CUSTOMER")
public Customer getCustomer(String customerId) {
    return customerRepository.findById(customerId);
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
