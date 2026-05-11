---
id: backend-workflow-new-feature
version: "1.0"
scope: chapter
type: workflow
chapter: backend
---

# Workflow: New Feature — Agregar Funcionalidad a Microservicio Existente

## Cuándo usar este workflow

Usa este workflow cuando:
- Existe un microservicio funcional y se quiere agregar nueva funcionalidad
- El servicio existente ya compila y tiene tests pasando
- Se tiene una especificación funcional clara del feature a agregar
- El contrato API se EXTIENDE (nuevos endpoints o campos opcionales) pero NO se rompe

NO uses este workflow cuando:
- No existe código previo → usa `greenfield.md`
- Se quiere reestructurar sin agregar funcionalidad → usa `tech-debt.md`
- El servicio existente no compila o tiene tests rotos → primero estabilizar

**Regla fundamental**: "Extender sin contaminar" — los módulos existentes no se modifican innecesariamente. Solo se agrega lo nuevo y se integra con la estructura existente.

---

## Pasos

### Fase 1: Recepción y Validación de Inputs

**Paso 1.1: Identificar el JTBD**
- El pragmático indica que quiere agregar funcionalidad a un microservicio existente
- Confirmar que es New Feature: el servicio existe, funciona, y se quiere extender
- Confirmar que el servicio actual compila y sus tests pasan

**Paso 1.2: Solicitar inputs obligatorios**

Solicitar al pragmático los inputs obligatorios. Aplicar `convenciones/_all/validacion-inputs.md`:

| # | Input | Qué debe contener |
|---|-------|-------------------|
| 1 | Repositorio existente | URL del repo o código fuente del servicio actual (DEBE compilar) |
| 2 | Especificación funcional del feature | Qué hace el feature, reglas de negocio, flujos, criterios de aceptación |
| 3 | Contrato API actualizado | OpenAPI/Swagger con los nuevos endpoints/campos agregados |
| 4 | Diagramas del feature | Secuencia del nuevo flujo, impacto en componentes existentes |
| 5 | Nuevas integraciones (si aplica) | Contratos de APIs externas nuevas, nuevas colas, nuevas tablas |
| 6 | Manejo de errores del feature | Nuevos códigos de error, mensajes, mapeo de errores |

Para cada input:
- Si está presente y completo → marcar como ✅ y continuar
- Si está incompleto → indicar QUÉ falta específicamente y solicitar
- Si está ausente → solicitar explicando POR QUÉ es necesario
- **NUNCA proceder sin los inputs completos**

**Paso 1.3: Confirmar inputs opcionales**

Preguntar si aplican:
- **Nueva base de datos/tablas**: esquema DDL de tablas nuevas, migraciones
- **Nuevas colas de mensajes**: topics/queues nuevos, formato de mensajes
- **Nuevos recursos cloud**: S3 buckets, DynamoDB tables adicionales
- **Cambios en configuración**: nuevas variables de entorno, nuevos secrets

Si el pragmático confirma que aplican → se vuelven obligatorios para esta ejecución.

**Paso 1.4: Validar compatibilidad del contrato**

Verificar que el contrato actualizado es BACKWARD COMPATIBLE:
- ✅ Nuevos endpoints agregados → OK
- ✅ Nuevos campos opcionales en responses existentes → OK
- ✅ Nuevos query params opcionales → OK
- ❌ Campos removidos de responses existentes → BREAKING CHANGE, rechazar
- ❌ Campos obligatorios nuevos en requests existentes → BREAKING CHANGE, rechazar
- ❌ Endpoints existentes removidos o renombrados → BREAKING CHANGE, rechazar

Si hay breaking changes → informar al pragmático y solicitar corrección del contrato.

---

### Fase 2: Análisis del Código Existente

**Paso 2.1: Leer y entender el servicio actual**

Qué hacer:
- Leer la estructura completa del proyecto existente
- Identificar el patrón arquitectónico actual:
  - Si es hexagonal → perfecto, extender siguiendo la misma estructura
  - Si NO es hexagonal → evaluar si se puede agregar el feature de forma aislada
  - Si la estructura actual impide agregar el feature limpiamente → **sugerir primero Tech Debt**
