# Tagging y naming de escenarios Gherkin

Los tags no son metadatos decorativos: son el mecanismo por el que el pipeline elige qué corre, dónde y con qué reporte. Un tagging inconsistente hace que un escenario no corra nunca y nadie lo note — el peor fallo posible en una suite de regresión.

## Anatomía de un escenario etiquetado

```gherkin
@loginConContrasena
Feature: Login con contraseña - HU-24688

  @HU-31233 @android @smoke @regression
  Scenario: Validación de que la pantalla de login se muestra al abrir la app en Android
    Given el usuario desea ingresar a la banca digital en Android
    When accede a la plataforma Mobile en Android
    Then el sistema debe mostrar la pantalla de inicio de sesión con campos de usuario y contraseña en Android
```

## Reglas de tagging

| Nivel | Regla |
|---|---|
| Feature | Un tag en camelCase que nombra la funcionalidad, una sola vez al inicio del archivo. Permite correr el feature completo sin enumerar escenarios. |
| Plataforma | **Exactamente uno** por escenario, del juego cerrado del arquetipo (`@web`, `@android`, `@ios`, `@ipad`, `@tablet`). Ni cero ni dos. |
| Browser | Obligatorio **solo** cuando la plataforma es web: `@chromium`, `@firefox` o `@safari`. Sin él, el escenario corre en el browser por defecto y la matriz de compatibilidad miente. |
| Trazabilidad | Exactamente un tag con el ID del caso en el ALM (`@HU-31233`, `@NT-31233`, el prefijo que use el cliente). |
| Tipo de prueba | Al menos uno: `@smoke` para el camino crítico, `@regression` para la suite completa. Ambos cuando aplica. |
| Exclusión | Un tag de exclusión reconocido por todos los perfiles (`@ignore`) para deshabilitar sin borrar. Todo perfil lo filtra con `and not @ignore`. |

Los tags de capacidades transversales (`@accessibility`, `@security`, `@visual`, `@contract`) se aplican según `[[calidad-transversal-capabilities]]` y son ortogonales a los anteriores.

## El placeholder de trazabilidad

Un feature se escribe muchas veces **antes** de que exista el caso en el ALM. Prohibirlo bloquea el trabajo; permitirlo sin control deja escenarios sin trazabilidad para siempre. El acuerdo:

1. Al generar, se usa un placeholder único y grepeable como primer tag de cada escenario: `@HU-XXXX`.
2. El placeholder **es un pendiente declarado**, no deuda silenciosa: se reporta en el mensaje final y en el delivery gate (`[[calidad-delivery-gate-contract]]`).
3. Cuando llegan los IDs reales, se reemplazan **en orden de aparición** en el feature.
4. Ningún escenario con placeholder se considera trazable a efectos de cobertura. La propiedad 8 de `static-correctness-properties.md` los cuenta y los reporta aparte.

```bash
grep -rn "@HU-XXXX" features/    # pendientes de asignar antes de cerrar
```

## Naming de escenarios

Un nombre de escenario debe ser autoexplicativo **leído de forma aislada**, fuera del archivo, en una fila de un reporte de ejecución. Es donde se lee de verdad: cuando algo falla en el pipeline, lo primero que ve una persona es esa línea.

Debe contener tres cosas: qué se valida, en qué contexto, y contra qué plataforma.

| Incorrecto | Correcto |
|---|---|
| Validación de login en Android | Validación de que la pantalla de login se muestra al abrir la app en Android |
| Caso 3 recuperación | Validación de que el sistema envía el código OTP al correo registrado al recuperar contraseña en Web |
| Test de mensajes de error | Validación de que se muestra el mensaje de credenciales inválidas tras un intento fallido en iOS |

Si el arquetipo tiene un prefijo de convención propio (`PN-PR-Front-`, `E2E-`), se respeta el existente: la convención del cliente manda. Lo que no es negociable es la parte descriptiva.

## Naming de steps: el texto debe describir lo que el código hace

Es la regla que más se viola y la que más caro sale, porque convierte el `.feature` —el artefacto que lee negocio— en ficción.

| Tipo | Regla | Incorrecto | Correcto |
|---|---|---|---|
| `Given` | Estado o precondición exacta | el usuario está en la app en Android | el usuario ha iniciado sesión en la banca digital en Android |
| `When` | Acción concreta del usuario | el usuario interactúa con la pantalla en Web | el usuario selecciona la opción "Recordar usuario" en Web |
| `Then` | Resultado observable concreto | el sistema debe responder en iOS | el sistema debe mostrar el mensaje "Los datos ingresados son incorrectos" en iOS |

Un `Then` genérico cuya implementación verifica un mensaje específico es un defecto de la misma gravedad que una aserción incorrecta: el escenario dice una cosa y prueba otra. En revisión se rechaza.

## Consistencia de idioma

El idioma de los steps sigue el del arquetipo, y es uno solo. Un arquetipo en español con steps en inglés mezclados fragmenta el vocabulario y rompe la reutilización, porque nadie encuentra el step existente al buscar en el idioma equivocado. Si el proyecto declara `# language: es` en los features, las palabras clave Gherkin también van en español.
