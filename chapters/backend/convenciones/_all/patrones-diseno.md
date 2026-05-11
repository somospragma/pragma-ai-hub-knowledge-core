---
id: backend-convencion-patrones-diseno
version: "1.0"
scope: chapter
type: convencion
chapter: backend
---

# Convención: Patrones de Diseño

## Objetivo

Definir las convenciones de patrones de diseño que se aplican transversalmente: mock de librerías corporativas, interfaces thin en dominio, gradle.properties obligatorio, y manejo de fallas parciales en composición.

---

## Patrón 1: Mock de Librerías Corporativas

### Cuándo aplica

Cuando el microservicio depende de librerías internas del cliente hospedadas en repositorios privados (Artifactory/Nexus) que NO están accesibles durante la generación de código.

### Protocolo

1. **SIEMPRE mockear las librerías internas del cliente.** Sin excepciones. Sin preguntar.
2. **El mock DEBE ser un módulo compilable y funcional** que replica la API pública (clases, interfaces, métodos, anotaciones) de la librería real.
3. **Usar los MISMOS nombres de paquete** que la librería real (documentados en las referencias del cliente en la KB).
4. **El mock NO es un stub vacío** — debe tener implementaciones funcionales que permitan compilar y pasar tests.
5. **Nombrar el módulo como `{client}-lib-mocks`** (ej: `ficohsa-lib-mocks`, `mercantil-lib-mocks`).
6. **Documentar en el README** qué reemplazar cuando se integre con el Artifactory real.

### Comportamientos Default de los Mocks

| Tipo de librería | Comportamiento del mock |
|-----------------|------------------------|
| Encriptación / Desencriptación | Pass-through: retorna el valor de entrada sin modificar |
| Logging | Funcional: loguea a SLF4J con las mismas firmas de método |
| HTTP Client / WebClient | Funcional: usa Spring WebClient internamente, replica la API surface |
| Autenticación / Autorización | Pass-through: acepta cualquier token, retorna respuesta autorizada por default |
| Parameter Store / Secrets Manager | In-memory Map: almacena valores en `Map<String, String>` |
| Cache | In-memory Map: usa `ConcurrentHashMap` como backend |
| Regionalización | Funcional: retorna config default con `sourceBank` como región |

### Ejemplo de estructura

```
my-microservice/
├── domain/
├── infrastructure/
├── application/
└── ficohsa-lib-mocks/          ← Módulo de mocks
    └── src/main/java/
        └── com/ficohsa/core/   ← Mismo paquete que la librería real
            ├── encryption/
            │   └── CryptoService.java    ← Pass-through
            ├── logging/
            │   └── ActionLogService.java ← Loguea a SLF4J
            └── security/
                └── AuthFilter.java       ← Acepta todo
```

---

## Patrón 2: Thin Interfaces en Dominio

### Cuándo aplica

Cuando librerías corporativas del cliente exponen interfaces puras (sin dependencias de framework) que se usan como parámetros en puertos y UseCases del dominio.

### Protocolo

1. **Interfaces thin de librerías del cliente ESTÁN PERMITIDAS en el dominio** si cumplen las condiciones.
2. **Condiciones para ser "thin":**
   - Sin anotaciones de framework (no `@Component`, no `@Service`, no Spring)
   - Sin imports de framework (`org.springframework.*`, `jakarta.*`)
   - Solo firmas de métodos (puro contrato)
3. **Si la interfaz tiene dependencias de framework → NO se permite en dominio.** Se DEBE envolver en un puerto del dominio.

### Ejemplos

```java
// ✅ PERMITIDO en dominio — interfaz thin, puro contrato
public interface IActionLog {
    String getLogString();
}

// ✅ PERMITIDO en dominio — solo firmas de métodos
public interface ILoggerService {
    Mono<Void> logTransaction(String transactionId, String action);
}

// ❌ NO PERMITIDO en dominio — importa Spring
import org.springframework.stereotype.Component;

@Component
public interface ISecurityFilter {
    void filter(ServerWebExchange exchange);
}
```

### Regla de decisión

| ¿La interfaz importa framework? | ¿Tiene anotaciones? | ¿Se permite en dominio? |
|----------------------------------|---------------------|------------------------|
| No | No | ✅ Sí — usar directamente |
| No | Sí | ❌ No — envolver en puerto |
| Sí | No | ❌ No — envolver en puerto |
| Sí | Sí | ❌ No — envolver en puerto |

---

## Patrón 3: gradle.properties Obligatorio

### Cuándo aplica

En TODO proyecto Java con Gradle. Sin excepciones.

### Protocolo

1. **`gradle.properties` DEBE existir en la raíz del proyecto** junto con `gradle/libs.versions.toml`.
2. **Ambos archivos DEBEN coexistir.** Ninguno reemplaza al otro.
3. **Separación de responsabilidades:**

| Archivo | Contenido |
|---------|-----------|
| `gradle.properties` | Versiones de plugins, settings de performance Gradle, credenciales corporativas (placeholders) |
| `gradle/libs.versions.toml` | Versiones de librerías/dependencias referenciadas via `libs.{alias}` |

