---
id: backend-skill-arquitectura-simple
version: "1.0"
scope: chapter
type: skill
chapter: backend
---

# Arquitectura Simple (Flat) — Patrón para Servicios sin Complejidad

## Definición

La arquitectura simple es una estructura plana sin separación en módulos hexagonales. Sigue el patrón clásico de capas: Controller → Service → Repository. Se usa exclusivamente para servicios sin lógica de negocio significativa.

## Cuándo Usar

| Caso de uso | Ejemplo |
|-------------|---------|
| CRUD puro | API de configuración, catálogos estáticos |
| Proxy / Passthrough | Gateway que reenvía requests sin transformar |
| Lambda de transformación | Función que convierte formato A → formato B |
| Servicio de infraestructura | Health check, config server, service discovery |
| PoC / Prototipo | Validación rápida de concepto |
| BFF simple | Backend-for-Frontend que solo agrega llamadas |

**Regla clave:** Si el servicio NO tiene reglas de negocio que validar, NO necesita arquitectura hexagonal.

## Estructura del Proyecto

```
my-simple-service/
├── src/
│   ├── controller/
│   │   └── ProductController.java
│   ├── service/
│   │   └── ProductService.java
│   ├── repository/
│   │   └── ProductRepository.java
│   ├── model/
│   │   ├── Product.java                # Entity JPA directa
│   │   └── dto/
│   │       ├── CreateProductRequest.java
│   │       └── ProductResponse.java
│   ├── config/
│   │   └── AppConfig.java
│   ├── exception/
│   │   └── GlobalExceptionHandler.java
│   └── MainApplication.java
├── src/test/
│   ├── controller/
│   │   └── ProductControllerTest.java
│   └── service/
│       └── ProductServiceTest.java
├── Dockerfile
├── build.gradle / pom.xml / package.json
└── README.md
```

## Diagrama de Flujo

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Controller  │────▶│   Service    │────▶│   Repository     │
│  (HTTP/API)  │     │  (Lógica     │     │  (Persistencia)  │
│              │◀────│   mínima)    │◀────│                  │
└──────────────┘     └──────────────┘     └──────────────────┘
       │                                          │
       │              ┌──────────┐                │
       └─────────────▶│   DTOs   │◀───────────────┘
                      └──────────┘
```

**Nota:** En arquitectura simple, el modelo puede ser compartido entre capas. No hay separación estricta entre modelo de dominio y modelo de persistencia.

## Ejemplo Completo — CRUD de Productos

### Controller

```java
@RestController
@RequestMapping("/api/v1/products")
public class ProductController {

    private final ProductService productService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProductResponse create(@Valid @RequestBody CreateProductRequest request) {
        return productService.create(request);
    }

    @GetMapping("/{id}")
    public ProductResponse getById(@PathVariable Long id) {
        return productService.getById(id);
    }

    @GetMapping
    public List<ProductResponse> getAll() {
        return productService.getAll();
    }

    @PutMapping("/{id}")
    public ProductResponse update(@PathVariable Long id,
                                   @Valid @RequestBody UpdateProductRequest request) {
        return productService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        productService.delete(id);
    }
}
```

### Service

```java
@Service
@Transactional
public class ProductService {

    private final ProductRepository productRepository;

    public ProductResponse create(CreateProductRequest request) {
        Product product = new Product(request.name(), request.price(), request.category());
        Product saved = productRepository.save(product);
        return toResponse(saved);
    }

    public ProductResponse getById(Long id) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new NotFoundException("Product not found: " + id));
        return toResponse(product);
    }

    public List<ProductResponse> getAll() {
        return productRepository.findAll().stream()
            .map(this::toResponse)
            .toList();
    }

    public ProductResponse update(Long id, UpdateProductRequest request) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new NotFoundException("Product not found: " + id));
        product.setName(request.name());
        product.setPrice(request.price());
        product.setCategory(request.category());
        Product saved = productRepository.save(product);
        return toResponse(saved);
    }

    public void delete(Long id) {
        if (!productRepository.existsById(id)) {
            throw new NotFoundException("Product not found: " + id);
        }
        productRepository.deleteById(id);
    }

    private ProductResponse toResponse(Product product) {
        return new ProductResponse(
            product.getId(),
            product.getName(),
            product.getPrice(),
            product.getCategory()
        );
    }
}
```

### Repository

```java
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByCategory(String category);
}
```

### Model (Entity directa)

```java
@Entity
@Table(name = "products")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private BigDecimal price;

    @Column(nullable = false)
    private String category;

    // Constructor, getters, setters
}
```

### DTOs

```java
public record CreateProductRequest(
    @NotBlank String name,
    @NotNull @Positive BigDecimal price,
    @NotBlank String category
) {}

