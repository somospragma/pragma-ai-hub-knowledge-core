---
id: backend-workflow-greenfield
version: "1.0"
scope: chapter
type: workflow
chapter: backend
---

# Workflow: Greenfield — Crear Microservicio desde Cero

## Cuándo usar este workflow

Usa este workflow cuando:
- El pragmático solicita crear un microservicio **nuevo** (no existe código previo)
- No hay repositorio existente con lógica de negocio que migrar
- Se parte de un contrato API y diagramas de arquitectura

NO uses este workflow cuando:
- Ya existe un repositorio con código funcional → usa `tech-debt.md`
- Ya existe un microservicio y se quiere agregar funcionalidad → usa `new-feature.md`

---

## Pasos

### Fase 1: Recepción y Validación de Inputs

**Paso 1.1: Identificar el JTBD**
- El pragmático indica que quiere crear un microservicio nuevo
- Confirmar que es Greenfield: no existe repositorio ni código previo
- Si existe código previo → redirigir a `tech-debt.md` o `new-feature.md`

**Paso 1.2: Solicitar inputs obligatorios**

Solicitar al pragmático los 6 inputs obligatorios. Aplicar las reglas de `convenciones/_all/validacion-inputs.md`:

| # | Input | Qué debe contener |
|---|-------|-------------------|
| 1 | Diagramas | Secuencia del flujo principal, diagrama de componentes |
| 2 | Tech Stack | Lenguaje, framework, versión, build tool, deployment target, tipo de arquitectura |
| 3 | Contrato del servicio | OpenAPI/Swagger 3.x con schemas completos (request, response, errores) |
| 4 | APIs externas que consume | Contratos con auth, ejemplos de request/response, timeouts esperados |
| 5 | Catálogo de configuración | Variables de entorno, Parameter Store paths, Secrets Manager keys |
| 6 | Manejo de errores | Códigos HTTP, mensajes de error, mapeo de errores downstream |

Para cada input:
- Si está presente y completo → marcar como ✅ y continuar
- Si está incompleto → indicar QUÉ falta específicamente y solicitar
- Si está ausente → solicitar explicando POR QUÉ es necesario para la generación
- **NUNCA proceder sin los 6 inputs completos**

**Paso 1.3: Confirmar inputs opcionales**

Preguntar al pragmático si aplican los siguientes inputs opcionales:

- **Base de datos**: tipo (PostgreSQL, MySQL, MongoDB, DynamoDB), esquema DDL, stored procedures
- **Message queues**: tecnología (Kafka, SQS, SNS, EventBridge), topics/queues, formato de mensajes
- **Recursos cloud adicionales**: S3 buckets, DynamoDB tables, ElastiCache, Redis
- **Reglas de negocio específicas**: validaciones complejas, cálculos, máquinas de estado

Regla: Si el pragmático confirma que un input opcional aplica → se convierte en **obligatorio** para esta ejecución y se valida con la misma rigurosidad.

**Paso 1.4: Resolver Tech Stack defaults**

Resolver valores no especificados:
- **Java version** → si no se especifica, preguntar al pragmático (opciones: 17, 21)
- **Nombre del servicio** → DEBE ser proporcionado por el pragmático (formato: kebab-case)
- **Base package** → si no se especifica, usar `co.com.pragma.{nombre-servicio}` (reemplazar guiones por puntos)
- **Reactive vs Imperative** → si no se especifica, preguntar presentando trade-offs:
  - Imperativo (Spring MVC): más simple, mejor para CRUD, equipo con menos experiencia reactiva
  - Reactivo (WebFlux): mejor throughput con I/O intensivo, backpressure, non-blocking
- **Build tool** → si no se especifica, usar Gradle con Kotlin DSL

Verificar: Todos los valores del tech stack están definidos antes de continuar.

---

### Fase 2: Análisis y Selección de Recursos

**Paso 2.1: Determinar el stack**

Basado en el tech stack definido en Fase 1, seleccionar UNO:

