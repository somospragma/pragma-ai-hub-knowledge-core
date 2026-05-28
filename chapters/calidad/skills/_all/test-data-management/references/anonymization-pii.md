# Anonimización de PII — Técnicas, Reglas por Dato, Cumplimiento Multi-Jurisdiccional

Cuando no es viable usar datos sintéticos puros y se requiere un snapshot prod-like, los datos deben anonimizarse **antes** de salir del perímetro productivo. Este documento describe técnicas, reglas por tipo de dato y herramientas, aplicables a cualquier jurisdicción. Las particularidades regionales (identificadores nacionales, marcos legales) se cubren en anexos.

## Principios universales

| Técnica                          | Descripción                                                           | Cuándo usar                              |
|----------------------------------|-----------------------------------------------------------------------|------------------------------------------|
| **Masking / Redacción**          | Sustituir caracteres (`****1234`)                                      | UI, evidencia visual                     |
| **Pseudonimización**             | Reemplazar valor por token; reversible con tabla de mapping             | Análisis ligado a usuario sin identidad  |
| **Tokenización**                 | Sustituir por token sin valor matemático; mapping centralizado (vault) | PCI, tarjetas de crédito                 |
| **Format-Preserving Encryption** | Cifrado que preserva longitud y formato                                | Cuando downstream valida formato         |
| **K-anonymization**              | Garantizar que cada combinación de quasi-identifiers aparece ≥ k veces | Datasets analíticos                      |
| **L-diversity**                  | K-anon + cada grupo tiene ≥ l valores distintos en el atributo sensible | Datasets de salud, finanzas              |
| **Differential Privacy**         | Añadir ruido controlado a agregaciones                                 | Estadísticas publicables                 |
| **Generalización**               | Sustituir valor por rango (`edad 32` → `30-39`)                        | Demografía                               |
| **Supresión**                    | Eliminar campo                                                         | PII no necesaria para el test            |
| **Síntesis**                     | Reemplazar por valor generado plausible (Faker)                        | Default del chapter                      |

## Reglas por tipo de dato — formato global

Identificadores y campos que aparecen en virtualmente cualquier sistema, independientemente de la región del cliente.

### Identificación e identidad

| Dato                       | Regla                                                                                   |
|----------------------------|-----------------------------------------------------------------------------------------|
| Email                      | Dominio reservado `@example.com` / `@example.org` (RFC 2606)                            |
| Teléfono internacional E.164 | Prefijo país real + número generado en rango reservado del país (ver tabla por país)  |
| Dirección postal           | Faker con locale + sufijo `(TEST)`                                                      |
| IP address (v4/v6)         | Generar en rangos reservados (`192.0.2.0/24`, `198.51.100.0/24`, `2001:db8::/32`)       |
| MAC address                | Generar en rango locally-administered (`02:xx:xx:xx:xx:xx`)                             |
| Passport number            | Generar formato plausible por país; nunca números reales                                |
| IBAN (UE/UK/varios)        | Generar con MOD-97 correcto + país de testing (`XX99...`) o BIN fake                    |
| SSN (EE.UU.)               | Usar rango reservado `900-xx-xxxx` ITIN-like; nunca SSN real                            |
| SIN (Canadá)               | 9 dígitos con Luhn válido; prefijo `8` reservado por ServiceCanada para testing         |
| NHS Number (UK)            | 10 dígitos con check digit MOD-11; rango de testing definido por NHS Digital            |

### Contacto

| Dato      | Regla                                                                              |
|-----------|------------------------------------------------------------------------------------|
| Email     | Dominio reservado `@example.com` / `@example.org` (RFC 2606)                       |
| Teléfono  | Prefijo del país real, número en rango reservado del país (ver Faker por locale)   |
| Dirección | Faker con locale + sufijo `(TEST)`                                                 |

### Financiero (global)

| Dato                 | Regla                                                                                       |
|----------------------|---------------------------------------------------------------------------------------------|
| Tarjeta de crédito   | Generar Luhn-valid pero usando **BIN reservado de testing** (Visa 4111-1111-1111-1111, etc.)|
| CVV                  | Siempre `123` o `000` (nunca real)                                                          |
| IBAN                 | Generar con MOD-97 correcto + país ficticio (`XX99...`) o BIN de banco fake                 |
| Cuenta bancaria local| Generar dígitos según longitud del país; nunca reusar dígitos productivos                   |
| SWIFT/BIC            | Generar 8-11 chars; usar codes reservados o de banco fake                                   |

