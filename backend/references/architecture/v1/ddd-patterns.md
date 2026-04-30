<!-- keywords: ddd, domain-driven design, bounded context, aggregate, entity, value object, domain event, domain service, repository, microservices -->
# Referencia: Patrones de Domain-Driven Design (DDD)

## Propósito

Establecer los lineamientos transversales para aplicar Domain-Driven Design en el desarrollo de microservicios del equipo backend. Al finalizar esta referencia, el lector podrá identificar y modelar correctamente Bounded Contexts, Aggregates, Entities, Value Objects, Domain Events y Domain Services, independientemente del lenguaje o framework utilizado.

## Ámbito de Aplicación

- Todos los microservicios con lógica de negocio moderada o compleja.
- Aplica de forma transversal a cualquier lenguaje (Java, TypeScript, Python) y cualquier patrón arquitectónico (hexagonal, onion, simple).
- Obligatorio cuando el dominio tiene más de 5 reglas de negocio o múltiples entidades con relaciones complejas.
- No aplica para servicios CRUD puros sin lógica de dominio.

## Paso a Paso / Lineamientos

### 1. Strategic Design: Bounded Contexts

Un Bounded Context es un límite explícito dentro del cual un modelo de dominio es consistente. Cada Bounded Context se implementa como un microservicio independiente.

#### Identificación de Bounded Contexts

```
Preguntas clave:
1. ¿Este concepto tiene el mismo significado en todos los contextos?
   → Si NO, hay un límite de contexto
2. ¿Equipos diferentes gestionan esta funcionalidad?
   → Si SÍ, probablemente son contextos separados
3. ¿Puede este módulo desplegarse independientemente?
   → Si SÍ, es candidato a Bounded Context
```

#### Ejemplo: Dominio bancario

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    Accounts     │  │    Payments     │  │      Loans      │
│    Context      │  │    Context      │  │     Context     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ Account         │  │ Payment         │  │ Loan            │
│ Balance         │  │ Transaction     │  │ Amortization    │
│ AccountHolder   │  │ PaymentMethod   │  │ Collateral      │
│ AccountStatus   │  │ PaymentStatus   │  │ Disbursement    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                     │
         └────────────────────┴─────────────────────┘
                      Domain Events
```

#### Relaciones entre Bounded Contexts (Context Map)

| Patrón de relación | Cuándo usar | Ejemplo |
|---------------------|-------------|---------|
| **Published Language** | Comunicación mediante un modelo compartido estándar | API REST con contratos OpenAPI |
| **Customer-Supplier** | Un contexto provee datos que otro consume | Accounts provee saldo a Payments |
| **Conformist** | El consumidor se adapta al modelo del proveedor | Integración con sistema legacy |
| **Anti-Corruption Layer (ACL)** | Proteger el dominio de modelos externos | Adaptador para API de terceros |
| **Shared Kernel** | Dos contextos comparten un subconjunto del modelo | Tipos monetarios compartidos |
| **Separate Ways** | Los contextos no se comunican | Módulos completamente independientes |

**Regla:** Preferir comunicación por Domain Events (asíncrona) sobre llamadas directas (síncrona) entre Bounded Contexts.

### 2. Ubiquitous Language (Lenguaje Ubicuo)

El código debe reflejar el lenguaje del negocio. No traducir ni inventar términos técnicos para conceptos de dominio.

| Práctica | Correcto | Incorrecto |
|----------|----------|------------|
| Nombres de clases | `LoanDisbursement` | `DataProcessor`, `EntityManager` |
| Nombres de métodos | `approveLoan()`, `freezeAccount()` | `process()`, `execute()`, `handle()` |
| Nombres de eventos | `LoanApproved`, `AccountFrozen` | `EntityUpdated`, `StatusChanged` |
| Nombres de excepciones | `InsufficientFundsException` | `BusinessException`, `CustomException` |

**Regla:** Si un experto de negocio no entiende el nombre de una clase o método, el nombre es incorrecto.

### 3. Building Blocks tácticos

#### 3.1 Aggregate

Un Aggregate es un grupo de objetos de dominio que se tratan como una unidad de consistencia transaccional. Tiene un Aggregate Root que es el único punto de acceso externo.

```
┌─────────────────────────────────────────────────┐
│                  AGGREGATE                       │
│                                                  │
│  ┌──────────────────┐                           │
│  │  Aggregate Root  │ ◄── Único punto de acceso │
│  │    (Entity)      │                           │
│  └────────┬─────────┘                           │
│           │                                      │
│     ┌─────┴─────┐                               │
│     │           │                                │
│  ┌──┴───┐  ┌───┴────┐                          │
│  │Entity│  │ Value  │                           │
│  │      │  │ Object │                           │
│  └──────┘  └────────┘                           │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Reglas de diseño de Aggregates:**