public record ProductResponse(
    Long id,
    String name,
    BigDecimal price,
    String category
) {}
```

## Ejemplo — Lambda de Transformación

```java
// Handler de Lambda que transforma formato CSV → JSON
public class CsvToJsonHandler implements RequestHandler<S3Event, String> {

    private final S3Client s3Client;
    private final ObjectMapper objectMapper;

    @Override
    public String handleRequest(S3Event event, Context context) {
        String bucket = event.getRecords().get(0).getS3().getBucket().getName();
        String key = event.getRecords().get(0).getS3().getObject().getKey();

        String csvContent = readFromS3(bucket, key);
        List<Map<String, String>> records = parseCsv(csvContent);
        String jsonContent = objectMapper.writeValueAsString(records);

        writeToS3(bucket, key.replace(".csv", ".json"), jsonContent);
        return "Processed: " + key;
    }
}
```

## Ejemplo — Proxy / Passthrough

```java
@RestController
@RequestMapping("/api/v1/external")
public class ExternalProxyController {

    private final WebClient webClient;

    @GetMapping("/users/{id}")
    public Mono<ExternalUserResponse> getUser(@PathVariable String id) {
        return webClient.get()
            .uri("/users/{id}", id)
            .retrieve()
            .bodyToMono(ExternalUserResponse.class);
    }
}
```

## Limitaciones de la Arquitectura Simple

| Limitación | Impacto |
|-----------|---------|
| Sin separación de concerns | Lógica de negocio se mezcla con infraestructura |
| Testabilidad limitada | Difícil testear lógica sin levantar contexto completo |
| Acoplamiento a frameworks | El modelo está atado a JPA/ORM |
| No escala con complejidad | Cada nueva regla de negocio ensucia el service |
| Sin puertos/adaptadores | Cambiar una integración requiere modificar el service |

## Señales de que Necesitas Migrar a Hexagonal

Migra a arquitectura hexagonal cuando observes CUALQUIERA de estas señales:

### 🚨 Señales Críticas (migrar inmediatamente)

1. **El Service tiene más de 3 métodos con lógica condicional**
   ```java
   // SEÑAL: Lógica de negocio creciendo en el service
   public OrderResponse create(CreateOrderRequest request) {
       if (request.type() == PREMIUM && customer.getLevel() > 3) {
           // aplicar descuento...
       }
       if (inventory.getStock(request.productId()) < request.quantity()) {
           // validar stock...
       }
       // Esto ya es lógica de negocio → necesita dominio
   }
   ```

2. **Se agregan más de 2 integraciones externas**
   ```java
   // SEÑAL: Múltiples dependencias externas
   public class OrderService {
       private final OrderRepository repository;
       private final PaymentClient paymentClient;      // integración 1
       private final InventoryClient inventoryClient;  // integración 2
       private final NotificationService notification; // integración 3
       // Demasiadas dependencias → necesita puertos/adaptadores
   }
   ```

3. **Los tests requieren mockear más de 2 dependencias**

4. **El controller mezcla validación de negocio con transformación de datos**

### ⚠️ Señales de Advertencia (planificar migración)

5. El archivo del Service supera las 200 líneas
6. Aparecen métodos privados que encapsulan "reglas"
7. Se duplica lógica entre endpoints diferentes
8. Se necesita reusar lógica en otro entry point (ej: agregar listener Kafka)

## Migración Simple → Hexagonal

```
ANTES (Simple):                    DESPUÉS (Hexagonal):

controller/                        infrastructure/entry-points/rest/
  └── ProductController.java         └── ProductController.java

service/                           domain/usecases/
  └── ProductService.java            ├── CreateProductUseCase.java
                                     └── GetProductUseCase.java

repository/                        domain/ports/spi/
  └── ProductRepository.java         └── ProductRepository.java (interfaz)

model/                             infrastructure/driven-adapters/persistence/
  └── Product.java (@Entity)         ├── ProductJpaAdapter.java
                                     └── entity/ProductEntity.java

                                   domain/model/
                                     └── Product.java (POJO puro)
```

## Regla Final

> La arquitectura simple es una **excepción justificada**, no la norma.
> El estándar de Pragma es hexagonal multi-módulo.
> Usar arquitectura simple requiere que el servicio sea genuinamente simple (CRUD puro, proxy, lambda).
> Ante la duda → usar hexagonal.
