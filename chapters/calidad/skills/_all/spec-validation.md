---
id: calidad-spec-validation
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: Valida OpenAPI 3.x, Swagger 2.0 y WSDL antes de generar pruebas; extrae endpoints, base URL, security schemes y enums.
tags: [openapi, swagger, wsdl, validation, contract]
---

# Spec Validation — Validación de Contratos Antes de Generar

## Cuándo aplicar

Aplica este skill **siempre** antes de generar cualquier prueba funcional o de performance. Es el paso 3 de `[[calidad-route-test-generation]]`.

Si la validación falla, **detén la generación** y reporta el error específico al usuario. Bajo ninguna circunstancia se generan pruebas a partir de un spec inválido, incompleto o inferido.

## Reglas mínimas de validación

### OpenAPI 3.x / Swagger 2.0

1. `len(spec_content) > 200` caracteres.
2. El contenido debe ser parseable como **JSON o YAML**. Si ambos fallan → error.
3. Debe contener al menos una de las claves `openapi` (3.x) o `swagger` (2.0) en la raíz.
4. Debe contener un objeto `info` con `title` y `version`.
5. Debe contener `paths` y este **no puede estar vacío** (`len(paths) > 0`).
6. Cada operación bajo `paths.<path>.<method>` debe tener `operationId` o, en su defecto, generar uno determinista a partir de `method + path`.

### WSDL

1. `len(spec_content) > 100` caracteres.
2. El contenido debe ser parseable como **XML**. Si falla → error.
3. Debe contener un elemento raíz `<definitions>` (namespace `http://schemas.xmlsoap.org/wsdl/`).
4. Debe contener al menos un `<service>/<port>/<soap:address location="...">` (o equivalente `soap12:address`) del que extraer la base URL.
5. Debe contener al menos un `<binding>` con operaciones SOAP.

### Detección de autenticación

- **OpenAPI 3.x**: buscar `components.securitySchemes` (Bearer, OAuth2, ApiKey, Basic). Si existe, activar el flujo de autenticación correspondiente en la generación.
- **Swagger 2.0**: buscar `securityDefinitions`. Misma semántica.
- **WSDL**: detectar policies `<wsp:Policy>` y headers de `wsse:Security` para activar flujos WS-Security.
- Si **no hay** definiciones de seguridad, **no inventes** un mecanismo de auth. Documenta en el reporte de generación que las pruebas asumen endpoints públicos.

## Salidas esperadas del skill

El skill produce un objeto estructurado consumido por los workflows de generación:

```yaml
base_url: "https://api.example.com/v1"     # de servers[0].url (OpenAPI), host+basePath (Swagger 2.0), soap:address (WSDL)
endpoints:
  - path: "/users/{id}"
    method: "GET"
    operation_id: "getUserById"
    tags: ["users"]
    request_schema: {...}                  # parameters + requestBody
    response_schemas:
      "200": {...}
      "404": {...}
security_schemes:
  - type: "bearer"
    name: "BearerAuth"
enums:
  UserStatus: ["ACTIVE", "INACTIVE", "BLOCKED"]
```

## Pseudocódigo de validación

Inspirado en `entrada/strands-ms-py-agent-qa/karate/validator.py` y `entrada/strands-ms-py-agent-qa/k6/swagger_parser.py`:

```python
def validate_spec(spec_content: str, kind: str) -> ValidationResult:
    if kind in ("openapi", "swagger"):
        if len(spec_content) < 200:
            raise SpecError("spec vacío o demasiado corto (<200 chars)")
        try:
            spec = json.loads(spec_content)
        except json.JSONDecodeError:
            try:
                spec = yaml.safe_load(spec_content)
            except yaml.YAMLError as e:
                raise SpecError(f"no es JSON ni YAML válido: {e}")
        if "openapi" not in spec and "swagger" not in spec:
            raise SpecError("no contiene clave raíz 'openapi' ni 'swagger'")
        if not spec.get("paths"):
            raise SpecError("no contiene paths o paths está vacío")
        return extract_endpoints(spec)

    if kind == "wsdl":
        if len(spec_content) < 100:
            raise SpecError("WSDL vacío o demasiado corto (<100 chars)")
        try:
            root = ET.fromstring(spec_content)
        except ET.ParseError as e:
            raise SpecError(f"WSDL no es XML válido: {e}")
        if not root.tag.endswith("definitions"):
            raise SpecError("WSDL no contiene <definitions> en raíz")
        if not find_soap_address(root):
            raise SpecError("WSDL sin endpoint <soap:address location>")
        return extract_wsdl_operations(root)
```

## Errores típicos y mensajes esperados

| Causa                              | Mensaje al usuario                                      |
|------------------------------------|---------------------------------------------------------|
| `spec_content` vacío               | "spec vacío"                                            |
| Texto no parseable                 | "no es JSON ni YAML válido"                             |
| Falta `paths` o está vacío         | "el spec no contiene paths"                             |
| WSDL sin XML válido                | "WSDL no es XML válido"                                 |
| WSDL sin `<soap:address>`          | "WSDL sin endpoint"                                     |
| Solo el path, no el contenido      | "se requiere el CONTENIDO del spec, no la ruta del archivo" |

## Restricciones

- **NUNCA proceder a generación si la validación falla.** Reporta el error específico y pide al usuario el spec corregido.
- **NUNCA inferir** endpoints, parámetros, schemas o auth que no estén en el spec. Si el spec dice que un campo es `string`, no lo conviertas en `integer` "porque tiene más sentido".
- Si el usuario provee únicamente la **ruta del archivo** del spec en lugar de su contenido, rechaza con el mensaje correspondiente y explica que se requiere el contenido completo.
- Encadena con `[[calidad-mandatory-inputs-protocol]]` para asegurar que el spec recibido es el esperado.