1. Mantener los Aggregates pequeños (idealmente 1-3 entidades)
2. Referenciar otros Aggregates solo por identidad (ID), nunca por referencia directa
3. Un solo Aggregate por transacción
4. La consistencia eventual entre Aggregates es aceptable y preferible
5. El Aggregate Root valida todas las invariantes del grupo

#### 3.2 Entity

Una Entity tiene identidad única que persiste a lo largo de su ciclo de vida. Dos entities son iguales si tienen el mismo ID, sin importar sus atributos.

**Características:**
- Tiene un identificador único e inmutable
- Tiene ciclo de vida (se crea, se modifica, puede eliminarse)
- La igualdad se basa en el ID, no en los atributos
- Contiene lógica de negocio relacionada con su estado

#### 3.3 Value Object

Un Value Object es un objeto inmutable sin identidad, definido completamente por sus atributos. Dos Value Objects son iguales si todos sus atributos son iguales.

**Características:**
- Inmutable: una vez creado, no cambia
- Sin identidad: no tiene ID
- Auto-validante: valida sus invariantes en la construcción
- Reemplazable: para "modificar", se crea uno nuevo

**Value Objects comunes en dominio financiero:**

| Value Object | Atributos | Validaciones |
|-------------|-----------|-------------|
| `Money` | amount, currency | amount ≥ 0, currency ISO 4217 válida |
| `AccountNumber` | value | Formato válido, dígito verificador |
| `DateRange` | startDate, endDate | startDate ≤ endDate |
| `Percentage` | value | 0 ≤ value ≤ 100 |
| `Email` | value | Formato RFC 5322 |
| `PhoneNumber` | countryCode, number | Formato E.164 |

#### 3.4 Domain Event

Un Domain Event representa algo que ocurrió en el dominio y que es relevante para el negocio. Se usa para comunicar cambios entre Aggregates y entre Bounded Contexts.

**Convenciones de nomenclatura:**
- Nombre en pasado: `OrderPlaced`, `PaymentProcessed`, `AccountClosed`
- Incluir siempre: timestamp del evento, ID del aggregate que lo originó
- Incluir los datos necesarios para que el consumidor no necesite consultar al productor

**Estructura estándar de un Domain Event:**

```
DomainEvent:
  ├── eventId: string (UUID, único por evento)
  ├── eventType: string (nombre del evento)
  ├── aggregateId: string (ID del aggregate que lo emitió)
  ├── occurredOn: datetime (cuándo ocurrió)
  ├── version: integer (versión del esquema del evento)
  └── payload: object (datos específicos del evento)
```

**Reglas:**
- Los eventos son inmutables: una vez emitidos, no se modifican
- Un Aggregate registra eventos pero no los publica directamente; la capa de aplicación o infraestructura se encarga de la publicación
- Los eventos entre Bounded Contexts deben ser autocontenidos (no requerir llamadas adicionales)

#### 3.5 Domain Service

Un Domain Service encapsula lógica de negocio que no pertenece naturalmente a ningún Aggregate o Entity.

