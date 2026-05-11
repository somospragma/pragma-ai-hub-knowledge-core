---
id: backend-skill-arquitectura-ddd
version: "1.0"
scope: chapter
type: skill
chapter: backend
---

# Domain-Driven Design (DDD) — Patrones Aplicados en Pragma

## Definición

DDD es un enfoque de diseño de software que centra el desarrollo en el dominio del negocio. En Pragma se aplica cuando el dominio es complejo, tiene reglas de negocio ricas y múltiples aggregates que interactúan.

## Patrones Tácticos

### Aggregates

Un Aggregate es un cluster de objetos de dominio tratados como una unidad para cambios de datos. Tiene una raíz (Aggregate Root) que es el único punto de acceso externo.

**Reglas:**
- Toda modificación pasa por el Aggregate Root
- Las transacciones se limitan a UN aggregate
- Referencias entre aggregates solo por ID (nunca por referencia directa)
- El aggregate garantiza la consistencia interna

```java
// Aggregate Root
public class Order {

    private final OrderId id;
    private CustomerId customerId;  // Referencia por ID, no por objeto
    private OrderStatus status;
    private final List<OrderLine> lines;  // Entidades internas
    private Money totalAmount;

    public void addLine(Product product, int quantity) {
        if (status != OrderStatus.DRAFT) {
            throw new OrderNotModifiableException(id);
        }
        OrderLine line = new OrderLine(product.getId(), product.getPrice(), quantity);
        lines.add(line);
        recalculateTotal();
    }

    public void confirm() {
        if (lines.isEmpty()) {
            throw new EmptyOrderException(id);
        }
        this.status = OrderStatus.CONFIRMED;
        // Registrar evento de dominio
        registerEvent(new OrderConfirmedEvent(id, customerId, totalAmount));
    }

    private void recalculateTotal() {
        this.totalAmount = lines.stream()
            .map(OrderLine::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }
}
```

**Tamaño del Aggregate:**
- Mantener aggregates pequeños (preferir pocos objetos internos)
- Si un aggregate crece demasiado, probablemente necesita dividirse
- Usar eventual consistency entre aggregates

### Entities (Entidades)

Objetos con identidad única que persiste a lo largo de su ciclo de vida. Dos entidades son iguales si tienen el mismo ID, sin importar sus atributos.

```java
public class OrderLine {

    private final OrderLineId id;
    private ProductId productId;
    private Money unitPrice;
    private int quantity;

    public Money getSubtotal() {
        return unitPrice.multiply(quantity);
    }

    public void updateQuantity(int newQuantity) {
        if (newQuantity <= 0) {
            throw new InvalidQuantityException(newQuantity);
        }
        this.quantity = newQuantity;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderLine other)) return false;
        return id.equals(other.id);  // Igualdad por identidad
    }
}
```

### Value Objects (Objetos de Valor)

Objetos inmutables sin identidad propia. Dos Value Objects son iguales si todos sus atributos son iguales.

**Reglas:**
- Inmutables (no tienen setters)
- Igualdad por valor (todos los campos)
- Auto-validantes (se crean válidos o lanzan excepción)
- Sin efectos secundarios

```java
public record Money(BigDecimal amount, Currency currency) {

    public Money {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new InvalidMoneyException("Amount must be non-negative");
        }
        if (currency == null) {
            throw new InvalidMoneyException("Currency is required");
        }
    }

    public static final Money ZERO = new Money(BigDecimal.ZERO, Currency.USD);

    public Money add(Money other) {
        assertSameCurrency(other);
        return new Money(amount.add(other.amount), currency);
    }

    public Money multiply(int factor) {
        return new Money(amount.multiply(BigDecimal.valueOf(factor)), currency);
    }

    private void assertSameCurrency(Money other) {
        if (!currency.equals(other.currency)) {
            throw new CurrencyMismatchException(currency, other.currency);
        }
    }
}
```

```java
public record CustomerId(String value) {

    public CustomerId {
        if (value == null || value.isBlank()) {
            throw new InvalidCustomerIdException("CustomerId cannot be blank");
        }
    }
}
```

### Domain Events (Eventos de Dominio)

Representan algo que ocurrió en el dominio. Se usan para comunicación entre bounded contexts y para desacoplar side effects.

**Reglas:**
- Inmutables (representan un hecho pasado)
- Nombrados en pasado (OrderConfirmed, PaymentProcessed)
- Contienen solo la información necesaria para el consumidor
- Se publican DESPUÉS de que la transacción del aggregate se completa

```java
public record OrderConfirmedEvent(
    OrderId orderId,
    CustomerId customerId,
    Money totalAmount,
    Instant occurredAt
) {
    public OrderConfirmedEvent(OrderId orderId, CustomerId customerId, Money totalAmount) {
        this(orderId, customerId, totalAmount, Instant.now());
    }
}
```

**Patrón de publicación desde el Aggregate:**

