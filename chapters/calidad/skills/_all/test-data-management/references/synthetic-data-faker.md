# Datos Sintéticos con Faker — JS/TS, Java, Python

Faker es la herramienta default del chapter para generar datos sintéticos. Existe en múltiples lenguajes con APIs equivalentes y soporta locales globales — elegir el locale por **jurisdicción del cliente**, no por suposición regional.

## Implementaciones

| Lenguaje     | Paquete                                | Locales relevantes (selección)                                                  |
|--------------|----------------------------------------|---------------------------------------------------------------------------------|
| JavaScript   | `@faker-js/faker`                      | `en_US`, `en_GB`, `de_DE`, `fr_FR`, `es_ES`, `it_IT`, `pt_BR`, `es_MX`, `ja_JP`, `zh_CN`, `ko_KR` |
| Python       | `Faker` (joke2k/faker)                 | `en_US`, `en_GB`, `de_DE`, `fr_FR`, `es_ES`, `it_IT`, `pt_BR`, `es_MX`, `ja_JP`, `zh_CN`, `ko_KR`, `ar_SA`, `hi_IN`, `ru_RU` |
| Java         | `net.datafaker:datafaker`              | `en-US`, `en-GB`, `de`, `fr`, `es`, `it`, `pt-BR`, `ja`, `zh-CN`, `ko`, `ru`    |
| Ruby         | `faker` gem                            | `en`, `en-GB`, `de`, `fr`, `es`, `it`, `pt-BR`, `ja`, `zh-CN`                   |

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

## Locales por jurisdicción

Selección del locale guiada por el cliente y su mercado objetivo. La siguiente tabla cubre los locales más usados; cualquiera de los tres lenguajes principales acepta selección equivalente.

| Mercado / región        | Locale JS                              | Locale Python   | Notas                                          |
|-------------------------|----------------------------------------|-----------------|------------------------------------------------|
| Estados Unidos          | `en_US`                                | `en_US`         | Default global cuando el cliente no especifica |
| Reino Unido             | `en_GB`                                | `en_GB`         | Direcciones y teléfonos UK                     |
| Alemania                | `de_DE`                                | `de_DE`         | Umlauts y formato dirección DE                 |
| Francia                 | `fr_FR`                                | `fr_FR`         | Acentos; código postal 5 dígitos               |
| España                  | `es_ES`                                | `es_ES`         | DNI/NIE no incluido por defecto (custom)       |
| Italia                  | `it_IT`                                | `it_IT`         | Codice Fiscale via paquete externo             |
| Brasil                  | `pt_BR`                                | `pt_BR`         | CPF/CNPJ via paquete externo                   |
| México                  | `es_MX`                                | `es_MX`         | CURP/RFC custom provider                       |
| Colombia                | `es_CO`                                | `es_CO`         | NUIP custom provider                           |
| Japón                   | `ja_JP`                                | `ja_JP`         | Kanji + romaji; nombres reales del locale      |
| China                   | `zh_CN`                                | `zh_CN`         | Caracteres simplificados                       |
| Corea del Sur           | `ko_KR`                                | `ko_KR`         | Hangul                                         |
| Arabia Saudí / árabe    | (no nativo)                            | `ar_SA`         | RTL; verificar UI                              |
| India                   | (limitado)                             | `hi_IN` / `en_IN` | Aadhaar/PAN via paquetes externos            |
| Rusia                   | (limitado)                             | `ru_RU`         | Cirílico                                       |

```javascript
// JavaScript — múltiples locales por jurisdicción
const { faker: fakerUS } = require('@faker-js/faker/locale/en_US');
const { faker: fakerGB } = require('@faker-js/faker/locale/en_GB');
const { faker: fakerDE } = require('@faker-js/faker/locale/de_DE');
const { faker: fakerJP } = require('@faker-js/faker/locale/ja_JP');
const { faker: fakerBR } = require('@faker-js/faker/locale/pt_BR');
const { faker: fakerMX } = require('@faker-js/faker/locale/es_MX');
```

```python
# Python
from faker import Faker
fake_us = Faker('en_US')
fake_gb = Faker('en_GB')
fake_de = Faker('de_DE')
fake_jp = Faker('ja_JP')
fake_br = Faker('pt_BR')
Faker.seed(12345)
```

```java
// Java (Datafaker)
import net.datafaker.Faker;
import java.util.Locale;
import java.util.Random;

Faker fakerUS = new Faker(new Locale("en", "US"), new Random(12345));
Faker fakerDE = new Faker(new Locale("de", "DE"), new Random(12345));
Faker fakerJP = new Faker(new Locale("ja"),       new Random(12345));
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

Cada locale formatea el teléfono según las convenciones del país. Si necesitas E.164 explícito o un país específico, pasa el patrón.

```javascript
// E.164 genérico
const e164 = faker.phone.number('+###########');

// Ejemplos por país (patrón explícito)
const us = faker.phone.number('+1 ### ### ####');   // Estados Unidos
const uk = faker.phone.number('+44 #### ######');   // Reino Unido
const de = faker.phone.number('+49 ### #######');   // Alemania
const jp = faker.phone.number('+81 ## #### ####');  // Japón
const co = faker.phone.number('+57 3## ### ####');  // Colombia
const mx = faker.phone.number('+52 ### ### ####');  // México
const br = faker.phone.number('+55 ## #####-####'); // Brasil
```

Para garantizar rangos reservados de testing del país, combinar con prefijos definidos por el regulador local (ej. UK Ofcom reserva `+44 113 496 0xxx`).

### Tarjeta de crédito test-safe

```javascript
// Devuelve Luhn-valid pero del BIN de pruebas
const card = faker.finance.creditCardNumber('visa'); // ej 4xxx...
// Para garantizar BIN reservado, usar valor estático:
const testCard = '4111111111111111'; // BIN reservado Visa para testing
```

### Identificadores nacionales out-of-the-box

`@faker-js/faker` y librerías equivalentes ofrecen generadores genéricos (nombre, email, dirección, IBAN, SSN US, etc.) por locale, pero **muchos identificadores nacionales no están incluidos** y requieren paquetes dedicados o custom providers — esto aplica globalmente, no solo a LATAM:

```javascript
// Brasil: CPF/CNPJ
const { generate: cpfGen } = require('@brazilian-utils/brazilian-utils/dist-node/cpf');
const cpf = cpfGen();

// Chile: RUT
const rut = require('rut.js');
const rutSintetico = rut.generate(); // "12.345.678-5"

// India: PAN / Aadhaar (paquetes comunitarios, ej. 'aadhaar-validator')
// Italia: Codice Fiscale (ej. 'codice-fiscale-utils')
// España: DNI/NIE (custom provider — letra MOD-23 calculada)
// Reino Unido: NHS number (custom provider — check MOD-11)
// Japón: My Number (custom provider — check digit dedicado)
```

La recomendación es mantener una librería interna `pragma-test-id-providers` con custom providers por país, alimentada a medida que los clientes lo requieren.

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
- **Asumir el locale del cliente por geografía del equipo de QA** → confirmar con el cliente; un cliente con sede en una región puede operar en mercados distintos.

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
- Locale elegido por jurisdicción del cliente, no por suposición regional.
- Encadena con `[[calidad-test-evidence-and-traceability]]` registrando seed y locale en el reporte.