| Stack | Cuándo aplica |
|-------|---------------|
| `java-spring` | Java + Spring MVC (imperativo) |
| `java-webflux` | Java + Spring WebFlux (reactivo) |
| `node-express` | Node.js/TypeScript + Express |
| `node-lambda` | Node.js/TypeScript + AWS Lambda (serverless) |

**Paso 2.2: Cargar steering del stack**

Aplicar automáticamente los siguientes archivos de steering:
- `steering/_all/perspectiva.md` — valores de ingeniería y principios rectores
- `steering/_all/limites.md` — restricciones y prohibiciones generales
- `steering/_all/decisiones.md` — decisiones arquitectónicas obligatorias
- `steering/{stack}/` — límites y decisiones específicos del stack seleccionado

Estos archivos definen el marco de restricciones para toda la generación.

**Paso 2.3: Seleccionar skills relevantes**

Basado en los inputs validados, cargar los skills necesarios:

| Skill | Cuándo cargar |
|-------|---------------|
| `skills/_all/arquitectura-{tipo}.md` | Siempre (según tipo de arquitectura elegida) |
| `skills/{stack}/arquetipo.md` | Siempre (estructura del proyecto) |
| `skills/{stack}/patrones.md` | Siempre (naming, SOLID, validación) |
| `skills/{stack}/build-system.md` | Siempre (Gradle/package.json) |
| `skills/{stack}/api-design.md` | Si tiene endpoints REST |
| `skills/{stack}/integraciones-db.md` | Si tiene base de datos |
| `skills/{stack}/integraciones-mensajeria.md` | Si tiene colas/eventos |
| `skills/{stack}/seguridad.md` | Siempre |
| `skills/{stack}/resiliencia.md` | Si consume APIs externas |
| `skills/{stack}/testing.md` | Siempre |
| `skills/{stack}/observabilidad.md` | Siempre |

**Paso 2.4: Aplicar convenciones**

Cargar y aplicar las convenciones transversales:
- `convenciones/_all/validacion-inputs.md` — ya ejecutado en Fase 1
- `convenciones/_all/estrategia-generacion.md` — guía el orden inside-out de Fase 3
- `convenciones/_all/documentacion-api.md` — para generar entry-points documentados
- `convenciones/_all/patrones-diseno.md` — mock libs, thin interfaces, gradle.properties

---

### Fase 3: Generación de Código (Inside-Out)

Seguir estrictamente la estrategia definida en `convenciones/_all/estrategia-generacion.md`: generar desde el dominio hacia afuera.

**Paso 3.1: Definir scaffold**

Qué hacer:
- Crear la estructura completa de carpetas según `skills/{stack}/arquetipo.md`
- Generar archivos de build según `skills/{stack}/build-system.md`:
  - `build.gradle.kts` (o `package.json`) con dependencias
  - `settings.gradle.kts` con módulos
  - `gradle/libs.versions.toml` (version catalog)
  - `gradle.properties` con versiones de plugins
- Generar `lombok.config` (si Java) con `lombok.addLombokGeneratedAnnotation = true`
- Generar `Dockerfile` multi-stage (build + runtime)
- Generar `.gitignore` apropiado

Cómo verificar:
- Ejecutar `./gradlew compileJava` (o `npm run build`) — el proyecto vacío DEBE compilar sin errores

**Paso 3.2: Generar domain/model**

Qué hacer:
- Crear entidades de dominio como POJOs puros (sin anotaciones de framework)
- Crear value objects inmutables
- Crear excepciones de dominio (extienden RuntimeException, con código de error)
- Crear enums de dominio
- Aplicar naming según `skills/{stack}/patrones.md`

Cómo verificar:
- Las clases de dominio NO importan nada de Spring, JPA, Lombok de infraestructura
- Cada entidad tiene sus invariantes validados en constructor

**Paso 3.3: Generar domain/ports**

