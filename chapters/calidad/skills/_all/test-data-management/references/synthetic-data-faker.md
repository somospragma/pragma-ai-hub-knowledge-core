# Datos Sintéticos con Faker — JS/TS, Java, Python

Faker es la herramienta default del chapter para generar datos sintéticos. Existe en múltiples lenguajes con APIs equivalentes y soporta locales globales — para el alcance del Chapter (LATAM + Estados Unidos), elegir el locale por **jurisdicción del cliente**.

## Implementaciones

| Lenguaje     | Paquete                                | Locales del alcance (selección)                                                  |
|--------------|----------------------------------------|----------------------------------------------------------------------------------|
| JavaScript   | `@faker-js/faker`                      | `en_US`, `es_CO`, `es_MX`, `es_AR`, `es_CL`, `es_PE`, `es_VE`, `pt_BR`, `es`     |
| Python       | `Faker` (joke2k/faker)                 | `en_US`, `es_CO`, `es_MX`, `es_AR`, `es_CL`, `es_PE`, `es_VE`, `pt_BR`, `es`     |
| Java         | `net.datafaker:datafaker`              | `en-US`, `es-CO`, `es-MX`, `es-AR`, `es-CL`, `es-PE`, `pt-BR`, `es`              |
| Ruby         | `faker` gem                            | `en`, `es-CO`, `es-MX`, `es-CL`, `es-PE`, `pt-BR`                                |

## Regla cero: seeds deterministas

```javascript
const { faker } = require('@faker-js/faker/locale/en_US');
faker.seed(12345);
const email1 = faker.internet.email(); // determinista
faker.seed(12345);
const email2 = faker.internet.email(); // === email1
```

En CI **siempre** seed fijo (desde env var `FAKER_SEED`). Local puede usar seed aleatorio, pero la suite debe loguearlo:

```javascript
const seed = Number(process.env.FAKER_SEED) || Date.now();
faker.seed(seed);
console.log(`[test-data] seed=${seed}`);
```

Esto permite reproducir cualquier corrida pasando el seed exacto.

## Locales por jurisdicción (alcance Chapter)

Selección del locale guiada por el cliente y su mercado objetivo dentro del alcance del Chapter (LATAM + Estados Unidos). La siguiente tabla cubre los locales usados; cualquiera de los tres lenguajes principales acepta selección equivalente.

| Mercado / país          | Locale JS    | Locale Python   | Notas                                          |
|-------------------------|--------------|-----------------|------------------------------------------------|
| Estados Unidos          | `en_US`      | `en_US`         | Default cuando el cliente opera principalmente en US |
| Colombia                | `es_CO`      | `es_CO`         | NUIP custom provider                           |
| México                  | `es_MX`      | `es_MX`         | CURP/RFC custom provider                       |
| Argentina               | `es_AR`      | `es_AR`         | DNI custom provider                            |
| Chile                   | `es_CL`      | `es_CL`         | RUT custom provider                            |
| Perú                    | `es_PE`      | `es_PE`         | DNI custom provider                            |
| Venezuela               | `es_VE`      | `es_VE`         | Cédula custom provider                         |
| Brasil                  | `pt_BR`      | `pt_BR`         | CPF/CNPJ via paquete externo                   |
| Centroamérica + Caribe + Uruguay + Bolivia + Ecuador + Paraguay | `es` genérico | `es` genérico | Sin locale dedicado; aplicar custom provider del documento local |

```javascript
// JavaScript — múltiples locales por jurisdicción
const { faker: fakerUS } = require('@faker-js/faker/locale/en_US');
const { faker: fakerCO } = require('@faker-js/faker/locale/es_CO');
const { faker: fakerMX } = require('@faker-js/faker/locale/es_MX');
const { faker: fakerBR } = require('@faker-js/faker/locale/pt_BR');
const { faker: fakerCL } = require('@faker-js/faker/locale/es_CL');
```

```python
# Python
from faker import Faker
fake_us = Faker('en_US')
fake_co = Faker('es_CO')
fake_mx = Faker('es_MX')
fake_br = Faker('pt_BR')
fake_cl = Faker('es_CL')
Faker.seed(12345)
```

```java
// Java (Datafaker)
import net.datafaker.Faker;
import java.util.Locale;
import java.util.Random;

Faker fakerUS = new Faker(new Locale("en", "US"), new Random(12345));
Faker fakerCO = new Faker(new Locale("es", "CO"), new Random(12345));
Faker fakerBR = new Faker(new Locale("pt", "BR"), new Random(12345));
```

## Casos comunes

### Email con dominio reservado

```javascript
const email = faker.internet.email({ provider: 'example.com' });
// "John.Doe@example.com"
```

Nunca usar `faker.internet.email()` sin `provider`: por defecto genera dominios reales (gmail, hotmail) que pueden colisionar con usuarios reales.

### Teléfono internacional formateado

Cada locale formatea el teléfono según las convenciones del país. Si necesitas E.164 explícito o un país específico del alcance, pasa el patrón.

