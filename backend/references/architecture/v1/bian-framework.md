<!-- keywords: bian, banking, framework, service domain, control record, behavior qualifier, banking architecture, api design, ddd, microservices -->
# Referencia: Framework BIAN para Servicios Bancarios

## Propósito

Establecer los lineamientos transversales para aplicar el framework BIAN (Banking Industry Architecture Network) versión 13.0 en el diseño y desarrollo de microservicios para el dominio financiero. Al finalizar esta referencia, el lector podrá identificar Service Domains, aplicar las operaciones estándar, diseñar APIs y modelos canónicos alineados con BIAN, y mapear correctamente los conceptos BIAN hacia DDD.

## Ámbito de Aplicación

- Todos los microservicios del dominio financiero y bancario del equipo.
- Aplica de forma transversal a cualquier lenguaje (Java, TypeScript, Python) y cualquier patrón arquitectónico (hexagonal, onion, simple).
- Versión de referencia: **BIAN Service Landscape 13.0** (junio 2025). No usar versiones 12.0 ni 14.0 salvo indicación explícita.

## Paso a Paso / Lineamientos

### 1. Conceptos fundamentales de BIAN

BIAN organiza la funcionalidad bancaria en una jerarquía:

```
Business Area (12)
  └── Business Domain (agrupación intermedia)
        └── Service Domain (~340 en SL 13.0)
              ├── Control Record (CR)
              ├── Behavior Qualifiers (BQ)
              └── Service Operations
```

**Definiciones clave:**

| Concepto | Definición | Analogía en código |
|----------|------------|--------------------|
| Business Area | Agrupación de alto nivel de capacidades bancarias | Módulo o bounded context de alto nivel |
| Service Domain | Unidad funcional discreta con responsabilidad única | Microservicio |
| Control Record (CR) | Instancia principal que gestiona el Service Domain | Aggregate Root |
| Behavior Qualifier (BQ) | Aspecto o subfunción específica del CR | Entidad hija del aggregate |
| Service Operation | Acción que se puede ejecutar sobre un CR o BQ | Método del servicio / endpoint |

### 2. Business Areas de BIAN 13.0

BIAN 13.0 define 12 Business Areas. Cada una agrupa múltiples Service Domains:

| # | Business Area | Descripción | Ejemplos de Service Domains |
|---|--------------|-------------|----------------------------|
| 1 | Reference Data | Datos maestros y de referencia | Party Reference Data, Product Directory, Location Data Management |
| 2 | Sales & Service | Gestión comercial y atención al cliente | Customer Offer, Customer Case Management, Customer Relationship Management |
| 3 | Operations & Execution | Procesamiento transaccional y operaciones | Payment Execution, Card Transaction, Clearing, Settlement |
| 4 | Risk & Compliance | Gestión de riesgos y cumplimiento normativo | Credit Risk, Fraud Detection, Regulatory Compliance, KYC |
| 5 | Finance & Risk Management | Control financiero y gestión de riesgo corporativo | Financial Accounting, Position Management, Market Risk |
| 6 | Products | Gestión de productos bancarios | Current Account, Savings Account, Loan, Mortgage |
| 7 | Channels | Canales de atención | Branch Operations, E-Branch Operations, Contact Center |
| 8 | Payments | Procesamiento de pagos | Payment Order, Payment Initiation, ACH Operations |
| 9 | Trade & Securities | Operaciones de mercado de capitales | Securities Trading, Trade Confirmation, Custody |
| 10 | Credit | Gestión crediticia | Credit Facility, Credit Administration, Collections |
| 11 | Corporate Services | Servicios corporativos internos | Human Resources, Procurement, Facilities Management |
| 12 | Business Support | Soporte al negocio | Business Architecture, IT Standards, Platform Operations |

> **Nota:** La lista completa de Service Domains (~340) se encuentra en el portal oficial de BIAN. Consultar la URL en la sección de Herramientas y Recursos para obtener el catálogo completo por Business Area.

### 3. Functional Patterns (Asset Types)

