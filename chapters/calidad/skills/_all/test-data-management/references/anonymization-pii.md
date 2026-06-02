# Anonimización de PII — Técnicas, Reglas por Dato, Cumplimiento (LATAM + Estados Unidos)

Cuando no es viable usar datos sintéticos puros y se requiere un snapshot prod-like, los datos deben anonimizarse **antes** de salir del perímetro productivo. Este documento describe técnicas, reglas por tipo de dato y herramientas, aplicables al alcance del Chapter (LATAM + Estados Unidos). Los identificadores universales aparecen en la sección principal; los identificadores nacionales del alcance se cubren en anexos.

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

## Reglas por tipo de dato — identificadores universales

Identificadores y campos que aparecen en virtualmente cualquier sistema del alcance, independientemente del país del cliente.

### Identificación e identidad

| Dato                       | Regla                                                                                   |
|----------------------------|-----------------------------------------------------------------------------------------|
| Email                      | Dominio reservado `@example.com` / `@example.org` (RFC 2606)                            |
| Teléfono internacional E.164 | Prefijo país real + número generado en rango reservado del país (ver tabla por país)  |
| Dirección postal           | Faker con locale + sufijo `(TEST)`                                                      |
| IP address (v4/v6)         | Generar en rangos reservados (`192.0.2.0/24`, `198.51.100.0/24`, `2001:db8::/32`)       |
| MAC address                | Generar en rango locally-administered (`02:xx:xx:xx:xx:xx`)                             |
| Passport number            | Generar formato plausible por país; nunca números reales                                |
| IBAN                       | Generar con MOD-97 correcto + país de testing (`XX99...`) o BIN fake. Puede aparecer en bancos LATAM que operan con clientes globales |

### Contacto

| Dato      | Regla                                                                              |
|-----------|------------------------------------------------------------------------------------|
| Email     | Dominio reservado `@example.com` / `@example.org` (RFC 2606)                       |
| Teléfono  | Prefijo del país real, número en rango reservado del país (ver Faker por locale)   |
| Dirección | Faker con locale + sufijo `(TEST)`                                                 |

### Financiero (universal)

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

## Reglas por tipo de dato — anexos del alcance

Cada anexo cubre identificadores nacionales del alcance del Chapter. Activar solo el subset que aplica al cliente.

### Anexo LATAM

| Dato                                      | Regla                                                                                   |
|-------------------------------------------|-----------------------------------------------------------------------------------------|
| Cédula Colombia (NUIP)                    | Generar 10 dígitos numéricos sin validación oficial; prefijo `99` para marcar sintético |
| CURP México                               | 18 chars; generar con `faker-js` locale `es_MX` con custom provider                    |
| RFC México                                | 13 chars (persona física) / 12 (moral); generar plausible, marcar prefijo `XAXX`        |
| RUT Chile                                 | Generar 8 dígitos + DV calculado (módulo 11)                                            |
| CPF Brasil                                | 11 dígitos + DV calculado (módulo 11); usar `faker-br` `cpf()`                          |
| CNPJ Brasil                               | 14 dígitos + DV calculado; `faker-br` `cnpj()`                                          |
| DNI Argentina                             | 7-8 dígitos numéricos                                                                   |
| DNI Perú                                  | 8 dígitos numéricos                                                                     |
| Cédula nacional (formato por país)        | Para Centroamérica + Caribe (Costa Rica, Panamá, República Dominicana, Honduras, Guatemala, El Salvador, Nicaragua) usar el formato local del documento; generar dígitos sintéticos sin reusar productivos |

### Anexo Estados Unidos

| Dato                          | Regla                                                                          |
|-------------------------------|--------------------------------------------------------------------------------|
| SSN (EE.UU.)                  | Rango reservado `000-xx-xxxx` / `9xx-xx-xxxx`; nunca SSN real                  |
| EIN (EE.UU.)                  | 9 dígitos formato `xx-xxxxxxx`; usar rango de testing                          |
| ITIN (EE.UU.)                 | 9 dígitos empezando por `9`, cuarto dígito 7 u 8                               |
| Driver's License (state-issued)| Formato por estado (variable 8-13 chars); generar plausible                   |
| Medicare Beneficiary ID (MBI) | 11 chars alfanuméricos formato definido por CMS; aplicar cuando el sistema toca salud bajo HIPAA |

## Cumplimiento por marco

Ningún dato productivo cruza el perímetro de producción sin pasar por un pipeline de anonimización auditable. Cada marco del alcance añade reglas específicas:

