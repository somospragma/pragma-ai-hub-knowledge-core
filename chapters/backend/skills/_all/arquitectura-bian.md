---
id: backend-skill-arquitectura-bian
version: "1.0"
scope: chapter
type: skill
chapter: backend
---

# Framework BIAN — Arquitectura para Servicios Bancarios

## Qué es BIAN

BIAN (Banking Industry Architecture Network) es un framework de arquitectura empresarial para la industria bancaria. Define un modelo de referencia que estandariza las capacidades funcionales de un banco en Service Domains independientes y reutilizables.

**Objetivo:** Proporcionar un lenguaje común y una estructura estándar para diseñar servicios bancarios interoperables, reduciendo la complejidad y facilitando la integración entre sistemas.

## Conceptos Fundamentales

### Service Domains

Un Service Domain es la unidad funcional mínima del banco. Representa una capacidad de negocio específica y autónoma.

```
┌─────────────────────────────────────────────────────────────┐
│                    BIAN Service Landscape                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Customer    │  │   Current    │  │    Payment       │  │
│  │  Offer       │  │   Account    │  │    Execution     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Party       │  │   Savings    │  │    Card          │  │
│  │  Reference   │  │   Account    │  │    Transaction   │  │
│  │  Data Mgmt   │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Customer    │  │   Loan       │  │    Fraud         │  │
│  │  Credit      │  │              │  │    Detection     │  │
│  │  Rating      │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Ejemplos de Service Domains comunes:**

| Service Domain | Descripción |
|---------------|-------------|
| Current Account | Gestión de cuentas corrientes |
| Savings Account | Gestión de cuentas de ahorro |
| Payment Execution | Ejecución de pagos y transferencias |
| Party Reference Data Management | Datos maestros de clientes |
| Customer Offer | Ofertas y productos para clientes |
| Customer Credit Rating | Calificación crediticia |
| Card Transaction | Transacciones con tarjeta |
| Loan | Gestión de préstamos |

### Control Records

El Control Record es la entidad principal de cada Service Domain. Representa el objeto de negocio central que el dominio gestiona.

```
┌─────────────────────────────────────────┐
│         Service Domain:                  │
│         Current Account                  │
│                                         │
│  Control Record: CurrentAccountFacility │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  BQ: Interest                   │    │
│  │  BQ: ServiceFees                │    │
│  │  BQ: AccountLien                │    │
│  │  BQ: DepositsAndWithdrawals     │    │
│  │  BQ: Payments                   │    │
│  │  BQ: IssuedDevice               │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘

CR = Control Record (entidad principal)
BQ = Behavior Qualifier (sub-entidades/aspectos)
```

**Relación CR → BQ:**
- El CR es el aggregate root del Service Domain
- Los BQ son aspectos o comportamientos específicos del CR
- Cada BQ puede tener sus propias operaciones

### Functional Patterns

BIAN define patrones funcionales que determinan el comportamiento de un Service Domain:

| Patrón | Descripción | Ejemplo |
|--------|-------------|---------|
| **Process** | Ejecuta un proceso de negocio completo | Payment Execution |
| **Maintain** | Gestiona el ciclo de vida de un registro | Party Reference Data Management |
| **Operate** | Opera una facilidad continua | Current Account |
| **Fulfill** | Cumple una obligación o compromiso | Loan |
| **Transact** | Ejecuta transacciones discretas | Card Transaction |
| **Monitor** | Supervisa y detecta condiciones | Fraud Detection |
| **Administer** | Administra políticas y configuración | Product Directory |
| **Design** | Diseña productos y servicios | Product Design |
| **Develop** | Desarrolla capacidades | System Development |
| **Direct** | Dirige y gobierna | Enterprise Strategy |
| **Manage** | Gestiona recursos | Staff Management |
| **Allocate** | Asigna recursos | Branch Currency Management |
| **Analyze** | Analiza información | Customer Behavior Insights |

### Operaciones Estándar por Patrón

Cada patrón funcional tiene operaciones estándar:

```
Patrón OPERATE (ej: Current Account):
  - Initiate   → Crear/abrir la facilidad
  - Update     → Modificar configuración
  - Control    → Acciones de control (suspender, reactivar)
  - Retrieve   → Consultar estado
  - Execute    → Ejecutar operación sobre BQ

Patrón PROCESS (ej: Payment Execution):
  - Initiate   → Iniciar el proceso
  - Update     → Actualizar datos del proceso
  - Execute    → Ejecutar paso del proceso
  - Request    → Solicitar acción
  - Retrieve   → Consultar estado

Patrón MAINTAIN (ej: Party Reference Data):
  - Register   → Registrar nuevo registro
  - Update     → Actualizar datos
  - Request    → Solicitar cambio
  - Retrieve   → Consultar datos