### Salud / sensible

| Dato                | Regla                                                                              |
|---------------------|------------------------------------------------------------------------------------|
| Historia clínica    | Generar con vocabulario clínico fake; nunca derivar de paciente real               |
| Diagnóstico         | Códigos CIE-10 / ICD-10 plausibles pero aleatorios                                 |
| Tipo de sangre      | Distribución uniforme                                                              |

## Reglas por tipo de dato — anexos regionales

Cada anexo cubre identificadores nacionales propios de la jurisdicción. Activar solo el subset que aplica al cliente.

### Anexo LATAM

| Dato                       | Regla                                                                                   |
|----------------------------|-----------------------------------------------------------------------------------------|
| Cédula Colombia (NUIP)     | Generar 10 dígitos numéricos sin validación oficial; prefijo `99` para marcar sintético |
| CURP México                | 18 chars; generar con `faker-js` locale `es_MX` con custom provider                    |
| RFC México                 | 13 chars (persona física) / 12 (moral); generar plausible, marcar prefijo `XAXX`        |
| RUT Chile                  | Generar 8 dígitos + DV calculado (módulo 11)                                            |
| CPF Brasil                 | 11 dígitos + DV calculado (módulo 11); usar `faker-br` `cpf()`                          |
| CNPJ Brasil                | 14 dígitos + DV calculado; `faker-br` `cnpj()`                                          |
| DNI Argentina              | 7-8 dígitos numéricos                                                                   |
| DNI Perú                   | 8 dígitos numéricos                                                                     |

### Anexo Europa

| Dato                                | Regla                                                                |
|-------------------------------------|----------------------------------------------------------------------|
| DNI/NIE/NIF España                  | 8 dígitos + letra calculada por módulo 23; prefijo `X/Y/Z` para NIE  |
| Codice Fiscale Italia               | 16 chars alfanuméricos; generar con librería dedicada o custom prov. |
| NHS Number Reino Unido              | 10 dígitos con check digit MOD-11                                    |
| Personalausweis (DE)                | 10 chars con check digit; usar rango reservado                       |
| AVS / Sozialversicherungsnummer (CH)| 13 dígitos formato `756.xxxx.xxxx.xx` con EAN-13 check               |
| Numéro de sécurité sociale (FR)     | 15 dígitos con clé MOD-97                                            |

### Anexo Estados Unidos / Canadá

| Dato                  | Regla                                                                          |
|-----------------------|--------------------------------------------------------------------------------|
| SSN (EE.UU.)          | Rango reservado `000-xx-xxxx` / `9xx-xx-xxxx`; nunca SSN real                  |
| EIN (EE.UU.)          | 9 dígitos formato `xx-xxxxxxx`; usar rango de testing                          |
| ITIN (EE.UU.)         | 9 dígitos empezando por `9`, cuarto dígito 7 u 8                               |
| Driver's License      | Formato por estado (variable 8-13 chars); generar plausible                    |
| SIN Canadá            | 9 dígitos Luhn-valid; prefijo `8` reservado para testing                       |

### Anexo APAC

| Dato                                | Regla                                                                |
|-------------------------------------|----------------------------------------------------------------------|
| Aadhaar India                       | 12 dígitos con Verhoeff check; usar rango sintético, nunca real      |
| PAN India                           | 10 chars alfanuméricos formato `AAAAA9999A`                          |
| MyKad Malasia                       | 12 dígitos formato `YYMMDD-PB-####`                                  |
| NRIC Singapur                       | 9 chars con check letter (algoritmo público)                         |
| Resident Registration Number Corea  | 13 dígitos formato `YYMMDD-Gxxxxxx`                                  |
| My Number Japón                     | 12 dígitos con check digit                                           |

## Cumplimiento por marco

Ningún dato productivo cruza el perímetro de producción sin pasar por un pipeline de anonimización auditable, sin importar la jurisdicción. Cada marco añade reglas específicas:

