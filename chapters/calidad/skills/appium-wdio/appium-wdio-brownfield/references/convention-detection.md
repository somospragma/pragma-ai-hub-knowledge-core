# Detección de convenciones del arquetipo

El objetivo es producir un objeto de convenciones **antes** de escribir nada. Todo lo que se genere después se valida contra él. Un archivo generado que no cumple una convención detectada se rechaza en revisión, por correcto que sea técnicamente.

## Orden de inspección

### 1. Runner y perfiles

Leer `cucumber.config.js` (o el archivo de configuración equivalente) completo. Extraer:

| Dato | Cómo se usa |
|---|---|
| Lista de perfiles y su nombre exacto | Determina qué plataformas soporta el arquetipo hoy |
| Globs de `require` por perfil | Dónde deben ir las definiciones nuevas para que se carguen |
| Expresión de tags por perfil | Qué tag debe llevar el escenario para correr en ese perfil |
| Directorio de reporte por perfil | Dónde mirar el resultado |
| `parallel` | Si el arquetipo asume aislamiento entre escenarios |
| `requireModule` | Cómo se compila TypeScript en ejecución |

El dato crítico es el glob: si el perfil `android` carga `steps/**/android/**/*.ts`, un archivo nuevo fuera de esa ruta no lo carga nadie y sus steps quedan `undefined` sin error de compilación.

### 2. Estructura de directorios

```bash
find src -type d -name steps -o -type d -name features | head
ls src/**/steps/                 # carpetas de épica y carpetas compartidas
ls test-data/                    # plataformas base con archivo propio
```

Extraer: patrón de nombres de carpeta de épica, carpetas compartidas existentes, subcarpetas de plataforma en uso, plataformas base con test-data propio.

### 3. Vocabulario de steps

```bash
# Inventario completo, ordenado por texto: duplicados y variantes quedan adyacentes
grep -rhoE "^(Given|When|Then)\('[^']+'" src --include='*.steps.ts' | sort -u
```

Extraer:

- **Idioma** de los steps. Se respeta, sin excepción.
- **Sufijo de plataforma**: si existe, cuáles son los valores exactos (`en Android` contra `en android` contra `- Android`).
- **Parámetro de plataforma**: si el arquetipo usa un parameter type y con qué nombre.
- **Estilo de redacción**: impersonal, primera persona, imperativo.
- **Steps reutilizables** por categoría, que alimentan el catálogo.

### 4. Tags

```bash
grep -rhoE "^\s*@[a-zA-Z0-9_-]+" src --include='*.feature' | sort | uniq -c | sort -rn
```

El conteo revela la taxonomía real: los tags de plataforma aparecen cientos de veces, los de trazabilidad una vez cada uno, y los raros suelen ser errores de escritura de un tag válido.

Extraer: juego de tags de plataforma, de tipo de prueba, prefijo de trazabilidad, tag de exclusión, y tags propios del cliente.

### 5. Capa de objetos de pantalla

```bash
ls src/**/screens/base/ src/**/pages/base/
```

Extraer: nombre de la clase base, repertorio de métodos disponibles, cómo recibe la plataforma el constructor, cómo carga los selectores, si hay mapa de plataformas derivadas y con qué nombre.

**Antes de agregar un método a la clase base, verificar que no exista con otro nombre.** Duplicar `waitForDisplayed` como `esperarVisible` fragmenta la capa.

### 6. Test-data

```bash
ls test-data/*/
python3 -c "import json;print(list(json.load(open('test-data/android/login.json')).keys()))"
```

Extraer: plataformas base con archivo propio, convención de nombres de archivo, nombres de los grupos de selectores, sintaxis de selector por plataforma, y si hay plantillas con marcador y con qué formato.

### 7. Configuración y capabilities

Leer los constructores de capabilities y el gestor de drivers. **No para juzgarlos, para entenderlos**: qué se lee de variables de entorno, qué está fijado, cómo se resuelve el dispositivo, si hay modo cloud, cómo se decide.

Extraer también el `.env.example`: es el contrato de configuración y dice qué variables hay que completar para correr.

### 8. Hooks y World

Extraer: qué hooks existen, cómo se decide qué driver se crea, qué campos tiene el World, qué evidencia se captura y cuándo, qué hace el teardown.

Si el World está tipado, **los steps nuevos usan ese tipo**. Si no lo está, se usa el patrón existente sin introducir uno nuevo: proponer el tipado es una recomendación, no un cambio a aplicar.

## El objeto de convenciones

El resultado de la inspección se declara explícitamente antes de generar:

```yaml
convenciones:
  runner:
    perfiles: [web, android, ios, ipad, tablet, android-web, ios-web]
    glob_steps_por_plataforma: "src/test/e2e/steps/**/{plataforma}/**/*.ts"
    carpetas_compartidas: [auth, common, navbar, home]
    reporte_por_perfil: "reports/{perfil}/"
  estructura:
    patron_carpeta_epica: "nt-{ID}_{nombre-kebab}"
    patron_archivo_feature: "nt-{ID}_{nombre-kebab}.feature"
    patron_archivo_steps: "nt-{ID}_{nombre-kebab}.steps.ts"
  steps:
    idioma: es
    sufijos: ["en Web", "en Android", "en iOS", "en iPad", "en Tablet Android"]
    parametro_plataforma: "{plataforma}"
    estilo: "tercera persona, sujeto 'el usuario' / 'el sistema'"
  tags:
    plataforma: ["@web", "@android", "@ios", "@ipad", "@tablet"]
    browser: ["@chromium", "@firefox", "@safari"]
    tipo: ["@smoke", "@regression"]
    trazabilidad_prefijo: "@NT-"
    exclusion: "@ignore"
  pantallas:
    clase_base: BaseScreen
    mapa_plataformas: { tablet: android, ipad: ios }
    carga_selectores: "TestDataLoader.load<T>(plataformaBase, archivo)"
  test_data:
    plataformas_base: [web, android, ios, shared]
    patron_archivo: "{epica}.json"
    grupos_observados: [selectors, loginErrorSelectors, otpSelectors]
  ejecucion:
    modos: [local, cloud]
    variable_modo: EXECUTION_MODE
```

Cada campo que quede sin resolver se pregunta al cliente. Asumir un valor por defecto del chapter donde el proyecto tiene otro es la vía más rápida a un rechazo en revisión.

## Señales de que el arquetipo tiene deuda

Se registran para el reporte, **no se corrigen** sin permiso:

- Steps sin sufijo conviviendo con steps que sí lo tienen: la convención se introdujo a mitad de camino y quedó incompleta.
- Un archivo de test-data por historia en vez de por épica: los selectores del mismo elemento van a divergir.
- Carpetas de plataforma con un solo archivo mientras el resto vive en la carpeta de otra plataforma: alguien copió sin mover.
- Perfiles que no cargan las carpetas compartidas.
- Tags de plataforma que no coinciden con ningún perfil: esos escenarios no corren nunca.

```bash
# Tags de plataforma usados en features contra tags declarados en los perfiles
grep -rhoE "@[a-z-]+" src --include='*.feature' | sort -u > /tmp/tags-usados.txt
grep -oE "'@[a-z-]+" cucumber.config.js | tr -d "'" | sort -u > /tmp/tags-perfiles.txt
comm -23 /tmp/tags-usados.txt /tmp/tags-perfiles.txt
```

La salida incluye tags legítimos que no son de plataforma; lo que se busca son tags **con aspecto de plataforma** que ningún perfil recoge. Cada uno es un conjunto de escenarios que nadie ejecuta desde que se escribieron.
