
# Mock de servicios SOAP/XML

Mockoon **no importa WSDL**. El mock SOAP se construye a mano (o vía `[[calidad-generate-mockoon-environment-prompt]]`) a partir del WSDL ya validado por `[[calidad-spec-validation]]`, con este patrón:

## Patrón: una ruta POST por endpoint SOAP, rules por operación

Los servicios SOAP típicamente exponen un único endpoint HTTP y discriminan la operación por el body. Mockoon parsea bodies con content-type `text/xml`, `application/xml` o `application/soap+xml` a una representación JSON interna (convención xml-js: `_attributes`/`_text`), accesible en rules y templating:

- **Rule por operación**: target `body`, path `Envelope.Body.consultarSaldo` (existencia) o `Envelope.Body.consultarSaldo.numeroCuenta._text` (valor). Es object-path sobre la representación xml-js, **no XPath real**.
- **Una respuesta por operación** del WSDL, más una respuesta default con SOAP Fault.

## Respuesta SOAP

Body XML con templating + header correcto:

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <consultarSaldoResponse>
      <numeroCuenta>{{body 'Envelope.Body.consultarSaldo.numeroCuenta._text'}}</numeroCuenta>
      <saldo>{{faker 'number.int' min=1000 max=999999}}</saldo>
      <moneda>COP</moneda>
    </consultarSaldoResponse>
  </soap:Body>
</soap:Envelope>
```

Header de la respuesta: `Content-Type: text/xml; charset=utf-8` (o `application/soap+xml` para SOAP 1.2 — respetar lo que el WSDL declare). Status 200 incluso para SOAP Faults de negocio (convención SOAP 1.1); usar 500 solo si el WSDL/firma lo especifica.

## SOAP Fault como respuesta default

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <soap:Fault>
      <faultcode>soap:Client</faultcode>
      <faultstring>Operacion no reconocida o payload invalido</faultstring>
    </soap:Fault>
  </soap:Body>
</soap:Envelope>
```

Así, cualquier request que no matchee las rules de operaciones conocidas recibe un Fault — el equivalente SOAP del 404, y exactamente lo que un test negativo de Karate espera poder provocar.

## Límites

- Sin validación de schema XSD del request: si el test necesita verificar que su propio payload es válido contra el XSD, esa validación vive en el test (Karate puede validar estructura del response con `match` sobre XML), no en el mock.
- Namespaces: el parseo xml-js conserva los prefijos tal como llegan (`soap:Envelope` vs `soapenv:Envelope`). Las rules deben usar el prefijo que el cliente real envía — verificar con un request de humo y `--log-transaction` antes de dar el mock por bueno.
- Para servicios legacy con encoding no-UTF8 o MTOM/attachments, Mockoon no es la herramienta; escalar a WireMock y documentar la decisión en STRATEGY.md.
