---
id: backend-workflow-tech-debt
version: "1.0"
scope: chapter
type: workflow
chapter: backend
---

# Workflow: Tech Debt — Refactorizar Microservicio Existente

## Cuándo usar este workflow

Usa este workflow cuando:
- Existe un microservicio funcional que necesita ser refactorizado
- El objetivo es mejorar la arquitectura interna SIN cambiar el comportamiento externo
- Se quiere migrar a arquitectura hexagonal, actualizar stack, o eliminar deuda técnica
- El contrato API (Swagger/OpenAPI) DEBE permanecer idéntico antes y después

NO uses este workflow cuando:
- No existe código previo → usa `greenfield.md`
- Se quiere agregar funcionalidad nueva → usa `new-feature.md`
- Solo se necesita un hotfix puntual → no requiere workflow completo

**Regla fundamental**: La refactorización es INVISIBLE para el consumidor del servicio. El Swagger antes y después DEBE ser idéntico byte a byte (salvo metadata de versión).

---

## Pasos

### Fase 1: Recepción y Validación de Inputs

**Paso 1.1: Identificar el JTBD**
- El pragmático indica que quiere refactorizar un microservicio existente
- Confirmar que es Tech Debt: existe código funcional que se quiere reestructurar
- Confirmar que NO se va a cambiar el comportamiento externo del servicio

**Paso 1.2: Solicitar inputs obligatorios**

Solicitar al pragmático los inputs obligatorios para refactorización. Aplicar `convenciones/_all/validacion-inputs.md`:

| # | Input | Qué debe contener |
|---|-------|-------------------|
| 1 | Repositorio existente | URL del repo o código fuente completo del servicio actual |
| 2 | Tech Stack OBJETIVO | Lenguaje, framework, versión, build tool, arquitectura destino |
| 3 | Contrato actual del servicio | OpenAPI/Swagger 3.x que NO debe cambiar (es el contrato de referencia) |
| 4 | APIs externas que consume | Contratos actuales con auth, timeouts (pueden cambiar la implementación, no el contrato) |
| 5 | Catálogo de configuración | Variables de entorno actuales + nuevas si cambia el esquema de config |
| 6 | Alcance de la refactorización | Qué se quiere mejorar: arquitectura, stack, performance, testing, todo |

Para cada input:
- Si está presente y completo → marcar como ✅ y continuar
- Si está incompleto → indicar QUÉ falta específicamente y solicitar
- Si está ausente → solicitar explicando POR QUÉ es necesario
- **NUNCA proceder sin los inputs completos**

**Paso 1.3: Confirmar inputs opcionales**

Preguntar si aplican:
- **Restricciones de migración**: ¿hay código que NO se puede tocar? ¿dependencias que deben mantenerse?
- **Librerías corporativas**: ¿hay libs internas que se deben mantener o reemplazar?
- **Base de datos**: ¿cambia el esquema? ¿se migra de motor? ¿se mantiene igual?
- **Deadline o fases**: ¿se hace todo de una vez o en fases incrementales?

Si el pragmático confirma que aplican → se vuelven obligatorios para esta ejecución.

**Paso 1.4: Resolver Tech Stack OBJETIVO**

Definir claramente el estado final deseado:
- **Stack actual** → documentar (ej: Java 11 + Spring Boot 2.x + Maven + monolítico)
- **Stack objetivo** → definir (ej: Java 21 + Spring Boot 3.x + Gradle + hexagonal)
- **Nombre del servicio** → mantener el existente o definir nuevo (kebab-case)
- **Base package** → mantener o migrar
- **Reactive vs Imperative** → definir si cambia o se mantiene

Verificar: El pragmático confirma el estado actual y el estado objetivo.

---

### Fase 2: Análisis del Código Existente

**Paso 2.1: Leer y mapear el repositorio actual**

Qué hacer:
- Leer la estructura completa del proyecto existente
- Identificar el patrón arquitectónico actual (MVC, capas, hexagonal parcial, monolítico)
- Mapear los paquetes/módulos y sus responsabilidades
- Identificar el entry point (main class, configuración)

Qué documentar:
- Estructura de carpetas actual
- Dependencias (build file)
- Configuración (application.yml/properties)

**Paso 2.2: Identificar la lógica de negocio**

Qué hacer:
- Localizar TODA la lógica de negocio dispersa en el código:
  - En controllers (lógica que debería estar en usecases)
  - En services (lógica mezclada con infraestructura)
  - En utils/helpers (lógica de dominio disfrazada)
  - En stored procedures (si aplica)
- Crear un inventario de reglas de negocio encontradas

Qué documentar:
- Lista de operaciones de negocio (futuros UseCases)
- Reglas de validación encontradas
- Transformaciones de datos con lógica

**Paso 2.3: Mapear dependencias e integraciones**

Qué hacer:
- Identificar todas las integraciones externas:
  - Bases de datos (queries, entities, repositories)
  - APIs externas (clientes HTTP, DTOs)
  - Colas de mensajes (producers, consumers)
  - Servicios cloud (S3, cache, etc.)
- Mapear qué puertos se necesitarán en la nueva arquitectura