4. **Versiones de plugins NO van en `libs.versions.toml`.**
5. **Versiones de librerías NO van en `gradle.properties`.**
6. **Credenciales corporativas DEBEN ser placeholders** inyectados por CI/CD, nunca valores hardcodeados.

### Ejemplo de `gradle.properties`

```properties
# Plugin versions
springBootVersion=3.2.4
sonarqubePluginVersion=4.4.1.3373
pitestVersion=1.15.0
jacocoPluginVersion=0.8.11
owaspDependencyTrackPluginVersion=9.0.9

# Gradle performance
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.jvmargs=-Xmx2048m -XX:+HeapDumpOnOutOfMemoryError

# Corporate repository credentials (injected by CI/CD)
artifactoryUser=${ARTIFACTORY_USER}
artifactoryPassword=${ARTIFACTORY_PASSWORD}
```

### Ejemplo de `gradle/libs.versions.toml`

```toml
[versions]
spring-webflux = "6.1.5"
reactor-core = "3.6.4"
lombok = "1.18.30"
mapstruct = "1.5.5.Final"

[libraries]
spring-webflux = { module = "org.springframework:spring-webflux", version.ref = "spring-webflux" }
reactor-core = { module = "io.projectreactor:reactor-core", version.ref = "reactor-core" }
lombok = { module = "org.projectlombok:lombok", version.ref = "lombok" }
mapstruct = { module = "org.mapstruct:mapstruct", version.ref = "mapstruct" }
```

---

## Patrón 4: Manejo de Fallas Parciales en Composición

### Cuándo aplica

En microservicios de composición/orquestación que llaman a MÚLTIPLES backends independientes. NO aplica a microservicios que llaman a un solo backend.

### Protocolo

1. **Si algunos backends fallan pero otros responden exitosamente:**
   - Retornar HTTP 200 con los datos disponibles.
   - Incluir un array `warnings` documentando qué backends fallaron y por qué.
   - Los campos de backends fallidos se setean a `null` (NO se omiten del JSON).

2. **Si TODOS los backends fallan:**
   - Retornar HTTP 502 (Bad Gateway) con un body de error listando todas las fallas.

3. **El array `warnings` SOLO está presente cuando al menos un backend falló.** En éxito total, no se incluye.

4. **Si la spec define un comportamiento diferente para fallas parciales, la spec tiene precedencia.**

### Ejemplo de respuesta con falla parcial

```json
{
  "meta": { "bian": { "...": "..." } },
  "data": {
    "accountBalance": 5000.00,
    "loanDetails": null,
    "cardInfo": null,
    "warnings": [
      {
        "source": "T24",
        "code": "TIMEOUT",
        "message": "T24 wrapper no respondió en 30s"
      },
      {
        "source": "CardSystem",
        "code": "CIRCUIT_BREAKER_OPEN",
        "message": "Circuit breaker de CardSystem está abierto"
      }
    ]
  },
  "links": { "self": "/accounts/123/summary" }
}
```

### Ejemplo de respuesta con falla total

```json
{
  "type": "https://api.pragma.com/errors/bad-gateway",
  "title": "Bad Gateway",
  "status": 502,
  "detail": "Todos los backends fallaron",
  "failures": [
    { "source": "T24", "code": "TIMEOUT", "message": "No respondió en 30s" },
    { "source": "Abanks", "code": "CONNECTION_REFUSED", "message": "Conexión rechazada" },
    { "source": "CardSystem", "code": "CIRCUIT_BREAKER_OPEN", "message": "Circuit breaker abierto" }
  ]
}
```

### Implementación en el UseCase

```java
public class GetAccountSummaryUseCase {

    private final IAccountGateway accountGateway;
    private final ILoanGateway loanGateway;
    private final ICardGateway cardGateway;

    public AccountSummary execute(String accountId) {
        var results = callBackendsInParallel(accountId);

        if (results.allFailed()) {
            throw new AllBackendsFailedException(results.getFailures());
        }

        return AccountSummary.builder()
            .accountBalance(results.getOrNull("account"))
            .loanDetails(results.getOrNull("loan"))
            .cardInfo(results.getOrNull("card"))
            .warnings(results.getWarnings())
            .build();
    }
}
```

---

## Reglas Inquebrantables

1. **Librerías corporativas se mockean SIEMPRE.** Sin preguntar.
2. **Solo interfaces thin (sin framework) se permiten en dominio.**
3. **`gradle.properties` es OBLIGATORIO en todo proyecto Java.**
4. **Fallas parciales retornan 200 + warnings, no 500.**
5. **Fallas totales retornan 502 con detalle de cada falla.**

---

## Fuentes

- ADR 015: Mandatory Mock of Client Internal Libraries
- ADR 021: Client Library Thin Interfaces Permitted in Domain
- ADR 022: gradle.properties Mandatory for All Java Projects
- ADR 026: Partial Failure Handling in Composition Microservices
