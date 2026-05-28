# Legacy SOAP / EJB — Patrones y Adaptación

## Patrones canónicos

- **SOAP envelope**: cada request es un XML envelope con `Header` (auth, WS-Security) y `Body` (operación + parámetros). Las assertions usan XPath.
- **WS-Security**: UsernameToken, X.509 signature, SAML assertion. Validar firma y timestamp (`<wsu:Timestamp>` con `Created`/`Expires`).
- **WSDL**: contrato. Equivalente del OpenAPI. Validar request/response contra el WSDL con `wsimport`/`wsdl2java`.
- **SOAP Faults**: errores devuelven `200 OK` con `<soap:Fault>` en body, con `faultcode`/`faultstring`/`detail`. Las assertions deben revisar `Fault`, no solo el status HTTP.
- **EJB remoto**: típicamente expuesto vía JAX-WS (SOAP) o RMI/IIOP. Para testing externo, conviene exponer un wrapper SOAP/REST.
- **MTOM/XOP**: attachments binarios. Validar el `Content-Type: multipart/related` y el `xop:Include`.

## Framework primario

**Karate** soporta SOAP nativamente: el body puede ser un string XML literal o un archivo `.xml` referenciado, y las assertions usan `match` con XPath (`/soap:Envelope/soap:Body/...`).

```gherkin
Feature: legacy SOAP service

Background:
  * url 'https://legacy.example.com/ws'
  * def envelope = read('classpath:soap/createCustomer.xml')

Scenario: crear cliente
  Given request envelope
  And header SOAPAction = 'createCustomer'
  And header Content-Type = 'text/xml; charset=utf-8'
  When method post
  Then status 200
  And match /Envelope/Body/createCustomerResponse/customerId == '#string'
  And match /Envelope/Body/Fault == '##null'
```

## Complementarios

- **SoapUI** (Open Source o Pro): IDE tradicional, útil cuando el cliente ya tiene suites históricas que vale la pena migrar gradualmente, no reescribir.
- **SOAPSonar** para load testing SOAP.
- **WireMock con extensión SOAP** o **Mountebank** para stubs.
- **soapUI → Karate migration script** para portar suites existentes.

## Migración progresiva: SOAP → REST

Patrón recomendado cuando el cliente está migrando un servicio SOAP a REST:

1. Capturar el contrato SOAP actual con Karate (suite verde que documenta el comportamiento real).
2. Implementar el endpoint REST nuevo.
3. Duplicar cada escenario Karate: uno apunta a SOAP, otro a REST, con las mismas assertions de negocio.
4. Cuando ambos pasan paridad por N días, deprecar el SOAP.

Esto evita el antipatrón "rewrite sin tests" que rompe la paridad funcional.

## Antipatrones

- Asumir que `status 200` significa éxito en SOAP — los Faults también son `200`.
- Hardcodear el envelope completo en cada feature — usa archivos `.xml` reutilizables con placeholders.
- Olvidar WS-Security timestamp — los tokens caducan y los tests pasan en local pero fallan en CI lento.
- Migrar de SOAP a REST sin suite de paridad — regresiones invisibles.
