
# Fórmula real de cobertura mínima

La cobertura mínima por endpoint NO es "5 escenarios fijos". Se calcula con la fórmula siguiente, en función del contrato real del endpoint.

## Fórmula

```
real_minimum = 1 (happy)
             + 1 (contract)
             + 1 (data-driven)
             + 4 (body base: missing / empty / null / malformed)
             + N  × 3 (required fields: absent / null / invalid-type)
             + Ne × 1 (enum: invalid value)
             + H  × 1 (mandatory headers: missing)
             + Hf × 1 (headers con formato: invalid format)
             + E  × [3–5] (encryption: wrong-key / invalid-format / plaintext / missing-header)
```

Donde:
- `N` = número de required fields del body.
- `Ne` = número de campos con enum.
- `H` = número de headers obligatorios.
- `Hf` = número de headers con formato validable (UUID, email, date-time).
- `E` = `1` si hay cifrado, `0` si no.

## Ejemplo numérico

`POST /transferencia` con: 3 required fields, 1 enum, 5 mandatory headers (3 con formato), cifrado activo.

```
1  (happy)
+ 1  (contract)
+ 1  (data-driven)
+ 4  (body base)
+ 9  (3 fields × 3)
+ 1  (1 enum)
+ 5  (5 headers × 1)
+ 3  (3 headers con formato × 1)
+ 3  (encryption mínimo)
= 28 escenarios
```

Reportar "5 escenarios" para este endpoint es cobertura cosmética.

## Cuándo aplica el piso de 5

Sólo para endpoints triviales: GET sin parámetros, sin required fields, sin mandatory headers, sin cifrado (ej: `GET /health`, `GET /version`). En esos casos: 1 happy + 1 contract + 1 data-driven (si tiene query opcional) + 2 negativos básicos = ~5.

## Uso

Antes de generar features, calcula `real_minimum` por endpoint y declara el número en la entrega. Si vas a reportar menos, justifica explícitamente por qué (campo no aplicable, header sin formato validable, etc).

## Modulación por riesgo

El `real_minimum` es el techo teórico de cobertura negativa. En la práctica, no todos los endpoints justifican el mismo nivel de esfuerzo: un `GET /paises` no merece la misma profundidad que un `POST /transferencia`. Para evitar inflar la suite con escenarios de bajo valor, se modula `real_minimum` con un `risk_factor`.

### Niveles de `risk_factor`

| Nivel      | Criterio                                                                                       | Factor |
|------------|------------------------------------------------------------------------------------------------|--------|
| `CRITICAL` | Transacciones financieras, datos sensibles (PII, salud), flujos regulados (SOX, PCI, HIPAA)    | 1.0    |
| `HIGH`     | Operaciones core no transaccionales, integraciones externas, escrituras de estado de negocio    | 0.7    |
| `MEDIUM`   | Queries no críticas, lecturas con filtros, configuraciones de usuario                          | 0.4    |
| `LOW`      | Health checks, metadata, catálogos estáticos, endpoints administrativos internos               | 0.2    |

### Fórmula efectiva

```
effective_minimum = max(3, ceil(real_minimum × risk_factor))
```

El piso de **3** (happy + contract + 1 negativo) aplica para cualquier endpoint no-trivial: incluso los `LOW` deben tener cobertura mínima de smoke + contrato + un negativo representativo.

### Ejemplos

| Endpoint                              | Riesgo     | `real_minimum` | Cálculo                  | `effective_minimum` |
|---------------------------------------|------------|----------------|--------------------------|---------------------|
| `POST /transferencia`                 | CRITICAL   | 28             | `ceil(28 × 1.0)`         | 28                  |
| `POST /preferencias-notificacion`     | MEDIUM     | 28             | `ceil(28 × 0.4) = 12`    | 12                  |
| `GET /paises`                         | LOW        | 28             | `ceil(28 × 0.2) = 6`     | 6                   |
| `GET /health`                         | LOW        | 5              | `ceil(5 × 0.2) = 1` → 3  | 3 (piso)            |

### Quién asigna el riesgo

La prioridad de riesgo la fija el **usuario** (PO, QA Lead o risk assessment del negocio), no el agente generador. La asignación por keywords del path es un anti-patrón (`/payment` no implica CRITICAL si es un mock interno).

- Si el usuario no asigna el riesgo, **defaultear a `HIGH`** y solicitar confirmación explícita antes de generar.
- Para el criterio general de cómo asignar prioridades por valor de negocio, ver el skill cross-cutting `[[calidad-business-driven-prioritization]]`.

### Cómo declarar el riesgo

Dos vías equivalentes:

1. **En el spec** como extensión OpenAPI:
   ```yaml
   paths:
     /transferencia:
       post:
         x-pragma-risk: CRITICAL
   ```
2. **Como input del workflow** (en el bloque de `extra_params`):
   ```json
   {
     "risk_map": {
       "POST /transferencia": "CRITICAL",
       "GET /paises": "LOW"
     }
   }
   ```

Si ambos están presentes, el `risk_map` del workflow gana sobre la extensión del spec (permite override puntual sin tocar el contrato).
