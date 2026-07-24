
# Templating dinámico y seed determinista

Motor de templates: **Handlebars + Faker.js**. Aplica en bodies, headers, data buckets, contenido/path de archivos y rules. El objetivo en este chapter no es realismo decorativo: es que el mock responda **coherente con el request** y **reproducible entre corridas**.

## Helpers de request (respuestas que reflejan lo que llegó)

```json
{
  "userId": "{{urlParam 'id'}}",
  "name": "{{queryParam 'name' 'John'}}",
  "lang": "{{{header 'Accept-Language' 'en'}}}",
  "echoedAmount": {{body 'amount' 0}}
}
```

- `{{body 'path' 'default'}}` — lee el body entrante (object-path o JSONPath). Con content-type XML/SOAP, lee la representación xml-js (ver `soap-xml-mocking.md`).
- `{{urlParam}}`, `{{queryParam}}`, `{{header}}`, `{{cookie}}`, `{{method}}`, `{{baseUrl}}`.

Regla del chapter: todo campo del response que el contrato define como eco o derivado del request (ids en path, montos, referencias) DEBE usar estos helpers, nunca valores fijos — de lo contrario el test valida coincidencias casuales.

## Faker con seed fijo

```bash
mockoon-cli start --data mocks/mockoon/environment.json --port 3010 \
  --faker-seed 12345 --faker-locale es
```

- `--faker-seed` produce la **misma secuencia de datos en cada arranque**: el dataset inicial de los buckets y los valores `{{faker ...}}` son reproducibles. Usar el mismo valor que el `FAKER_SEED` de la suite (`[[calidad-test-data-management]]`, `references/synthetic-data-faker.md`) para que datos del test y datos del mock salgan de la misma política.
- `--faker-locale` alinea el locale a la jurisdicción del cliente (mismos locales que la suite: `es_CO`, `es_MX`, `pt_BR`, `en_US`, etc. — verificar disponibilidad del locale en Faker; fallback `es`).
- Sintaxis: `{{faker 'person.firstName'}}`, `{{faker 'number.int' min=10 max=100}}`, `{{faker 'string.alphanumeric' 25}}`.

## Otros helpers útiles para escenarios de prueba

- `{{#repeat min max}}` — listas de tamaño controlado (con seed fijo, tamaño estable).
- `{{oneOf (array 'ACTIVE' 'INACTIVE')}}` — enums del spec (con seed fijo, determinista).
- `{{uuid}}`, `{{objectId}}`, `{{now 'yyyy-MM-dd'}}`, `{{#switch}}/{{#case}}`.
- `{{setVar}}`/`{{@var}}` (locales al request), `{{setGlobalVar}}`/`{{getGlobalVar}}` (cross-request, ver `stateful-crud-and-data-buckets.md`).

## Respuestas múltiples, rules y latencia

- Cada ruta admite N respuestas; modos: **rules** (default — discriminar por body/query/header/route param/variable global), **sequential** (200 → 500 → 404, cicla; útil para probar retry logic), **random** (evitar en suites deterministas salvo que el test lo controle), **fallback** (cae a la siguiente ruta y finalmente al proxy — la base del hybrid).
- Latencia global por environment + por respuesta ("Response delay" en ms): modela timeouts y esperas del contrato. `--enable-random-latency` la aleatoriza entre 0 y el valor — **no usarlo** en corridas que validan determinismo.

## Anti-patrones

- Respuestas `random` en escenarios que el test asume deterministas: el smoke gate se vuelve flaky por diseño.
- Templating pesado + `--log-transaction` en corridas grandes: degrada el mock (single-process Node); para el smoke 1:1 de K6 mantener respuestas livianas.
- Reglas de negocio inventadas en rules que no existen en spec/firma: el mock no es el lugar para "adivinar" el backend.