Qué hacer:
- Crear interfaces de puertos de salida (driven ports):
  - Java: `I{Nombre}Gateway` (prefijo I, sufijo Gateway)
  - TypeScript: `{Nombre}Gateway` (sin prefijo I)
- Definir firmas basadas en el contrato API y las integraciones identificadas
- Un puerto por responsabilidad (Single Responsibility)

Cómo verificar:
- Los puertos solo usan tipos del dominio (no DTOs de infraestructura)
- Cada puerto tiene una responsabilidad clara y acotada

**Paso 3.4: Generar domain/usecases**

Qué hacer:
- Crear un UseCase por operación de negocio (1 clase = 1 operación)
- Inyectar puertos por constructor (no field injection)
- Implementar lógica de negocio según diagramas de secuencia y reglas
- NO usar anotaciones de framework (@Service, @Component, etc.)
- Nombrar: `{Accion}{Entidad}UseCase` (ej: `CreateOrderUseCase`)

Cómo verificar:
- Cada UseCase tiene un único método público `execute()`
- No hay imports de Spring/framework en el paquete de dominio
- La lógica refleja los diagramas de secuencia proporcionados

**Paso 3.5: Generar infrastructure/driven-adapters**

Qué hacer:
- Crear adaptadores de persistencia (implementan puertos de DB):
  - Entity JPA/Mongo con anotaciones de persistencia
  - Repository interface (Spring Data)
  - Adapter class que implementa el puerto e inyecta el repository
  - Mapper MapStruct (Java) o función mapper (TypeScript) entre entity y domain model
- Crear adaptadores de APIs externas (implementan puertos de servicios):
  - DTO de request/response del servicio externo
  - Client class con WebClient/RestClient configurado
  - Circuit breaker y retry según `skills/{stack}/resiliencia.md`
  - Mapper entre DTO externo y domain model
- Crear adaptadores de mensajería (si aplica):
  - Producer/Publisher con serialización
  - Consumer/Listener con deserialización y error handling

Cómo verificar:
- Cada adapter implementa exactamente un puerto del dominio
- Los mappers no tienen lógica de negocio (solo transformación)
- Los DTOs de infraestructura son independientes del dominio

**Paso 3.6: Generar infrastructure/entry-points**

Qué hacer:
- Crear controllers/handlers/routers según el stack y `skills/{stack}/api-design.md`
- Crear DTOs de request/response:
  - Java: Records inmutables con validación Bean Validation
  - TypeScript: types/interfaces con validación Zod/class-validator
- Crear mappers REST (DTO ↔ domain model)
- Implementar validación de inputs en la capa de entry-point
- Implementar global error handler siguiendo RFC 7807 (Problem Details)
- Agregar anotaciones OpenAPI `@Operation`, `@ApiResponse` (si Java Spring)
- Documentar según `convenciones/_all/documentacion-api.md`

Cómo verificar:
- Los controllers NO contienen lógica de negocio (solo delegan al UseCase)
- Todos los endpoints del contrato OpenAPI están implementados
- El error handler cubre todos los códigos de error definidos en inputs

**Paso 3.7: Generar application**

Qué hacer:
- Crear `MainApplication` con `@SpringBootApplication` (o equivalente)
- Crear `UseCasesConfig`:
  - Registro automático de UseCases con component scan por regex
  - O registro manual con `@Bean` si se prefiere explícito
- Crear configuración de clientes HTTP (WebClient/RestClient beans)
- Crear `application.yml` con profiles:
  - `default` — configuración base
  - `local` — para desarrollo local (H2, mocks)
  - `dev`, `qa`, `prod` — por ambiente (placeholders para Parameter Store)

Cómo verificar:
- La aplicación arranca sin errores con profile `local`
- Todos los beans se resuelven correctamente (no hay dependencias circulares)

**Paso 3.8: Generar mock de librerías corporativas (si aplica)**

Qué hacer (solo si el cliente tiene librerías corporativas que no están en Maven Central):
- Crear módulo `{client}-lib-mocks` en el proyecto
- Implementar mocks funcionales:
  - Pass-through para librerías de logging/tracing
  - In-memory para librerías de caché
  - No-op para librerías de métricas