**Cuándo usar Domain Service:**
- La operación involucra múltiples Aggregates del mismo contexto
- La lógica no tiene un "dueño" natural entre las entidades
- Se necesita coordinar una regla de negocio compleja

**Cuándo NO usar Domain Service:**
- La lógica pertenece claramente a un Aggregate → ponerla en el Aggregate
- Es orquestación de casos de uso → usar Application Service / Use Case
- Es lógica técnica (logging, cache) → no es dominio

#### 3.6 Repository (como concepto de dominio)

Un Repository es una abstracción que permite obtener y persistir Aggregates. En el dominio se define como interfaz/contrato; la implementación concreta vive en infraestructura.

**Reglas:**
- Un Repository por Aggregate Root (no por Entity ni por Value Object)
- El Repository trabaja con el Aggregate completo, no con entidades sueltas
- La interfaz del Repository vive en el dominio; la implementación en infraestructura
- Métodos típicos: `save()`, `findById()`, `delete()`, `findByCriteria()`

### 4. Flujo de una operación DDD

```
1. Request llega al Controller/Handler (infraestructura)
2. Controller delega al Application Service / Use Case (aplicación)
3. Application Service:
   a. Obtiene el Aggregate del Repository
   b. Invoca método de negocio en el Aggregate
   c. El Aggregate valida invariantes y registra Domain Events
   d. Persiste el Aggregate via Repository
   e. Publica los Domain Events registrados
4. Response fluye en sentido inverso
```

**Regla clave:** La lógica de negocio vive en el Aggregate, no en el Application Service. El Application Service solo orquesta.

### 5. Patrones de comunicación entre Aggregates

#### Dentro del mismo Bounded Context

- Usar Domain Events internos
- El Application Service puede coordinar múltiples Aggregates en la misma transacción solo si es estrictamente necesario (preferir consistencia eventual)

#### Entre Bounded Contexts diferentes

- Siempre asíncrono via Domain Events publicados en un broker (EventBridge, SQS, Kafka)
- Aplicar Anti-Corruption Layer si el modelo del otro contexto difiere del propio
- Nunca compartir base de datos entre Bounded Contexts

### 6. Errores comunes a evitar

| Error | Por qué es problema | Solución |
|-------|---------------------|----------|
| Aggregate Root gigante | Problemas de concurrencia y rendimiento | Dividir en Aggregates más pequeños |
| Lógica de negocio en Application Service | El dominio se vuelve anémico | Mover lógica al Aggregate |
| Referenciar Aggregates por objeto | Acoplamiento fuerte, problemas de lazy loading | Referenciar solo por ID |
| Value Objects mutables | Efectos secundarios inesperados | Hacerlos inmutables, crear nuevos para "modificar" |
| Domain Events con datos insuficientes | Consumidores necesitan llamar al productor | Incluir todos los datos necesarios en el evento |
| Un Repository por Entity | Rompe el concepto de Aggregate | Un Repository por Aggregate Root |
| Nombres genéricos | Pierde el lenguaje ubicuo | Usar nombres del dominio de negocio |

## Checklist de Verificación

- [ ] Los Bounded Contexts están identificados y documentados con su Context Map
- [ ] El código usa el lenguaje ubicuo del dominio (nombres que el negocio entiende)
- [ ] Cada Aggregate tiene un Root claramente definido
- [ ] Los Aggregates son pequeños (1-3 entidades máximo)
- [ ] Las referencias entre Aggregates son por ID, no por objeto
- [ ] Los Value Objects son inmutables y auto-validantes
- [ ] Los Domain Events están nombrados en pasado y son autocontenidos
- [ ] Los Repositories están definidos como interfaces en el dominio (uno por Aggregate Root)
- [ ] La lógica de negocio vive en los Aggregates, no en los Application Services
- [ ] La comunicación entre Bounded Contexts es asíncrona via Domain Events

## Purpose

_(No additional information required for this section.)_

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
