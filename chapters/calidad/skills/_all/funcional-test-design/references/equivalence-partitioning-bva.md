
# Particiones de equivalencia y análisis de valores límite (BVA)

## Particiones de equivalencia

Dividir cada entrada (campo, parámetro, estado inicial) en clases donde el sistema se comporta igual: probar un valor por clase equivale a probarlos todos.

Procedimiento:

1. Por cada entrada del CA, listar particiones **válidas** e **inválidas**. Ejemplo, monto de transferencia con regla "entre 1.000 y 20.000.000 COP":
   - Válidas: `[1.000 – 20.000.000]`
   - Inválidas: `< 1.000`, `> 20.000.000`, no numérico, vacío/nulo, negativo, decimales si no se permiten
2. Un caso por partición. Los casos de particiones inválidas van de a UNA inválida por caso (si combinas dos entradas inválidas y el sistema rechaza, no sabes cuál validación actuó).
3. Las particiones invisibles también cuentan: estado del usuario (activo/bloqueado), permisos, configuración regional.

## BVA — valores límite

Los defectos viven en los bordes. Por cada partición con orden (números, longitudes, fechas, tamaños):

| Valor | Ejemplo (límite superior 20.000.000) | Resultado esperado |
|---|---|---|
| Límite exacto | 20.000.000 | Aceptado |
| Límite + 1 (mínimo incremento) | 20.000.001 | Rechazado con mensaje definido |
| Límite − 1 | 19.999.999 | Aceptado |

Y lo simétrico en el límite inferior. Para longitudes de texto: exacto, +1 (truncado o rechazado — el CA debe decir cuál), −1. Para fechas: el día del borde, el siguiente, el anterior (y los bordes del calendario: fin de mes, 29 de febrero, cambio de año).

**Si el CA no define el límite, no se inventa**: es un hallazgo de `[[calidad-funcional-story-analysis]]` (ambigüedad de cuantificación) y vuelve como pregunta al PO. BVA sin límite escrito es adivinación.

## Empaquetado data-driven

Particiones y límites del mismo comportamiento NO generan N casos casi idénticos: generan UN caso parametrizado con su tabla de valores:

```gherkin
Escenario: Validación de monto de transferencia
  Dado un cliente autenticado con saldo suficiente
  Cuando intenta transferir el monto @monto COP
  Entonces el sistema responde @resultado y muestra @mensaje

  | @monto      | @resultado | @mensaje                    |
  | 1000        | acepta     | -                           |
  | 999         | rechaza    | "Monto mínimo 1.000 COP"    |
  | 20000000    | acepta     | -                           |
  | 20000001    | rechaza    | "Monto máximo 20.000.000"   |
  | 0           | rechaza    | "Monto mínimo 1.000 COP"    |
  | -5000       | rechaza    | "Monto inválido"            |
  | abc         | rechaza    | "Monto inválido"            |
```

La tabla ES el registro de la técnica aplicada: quien la lee ve las particiones y los bordes. Formato completo del caso en `test-case-format.md`.