Cada Service Domain implementa exactamente un Functional Pattern que determina su comportamiento. Los Functional Patterns de BIAN 13.0 son:

| Functional Pattern | Propósito | Ejemplo de Service Domain |
|-------------------|-----------|--------------------------|
| **Direct** | Dirigir y supervisar actividades | Corporate Strategy, Business Direction |
| **Manage** | Gestionar un recurso o capacidad de forma continua | Customer Relationship Management, Employee Management |
| **Administer** | Administrar un marco normativo o regulatorio | Regulatory Compliance, Legal Compliance |
| **Design** | Diseñar productos, procesos o servicios | Product Design, Service Design |
| **Develop** | Desarrollar capacidades o activos | Software Development, Staff Development |
| **Process** | Procesar transacciones o solicitudes discretas | Payment Execution, Card Transaction |
| **Operate** | Operar infraestructura o plataformas | Platform Operations, IT Operations |
| **Fulfill** | Cumplir con un producto o servicio contratado | Current Account, Savings Account, Loan |
| **Transact** | Ejecutar transacciones financieras | Securities Trading, Foreign Exchange |
| **Enroll** | Registrar o inscribir participantes | Customer Enrollment, Product Enrollment |
| **Agree Terms** | Negociar y acordar términos | Service Agreement, Customer Agreement |
| **Allocate** | Asignar recursos o capacidades | Resource Allocation, Budget Allocation |
| **Analyze** | Analizar información para generar insights | Customer Behavior Analysis, Market Analysis |
| **Assess** | Evaluar y calificar | Credit Assessment, Risk Assessment |
| **Catalog** | Catalogar y organizar información | Product Catalog, Service Catalog |
| **Monitor** | Monitorear actividades o condiciones | Fraud Monitoring, Compliance Monitoring |
| **Track** | Rastrear estado y progreso | Case Tracking, Delivery Tracking |

**Regla:** Al crear un nuevo Service Domain, primero identificar cuál Functional Pattern aplica. Esto define las operaciones disponibles y la estructura del Control Record.

### 4. Service Operations

BIAN define un conjunto estándar de operaciones que se aplican sobre Control Records (CR) y Behavior Qualifiers (BQ):

#### Operaciones sobre Control Record (CR)

| Operación | Cuándo usar | Ejemplo |
|-----------|-------------|---------|
| **Initiate** | Crear una nueva instancia del CR | Abrir una cuenta, iniciar un préstamo |
| **Update** | Modificar atributos de un CR existente | Actualizar datos de una cuenta |
| **Retrieve** | Consultar el estado de un CR | Obtener detalle de una cuenta |
| **Control** | Cambiar el estado operativo del CR (suspender, reactivar, cerrar) | Suspender una cuenta por fraude |
| **Execute** | Ejecutar una acción automatizada sobre el CR | Ejecutar un pago programado |
| **Request** | Solicitar una acción que requiere aprobación o intervención | Solicitar aumento de límite de crédito |
| **Grant** | Otorgar una autorización o permiso | Aprobar una solicitud de crédito |
| **Register** | Registrar información o un participante | Registrar un nuevo cliente |
| **Notify** | Enviar una notificación sobre un evento del CR | Notificar vencimiento de pago |
| **Capture** | Capturar información externa al sistema | Capturar datos de un documento escaneado |

#### Operaciones sobre Behavior Qualifier (BQ)

Las mismas operaciones aplican a nivel de BQ, pero en el contexto de un aspecto específico del CR:

```
CR: Current Account (Initiate, Update, Retrieve, Control)
  └── BQ: Deposits And Withdrawals (Initiate, Retrieve)
  └── BQ: Service Fees (Retrieve, Update)
  └── BQ: Interest (Retrieve, Update)
  └── BQ: Account Sweep (Initiate, Update, Retrieve, Control)
```

**Regla:** No todas las operaciones aplican a todos los CR/BQ. Seleccionar solo las operaciones que tengan sentido para el dominio.

### 5. Diseño de APIs BIAN

Las URLs de las APIs deben seguir la convención BIAN:

#### Patrón de URL