- Identificar el stack actual (framework, versión, build tool)

Qué documentar:
- Estructura de carpetas actual
- Stack y versiones
- Patrón arquitectónico identificado

**Paso 2.2: Analizar impacto del feature**

Qué hacer:
- Determinar qué módulos/paquetes existentes se ven afectados:
  - ¿Se necesitan nuevos UseCases? → listar
  - ¿Se necesitan nuevos puertos? → listar
  - ¿Se necesitan nuevos adapters? → listar
  - ¿Se necesitan nuevos endpoints? → listar
  - ¿Se modifican UseCases existentes? → listar y justificar por qué es necesario
- Identificar puntos de integración con código existente

Qué documentar:
- Mapa de impacto: qué es NUEVO vs qué se MODIFICA
- Justificación para cada modificación a código existente

**Paso 2.3: Verificar estado del servicio**

Qué hacer:
- Ejecutar build: `./gradlew build` (o `npm run build`)
- Ejecutar tests: `./gradlew test` (o `npm test`)
- Si el build falla → DETENER. Informar al pragmático que el servicio debe estabilizarse primero
- Si tests fallan → DETENER. Los tests existentes deben pasar antes de agregar features

Qué verificar:
- ✅ Build exitoso
- ✅ Todos los tests existentes pasan
- ✅ No hay warnings críticos

**Paso 2.4: Cargar steering y skills**

Basado en el stack identificado:
- Aplicar `steering/_all/` — perspectiva, límites, decisiones
- Aplicar `steering/{stack}/` — límites del stack específico
- Cargar skills relevantes para el feature:
  - `skills/{stack}/patrones.md` — siempre
  - `skills/{stack}/api-design.md` — si hay nuevos endpoints
  - `skills/{stack}/integraciones-db.md` — si hay nuevas tablas
  - `skills/{stack}/integraciones-mensajeria.md` — si hay nuevas colas
  - `skills/{stack}/resiliencia.md` — si hay nuevas APIs externas
  - `skills/{stack}/testing.md` — siempre
  - `skills/{stack}/seguridad.md` — si el feature maneja datos sensibles

---

### Fase 3: Generación Incremental (Solo lo Nuevo)

**Regla**: Solo generar código NUEVO. No refactorizar código existente a menos que sea estrictamente necesario para integrar el feature. Seguir `convenciones/_all/estrategia-generacion.md` (inside-out).

**Paso 3.1: Generar nuevos domain/model (si aplica)**

Qué hacer:
- Crear NUEVAS entidades de dominio que el feature requiere
- Crear nuevos value objects
- Crear nuevas excepciones de dominio específicas del feature
- Crear nuevos enums

Qué NO hacer:
- NO modificar entidades existentes a menos que el feature lo requiera explícitamente
- Si se necesita extender una entidad existente → agregar campos, NO reestructurar

Cómo verificar:
- Las nuevas clases siguen las mismas convenciones que las existentes
- No hay conflictos con el modelo existente

**Paso 3.2: Generar nuevos domain/ports (si aplica)**

Qué hacer:
- Crear NUEVAS interfaces de puertos para las nuevas integraciones
- Si un puerto existente necesita un método nuevo → agregarlo a la interfaz existente
- Aplicar naming consistente con los puertos existentes

Qué NO hacer:
- NO renombrar puertos existentes
- NO cambiar firmas de métodos existentes

Cómo verificar:
- Los nuevos puertos siguen la misma convención de naming
- Los métodos agregados a puertos existentes no rompen implementaciones actuales

**Paso 3.3: Generar nuevos domain/usecases**

Qué hacer:
- Crear NUEVOS UseCases para las operaciones del feature
- Cada UseCase nuevo sigue el patrón de los existentes (1 clase = 1 operación)
- Inyectar puertos (existentes y nuevos) por constructor
- Implementar la lógica de negocio del feature según la especificación

Qué NO hacer:
- NO modificar UseCases existentes a menos que sea estrictamente necesario
- Si se necesita reutilizar lógica → extraer a un domain service compartido