| Jurisdicción / Marco           | Implicaciones para QA                                                          |
|--------------------------------|--------------------------------------------------------------------------------|
| GDPR / UK-GDPR (UE, UK)        | Anonimización irreversible o pseudonimización con base legal. DPO obligatorio. |
| HIPAA (EE.UU.)                 | Safe Harbor (eliminar 18 identifiers) o Expert Determination para PHI.         |
| CCPA / CPRA (California)       | Right to delete; documentar uso en QA y permitir purga bajo solicitud.         |
| LGPD (Brasil)                  | Anonimización irreversible o consentimiento explícito. DPO obligatorio.        |
| Ley 1581 (Colombia)            | Datos en QA deben anonimizarse o ser sintéticos. Registrar tratamiento.        |
| LFPDPPP (México)               | Aviso de privacidad obligatorio; principio de finalidad limita uso en QA.      |
| Ley 25.326 (Argentina)         | Datos sensibles requieren consentimiento expreso por escrito.                  |
| Ley 19.628 / 21.719 (Chile)    | Ley 21.719 introduce sanciones tipo GDPR; alinear a partir de 2026.            |
| Ley 29.733 (Perú)              | Registro de bancos de datos personales obligatorio.                            |
| PIPL (China)                   | Localización de datos; transferencia internacional con CAC approval.           |
| APPI (Japón)                   | Notificación obligatoria de uso secundario.                                    |
| PDPA (Singapur / Malasia / TH) | Consent mandatorio; restricciones de transferencia internacional.              |
| POPIA (Sudáfrica)              | Information Officer obligatorio; data subject rights similares a GDPR.         |

**Regla común**: ningún dato productivo cruza el perímetro de producción sin pasar por un pipeline de anonimización auditable.

## Herramientas

| Herramienta            | Propósito                                                          |
|------------------------|--------------------------------------------------------------------|
| **ARX**                | Anonimización k-anon / l-diversity, GUI + CLI. OSS (Java).         |
| **Faker (js/py/java)** | Generación sintética con locales globales (ver Faker — locales globales). |
| **Snowfakery**         | DSL declarativo para generar datasets relacionales coherentes.     |
| **Synthea**            | Generación sintética para salud (estándar HL7/FHIR).               |
| **Microsoft Presidio** | Detección y enmascarado automático de PII en texto libre.          |
| **DataVeil / Tonic**   | Comerciales; pipelines de anonimización a escala.                  |

## Pipeline de anonimización recomendado

```
[DB prod (snapshot)] 
    → [Detección de PII con Presidio / reglas]
    → [Anonimización por columna (Faker / FPE / tokenización)]
    → [Validación de integridad referencial]
    → [Validación k-anon mínimo]
    → [Carga a DB QA]
    → [Hash del dataset registrado en evidencia]
```

Cada paso debe ser auditable: la salida lleva un manifest con la regla aplicada por columna y el hash del dataset.

## Faker — locales globales

Elegir el locale por **jurisdicción del cliente**, no por defaults regionales. Mantener un mapping `cliente → locale(s)` versionado.

```javascript
// JavaScript — seleccionar el locale por cliente
const { faker } = require('@faker-js/faker/locale/en_US');
// otras opciones disponibles: en_GB, de_DE, fr_FR, it_IT, es_ES,
// pt_BR, es_MX, es_CO, ja_JP, zh_CN, ko_KR, ar_SA, hi_IN, ru_RU
faker.seed(12345);

const usuario = {
  nombre: faker.person.firstName(),
  apellido: faker.person.lastName(),
  email: faker.internet.email({ provider: 'example.com' }),
  telefono: faker.phone.number(),               // E.164 formateado por locale
  direccion: faker.location.streetAddress() + ' (TEST)',
};
```

```python
# Python — múltiples locales en paralelo
from faker import Faker
fake_us = Faker('en_US')
fake_de = Faker('de_DE')
fake_jp = Faker('ja_JP')
fake_br = Faker('pt_BR')
Faker.seed(12345)
```

```java
// Java — Datafaker
import net.datafaker.Faker;
import java.util.Locale;
import java.util.Random;

Faker fakerUS = new Faker(new Locale("en", "US"), new Random(12345));
Faker fakerDE = new Faker(new Locale("de", "DE"), new Random(12345));
```

Para identificadores nacionales que `faker` no incluye out-of-the-box (CPF/CNPJ Brasil, RUT Chile, Aadhaar India, NHS UK), usar paquetes dedicados o custom providers — ver `synthetic-data-faker.md`.

## Restricciones

- La anonimización es responsabilidad del **equipo de datos del cliente**, no del equipo de QA. QA recibe el dataset ya anonimizado.
- La pseudonimización **no es** anonimización (es reversible); para cumplimiento, exige anonimización irreversible.
- Nunca confíes en "anonimización" hecha solo con masking de UI: el backend sigue con el dato real.
- Documenta en cada release qué dataset se usó y su hash.
- Encadena con `[[calidad-test-evidence-and-traceability]]`.