```
/{service-domain}/{cr-reference-id}/{behavior-qualifier}/{bq-reference-id}/{operation}
```

#### Mapeo a métodos HTTP

| Operación BIAN | Método HTTP | URL ejemplo |
|----------------|-------------|-------------|
| Initiate (CR) | POST | `/current-account/initiate` |
| Retrieve (CR) | GET | `/current-account/{cr-id}/retrieve` |
| Update (CR) | PUT | `/current-account/{cr-id}/update` |
| Control (CR) | PUT | `/current-account/{cr-id}/control` |
| Execute (CR) | PUT | `/current-account/{cr-id}/execute` |
| Request (CR) | POST | `/current-account/{cr-id}/request` |
| Initiate (BQ) | POST | `/current-account/{cr-id}/deposits-and-withdrawals/initiate` |
| Retrieve (BQ) | GET | `/current-account/{cr-id}/deposits-and-withdrawals/{bq-id}/retrieve` |

#### Convenciones de nomenclatura en URLs

- Usar **kebab-case** para nombres de Service Domains y BQs: `current-account`, `deposits-and-withdrawals`
- Los IDs de referencia usan el sufijo `-id`: `cr-reference-id`, `bq-reference-id`
- La operación va al final de la URL como sustantivo: `/initiate`, `/retrieve`, `/update`

### 6. Modelo Canónico de Datos

BIAN define modelos de datos estándar. Al implementar, seguir estas convenciones de nomenclatura:

#### Nomenclatura de entidades

| Concepto BIAN | Convención de nombre | Ejemplo |
|---------------|---------------------|---------|
| Control Record | `{ServiceDomain}Facility` o `{ServiceDomain}Fulfillment` | `CurrentAccountFacility` |
| Behavior Qualifier | Nombre descriptivo del aspecto | `DepositsAndWithdrawals`, `ServiceFees` |
| Referencia | `{entidad}Reference` | `currentAccountFacilityReference` |
| Estado | `{entidad}Status` | `accountStatus` |
| Tipo | `{entidad}Type` | `transactionType` |
| Fecha | `{descripcion}Date` o `{descripcion}DateTime` | `valueDate`, `transactionDateTime` |
| Monto | `{descripcion}Amount` con moneda separada | `transactionAmount` + `transactionCurrency` |

#### Estructura estándar de un Control Record

```
ControlRecord:
  ├── {cr}Reference          (identificador único)
  ├── customerReference      (referencia al cliente)
  ├── {cr}Type               (tipo/clasificación)
  ├── {cr}Status             (estado actual)
  ├── {cr}Currency           (moneda, si aplica)
  ├── dateOfOpening          (fecha de creación)
  ├── configuration          (configuración específica)
  └── behaviorQualifiers[]   (lista de BQs asociados)
```

#### Estructura estándar de un Behavior Qualifier

```
BehaviorQualifier:
  ├── {bq}Reference          (identificador único)
  ├── {bq}Type               (tipo/clasificación)
  ├── {bq}Status             (estado)
  ├── {bq}Amount             (monto, si aplica)
  ├── {bq}Currency           (moneda, si aplica)
  ├── {bq}DateTime           (fecha/hora del evento)
  └── {bq}Description        (descripción)
```

### 7. Mapeo BIAN a DDD

Para implementar Service Domains usando patrones DDD:

| Concepto BIAN | Concepto DDD | Notas |
|---------------|-------------|-------|
| Business Area | Subdomain | Agrupación estratégica |
| Service Domain | Bounded Context | Un microservicio = un Service Domain |
| Control Record | Aggregate Root | Raíz de consistencia transaccional |
| Behavior Qualifier | Entity (dentro del Aggregate) | Entidad hija del aggregate |
| Service Operation | Application Service / Use Case | Orquesta la lógica |
| Canonical Data Model | Value Objects + Entities | Modelos del dominio |
| BIAN Events | Domain Events | Comunicación entre bounded contexts |
| Functional Pattern | Determina el tipo de Aggregate | Fulfill = Aggregate con ciclo de vida largo |

