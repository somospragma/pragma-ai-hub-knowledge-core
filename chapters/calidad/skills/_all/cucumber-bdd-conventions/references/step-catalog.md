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

## Protocolo de consulta (BLOCKER — obligatorio antes de redactar Gherkin)

**No se genera ningún archivo de definiciones hasta completar este protocolo y emitir su tabla.**

1. Abrir el catálogo **antes** de escribir el primer escenario, no después.
2. Listar los steps del catálogo que cubren la historia en curso, por categoría.
3. Para cada acción o verificación que el catálogo **no** cubra, ejecutar la búsqueda en código descrita abajo —**exacta y por similitud**— antes de declararla inexistente.
4. Emitir la tabla de clasificación, con el archivo donde vive cada step existente:

   | Step | Clasificación | Archivo existente | Acción |
   |---|---|---|---|
   | el usuario autenticado visualiza el detalle en Android | `reuse` | `steps/nt-100_.../android/...steps.ts` | **NO crear** |
   | el sistema debe mostrar la fecha del movimiento en tránsito en Android | `new-local` | — | Crear |

   Las clasificaciones son `reuse` / `extend-platform` / `new-local` / `new-shared`. Un step clasificado `reuse` **no se redefine**: el perfil ya lo carga.

Verificado en campo: se redefinieron steps que ya existían en otra épica del mismo proyecto porque la tabla se enunció en la estrategia pero nunca se contrastó contra el glob del perfil. El resultado fue ambigüedad en ejecución y mantenimiento duplicado.

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

### Búsqueda por similitud (no solo exacta)

La búsqueda exacta no basta. Los steps que verifican **elementos comunes** —fechas, montos, estados, títulos, mensajes— existen en varias épicas con texto casi idéntico, y la colisión aparece recién en ejecución:

```bash
# Combinar los sustantivos clave del step candidato, no su texto completo
grep -rniE "fecha.*(transacción|expiración)|(transacción|expiración).*fecha" src --include='*.steps.ts'
grep -rniE "monto|importe|saldo" src --include='*.steps.ts'
```

Si aparecen steps similares, el nuevo se hace **más específico** antes de escribirlo (ver la regla siguiente).

### Regla de especificidad para elementos comunes

Un step que verifica un elemento genérico **debe llevar su contexto en el nombre**. Sin el contexto, el mismo texto sirve para tres épicas y colisiona con la primera que llegue:

```
Incorrecto: el sistema debe mostrar la fecha de transacción en Android
Correcto:   el sistema debe mostrar la fecha de transacción del movimiento en tránsito en Android
```

Aplica especialmente a fechas (transacción, expiración, creación), montos (total, parcial, pendiente), estados (activo, pendiente, cancelado), títulos y encabezados. El sufijo de plataforma no resuelve esto: dos épicas de la misma plataforma colisionan igual (ver `platform-suffix-and-ambiguity.md`).

## Validación anti-duplicación (post-generación, obligatoria)

Después de generar y **antes** de declarar la entrega, listar las definiciones repetidas:

```bash
grep -rhoE "^(Given|When|Then)\('[^']+'" src --include='*.steps.ts' | sort | uniq -d
```

Cualquier salida es **blocker**: hay definiciones duplicadas y el escenario va a fallar como `ambiguous`. Se corrige antes de continuar, nunca se reporta como "advertencia".

Complementariamente, un `--dry-run` filtrado por el tag de la historia debe cerrar sin `ambiguous` ni `undefined` antes de la primera ejecución real.

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
