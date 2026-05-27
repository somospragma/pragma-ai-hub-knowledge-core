# Anonimización de PII — Técnicas, Reglas por Dato, Cumplimiento LATAM

Cuando no es viable usar datos sintéticos puros y se requiere un snapshot prod-like, los datos deben anonimizarse **antes** de salir del perímetro productivo. Este documento describe técnicas, reglas por tipo de dato y herramientas.

## Técnicas

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

## Reglas por tipo de dato LATAM

### Identificación personal

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

### Contacto

| Dato      | Regla                                                                              |
|-----------|------------------------------------------------------------------------------------|
| Email     | Dominio reservado `@example.com` / `@example.org` (RFC 2606)                       |
| Teléfono  | Prefijo del país real, número generado en rango `555-XXX-XXXX` (formato NANP-like) |
| Dirección | Faker con locale + sufijo `(TEST)`                                                 |

### Financiero

| Dato                 | Regla                                                                                       |
|----------------------|---------------------------------------------------------------------------------------------|
| Tarjeta de crédito   | Generar Luhn-valid pero usando **BIN reservado de testing** (Visa 4111-1111-1111-1111, etc.)|
| CVV                  | Siempre `123` o `000` (nunca real)                                                          |
| IBAN                 | Generar con MOD-97 correcto + país ficticio (`XX99...`) o BIN de banco fake                 |
| Cuenta bancaria local| Generar dígitos según longitud del país; nunca reusar dígitos productivos                    |

### Salud / sensible

| Dato                | Regla                                                                              |
|---------------------|------------------------------------------------------------------------------------|
| Historia clínica    | Generar con vocabulario clínico fake; nunca derivar de paciente real                |
| Diagnóstico         | Códigos CIE-10 plausibles pero aleatorios                                          |
| Tipo de sangre      | Distribución uniforme                                                              |

## Cumplimiento LATAM por marco

| País      | Norma                       | Implicaciones para QA                                                         |
|-----------|-----------------------------|-------------------------------------------------------------------------------|
| Colombia  | Ley 1581 / Decreto 1377     | Datos en QA deben anonimizarse o ser sintéticos. Registrar tratamiento.       |
| Brasil    | LGPD (Lei 13.709)           | Anonimización irreversible o consentimiento explícito. DPO obligatorio.       |
| México    | LFPDPPP                     | Aviso de privacidad obligatorio; principio de finalidad limita uso en QA.     |
| Argentina | Ley 25.326                  | Datos sensibles requieren consentimiento expreso por escrito.                 |
| Chile     | Ley 19.628 / Ley 21.719 (2024)| Nueva ley 21.719 introduce sanciones tipo GDPR; alinear a partir de 2026.   |
| Perú      | Ley 29.733                  | Registro de bancos de datos personales obligatorio.                           |

**Regla común**: ningún dato productivo cruza el perímetro de producción sin pasar por un pipeline de anonimización auditable.

## Herramientas

| Herramienta            | Propósito                                                          |
|------------------------|--------------------------------------------------------------------|
| **ARX**                | Anonimización k-anon / l-diversity, GUI + CLI. OSS (Java).         |
| **Faker (js/py/java)** | Generación sintética con locales LATAM (`es_CO`, `pt_BR`, etc.).  |
| **Snowfakery**         | DSL declarativo para generar datasets relacionales coherentes.     |
| **Synthea**            | Generación sintética para salud (estándar HL7/FHIR).               |
| **Microsoft Presidio** | Detección y enmascarado automático de PII en texto libre.          |
| **DataVeil / Tonic**   | Comerciales; pipelines de anonimización a escala.                   |

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

## Snippet — Faker locale LATAM (Node)

```javascript
const { faker } = require('@faker-js/faker/locale/es_CO');
faker.seed(12345);

const usuario = {
  nombre: faker.person.firstName(),
  apellido: faker.person.lastName(),
  email: faker.internet.email({ provider: 'example.com' }),
  telefono: faker.phone.number('+57 3## ### ####'),
  direccion: faker.location.streetAddress() + ' (TEST)',
};
```

Para CPF/CNPJ Brasil, usar `@faker-js/faker/locale/pt_BR` o paquete `brazilian-utils`. Para RUT chileno, custom provider o `rut.js`.

## Restricciones

- La anonimización es responsabilidad del **equipo de datos del cliente**, no del equipo de QA. QA recibe el dataset ya anonimizado.
- La pseudonimización **no es** anonimización (es reversible); para cumplimiento, exige anonimización irreversible.
- Nunca confíes en "anonimización" hecha solo con masking de UI: el backend sigue con el dato real.
- Documenta en cada release qué dataset se usó y su hash.
- Encadena con `[[calidad-test-evidence-and-traceability]]`.