```java
public abstract class AggregateRoot {

    private final List<DomainEvent> domainEvents = new ArrayList<>();

    protected void registerEvent(DomainEvent event) {
        domainEvents.add(event);
    }

    public List<DomainEvent> pullDomainEvents() {
        List<DomainEvent> events = List.copyOf(domainEvents);
        domainEvents.clear();
        return events;
    }
}
```

### Bounded Contexts (Contextos Delimitados)

Un Bounded Context define los límites explícitos donde un modelo de dominio es válido. Cada contexto tiene su propio lenguaje ubicuo, modelos y reglas.

```
┌─────────────────────┐         ┌─────────────────────┐
│   Orders Context    │         │  Payments Context   │
│                     │         │                     │
│  Order              │  Event  │  Payment            │
│  OrderLine          │────────▶│  PaymentMethod      │
│  OrderStatus        │         │  Transaction        │
│                     │         │                     │
│  "Customer" = ID    │         │  "Customer" = Payer │
└─────────────────────┘         └─────────────────────┘
         │                                │
         │         Anti-Corruption        │
         │            Layer               │
         ▼                                ▼
┌─────────────────────────────────────────────────────┐
│              Inventory Context                        │
│                                                     │
│  Product (diferente modelo que en Orders)            │
│  Stock                                              │
│  Warehouse                                          │
└─────────────────────────────────────────────────────┘
```

**Anti-Corruption Layer (ACL):**

Traduce entre modelos de diferentes contextos. Protege tu dominio de modelos externos.

```java
// ACL en el contexto de Payments que traduce del contexto de Orders
public class OrderPaymentTranslator {

    public PaymentRequest fromOrderConfirmed(OrderConfirmedEvent event) {
        return new PaymentRequest(
            new PayerId(event.customerId().value()),  // Traducción de concepto
            event.totalAmount(),
            PaymentReason.ORDER_PAYMENT
        );
    }
}
```

### Repositories (Repositorios)

Abstracción de persistencia definida en el dominio. Simula una colección en memoria de aggregates.

**Reglas:**
- Se define UN repositorio por Aggregate Root
- La interfaz vive en el dominio (puerto SPI)
- Trabaja con objetos de dominio, NUNCA con entities de persistencia
- Métodos nombrados con lenguaje de dominio

```java
// En domain/ports/spi/
public interface OrderRepository {

    Order save(Order order);
    Optional<Order> findById(OrderId id);
    List<Order> findByCustomer(CustomerId customerId);
    List<Order> findPendingOlderThan(Duration duration);

    // NO: findByStatusAndCreatedAtBefore (lenguaje técnico)
    // SÍ: findPendingOlderThan (lenguaje de dominio)
}
```

## Patrones Estratégicos

### Context Mapping

Relaciones entre Bounded Contexts:

| Relación | Descripción | Ejemplo |
|----------|-------------|---------|
| **Partnership** | Dos equipos cooperan, éxito conjunto | Orders ↔ Inventory |
| **Customer-Supplier** | Upstream provee, downstream consume | Payments → Orders |
| **Conformist** | Downstream se adapta al modelo upstream | Tu servicio → API externa |
| **ACL** | Capa de traducción para proteger tu modelo | Tu dominio ← Legacy system |
| **Published Language** | Contrato compartido (OpenAPI, eventos) | Event schema compartido |

### Ubiquitous Language (Lenguaje Ubicuo)

- Cada Bounded Context tiene su propio vocabulario
- Los nombres de clases, métodos y variables DEBEN usar el lenguaje del dominio
- "Customer" puede significar cosas diferentes en contextos diferentes
- El código ES la documentación del lenguaje ubicuo

## Cuándo Usar DDD

| Criterio | Aplica DDD |
|----------|-----------|
| Dominio con reglas de negocio complejas | ✅ Sí |
| Múltiples aggregates que interactúan | ✅ Sí |
| Equipo con acceso a expertos de dominio | ✅ Sí |
| Dominio que evoluciona frecuentemente | ✅ Sí |
| CRUD simple sin invariantes | ❌ No, usar arquitectura simple |
| Servicio de integración puro (proxy) | ❌ No, usar hexagonal sin DDD |
| Prototipo o MVP rápido | ❌ No, complejidad innecesaria |

## DDD + Arquitectura Hexagonal en Pragma

DDD se implementa DENTRO de la capa de dominio de la arquitectura hexagonal:

```
domain/
├── model/
│   ├── aggregate/          # Aggregate Roots
│   │   └── Order.java
│   ├── entity/             # Entidades internas
│   │   └── OrderLine.java
│   ├── valueobject/        # Value Objects
│   │   ├── Money.java
│   │   ├── OrderId.java
│   │   └── CustomerId.java
│   ├── event/              # Domain Events
│   │   └── OrderConfirmedEvent.java
│   └── exception/          # Excepciones de dominio
│       └── OrderNotModifiableException.java
├── ports/
│   └── spi/
│       └── OrderRepository.java
└── usecases/
    └── ConfirmOrderUseCase.java
```
