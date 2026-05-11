---
id: backend-convencion-documentacion-api
version: "1.0"
scope: chapter
type: convencion
chapter: backend
---

# Convención: Documentación de APIs

## Objetivo

Garantizar que toda API expuesta por un microservicio tenga documentación OpenAPI 3.x auto-generada desde el código, siempre sincronizada con la implementación, con cero drift y mínimo esfuerzo.

---

## Protocolo Paso a Paso

### Paso 1: Adoptar API-First

El contrato de la API se define ANTES de implementar:

1. **Definir el contrato OpenAPI/AsyncAPI** como parte de los inputs del JTBD.
2. **Usar el contrato como fuente de verdad** para generar controllers, DTOs, y validaciones.
3. **La implementación se ajusta al contrato**, no al revés.

**Regla:** Si no hay contrato definido, se DEBE solicitar al pragmatic antes de generar código.

---

### Paso 2: Documentación OpenAPI Obligatoria

Toda API REST pública DEBE tener especificación OpenAPI 3.x:

| Requisito | Obligatorio |
|-----------|-------------|
| Spec OpenAPI 3.x auto-generada desde código | ✅ Sí |
| Endpoint `/v3/api-docs` accesible en non-prod | ✅ Sí |
| Swagger UI accesible en non-prod | ✅ Sí |
| Summary y description en cada endpoint | ✅ Sí |
| Response codes documentados | ✅ Sí |
| Request/Response schemas completos | ✅ Sí |
| Ejemplos de request/response | ✅ Sí |
| Swagger UI en producción | ❌ Deshabilitado o asegurado |

---

### Paso 3: Anotar Cada Endpoint

Al generar entry-points, CADA endpoint DEBE incluir anotaciones OpenAPI:

```java
@Operation(
    summary = "Consultar saldo de cuenta",
    description = "Retorna el saldo disponible y contable de una cuenta dado su número"
)
@ApiResponses(value = {
    @ApiResponse(
        responseCode = "200",
        description = "Saldo consultado exitosamente",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(implementation = BalanceResponseDTO.class),
            examples = @ExampleObject(value = """
                {
                  "accountNumber": "1234567890",
                  "availableBalance": 5000.00,
                  "bookBalance": 5200.00,
                  "currency": "HNL"
                }
                """)
        )
    ),
    @ApiResponse(
        responseCode = "404",
        description = "Cuenta no encontrada",
        content = @Content(schema = @Schema(implementation = ErrorResponseDTO.class))
    )
})
@GetMapping("/accounts/{accountNumber}/balance")
public Mono<BalanceResponseDTO> getBalance(
    @Parameter(description = "Número de cuenta", required = true, example = "1234567890")
    @PathVariable String accountNumber
) { ... }
```

---

### Paso 4: Anotar Cada DTO

Los DTOs de request y response DEBEN tener anotaciones `@Schema`:

```java
@Schema(description = "Respuesta con el saldo de la cuenta")
public record BalanceResponseDTO(
    @Schema(description = "Número de cuenta", example = "1234567890")
    String accountNumber,

    @Schema(description = "Saldo disponible", example = "5000.00")
    BigDecimal availableBalance,

    @Schema(description = "Saldo contable", example = "5200.00")
    BigDecimal bookBalance,

    @Schema(description = "Moneda ISO 4217", example = "HNL")
    String currency
) {}
```

---

### Paso 5: Documentación AsyncAPI para Eventos

Todo evento publicado o consumido DEBE tener especificación AsyncAPI:

1. **Definir el esquema del mensaje** (payload, headers, metadata).
2. **Documentar el canal** (topic/queue name, protocolo).
3. **Incluir ejemplos** del payload del evento.
4. **Documentar el contrato de DLQ** si aplica.

---

### Paso 6: Configurar Generación Automática

La documentación se genera automáticamente desde el código usando las herramientas del framework:

| Framework | Herramienta | Dependencia |
|-----------|-------------|-------------|
| Spring WebFlux | SpringDoc OpenAPI | `springdoc-openapi-starter-webflux-ui` |
| Spring MVC | SpringDoc OpenAPI | `springdoc-openapi-starter-webmvc-ui` |
| Node.js/Express | swagger-jsdoc + swagger-ui-express | `swagger-jsdoc`, `swagger-ui-express` |

**Regla:** La documentación NUNCA se escribe manualmente como archivo YAML/JSON separado. Se genera desde las anotaciones del código para garantizar sincronización.

---

### Paso 7: Verificar la Documentación

Después de generar el código:

1. Verificar que el endpoint `/v3/api-docs` retorna el spec completo.
2. Verificar que Swagger UI renderiza correctamente todos los endpoints.
3. Verificar que los ejemplos de request/response son válidos.
4. Verificar que los schemas coinciden con los DTOs generados.

---

## Reglas Inquebrantables

1. **Toda API pública DEBE tener spec OpenAPI 3.x.** Sin excepciones.
2. **Todo evento DEBE tener spec AsyncAPI.** Sin excepciones.
3. **La documentación se genera desde el código.** No se escribe manualmente.
4. **Cada endpoint DEBE tener:** summary, description, response codes, schemas, y ejemplos.
5. **Swagger UI DEBE estar deshabilitado o asegurado en producción.**
6. **No se inventan specs.** Solo se documentan las arquitecturas y contratos disponibles en la KB.

---

## Fuentes

- ADR 012: Architectural API Documentation (OpenAPI)