- Aplicar según `convenciones/_all/patrones-diseno.md`

Cómo verificar:
- El proyecto compila sin necesidad de acceso al Nexus/Artifactory del cliente
- Los mocks implementan las mismas interfaces que las librerías reales

---

### Fase 4: Testing

**Paso 4.1: Generar tests unitarios**

Qué hacer:
- Tests para cada UseCase:
  - Mock de todos los puertos (Mockito/Jest)
  - Caso feliz + casos de error
  - Verificar interacciones con puertos
- Tests para mappers:
  - Verificar transformación completa de campos
  - Verificar manejo de nulls/opcionales
- Tests para validaciones de dominio:
  - Verificar que invariantes se cumplen
  - Verificar excepciones con datos inválidos

Aplicar: `skills/{stack}/testing.md`

**Paso 4.2: Generar tests de integración**

Qué hacer:
- Tests para entry-points:
  - Java Spring: `@WebMvcTest` con MockMvc / `@WebFluxTest` con WebTestClient
  - Node: Supertest con app levantada
  - Verificar status codes, headers, body de response
  - Verificar validación de inputs (400 Bad Request)
- Tests para driven-adapters con Testcontainers:
  - PostgreSQL/MySQL/MongoDB container
  - Verificar CRUD completo
  - Verificar queries complejas

**Paso 4.3: Generar tests de arquitectura (si Java)**

Qué hacer:
- ArchUnit tests que verifican:
  - El paquete `domain` NO importa nada de `infrastructure`
  - El paquete `domain` NO importa Spring Framework
  - Las clases en `usecases` terminan en `UseCase`
  - Las interfaces en `ports` siguen la convención de naming
  - No hay dependencias cíclicas entre paquetes

---

### Fase 5: Verificación

**Paso 5.1: Compilación**

Qué hacer:
- Ejecutar build completo: `./gradlew build` (o `npm run build`)
- Si falla → leer el error, diagnosticar la causa raíz, corregir
- Repetir hasta que compile limpio (máximo 3 intentos, luego reportar al pragmático)

**Paso 5.2: Tests**

Qué hacer:
- Ejecutar suite completa: `./gradlew test` (o `npm test`)
- Si falla → analizar el test fallido, corregir implementación o test
- Todos los tests DEBEN pasar en verde

**Paso 5.3: Cobertura**

Qué hacer:
- Ejecutar reporte de cobertura (JaCoCo/Istanbul)
- Verificar umbrales mínimos:
  - Dominio (usecases + model): ≥ 85% line coverage
  - General (todo el proyecto): ≥ 70% line coverage
- Si está por debajo → agregar tests para cubrir los gaps

**Paso 5.4: Resumen final**

Presentar al pragmático un resumen estructurado:

```
## Resultado de la Generación

### Estructura generada
- [árbol de directorios principal]

### Endpoints disponibles
- [lista de endpoints con método HTTP y path]

### Integraciones configuradas
- [bases de datos, APIs externas, colas]

### Cobertura de tests
- Dominio: X%
- General: Y%
- Tests unitarios: N
- Tests integración: M

### Próximos pasos recomendados
- [configurar CI/CD]
- [configurar ambientes]
- [revisar secrets en Parameter Store]
```

---

## Criterios de Finalización

El workflow se considera completo cuando:
1. ✅ Todos los inputs obligatorios fueron validados
2. ✅ La estructura del proyecto sigue el arquetipo del stack
3. ✅ El código compila sin errores ni warnings
4. ✅ Todos los tests pasan en verde
5. ✅ La cobertura cumple los umbrales mínimos
6. ✅ Todos los endpoints del contrato están implementados
7. ✅ El error handling cubre todos los casos definidos
8. ✅ La documentación OpenAPI está generada (si aplica)
9. ✅ El pragmático recibió el resumen final