Cómo verificar:
- Los nuevos UseCases son independientes de los existentes
- La lógica implementa correctamente la especificación funcional

**Paso 3.4: Generar nuevos infrastructure/driven-adapters**

Qué hacer:
- Crear NUEVOS adaptadores para nuevas integraciones:
  - Nueva tabla → nuevo adapter de persistencia (entity, repository, adapter, mapper)
  - Nueva API externa → nuevo client adapter (DTO, client, mapper)
  - Nueva cola → nuevo adapter de mensajería
- Si un adapter existente necesita un método nuevo → agregarlo

Qué NO hacer:
- NO reestructurar adapters existentes
- NO cambiar la configuración de conexiones existentes

Cómo verificar:
- Los nuevos adapters implementan los nuevos puertos
- Los adapters existentes modificados siguen pasando sus tests

**Paso 3.5: Generar nuevos infrastructure/entry-points**

Qué hacer:
- Crear NUEVOS controllers/handlers para los nuevos endpoints
- Crear DTOs de request/response para el feature
- Crear mappers REST para los nuevos DTOs
- Agregar los nuevos errores al global error handler existente
- Documentar con anotaciones OpenAPI (si Java Spring)
- Aplicar `convenciones/_all/documentacion-api.md`

Qué NO hacer:
- NO modificar controllers existentes a menos que sea necesario
- NO cambiar DTOs existentes (solo agregar campos opcionales si el contrato lo requiere)

Cómo verificar:
- Los nuevos endpoints coinciden con el contrato API actualizado
- Los endpoints existentes siguen funcionando exactamente igual
- El error handler cubre los nuevos códigos de error

**Paso 3.6: Actualizar application/configuration**

Qué hacer:
- Registrar nuevos beans (UseCases, adapters) en la configuración
- Agregar nuevas propiedades en application.yml (sin modificar las existentes)
- Agregar nuevas dependencias en build.gradle/package.json (si el feature las requiere)
- Configurar nuevos clientes HTTP (si hay nuevas APIs externas)

Qué NO hacer:
- NO cambiar versiones de dependencias existentes
- NO modificar configuración de beans existentes
- NO cambiar profiles existentes (solo agregar propiedades nuevas)

Cómo verificar:
- La aplicación arranca correctamente con la nueva configuración
- Los beans existentes no se ven afectados

**Paso 3.7: Migraciones de base de datos (si aplica)**

Qué hacer:
- Crear scripts de migración (Flyway/Liquibase) para nuevas tablas
- Si se agregan columnas a tablas existentes → migración con ALTER TABLE
- Las migraciones deben ser backward compatible (nullable, con defaults)

Qué NO hacer:
- NO modificar migraciones existentes
- NO hacer DROP de columnas o tablas existentes
- NO agregar constraints que rompan datos existentes

Cómo verificar:
- Las migraciones se ejecutan sin errores sobre la base actual
- Los datos existentes no se ven afectados

---

### Fase 4: Testing del Feature

**Paso 4.1: Generar tests unitarios del feature**

Qué hacer:
- Tests para cada NUEVO UseCase:
  - Mock de puertos
  - Caso feliz + casos de error del feature
  - Verificar interacciones con puertos
- Tests para nuevos mappers
- Tests para nuevas validaciones de dominio

Aplicar: `skills/{stack}/testing.md`

**Paso 4.2: Generar tests de integración del feature**

Qué hacer:
- Tests para NUEVOS entry-points:
  - Verificar status codes, headers, body
  - Verificar validación de inputs (400 Bad Request)
  - Verificar errores específicos del feature
- Tests para NUEVOS driven-adapters:
  - Testcontainers para nuevas tablas
  - Verificar operaciones CRUD del feature

**Paso 4.3: Verificar tests existentes**

Qué hacer:
- Ejecutar TODA la suite de tests existente
- TODOS los tests previos DEBEN seguir pasando
- Si un test existente falla → es un bug introducido por el feature, corregir
- NO modificar tests existentes para que pasen (eso oculta regresiones)

