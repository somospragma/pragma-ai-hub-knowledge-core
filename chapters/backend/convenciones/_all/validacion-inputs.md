---
id: backend-convencion-validacion-inputs
version: "1.0"
scope: chapter
type: convencion
chapter: backend
---

# Convención: Validación de Inputs Antes de Generar Código

## Objetivo

Garantizar que NUNCA se genere código sin tener todos los inputs completos y validados. Si falta información, se PREGUNTA. Si no responde, se PREGUNTA DE NUEVO. La generación sin inputs completos está PROHIBIDA.

---

## Protocolo Paso a Paso

### Paso 1: Identificar el JTBD (Job To Be Done)

Determinar cuál es el trabajo que el pragmatic necesita ejecutar:

| JTBD | Descripción | Cuándo aplica |
|------|-------------|---------------|
| **Greenfield** | Crear un microservicio desde cero | No existe código previo |
| **Tech Debt** | Refactorizar un microservicio existente | Existe código que debe reestructurarse |
| **New Feature** | Extender un microservicio existente | Existe código funcional al que se agrega funcionalidad |

**Regla:** Si no es claro cuál JTBD aplica, PREGUNTAR al pragmatic. No asumir.

---

### Paso 2: Validar Inputs Obligatorios según el JTBD

Cada JTBD tiene inputs obligatorios documentados. Para cada input:

1. **Presente y completo** → Continuar.
2. **Presente pero incompleto** → Indicar QUÉ falta específicamente y solicitar que lo complete.
3. **Ausente** → Solicitar explícitamente, explicando POR QUÉ es necesario.

#### Inputs obligatorios por JTBD:

**Greenfield:**
- Diagramas de flujo (happy path + flujos de error)
- Tech stack
- Contrato de servicio (Swagger/OpenAPI)
- APIs externas consumidas
- Catálogo de configuración
- Manejo de errores

**Tech Debt:**
- Repositorio del microservicio en producción
- Tech stack objetivo
- Contrato API actual (Swagger)
- APIs externas consumidas
- Documentación de flujos críticos de negocio
- Catálogo de configuración
- Manejo de errores

**New Feature:**
- Repositorio del microservicio actual
- Especificación funcional del feature
- Contrato API actualizado (Swagger)
- Contratos de nuevas integraciones
- Manejo de errores del feature

---

### Paso 3: Validar Tech Stack Defaults

Los siguientes inputs técnicos son OBLIGATORIOS. Si no los proporciona el pragmatic, se usa el default del cliente. Si no hay default del cliente, se PREGUNTA:

| Input | Descripción | Default |
|-------|-------------|---------|
| Java version | Versión del JDK (17, 21) | Default del cliente en KB |
| Nombre del servicio | Nombre del artefacto Gradle (kebab-case) | DEBE ser proporcionado por el pragmatic |
| Base package | Paquete base Java (ej: `com.ficohsa`, `com.mercantil`) | Default del cliente en KB |
| Reactive vs Imperative | WebFlux (reactive) o Spring MVC (imperative) | Reactive (WebFlux) |

**Regla:** Estos inputs NO se preguntan si pueden resolverse desde la KB o desde los inputs del spec. Solo se preguntan si NO hay forma de resolverlos.

---

### Paso 4: Validar Inputs del Cliente (si aplica)

Si el pragmatic trabaja en una cuenta con inputs adicionales específicos del cliente, esos inputs TAMBIÉN deben validarse. Consultar la documentación del cliente en la KB para identificar qué inputs adicionales requiere.

---

### Paso 5: Confirmar Inputs Opcionales

Preguntar si aplican los siguientes inputs opcionales:

- **Base de datos** (tipo, esquema, stored procedures)
- **Colas de mensajes** (Kafka, SQS, RabbitMQ)
- **Recursos cloud** (S3, DynamoDB, Parameter Store)
- **Reglas de negocio** adicionales

**Regla:** Si el pragmatic dice que un input opcional aplica, ese input se convierte en OBLIGATORIO para esa ejecución y debe validarse con el mismo rigor.

---

### Paso 6: Confirmar Antes de Generar

Una vez todos los inputs están completos:

1. Presentar un RESUMEN de lo que se entendió.
2. Solicitar confirmación EXPLÍCITA antes de generar código.
3. La generación NO comienza sin confirmación.

---

## Reglas Inquebrantables

1. **NUNCA generar código sin inputs completos.**
2. **Si falta algo, PREGUNTAR.** No asumir, no inventar, no usar placeholders.
3. **Si no responde, PREGUNTAR DE NUEVO.** No proceder en silencio.
4. **Si los inputs son inconsistentes entre sí** (ej: el Swagger dice una cosa y el diagrama otra), PREGUNTAR cuál es la fuente de verdad.
5. **Si un input toma tiempo en llegar** (ej: el Swagger del equipo externo), la generación queda BLOQUEADA hasta que llegue.

---

## Ejemplo de Interacción

```
Agente: He identificado que necesitas un Greenfield. Revisando los inputs:
  ✅ Diagrama de flujo: presente
  ✅ Tech stack: Java 17, WebFlux, Gradle
  ❌ Contrato API (Swagger): NO proporcionado
  ✅ APIs externas: 2 APIs documentadas
  ❌ Manejo de errores: NO proporcionado

Necesito los siguientes inputs para continuar:
1. El contrato OpenAPI/Swagger del servicio
2. El catálogo de errores (códigos HTTP, mensajes, mapeo de errores downstream)

¿Puedes proporcionarlos?
```

---

## Fuentes

- ADR 001: Mandatory Input Validation Before Executing Any JTBD
- ADR 002: Input Analysis Protocol for Greenfield
- ADR 003: Input Analysis Protocol for Tech Debt
- ADR 004: Input Analysis Protocol for New Feature