```

## Mapeo BIAN → Arquitectura Hexagonal Pragma

### Estructura de Proyecto

```
service-domain-current-account/
├── domain/
│   ├── model/
│   │   ├── CurrentAccountFacility.java      # Control Record → Aggregate Root
│   │   ├── DepositsAndWithdrawals.java      # BQ → Entidad interna
│   │   ├── ServiceFees.java                 # BQ → Entidad interna
│   │   ├── AccountLien.java                 # BQ → Entidad interna
│   │   └── valueobject/
│   │       ├── AccountId.java
│   │       ├── AccountBalance.java
│   │       └── AccountStatus.java
│   ├── ports/
│   │   └── spi/
│   │       ├── CurrentAccountRepository.java
│   │       └── CoreBankingGateway.java
│   └── usecases/
│       ├── InitiateCurrentAccountUseCase.java    # Operación: Initiate
│       ├── UpdateCurrentAccountUseCase.java      # Operación: Update
│       ├── RetrieveCurrentAccountUseCase.java    # Operación: Retrieve
│       └── ExecuteDepositsAndWithdrawalsUseCase.java  # BQ Execute
├── infrastructure/
│   ├── entry-points/
│   │   └── rest/
│   │       ├── CurrentAccountController.java
│   │       └── dto/
│   │           ├── InitiateCurrentAccountRequest.java
│   │           └── CurrentAccountResponse.java
│   ├── driven-adapters/
│   │   ├── persistence/
│   │   │   └── CurrentAccountJpaAdapter.java
│   │   └── core-banking/
│   │       └── CoreBankingRestAdapter.java
│   └── helpers/
└── application/
    └── MainApplication.java
```

### Mapeo de Conceptos

| BIAN | Hexagonal Pragma | Ubicación |
|------|-----------------|-----------|
| Service Domain | Microservicio | Proyecto completo |
| Control Record | Aggregate Root | `domain/model/` |
| Behavior Qualifier | Entidad interna del aggregate | `domain/model/` |
| Operación (Initiate, Update...) | UseCase | `domain/usecases/` |
| Service Operation (API) | Entry Point (Controller) | `infrastructure/entry-points/` |
| Dependencia externa | Driven Adapter | `infrastructure/driven-adapters/` |

### Nomenclatura de Endpoints (Estilo BIAN)

```
POST   /current-account/{cr-id}/initiation
PUT    /current-account/{cr-id}/update
GET    /current-account/{cr-id}/retrieval
POST   /current-account/{cr-id}/deposits-and-withdrawals/{bq-id}/execution
GET    /current-account/{cr-id}/deposits-and-withdrawals/{bq-id}/retrieval
```

### Ejemplo de UseCase BIAN

```java
public class InitiateCurrentAccountUseCase {

    private final CurrentAccountRepository repository;
    private final CoreBankingGateway coreBanking;

    public CurrentAccountFacility execute(InitiateAccountCommand command) {
        // Validar con core bancario
        coreBanking.validateCustomerEligibility(command.getCustomerId());

        // Crear el Control Record
        CurrentAccountFacility account = CurrentAccountFacility.initiate(
            command.getCustomerId(),
            command.getProductType(),
            command.getCurrency()
        );

        return repository.save(account);
    }
}
```

### Ejemplo de Control Record

```java
public class CurrentAccountFacility {

    private final AccountId id;
    private CustomerId customerId;
    private AccountStatus status;
    private AccountBalance balance;
    private List<DepositsAndWithdrawals> transactions;
    private List<ServiceFees> fees;

    public static CurrentAccountFacility initiate(
            CustomerId customerId,
            ProductType productType,
            Currency currency) {
        return new CurrentAccountFacility(
            AccountId.generate(),
            customerId,
            AccountStatus.ACTIVE,
            AccountBalance.zero(currency),
            new ArrayList<>(),
            new ArrayList<>()
        );
    }

    public DepositsAndWithdrawals executeDeposit(Money amount, String reference) {
        if (status != AccountStatus.ACTIVE) {
            throw new AccountNotActiveException(id);
        }
        DepositsAndWithdrawals transaction = DepositsAndWithdrawals.deposit(amount, reference);
        transactions.add(transaction);
        balance = balance.credit(amount);
        return transaction;
    }
}
```

## Cuándo Usar BIAN

| Criterio | Aplica BIAN |
|----------|------------|
| Proyecto bancario con requisito de alineación BIAN | ✅ Sí |
| Cliente bancario (especialmente Ficohsa) | ✅ Sí |
| Service Domain claramente identificado en catálogo BIAN | ✅ Sí |
| Integración con core bancario | ✅ Sí |
| Proyecto fintech sin requisito BIAN explícito | ❌ No, usar hexagonal estándar |
| Servicio interno no bancario | ❌ No, usar hexagonal estándar |
| Microservicio de soporte (notificaciones, archivos) | ❌ No, usar hexagonal estándar |

## Referencia Rápida

- **Catálogo BIAN:** Define ~300 Service Domains
- **Versión actual:** BIAN 12.0
- **Formato de API:** RESTful con nomenclatura BIAN estándar
- **ISO 20022:** BIAN se alinea con ISO 20022 para mensajería financiera
- **Granularidad:** Un microservicio = Un Service Domain (idealmente)