**CRÍTICO**: Si tests existentes fallan después de agregar el feature, significa que se contaminó código existente. Revisar y corregir.

**Paso 4.4: Generar tests de no-regresión de endpoints existentes**

Qué hacer:
- Verificar que los endpoints existentes responden exactamente igual:
  - Mismos status codes
  - Mismos response bodies
  - Mismos tiempos de respuesta (no degradación significativa)
- Si hay degradación → investigar si el feature introdujo overhead

---

### Fase 5: Verificación

**Paso 5.1: Compilación**

Qué hacer:
- Ejecutar build completo: `./gradlew build` (o `npm run build`)
- Si falla → diagnosticar y corregir
- Verificar que no hay nuevos warnings

**Paso 5.2: Tests completos**

Qué hacer:
- Ejecutar TODA la suite: `./gradlew test` (o `npm test`)
- Tests existentes: DEBEN pasar (no-regresión)
- Tests nuevos: DEBEN pasar (feature funciona)
- Si falla cualquier test → corregir antes de continuar

**Paso 5.3: Cobertura**

Qué hacer:
- Verificar cobertura del código NUEVO:
  - Nuevos UseCases: ≥ 85% line coverage
  - Nuevos adapters: ≥ 70% line coverage
- Verificar que la cobertura GENERAL no bajó respecto al estado anterior
- Si bajó → agregar tests para compensar

**Paso 5.4: Validación de contrato**

Qué hacer:
- Generar el Swagger completo del servicio actualizado
- Verificar que:
  - Los endpoints NUEVOS están presentes y correctos
  - Los endpoints EXISTENTES no cambiaron
  - El contrato es backward compatible
- Comparar con el contrato actualizado proporcionado por el pragmático

**Paso 5.5: Resumen final**

Presentar al pragmático:

```
## Resultado del Feature

### Feature implementado
- [nombre y descripción breve del feature]

### Código nuevo generado
- UseCases: [lista]
- Adapters: [lista]
- Endpoints: [lista con método HTTP y path]
- Migraciones: [lista de scripts]

### Código existente modificado
- [lista de archivos modificados con justificación]
- (idealmente vacía o mínima)

### Nuevos endpoints disponibles
| Método | Path | Descripción |
|--------|------|-------------|
| ... | ... | ... |

### Tests
- Tests nuevos: N passing
- Tests existentes: M passing (sin regresiones)
- Cobertura nuevo código: X%
- Cobertura general: Y% (antes: Z%)

### Integraciones nuevas
- [bases de datos, APIs, colas agregadas]

### Próximos pasos recomendados
- [probar en ambiente de QA]
- [validar con equipo de producto]
- [actualizar documentación de API pública]
```

---

## Criterios de Finalización

El workflow se considera completo cuando:
1. ✅ Todos los inputs obligatorios fueron validados
2. ✅ El feature está implementado según la especificación funcional
3. ✅ El código nuevo sigue la arquitectura del servicio existente
4. ✅ El build compila sin errores
5. ✅ TODOS los tests pasan (nuevos Y existentes)
6. ✅ No hay regresiones en endpoints existentes
7. ✅ El contrato API es backward compatible
8. ✅ La cobertura cumple umbrales mínimos
9. ✅ El código existente se modificó lo mínimo necesario (o nada)
10. ✅ El pragmático recibió el resumen final

---

## Decisión: ¿Feature o Tech Debt primero?

Si durante el análisis (Fase 2) se detecta que:
- El servicio NO tiene arquitectura limpia
- Agregar el feature requiere modificar extensivamente código existente
- La estructura actual impide una integración limpia

Entonces **DETENER** y sugerir al pragmático:

> "El servicio actual no tiene una estructura que permita agregar este feature de forma limpia. Recomiendo ejecutar primero el workflow de Tech Debt para refactorizar la arquitectura, y luego agregar el feature sobre la estructura nueva. ¿Procedemos con Tech Debt primero?"

Si el pragmático acepta → ejecutar `tech-debt.md` primero, luego volver a `new-feature.md`.
Si el pragmático rechaza → proceder con el feature de la mejor forma posible, documentando las limitaciones.