### Internacional (aplicación universal)

| Marco            | Implicaciones para QA                                                          |
|------------------|--------------------------------------------------------------------------------|
| PCI-DSS 4.0      | Tarjetas: nunca PAN real fuera de zona PCI; tokenización obligatoria.          |
| ISO 27001 / 27018| Política documentada de tratamiento de datos en QA; control de acceso al dataset. |
| SOC 2            | Evidencia auditable de anonimización por release.                              |

### Estados Unidos

| Marco                  | Implicaciones para QA                                                          |
|------------------------|--------------------------------------------------------------------------------|
| HIPAA                  | Safe Harbor (eliminar 18 identifiers) o Expert Determination para PHI.         |
| CCPA / CPRA            | Right to delete; documentar uso en QA y permitir purga bajo solicitud.         |
| SOX                    | Trazabilidad de los datasets usados en QA de sistemas financieros públicos.    |
| GLBA                   | Salvaguardas técnicas para datos financieros de consumidores.                  |
| FedRAMP                | Anonimización + segregación de ambientes obligatoria; auditoría continua.      |

### LATAM

| Marco                          | Implicaciones para QA                                                          |
|--------------------------------|--------------------------------------------------------------------------------|
| Ley 1581 / Decreto 1377 (CO)   | Datos en QA deben anonimizarse o ser sintéticos. Registrar tratamiento.        |
| LGPD (BR)                      | Anonimización irreversible o consentimiento explícito. DPO obligatorio.        |
| LFPDPPP (MX)                   | Aviso de privacidad obligatorio; principio de finalidad limita uso en QA.      |
| Ley 19.628 / Ley 21.719 (CL)   | Ley 21.719 introduce sanciones reforzadas; alinear a partir de 2026.           |
| Ley 25.326 (AR)                | Datos sensibles requieren consentimiento expreso por escrito.                  |
| Ley 29.733 (PE)                | Registro de bancos de datos personales obligatorio.                            |
| Otras jurisdicciones LATAM (Centroamérica, Caribe) | Aplicar marco nacional + estándares internacionales como mínimo común. |

**Regla común**: ningún dato productivo cruza el perímetro de producción sin pasar por un pipeline de anonimización auditable.

## Herramientas

| Herramienta            | Propósito                                                          |
|------------------------|--------------------------------------------------------------------|
| **ARX**                | Anonimización k-anon / l-diversity, GUI + CLI. OSS (Java).         |
| **Faker (js/py/java)** | Generación sintética con locales del alcance (ver Faker — locales). |
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

## Faker — locales del alcance

Elegir el locale por **jurisdicción del cliente** dentro del alcance del Chapter (LATAM + Estados Unidos). Mantener un mapping `cliente → locale(s)` versionado.

```javascript
// JavaScript — seleccionar el locale por cliente
const { faker } = require('@faker-js/faker/locale/en_US');
// otras opciones del alcance: es_CO, es_MX, es_AR, es_CL, es_PE, pt_BR,
// y es genérico para Centroamérica + Caribe + Uruguay + Bolivia + Ecuador + Paraguay donde no hay locale dedicado
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
fake_co = Faker('es_CO')
fake_mx = Faker('es_MX')
fake_br = Faker('pt_BR')
Faker.seed(12345)
```

```java
// Java — Datafaker
import net.datafaker.Faker;
import java.util.Locale;
import java.util.Random;

Faker fakerUS = new Faker(new Locale("en", "US"), new Random(12345));
Faker fakerCO = new Faker(new Locale("es", "CO"), new Random(12345));
Faker fakerBR = new Faker(new Locale("pt", "BR"), new Random(12345));
```

Para identificadores nacionales que `faker` no incluye out-of-the-box (CPF/CNPJ Brasil, RUT Chile, NUIP/CURP/RFC), usar paquetes dedicados o custom providers — ver `synthetic-data-faker.md`.

## Restricciones

- La anonimización es responsabilidad del **equipo de datos del cliente**, no del equipo de QA. QA recibe el dataset ya anonimizado.
- La pseudonimización **no es** anonimización (es reversible); para cumplimiento, exige anonimización irreversible.
- Nunca confíes en "anonimización" hecha solo con masking de UI: el backend sigue con el dato real.
- Documenta en cada release qué dataset se usó y su hash.
- Para clientes fuera del alcance del Chapter (LATAM + Estados Unidos), escalar para definir reglas adicionales; no extender este documento por defecto.
- Encadena con `[[calidad-test-evidence-and-traceability]]`.