Qué documentar:
- Lista de integraciones → futuros driven-adapters
- Lista de endpoints expuestos → futuros entry-points
- Dependencias entre componentes

**Paso 2.4: Extraer el contrato API actual**

Qué hacer:
- Si existe Swagger/OpenAPI → usarlo como referencia inmutable
- Si NO existe → generarlo a partir del código actual (endpoints, DTOs, status codes)
- Este contrato es la LÍNEA BASE: todo lo que se genere debe producir exactamente el mismo contrato

Qué verificar:
- El contrato documenta TODOS los endpoints actuales
- Incluye todos los status codes posibles
- Incluye todos los schemas de request/response

**Paso 2.5: Determinar el stack objetivo**

Basado en el tech stack objetivo definido en Fase 1, seleccionar:

| Stack | Cuándo aplica |
|-------|---------------|
| `java-spring` | Java + Spring MVC (imperativo) |
| `java-webflux` | Java + Spring WebFlux (reactivo) |
| `node-express` | Node.js/TypeScript + Express |
| `node-lambda` | Node.js/TypeScript + AWS Lambda (serverless) |

**Paso 2.6: Cargar steering y skills**

Aplicar automáticamente:
- `steering/_all/` — perspectiva, límites, decisiones obligatorias
- `steering/{stack}/` — límites y decisiones del stack objetivo
- Skills según el mismo criterio que en `greenfield.md` Paso 2.3
- `convenciones/_all/estrategia-generacion.md` — guía la migración inside-out

---

### Fase 3: Migración de Código (Inside-Out)

**Regla**: Migrar capa por capa, empezando por el dominio. En cada paso, el código existente sigue funcionando hasta que se reemplaza completamente.

**Paso 3.1: Crear scaffold del proyecto objetivo**

Qué hacer:
- Crear la estructura de carpetas según `skills/{stack}/arquetipo.md`
- Generar archivos de build con las dependencias del stack objetivo
- Generar configuración base (application.yml con profiles)
- Generar gradle.properties, lombok.config, Dockerfile (según aplique)

Cómo verificar:
- El scaffold vacío compila sin errores

**Paso 3.2: Migrar domain/model**

Qué hacer:
- Extraer entidades de dominio del código existente
- Limpiar: remover anotaciones de framework (JPA, Lombok de infraestructura, Jackson)
- Convertir a POJOs puros con invariantes en constructor
- Crear value objects donde corresponda
- Crear excepciones de dominio (reemplazar excepciones genéricas)
- Crear enums de dominio

Cómo verificar:
- Las entidades de dominio NO tienen imports de infraestructura
- La lógica de negocio que estaba en las entidades se preserva

**Paso 3.3: Migrar domain/ports**

Qué hacer:
- Crear interfaces de puertos basadas en el mapeo de Paso 2.3:
  - Un puerto por cada integración externa identificada
  - Un puerto por cada repositorio de datos
- Definir firmas usando SOLO tipos del dominio
- Aplicar naming: `I{Nombre}Gateway` (Java) / `{Nombre}Gateway` (TypeScript)

Cómo verificar:
- Los puertos cubren TODAS las integraciones identificadas en Fase 2
- No hay tipos de infraestructura en las firmas

**Paso 3.4: Migrar domain/usecases**

Qué hacer:
- Crear un UseCase por cada operación de negocio identificada en Paso 2.2
- Extraer la lógica de negocio de:
  - Controllers → mover al UseCase correspondiente
  - Services → separar lógica de negocio de lógica de infraestructura
  - Utils → mover lógica de dominio al UseCase o al model
- Inyectar puertos por constructor
- NO usar anotaciones de framework

Cómo verificar:
- TODA la lógica de negocio identificada en Paso 2.2 está en UseCases
- Los UseCases no tienen dependencias de infraestructura
- El comportamiento es equivalente al original

**Paso 3.5: Migrar infrastructure/driven-adapters**

Qué hacer:
- Crear adaptadores que implementan los puertos del dominio:
  - Persistencia: nueva entity con anotaciones, repository, adapter, mapper
  - APIs externas: nuevo client con WebClient/RestClient, DTOs, mapper
  - Mensajería: nuevo producer/consumer con configuración actualizada
- Mantener la misma lógica de acceso a datos (queries equivalentes)
- Implementar resiliencia según `skills/{stack}/resiliencia.md`

Cómo verificar:
- Cada adapter implementa exactamente un puerto
- Las queries producen los mismos resultados que las originales
- Los mappers transforman correctamente entre domain y infrastructure

**Paso 3.6: Migrar infrastructure/entry-points**

Qué hacer:
- Crear controllers/handlers nuevos que:
  - Exponen EXACTAMENTE los mismos endpoints (paths, methods, params)
  - Usan EXACTAMENTE los mismos DTOs de request/response (o equivalentes)
  - Retornan EXACTAMENTE los mismos status codes
  - Producen EXACTAMENTE el mismo formato de errores
- Crear DTOs de request/response (Records en Java)
- Crear mappers REST
- Implementar global error handler (RFC 7807) que mapea los mismos errores

