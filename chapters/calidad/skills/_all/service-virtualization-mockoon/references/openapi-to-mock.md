
# Del spec OpenAPI al mock

Mockoon importa **OpenAPI 3.0 y Swagger 2.0** (JSON y YAML) y convierte: título, server/base path, rutas con parámetros, métodos, status codes, headers, y genera sample responses desde los schemas y examples del spec.

## Dos vías

1. **Arranque directo desde el spec** (rápido, sin estado ni enriquecimiento):

```bash
mockoon-cli start --data ./openapi.yaml --port 3010
```

El CLI acepta la spec como `--data` sin conversión previa. Sirve para un primer humo del mock, pero no permite CRUD stateful ni rules.

2. **Convertir y enriquecer** (la vía estándar del chapter):

```bash
mockoon-cli import --input ./openapi.yaml --output mocks/mockoon/environment.json
```

Después de importar, el agente enriquece el data file (vía `[[calidad-generate-mockoon-environment-prompt]]` o edición dirigida):

- Convertir los recursos CRUD a rutas `crud` + data buckets (correlación de IDs).
- Agregar respuestas de error (401, 404, 422, 500) con rules, derivadas de los status codes del spec.
- Reemplazar valores estáticos por templating Faker donde el realismo importe (ver `dynamic-templating-and-faker-seed.md`).
- Ajustar el puerto a la convención (`3010`) y el `endpointPrefix` al base path real.

## Qué exige el spec para que el mock sea fiel

Esta es la razón por la que `[[calidad-sut-readiness-gate]]` endurece el input `spec` en modo pre-desarrollo:

- **Response schemas completos** por status code: sin `components.schemas` en las respuestas, Mockoon no tiene de dónde derivar los bodies y el mock devuelve estructuras vacías o inventadas → los `match` de Karate y los `check()` de K6 validarían contra ficción.
- **Examples** cuando existan: mejoran la fidelidad de los sample responses.
- **Security schemes declarados**: el mock no valida tokens, pero los tests sí deben enviar los headers que el contrato exige; si el spec no declara `security`, el test tampoco lo inventará.

Si el spec no cumple, **STOP**: pedir al equipo de desarrollo que complete el contrato antes de construir. Un contrato incompleto que se "rellena" a mano en el mock es deuda que explota en el switchover.

## Fidelidad y límites

- El import no trae reglas de negocio (validaciones condicionales, límites, flujos): esas se agregan como rules solo si están declaradas en spec/firma/user story.
- Al exportar de vuelta a OpenAPI se pierden rules, templating y buckets: el data file nativo es la fuente de verdad del mock; el spec sigue siendo la fuente de verdad del contrato.
- Mockoon no valida los requests entrantes contra el spec automáticamente. Si el proyecto necesita esa validación (detectar que el propio test manda payloads inválidos), usar la regla opt-in "valid JSON Schema" por ruta (bucket con el schema + respuesta 400 default), o validar el request en el propio test.
- **WSDL no se importa** — para SOAP ver `soap-xml-mocking.md`.
