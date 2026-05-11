---
id: backend-skill-arquitectura-hexagonal
version: "1.0"
scope: chapter
type: skill
chapter: backend
---

# Arquitectura Hexagonal Multi-Módulo — Referencia Canónica Pragma

## Definición

La arquitectura hexagonal (Ports & Adapters) es el estándar de Pragma para microservicios con lógica de negocio. Separa el dominio de los detalles técnicos mediante puertos (interfaces) y adaptadores (implementaciones).

## Diagrama de Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                     INFRAESTRUCTURA                              │
│                                                                 │
│  ┌─────────────────┐                  ┌──────────────────────┐  │
│  │  Entry Points   │                  │  Driven Adapters     │  │
│  │  (REST, gRPC,   │                  │  (DB, HTTP clients,  │  │
│  │   Kafka, SQS)   │                  │   Redis, S3, Kafka)  │  │
│  └────────┬────────┘                  └──────────┬───────────┘  │
│           │                                      │              │
│  ┌────────┴──────────────────────────────────────┴───────────┐  │
│  │                      Helpers                               │  │
│  │              (Config, Mappers, Exceptions)                 │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ depende de
┌───────────────────────────────▼─────────────────────────────────┐
│                       APLICACIÓN                                 │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Assembler / DI                           │  │
│  │         (Configuración, inyección de dependencias)         │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ depende de
┌───────────────────────────────▼─────────────────────────────────┐
│                        DOMINIO                                   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │    Model     │  │   Ports (SPI)    │  │    Use Cases     │  │
│  │  (Entities,  │  │  (Interfaces de  │  │  (Lógica de      │  │
│  │   VOs, Enums)│  │   salida)        │  │   negocio)       │  │
│  └──────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Regla de Dependencia

```
infraestructura → aplicación → dominio

NUNCA al revés. El dominio NO conoce la infraestructura.
```

- **Dominio**: cero dependencias externas. Solo Java/Kotlin/TypeScript puro.
- **Aplicación**: depende solo del dominio. Ensambla y configura.
- **Infraestructura**: depende de aplicación y dominio. Implementa los puertos.

## Módulos y Estructura

### Módulo `domain`

Contiene la lógica de negocio pura, sin dependencias de frameworks.

```
domain/
├── model/
│   ├── Customer.java              # Entidad / Aggregate Root
│   ├── CustomerId.java            # Value Object
│   ├── CustomerStatus.java        # Enum de dominio
│   └── exceptions/
│       └── CustomerNotFoundException.java
├── ports/
│   └── spi/
│       ├── CustomerRepository.java      # Puerto de persistencia
│       ├── NotificationSender.java      # Puerto de notificaciones
│       └── PaymentGateway.java          # Puerto de pagos externos
└── usecases/
    ├── CreateCustomerUseCase.java
    ├── GetCustomerUseCase.java
    └── UpdateCustomerStatusUseCase.java
```

**Reglas del dominio:**
- Las clases del modelo NO tienen anotaciones de frameworks (@Entity, @Column, etc.)
- Los puertos SPI son interfaces puras definidas en el dominio
- Los UseCases implementan UN caso de uso de negocio
- Un UseCase NUNCA llama a otro UseCase

### Módulo `infrastructure`

Implementa los detalles técnicos: adaptadores de entrada y salida.

```
infrastructure/
├── entry-points/
│   ├── rest/
│   │   ├── CustomerController.java
│   │   ├── dto/
│   │   │   ├── CreateCustomerRequest.java
│   │   │   └── CustomerResponse.java
│   │   └── mapper/
│   │       └── CustomerRestMapper.java
│   ├── grpc/
│   │   └── CustomerGrpcService.java
│   └── kafka/
│       └── CustomerEventListener.java
├── driven-adapters/
│   ├── persistence/
│   │   ├── CustomerJpaRepository.java
│   │   ├── CustomerJpaAdapter.java    # Implementa CustomerRepository
│   │   ├── entity/
│   │   │   └── CustomerEntity.java    # @Entity JPA aquí
│   │   └── mapper/
│   │       └── CustomerPersistenceMapper.java
│   ├── rest-client/
│   │   ├── PaymentRestAdapter.java    # Implementa PaymentGateway
│   │   └── dto/
│   │       └── PaymentExternalResponse.java
│   └── messaging/
│       └── NotificationKafkaAdapter.java  # Implementa NotificationSender
└── helpers/
    ├── config/
    │   └── RestClientConfig.java
    └── exceptions/
        └── GlobalExceptionHandler.java
```

**Reglas de infraestructura:**
- Los entry-points reciben requests, mapean a modelo de dominio, invocan UseCases
- Los driven-adapters implementan los puertos SPI del dominio
- Cada adaptador tiene sus propios DTOs/entities — NUNCA exponer el modelo de dominio
- Los mappers convierten entre modelo de dominio y representaciones técnicas

### Módulo `application`

Ensambla todo: configura la inyección de dependencias.

```
application/
├── config/
│   └── UseCaseConfig.java         # @Configuration, @Bean de UseCases
├── MainApplication.java           # Punto de entrada (Spring Boot, etc.)
└── build.gradle                   # Dependencias de todos los módulos
```

**Reglas de aplicación:**
- Es el único módulo que conoce TODOS los demás
- Configura la inyección de dependencias
- NO contiene lógica de negocio
- Es el módulo que se despliega (genera el JAR/WAR ejecutable)

## Ejemplo de UseCase

```java
public class CreateCustomerUseCase {

    private final CustomerRepository customerRepository;
    private final NotificationSender notificationSender;

    public CreateCustomerUseCase(CustomerRepository customerRepository,
                                  NotificationSender notificationSender) {
        this.customerRepository = customerRepository;
        this.notificationSender = notificationSender;
    }

    public Customer execute(Customer customer) {
        customer.validate(); // Validación de negocio en el modelo
        Customer saved = customerRepository.save(customer);
        notificationSender.sendWelcome(saved);
        return saved;
    }
}
```

## Ejemplo de Puerto SPI

```java
// En domain/ports/spi/
public interface CustomerRepository {
    Customer save(Customer customer);
    Optional<Customer> findById(CustomerId id);
    List<Customer> findByStatus(CustomerStatus status);
}
```

## Ejemplo de Adaptador

```java
// En infrastructure/driven-adapters/persistence/
@Repository
public class CustomerJpaAdapter implements CustomerRepository {

    private final CustomerJpaRepository jpaRepository;
    private final CustomerPersistenceMapper mapper;

    @Override
    public Customer save(Customer customer) {
        CustomerEntity entity = mapper.toEntity(customer);
        CustomerEntity saved = jpaRepository.save(entity);
        return mapper.toDomain(saved);
    }

    @Override
    public Optional<Customer> findById(CustomerId id) {
        return jpaRepository.findById(id.getValue())
            .map(mapper::toDomain);
    }
}
```

## Cuándo Usar Esta Arquitectura

| Criterio | Aplica |
|----------|--------|
| Microservicio con lógica de negocio | ✅ Sí |
| Múltiples integraciones externas | ✅ Sí |
| Dominio que evoluciona frecuentemente | ✅ Sí |
| Necesidad de testear dominio aislado | ✅ Sí |
| CRUD simple sin lógica | ❌ Usar arquitectura simple |
| Lambda de transformación | ❌ Usar arquitectura simple |
| Prototipo o PoC | ❌ Usar arquitectura simple |

## Regla por Defecto

Si NO se especifica una arquitectura explícitamente en el proyecto → DEBE usarse arquitectura hexagonal multi-módulo. Es el estándar de Pragma.