**CRÍTICO**: El contrato externo NO cambia. Los consumidores del servicio no deben notar la refactorización.

Cómo verificar:
- Generar el Swagger del nuevo código
- Comparar byte a byte con el Swagger original (Paso 2.4)
- Si hay diferencias → corregir hasta que sean idénticos

**Paso 3.7: Migrar application/configuration**

Qué hacer:
- Crear MainApplication con configuración del stack objetivo
- Crear UseCasesConfig con registro de beans
- Migrar configuración de application.yml/properties al nuevo formato
- Mantener los mismos nombres de variables de entorno (o documentar cambios)

Cómo verificar:
- La aplicación arranca correctamente
- Todos los beans se resuelven

**Paso 3.8: Migrar/crear mock de librerías corporativas (si aplica)**

Qué hacer:
- Si el código original usa librerías corporativas:
  - Crear módulo de mocks según `convenciones/_all/patrones-diseno.md`
  - Implementar mocks funcionales equivalentes
- Si se reemplazan por librerías estándar → documentar el reemplazo

---

### Fase 4: Testing (No-Regresión)

**Paso 4.1: Generar tests unitarios**

Qué hacer:
- Tests para cada UseCase migrado:
  - Replicar los escenarios del código original
  - Agregar casos que el original no cubría
- Tests para mappers (transformación correcta)
- Tests para validaciones de dominio

Aplicar: `skills/{stack}/testing.md`

**Paso 4.2: Generar tests de integración**

Qué hacer:
- Tests para entry-points que verifican:
  - Mismos endpoints responden igual que antes
  - Mismos status codes para mismos inputs
  - Mismos formatos de error
- Tests para driven-adapters con Testcontainers:
  - Mismas queries producen mismos resultados

**Paso 4.3: Generar tests de contrato (no-regresión)**

Qué hacer:
- Test automatizado que:
  1. Carga el Swagger original (línea base de Paso 2.4)
  2. Genera el Swagger del código nuevo
  3. Compara ambos
  4. FALLA si hay cualquier diferencia en paths, methods, schemas, status codes
- Este test es la garantía de no-regresión

**Paso 4.4: Generar tests de arquitectura (si Java)**

Qué hacer:
- ArchUnit tests que verifican la nueva estructura:
  - `domain` no importa `infrastructure`
  - `domain` no importa Spring Framework
  - Naming conventions se cumplen
  - No hay dependencias cíclicas

---

### Fase 5: Verificación y Comparación

**Paso 5.1: Compilación**

Qué hacer:
- Ejecutar build completo: `./gradlew build` (o `npm run build`)
- Si falla → diagnosticar y corregir
- Repetir hasta que compile limpio

**Paso 5.2: Tests**

Qué hacer:
- Ejecutar suite completa: `./gradlew test` (o `npm test`)
- TODOS los tests deben pasar, especialmente los de no-regresión
- Si falla un test de contrato → la migración tiene un bug, corregir

**Paso 5.3: Comparación de contrato API**

Qué hacer:
- Generar el OpenAPI/Swagger del código nuevo
- Comparar con el original:
  - Paths: idénticos
  - Methods: idénticos
  - Request schemas: idénticos
  - Response schemas: idénticos
  - Status codes: idénticos
  - Error formats: idénticos
- Si hay CUALQUIER diferencia → es un bug de migración, corregir

**Paso 5.4: Cobertura**

Qué hacer:
- Verificar umbrales mínimos:
  - Dominio: ≥ 85% line coverage
  - General: ≥ 70% line coverage
- La cobertura debe ser IGUAL o MEJOR que la del código original

**Paso 5.5: Resumen final**

Presentar al pragmático:

```
## Resultado de la Refactorización

### Comparación Antes/Después
| Aspecto | Antes | Después |
|---------|-------|---------|
| Arquitectura | {original} | Hexagonal |
| Java version | {original} | {objetivo} |
| Build tool | {original} | {objetivo} |
| Cobertura | {original}% | {nueva}% |
| Contrato API | ✅ Sin cambios | ✅ Idéntico |

### Estructura nueva
- [árbol de directorios]

### Lógica migrada
- [lista de UseCases creados]
- [lista de adapters creados]

### Tests de no-regresión
- Test de contrato: ✅ PASS
- Tests unitarios: N passing
- Tests integración: M passing

### Deuda técnica eliminada
- [lista de mejoras realizadas]

### Próximos pasos recomendados
- [ejecutar en ambiente de QA]
- [comparar performance antes/después]
- [actualizar documentación de operaciones]
```

---

## Criterios de Finalización

El workflow se considera completo cuando:
1. ✅ El código nuevo compila sin errores
2. ✅ Todos los tests pasan (unitarios, integración, arquitectura)
3. ✅ El test de contrato (no-regresión) pasa — Swagger idéntico
4. ✅ La cobertura cumple umbrales mínimos
5. ✅ La arquitectura nueva sigue el arquetipo del stack
6. ✅ El dominio no tiene dependencias de infraestructura
7. ✅ El pragmático recibió el resumen comparativo
8. ✅ NO hay cambios visibles para los consumidores del servicio
