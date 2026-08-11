# Propiedades de corrección verificables por análisis estático

Una propiedad es una afirmación que debe ser verdadera para **todos** los archivos del arquetipo, no para algunos. A diferencia de una guía de estilo, se verifica sin ejecutar la suite: son el gate barato que se corre antes de entregar y en cada pull request.

Las 12 propiedades se agrupan en cuatro familias: resolución de steps (1, 2, 12), separación de responsabilidades (3, 10, 11), estructura (4, 5) y ejecutabilidad (6, 7, 8, 9).

Las rutas y los juegos de valores de los ejemplos se ajustan al arquetipo concreto: lo que no cambia es qué se verifica y por qué.

## Familia A — Resolución de steps

### Propiedad 1: toda definición termina con un sufijo de plataforma válido

Para cualquier definición de step en cualquier archivo de definiciones, el texto termina con exactamente uno de los sufijos del arquetipo, o con el parámetro de plataforma.

```bash
grep -rhoE "^(Given|When|Then)\('[^']+'" src --include='*.steps.ts' \
  | grep -vE "(en Web|en Android|en iOS|en iPad|en Tablet Android|\{plataforma\})'$" 
```

Salida esperada: vacía. Cada línea es un step que colisionará en el registro global. Ver `platform-suffix-and-ambiguity.md`.

### Propiedad 2: el catálogo refleja los steps compartidos

Para todo step definido en una carpeta compartida, existe una entrada en el catálogo con su texto exacto.

```bash
# Steps compartidos declarados en código
grep -rhoE "^(Given|When|Then)\('[^']+'" src/**/steps/{auth,common,navbar,home} --include='*.steps.ts' \
  | sed -E "s/^(Given|When|Then)\('//; s/'$//" | sort -u > /tmp/en-codigo.txt
# Steps listados en el catálogo
grep -oE "^\| [^|]+ \|" docs/step-catalog.md | sed -E 's/^\| //; s/ \|$//' | sort -u > /tmp/en-catalogo.txt
comm -23 /tmp/en-codigo.txt /tmp/en-catalogo.txt
```

Salida esperada: vacía. Cada línea es un step compartido invisible para quien consulte el catálogo, que será reimplementado.

### Propiedad 12: sin duplicación de texto entre épicas

Para cualquier par de archivos de definiciones en épicas distintas y misma plataforma, no existen dos definiciones con texto idéntico. Si el texto se repite, pertenece a la carpeta compartida.

```bash
grep -rhoE "^(Given|When|Then)\('[^']+'" src --include='*.steps.ts' \
  | sort | uniq -d
```

Salida esperada: vacía. Cada línea es un `Ambiguous step definition` esperando a que alguien corra el perfil que carga ambas.

## Familia B — Separación de responsabilidades

### Propiedad 3: cero selectores hardcodeados en código

Ningún archivo de definiciones, objeto de página u objeto de pantalla contiene literales que sean selectores de UI. Los selectores viven en los archivos de test-data.

```bash
grep -rnE "//android\.|//XCUIElement|\[@content-desc|\[@resource-id|\[aria-label|:has-text\(" \
  src --include='*.ts' | grep -v '/test-data/'
```

Salida esperada: vacía. Cada hallazgo es un cambio de UI que obligará a tocar código en vez de datos, multiplicado por las plataformas afectadas.

### Propiedad 10: claves camelCase en los archivos de test-data

Para todo archivo JSON de test-data, las claves de primer nivel (los grupos de selectores) están en camelCase.

```bash
python3 - <<'PY'
import json, pathlib, re
malas = []
for f in pathlib.Path('test-data').rglob('*.json'):
    for k in json.loads(f.read_text()).keys():
        if not re.fullmatch(r'[a-z][A-Za-z0-9]*', k):
            malas.append(f"{f}: {k}")
print('\n'.join(malas))
PY
```

Salida esperada: vacía.

### Propiedad 11: convención de nombres de archivos de test-data

Todo archivo de test-data vive en `test-data/{plataforma-base}/{nombre}.json`, con plataforma base del juego cerrado del arquetipo y nombre en kebab-case.

```bash
find test-data -name '*.json' \
  | grep -vE "^test-data/(web|android|ios|shared)/[a-z0-9]+(-[a-z0-9]+)*\.json$"
```

Salida esperada: vacía.

## Familia C — Estructura

### Propiedad 4: rutas de los archivos de feature

Todo `.feature` sigue el patrón de rutas del arquetipo, con carpeta por épica.