```javascript
// E.164 genérico
const e164 = faker.phone.number('+###########');

// Ejemplos por país (patrón explícito)
const us = faker.phone.number('+1 ### ### ####');     // Estados Unidos
const co = faker.phone.number('+57 3## ### ####');    // Colombia
const mx = faker.phone.number('+52 ### ### ####');    // México
const br = faker.phone.number('+55 ## #####-####');   // Brasil
const ar = faker.phone.number('+54 ## #### ####');    // Argentina
const cl = faker.phone.number('+56 # #### ####');     // Chile
const pe = faker.phone.number('+51 ### ### ###');     // Perú
const cr = faker.phone.number('+506 #### ####');      // Costa Rica
const pa = faker.phone.number('+507 #### ####');      // Panamá
const dor= faker.phone.number('+1 809 ### ####');     // República Dominicana (+1-809/849/829)
```

Para garantizar rangos reservados de testing del país, combinar con prefijos definidos por el regulador local cuando exista.

### Tarjeta de crédito test-safe

```javascript
// Devuelve Luhn-valid pero del BIN de pruebas
const card = faker.finance.creditCardNumber('visa'); // ej 4xxx...
// Para garantizar BIN reservado, usar valor estático:
const testCard = '4111111111111111'; // BIN reservado Visa para testing
```

### Identificadores nacionales del alcance — out-of-the-box

`@faker-js/faker` y librerías equivalentes ofrecen generadores genéricos (nombre, email, dirección, IBAN, SSN US) por locale, pero **muchos identificadores nacionales LATAM no están incluidos** y requieren paquetes dedicados o custom providers:

```javascript
// Estados Unidos: SSN, Driver's License (Faker soporta SSN out-of-the-box)
const ssn = faker.helpers.replaceSymbols('9##-##-####'); // ITIN-like

// Brasil: CPF/CNPJ
const { generate: cpfGen } = require('@brazilian-utils/brazilian-utils/dist-node/cpf');
const cpf = cpfGen();

// Chile: RUT
const rut = require('rut.js');
const rutSintetico = rut.generate(); // "12.345.678-5"

// Colombia: NUIP (custom provider — 10 dígitos, prefijo `99` sintético)
// México: CURP / RFC (custom provider — 18 / 13 chars con check digit)
// Argentina / Perú: DNI (custom provider — 8 dígitos)
// Centroamérica + Caribe: cédula nacional por país (custom provider)
```

La recomendación es mantener una librería interna `pragma-test-id-providers` con custom providers por país del alcance, alimentada a medida que los clientes lo requieren.

## Patrón de uso con builders

Integra Faker dentro del builder, no en cada test. El locale se elige al instanciar el builder según el cliente.

```typescript
import { faker } from '@faker-js/faker/locale/en_US';

export const aUser = (seed?: Partial<User>) => ({
  id: faker.string.uuid(),
  firstName: faker.person.firstName(),
  lastName: faker.person.lastName(),
  email: faker.internet.email({ provider: 'example.com' }),
  phone: faker.phone.number('+1 ### ### ####'),
  ...seed,
});
```

Los tests no llaman a Faker directamente: piden `aUser({ role: 'ADMIN' })`.

## Anti-patrones

- **Generar datos distintos en cada corrida sin loguear el seed** → bugs irreproducibles.
- **Llamar Faker desde cada test** → acoplamiento y duplicación; centralizar en builders.
- **Usar `faker.internet.email()` sin provider** → posible colisión con usuarios reales.
- **Generar números de tarjeta sin BIN reservado** → riesgo de coincidir con tarjeta real.
- **Compartir un Faker singleton mutable entre tests paralelos** → race conditions en el seed.
- **Hardcodear datos que podrían ser sintéticos** → cambia el esquema y todo rompe.
- **Asumir el locale del cliente por geografía del equipo de QA** → confirmar con el cliente; un cliente con sede en una región puede operar en varios países del alcance.

## Snippet completo: setup reproducible para Karate

`karate-config.js`:

```javascript
function fn() {
  const seed = java.lang.System.getenv('FAKER_SEED') || '12345';
  const locale = java.lang.System.getenv('FAKER_LOCALE') || 'en-US';
  karate.log('Test data seed:', seed, 'locale:', locale);
  const Faker = Java.type('net.datafaker.Faker');
  const Locale = Java.type('java.util.Locale');
  const Random = Java.type('java.util.Random');
  const parts = locale.split('-');
  const javaLocale = parts.length > 1 ? new Locale(parts[0], parts[1]) : new Locale(parts[0]);
  const faker = new Faker(javaLocale, new Random(parseInt(seed)));
  return {
    baseUrl: java.lang.System.getenv('BASE_URL') || 'https://api-dev.example.com',
    faker: faker,
    testDataSeed: seed,
    testDataLocale: locale,
  };
}
```

Y en cualquier feature:

```gherkin
Background:
  * def email = faker.internet().emailAddress()
  * def nombre = faker.name().firstName()
```

## Restricciones

- Seed fijo en CI siempre. Reportar el seed en cada ejecución para reproducibilidad.
- Dominios reservados (`example.com`, `example.org`) — nunca `gmail.com`.
- BIN reservados para tarjetas — nunca generar BINs reales.
- Locale elegido por jurisdicción del cliente dentro del alcance del Chapter (LATAM + Estados Unidos). Para clientes fuera del alcance, escalar.
- Encadena con `[[calidad-test-evidence-and-traceability]]` registrando seed y locale en el reporte.