**Reglas de mapeo:**

1. Un Service Domain = un Bounded Context = un microservicio
2. El Control Record es siempre el Aggregate Root
3. Los BQs son entidades dentro del aggregate, accesibles solo a través del CR
4. Las Service Operations se implementan como Use Cases o Application Services
5. Los eventos entre Service Domains se implementan como Domain Events
6. El Functional Pattern guía el diseño del aggregate:
   - **Fulfill**: Aggregate con ciclo de vida largo (cuenta, préstamo)
   - **Process**: Aggregate transaccional de corta duración (pago, transferencia)
   - **Manage**: Aggregate de gestión continua (relación con cliente)

### 8. Ejemplo transversal (agnóstico al lenguaje)

#### Caso: Current Account Service Domain

```
Service Domain: Current Account
Functional Pattern: Fulfill
Business Area: Products

Control Record: CurrentAccountFacility
  ├── currentAccountFacilityReference: string (UUID)
  ├── customerReference: string
  ├── accountType: "Checking" | "Savings"
  ├── accountCurrency: string (ISO 4217)
  ├── accountStatus: "Active" | "Dormant" | "Suspended" | "Closed"
  ├── dateOfOpening: date
  │
  ├── BQ: DepositsAndWithdrawals
  │     ├── depositsAndWithdrawalsReference: string
  │     ├── transactionType: "Deposit" | "Withdrawal" | "Transfer"
  │     ├── transactionAmount: decimal
  │     ├── transactionCurrency: string
  │     ├── valueDate: datetime
  │     └── transactionStatus: "Initiated" | "Completed" | "Failed"
  │
  ├── BQ: ServiceFees
  │     ├── serviceFeeReference: string
  │     ├── feeType: string
  │     ├── feeAmount: decimal
  │     └── applicationDate: date
  │
  └── BQ: Interest
        ├── interestReference: string
        ├── interestRate: decimal
        ├── interestType: "Fixed" | "Variable"
        └── accrualDate: date

Operaciones:
  CR: Initiate, Update, Retrieve, Control
  BQ DepositsAndWithdrawals: Initiate, Retrieve
  BQ ServiceFees: Retrieve, Update
  BQ Interest: Retrieve, Update

API Endpoints:
  POST   /current-account/initiate
  GET    /current-account/{cr-id}/retrieve
  PUT    /current-account/{cr-id}/update
  PUT    /current-account/{cr-id}/control
  POST   /current-account/{cr-id}/deposits-and-withdrawals/initiate
  GET    /current-account/{cr-id}/deposits-and-withdrawals/{bq-id}/retrieve
  GET    /current-account/{cr-id}/service-fees/{bq-id}/retrieve
  PUT    /current-account/{cr-id}/interest/{bq-id}/update
```

> **Nota:** Este es un ejemplo ilustrativo. La implementación concreta depende del patrón arquitectónico elegido (hexagonal, onion, simple). Para implementación específica por lenguaje, ver los archivos `bian-framework.{lenguaje}.md`.

## Checklist de Verificación

- [ ] El Service Domain está identificado en el catálogo BIAN 13.0
- [ ] Se identificó el Functional Pattern correcto para el Service Domain
- [ ] El Control Record tiene un Reference único como identificador
- [ ] Los Behavior Qualifiers están correctamente identificados como subfunciones del CR
- [ ] Solo se implementaron las Service Operations que aplican al dominio
- [ ] Las URLs de la API siguen la convención BIAN: `/{service-domain}/{cr-id}/{bq}/{bq-id}/{operation}`
- [ ] Los nombres de campos siguen la nomenclatura BIAN: `{entidad}Reference`, `{entidad}Status`, `{entidad}Type`
- [ ] El mapeo a DDD es correcto: CR = Aggregate Root, BQ = Entity
- [ ] Los montos siempre tienen su campo de moneda asociado (ISO 4217)
- [ ] Los eventos entre Service Domains están definidos como Domain Events

## Relación con otros documentos

- the Java-specific BIAN implementation reference — Implementación específica en Java

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
