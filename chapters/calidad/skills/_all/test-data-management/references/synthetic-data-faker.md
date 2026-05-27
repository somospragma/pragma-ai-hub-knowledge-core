# Datos Sintéticos con Faker — JS/TS, Java, Python

Faker es la herramienta default del chapter para generar datos sintéticos. Existe en múltiples lenguajes con APIs equivalentes y soporta locales LATAM.

## Implementaciones

| Lenguaje     | Paquete                                | Locales LATAM relevantes              |
|--------------|----------------------------------------|---------------------------------------|
| JavaScript   | `@faker-js/faker`                      | `es_CO`, `es_MX`, `es_CL`, `es_AR`, `pt_BR` |
| Python       | `Faker` (joke2k/faker)                 | `es_CO`, `es_MX`, `es_CL`, `es_AR`, `pt_BR` |
| Java         | `net.datafaker:datafaker`              | `es`, `pt-BR`                         |
| Ruby         | `faker` gem                            | `es`, `pt-BR`                         |

## Regla cero: seeds deterministas

```javascript
const { faker } = require('@faker-js/faker/locale/es_CO');
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

## Locales LATAM por país

```javascript
// JavaScript
const { faker: fakerCO } = require('@faker-js/faker/locale/es_CO');
const { faker: fakerMX } = require('@faker-js/faker/locale/es_MX');
const { faker: fakerBR } = require('@faker-js/faker/locale/pt_BR');
const { faker: fakerCL } = require('@faker-js/faker/locale/es_CL');
const { faker: fakerAR } = require('@faker-js/faker/locale/es_AR');
```

```python
# Python
from faker import Faker
fake_co = Faker('es_CO')
fake_mx = Faker('es_MX')
fake_br = Faker('pt_BR')
Faker.seed(12345)
```

```java
// Java (Datafaker)
import net.datafaker.Faker;
import java.util.Locale;

Faker fakerCO = new Faker(new Locale("es", "CO"));
Faker fakerBR = new Faker(new Locale("pt", "BR"));
// seed
Faker seeded = new Faker(new Locale("es", "CO"), new Random(12345));
```

## Casos comunes

### Email con dominio reservado

```javascript
const email = faker.internet.email({ provider: 'example.com' });
// "Juan.Perez@example.com"
```

Nunca usar `faker.internet.email()` sin `provider`: por defecto genera dominios reales (gmail, hotmail) que pueden colisionar con usuarios reales.

### Teléfono LATAM formateado

```javascript
const tel = faker.phone.number('+57 3## ### ####'); // Colombia
```

### Tarjeta de crédito test-safe

```javascript
// Devuelve Luhn-valid pero del BIN de pruebas
const card = faker.finance.creditCardNumber('visa'); // ej 4xxx...
// Para garantizar BIN reservado, usar valor estático:
const testCard = '4111111111111111'; // BIN reservado Visa para testing
```

### Cédulas / RUT con DV

`@faker-js/faker` no incluye cédulas LATAM out-of-the-box; usar custom providers o paquetes:

```javascript
// Chile: rut.js
const rut = require('rut.js');
const rutSintetico = rut.generate(); // "12.345.678-5"

// Brasil: brazilian-utils
const { generate: cpfGen } = require('@brazilian-utils/brazilian-utils/dist-node/cpf');
const cpf = cpfGen();
```

## Patrón de uso con builders

Integra Faker dentro del builder, no en cada test:

```typescript
import { faker } from '@faker-js/faker/locale/es_CO';

export const aUser = (seed?: Partial<User>) => ({
  id: faker.string.uuid(),
  firstName: faker.person.firstName(),
  lastName: faker.person.lastName(),
  email: faker.internet.email({ provider: 'example.com' }),
  phone: faker.phone.number('+57 3## ### ####'),
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

## Snippet completo: setup reproducible para Karate

`karate-config.js`:

```javascript
function fn() {
  const seed = java.lang.System.getenv('FAKER_SEED') || '12345';
  karate.log('Test data seed:', seed);
  const Faker = Java.type('net.datafaker.Faker');
  const faker = new Faker(new java.util.Locale('es', 'CO'),
                          new java.util.Random(parseInt(seed)));
  return {
    baseUrl: java.lang.System.getenv('BASE_URL') || 'https://api-dev.example.com',
    faker: faker,
    testDataSeed: seed,
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
- Encadena con `[[calidad-test-evidence-and-traceability]]` registrando seed en el reporte.
