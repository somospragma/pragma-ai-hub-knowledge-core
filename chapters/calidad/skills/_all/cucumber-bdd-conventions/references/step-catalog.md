# Step Catalog — inventario de steps reutilizables

El catálogo es un artefacto de primera clase del arquetipo, no documentación opcional. Es lo único que permite a una persona nueva —o a un agente— saber qué vocabulario Gherkin ya existe antes de inventar uno nuevo.

## Ubicación y formato

Un único archivo Markdown versionado con el código, en un lugar previsible del repositorio (`docs/step-catalog.md` o junto a las specs del proyecto). Una tabla por categoría funcional:

| Columna | Contenido |
|---|---|
| `Texto del step` | Texto exacto, con los parámetros en formato Cucumber Expressions (`{string}`, `{int}`, `{plataforma}`) |
| `Tipo` | `Given`, `When` o `Then` |
| `Plataformas` | Lista de plataformas donde está implementado |
| `Archivo` | Ruta relativa del archivo de definiciones que lo implementa |
| `Categoría` | Categoría funcional a la que pertenece |

Las categorías se derivan del dominio, no de la técnica. Un juego que funciona en la mayoría de arquetipos de aplicación transaccional: `auth`, `navegacion`, `mensajes`, `formularios`, `recuperacion`, `splash`, `dashboard`. Añadir categorías es barato; mezclarlas no.

Ejemplo de fila:

```
| el sistema debe mostrar el mensaje {string} en {plataforma} | Then | web, android, ios, ipad, tablet | steps/common/messages.steps.ts | mensajes |
```

## Protocolo de consulta (obligatorio antes de redactar Gherkin)

1. Abrir el catálogo **antes** de escribir el primer escenario, no después.
2. Listar los steps del catálogo que cubren la historia en curso, por categoría.
3. Para cada acción o verificación que el catálogo **no** cubra, ejecutar la búsqueda en código descrita abajo antes de declararla inexistente.
4. Declarar en el turno la clasificación resultante (`reuse` / `extend-platform` / `new-local` / `new-shared`). Esa tabla es la traza de que el paso se hizo.

## Búsqueda en código: cómo se hace bien

El catálogo puede estar incompleto; el código es la fuente de verdad. La búsqueda debe cubrir **todas las épicas y todas las plataformas**, porque el registro de Cucumber es global por perfil.

```bash
# 1. Texto literal (o su fragmento más distintivo, sin los parámetros)
grep -rn "debe mostrar el mensaje" src --include='*.steps.ts'

# 2. Inventario completo de definiciones, para leer variantes semánticas
grep -rhoE "^(Given|When|Then)\('([^']+)'" src --include='*.steps.ts' | sort -u

# 3. Mismo texto, otras plataformas: buscar sin el sufijo
grep -rn "el usuario cierra sesión" src --include='*.steps.ts'
```

La segunda búsqueda es la que más rinde: el step existe pero redactado distinto ("el sistema muestra el mensaje" contra "el sistema debe mostrar el mensaje"). Un duplicado semántico no rompe la ejecución pero fragmenta el vocabulario, y en la siguiente historia alguien reimplementa la tercera variante.

## Cuándo un step entra al catálogo

Entra todo step **transversal**: el que aplica o va a aplicar a más de una épica. No entran los steps específicos de una épica, que se quedan en su carpeta y no se documentan — inflarían el catálogo hasta volverlo inútil.

La señal de que un step local debe promoverse a compartido es que una segunda épica lo necesita. En ese momento se mueve a la carpeta compartida, se registra en el catálogo y se actualizan los imports. No se copia.

## Generación inicial cuando no existe

En un arquetipo que ya tiene decenas de features y ningún catálogo, generarlo es el primer entregable, antes de agregar nada:

```bash
grep -rn -oE "^(Given|When|Then)\('([^']+)'" src --include='*.steps.ts' \
  | sed 's/:\(Given\|When\|Then\)(.\(.*\).$/ | \1 | \2/' \
  | sort -t'|' -k3
```

La salida se ordena por texto de step, con lo que los duplicados y las variantes semánticas quedan adyacentes y visibles. El inventario resultante se agrupa a mano en categorías: es trabajo de una sola vez y paga en cada historia siguiente.

## Mantenimiento

- Un step compartido nuevo o modificado se refleja en el catálogo **en el mismo cambio**. Sin excepción.
- Un step eliminado se elimina del catálogo.
- Si el catálogo y el código divergen, el código manda y el catálogo se corrige; nunca al revés.
- La propiedad 2 de `static-correctness-properties.md` verifica esta consistencia por análisis estático.
