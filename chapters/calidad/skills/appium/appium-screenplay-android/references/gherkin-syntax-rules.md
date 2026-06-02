
# Reglas de sintaxis Gherkin (estrictas)

Toda violación bloquea el health-check stage `feature:gherkin-syntax-valid` y por tanto el acceptance criterion 4.

## Encoding y line endings

- Archivo `*.feature` en UTF-8 **sin BOM**.
- Line endings normalizados a `LF` (CRLF → LF antes de escribir).
- Cero caracteres de control `\x00-\x1F` (excepto `\t` `\n`) ni `\x7F`.

## Estructura

- Un único `Feature:` por archivo (al inicio).
- Cada `Scenario:` con al menos un `Given`, un `When` y un `Then` (en cualquier orden, pero los tres presentes).
- Cero `Scenario:` vacío.

## Comentarios

- `#` **solo al inicio de línea** (con indentación opcional).
- **PROHIBIDO** `# note` inline después de un step keyword:

```gherkin
# OK
# Validar carga inicial
When la aplicacion termina de cargar

# ERROR — Gherkin lo rechaza
When la aplicacion termina de cargar # nota inline
```

## Tags

- ASCII puro: regex `@[A-Za-z0-9_]+`.
- **NO** acentos: `@validacion` OK, `@validación` rechazado.
- **NO** puntuación: `@smoke,` rechazado, usar espacios entre tags.

```gherkin
# OK
@android @smoke
Scenario: ...

# ERROR
@android, @smoke,
Scenario: ...
```

## Headers decorativos

Solo caracteres `=`, `*`, `-` y espacios después del `#`. Regex permitido: `^[\t ]*#[\s=*\-]*$`.

```gherkin
# =================================
# Login de usuario
# =================================
Feature: Login
```

## Strings de step

Los **strings que va a parsear el step definition** (no las palabras clave) pueden tener acentos sin problema:

```gherkin
When el usuario ingresa "contraseña válida"
```

Las palabras clave Gherkin (`Feature`, `Scenario`, `Given`, `When`, `Then`, `And`, `But`) deben ir en inglés en este stack.
