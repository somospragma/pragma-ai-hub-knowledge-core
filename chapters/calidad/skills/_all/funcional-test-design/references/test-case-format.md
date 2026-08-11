
# Formato del caso de prueba de alto nivel

Formato canónico del chapter, portable a markdown local, Azure Test Plans y Jira (Xray/Zephyr). Gherkin **en español** por defecto.

## Estructura del caso

```markdown
### TC-{HU}-{nn}: {título — comportamiento verificado, no instrucción}
- **Trazabilidad**: HU-123 / CA-2 (+ regla R1 del example map si aplica)
- **Prioridad**: CRITICAL | HIGH | MEDIUM | LOW  (del risk map — [[calidad-business-driven-prioritization]])
- **Técnica**: BVA sobre monto | tabla de decisión R3 | pairwise | ...
- **Nivel sugerido**: api | ui | mobile | manual  (lo confirma la estrategia)
- **Tipo**: funcional | negativo | borde | seguridad | ...
- **Precondiciones**: estado inicial verificable (datos, permisos, estado de la entidad)

Dado un cliente autenticado con saldo disponible de @saldo COP
Cuando intenta transferir @monto COP a una cuenta de terceros
Entonces el sistema @resultado
Y muestra el mensaje @mensaje

| @saldo  | @monto  | @resultado           | @mensaje                  |
| 100000  | 100000  | aprueba la operación | "Transferencia exitosa"   |
| 100000  | 100001  | rechaza la operación | "Saldo insuficiente"      |
```

## Reglas de redacción

1. **Título = comportamiento**, con el resultado implícito ("Rechaza transferencia que excede el saldo"), no "Probar transferencias".
2. **Cada paso Entonces/Y es decidible**: resultado observable con dato concreto. Prohibidas las palabras "correctamente", "adecuadamente", "según lo esperado".
3. **Data-driven por defecto**: variantes de la misma lógica = un caso + tabla de parámetros `@param` (particiones, límites, matrices pairwise). Casos redundantes sin parametrizar son deuda.
4. **Independencia**: cada caso construye su precondición (o la declara como setup); ningún caso depende del residuo de otro.
5. **Datos concretos y obtenibles**: coordinados con `[[calidad-test-data-management]]` (¿ese cliente con ese saldo existe/se puede sembrar?). "Un usuario válido" no es un dato.
6. **Gherkin de comportamiento, no de UI**: "Cuando intenta transferir" y no "Cuando hace click en el botón azul Continuar" — el caso de alto nivel sobrevive a los rediseños de pantalla; el paso a selectores es de la automatización.
7. Casos negativos y de borde llevan `Tipo` explícito — el conteo happy/negativo/borde del lote es parte del entregable.

## Mapeo a destinos

| Campo canónico | Azure Test Plans | Jira + Xray/Zephyr | Automatización |
|---|---|---|---|
| Título | Title | Summary | `Scenario:` |
| Pasos Gherkin | Steps ("paso | resultado esperado") | Steps / Gherkin nativo (Xray Cucumber) | Steps del `.feature` / spec |
| Tabla `@param` | Parameter Values | Datasets (Xray) | `Examples:` |
| Prioridad | Priority 1-4 (CRITICAL=1 ... LOW=4) | Priority | tag `@critical`... |
| Trazabilidad | Link "Tests" a la HU | Link "tests" / requirement coverage | tag `@user-story:HU-123` |

La publicación al ALM la ejecuta `[[calidad-design-test-cases]]` vía `[[calidad-alm-mcp-integration]]`.

## Matriz de trazabilidad (cierre del entregable)

```markdown
| CA | Casos | Positivo | Negativo | Borde |
|---|---|---|---|---|
| CA-1 | TC-123-01, TC-123-02 | 1 | 1 | 0 |
| CA-2 | TC-123-03 (DD 7 filas) | 1 | 4 | 2 |
Cobertura: 100% de CA con >=1 caso. Casos sin CA: 0 (o justificar la regla que cubren).
```
