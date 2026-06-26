# Pre-flight check — Karate greenfield

Antes de generar cualquier artefacto Karate el agente debe ejecutar un pre-flight que valide herramientas y versiones del entorno local. Si alguna validación falla, aplicar la degradación correspondiente y reportar al usuario antes de continuar. El protocolo de enforcement está descrito en `[[calidad-pre-generation-protocol]]`.

## Validaciones obligatorias

- `java -version` debe estar en el rango aceptable: 11.x o 17.x. Cualquier valor entre 12 y 16 es incompatible con Karate 1.4.1 (GraalJS rompe). Valores 18 o superiores son no probados oficialmente.
- `mvn -version` debe responder sin error.
- `$JAVA_HOME` debe estar definida y apuntar a un JDK existente (no a un JRE).
- En modo brownfield, validar que el `karate-config.js` referenciado por el spec existe y es alcanzable desde `src/test/java/`.

## Detección de incompatibilidades

Si el sistema reporta una versión de Java en el rango 12–16:

1. Buscar un JDK 11 o 17 alterno:
   - macOS: `/usr/libexec/java_home -V` (lista todas las JVM instaladas).
   - Linux: `update-alternatives --list java` o `ls /usr/lib/jvm/`.
2. Sugerir el override:
   ```
   export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java-11))))
   ```
   o, en macOS:
   ```
   export JAVA_HOME=$(/usr/libexec/java_home -v 11)
   export PATH=$JAVA_HOME/bin:$PATH
   ```
3. Mensaje sugerido al usuario:
   > Tu Java X no es compatible con Karate 1.4.1 (GraalJS requiere Java 11 o 17+). Detecté Java 11 en /opt/homebrew/.../openjdk@11. ¿Lo uso?

Si el usuario no autoriza el override, degradar a `scaffold-only` y documentar la razón en `.evidence/preflight-result.json`.

## Tabla de versiones soportadas

| Java  | Karate 1.4.1 | Notas                              |
|-------|--------------|------------------------------------|
| 11    | ✓            | Recomendado                        |
| 12-16 | ✗            | GraalJS incompatible               |
| 17    | ✓            | LTS, recomendado                   |
| 18+   | ⚠️           | No probado oficialmente            |

## Script shippeable

El agente debe copiar ``references/templates.md` (sección `preflight-karate.sh`)` al proyecto generado bajo `scripts/preflight.sh` y darle permisos `0755`. Ese script reproduce las mismas validaciones en CI o en máquinas de desarrolladores sin necesidad de re-invocar al agente. Ver `[[calidad-delivery-gate-contract]]` para la convención de scripts entregables y `[[calidad-post-generation-protocol]]` para el archivado de la evidencia.