```bash
find src -name '*.feature' \
  | grep -vE "features/[a-z0-9-]+(_[a-z0-9-]+)?/[a-z0-9-]+(_[a-z0-9-]+)?\.feature$"
```

### Propiedad 5: rutas de los archivos de definiciones

Todo archivo de definiciones específico de una épica vive bajo una subcarpeta de plataforma válida.

```bash
find src -name '*.steps.ts' -path '*/steps/*' \
  | grep -vE "steps/[^/]+/(web|android|ios|ipad|tablet|mobile-web)/[^/]+\.steps\.ts$" \
  | grep -vE "steps/(auth|common|navbar|home)/"
```

Salida esperada: vacía en ambas. Un archivo fuera de la convención no lo carga ningún perfil: sus steps quedan `undefined` y el escenario nunca corre.

## Familia D — Ejecutabilidad

Las cuatro se verifican con un solo recorrido de los `.feature`. El script agrupa los tags que preceden a cada `Scenario:` y evalúa las condiciones.

```python
# verificar-features.py
import pathlib, re, sys

PLATAFORMAS = {'@web', '@android', '@ios', '@ipad', '@tablet'}
BROWSERS    = {'@chromium', '@firefox', '@safari'}
TIPOS       = {'@smoke', '@regression'}
NOMBRE_OK   = re.compile(r' en (Web|Android|iOS|iPad|Tablet Android)$')
TRAZA       = re.compile(r'^@[A-Z]{2,}-(\d+|X{4})$')

fallos, placeholders = [], []
for f in pathlib.Path('src').rglob('*.feature'):
    tags = []
    for n, linea in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
        s = linea.strip()
        if s.startswith('@'):
            tags += s.split()
        elif s.startswith(('Scenario:', 'Escenario:', 'Scenario Outline:', 'Esquema del escenario:')):
            nombre = s.split(':', 1)[1].strip()
            ubic = f"{f}:{n}"
            t = set(tags)
            # Propiedad 6
            if len(t & PLATAFORMAS) != 1:
                fallos.append(f"P6 {ubic}: {len(t & PLATAFORMAS)} tags de plataforma")
            # Propiedad 7
            if '@web' in t and len(t & BROWSERS) != 1:
                fallos.append(f"P7 {ubic}: escenario web sin tag de browser")
            # Propiedad 8
            traza = [x for x in t if TRAZA.match(x)]
            if len(traza) != 1:
                fallos.append(f"P8 {ubic}: {len(traza)} tags de trazabilidad")
            elif traza[0].endswith('XXXX'):
                placeholders.append(f"{ubic}: {traza[0]}")
            if not (t & TIPOS):
                fallos.append(f"P8 {ubic}: sin tag de tipo de prueba")
            # Propiedad 9
            if not NOMBRE_OK.search(nombre):
                fallos.append(f"P9 {ubic}: el nombre no declara plataforma")
            tags = []
        elif s and not s.startswith('#'):
            tags = []

print('\n'.join(fallos) or 'OK: propiedades 6, 7, 8 y 9 verificadas')
if placeholders:
    print(f"\nPendientes de trazabilidad ({len(placeholders)}):")
    print('\n'.join(placeholders))
sys.exit(1 if fallos else 0)
```

- **Propiedad 6** — exactamente un tag de plataforma por escenario. Cero: no lo recoge ningún perfil, nunca corre. Dos: corre en dos perfiles con un solo driver y falla en el segundo.
- **Propiedad 7** — todo escenario web lleva tag de browser. Sin él, la matriz de compatibilidad reporta cobertura que no existe.
- **Propiedad 8** — un tag de trazabilidad y al menos uno de tipo. Los placeholders se reportan aparte, como pendientes declarados.
- **Propiedad 9** — el nombre del escenario declara la plataforma, para que el reporte de ejecución sea legible sin abrir el archivo.

## Cómo se usan estas propiedades

- **Al generar**: se corren sobre los archivos tocados antes de declarar la generación terminada. Una propiedad que falla es blocker, no observación.
- **Al extender un arquetipo ajeno**: se corren sobre el árbol completo **antes** de tocar nada, para separar lo que ya estaba roto de lo que uno rompió. Las violaciones preexistentes se reportan con evidencia; no se corrigen sin permiso.
- **En CI**: como job de lint de la suite, junto a la compilación de tipos y el linter. Es el uso que más rinde, porque corre en cada pull request y cuesta segundos.
- **En el delivery gate**: el resultado se incluye en `[[calidad-delivery-gate-contract]]`, con el conteo de placeholders pendientes.
