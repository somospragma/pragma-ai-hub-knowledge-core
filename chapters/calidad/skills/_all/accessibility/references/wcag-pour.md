# WCAG bajo principios POUR

Toda evaluación de accesibilidad se estructura sobre los cuatro principios WCAG
(Perceptible, Operable, Comprensible, Robusto) en su versión vigente (2.1 / 2.2),
niveles A / AA / AAA. Para banca/financiero el nivel mínimo recomendado es **AA**.

## Perceptible

La información y los componentes deben presentarse de forma que el usuario los perciba.
Validar:

- Contraste de color (texto vs fondo; iconos y bordes significativos).
- Tipografía y legibilidad (tamaño, interlineado, fuentes).
- Jerarquía visual y estructura semántica (encabezados, listas, tablas).
- Alternativas textuales esperadas (alt text, `contentDescription`/`accessibilityLabel`).
- Labels asociados a controles e inputs.
- Iconografía con nombre accesible.
- Contenido multimedia (subtítulos, transcripciones, alternativas).
- Zoom y reflow sin pérdida de contenido ni funcionalidad.

## Operable

Los componentes de interfaz y la navegación deben poder operarse.
Validar:

- Navegación esperada y consistente.
- Foco visible y documentado; orden de foco coherente con el flujo visual.
- Uso completo sin mouse (teclado / switch / control por voz); sin trampas de foco.
- Interacción touch y tamaños táctiles (>= 48dp Android / 44pt iOS / objetivo suficiente en web).
- Gestos con alternativa accesible.
- Tiempos suficientes (sin límites que excluyan).
- Formularios operables con teclado y tecnologías asistivas.

## Comprensible

La información y el manejo de la interfaz deben ser comprensibles.
Validar:

- Lenguaje claro y carga cognitiva controlada.
- Prevención de errores y mensajes accionables.
- Ayudas contextuales y consistencia de interacción.
- Claridad financiera (montos, comisiones, condiciones).
- Confirmaciones antes de acciones críticas (pagos, transferencias, firma).

## Robusto

El contenido debe ser interpretable por una amplia variedad de agentes de usuario,
incluidas las tecnologías asistivas.
Validar:

- Name, Role, Value correctos en cada control (compatibilidad con lectores de pantalla).
- Estructura prevista para accesibilidad (roles, landmarks, relaciones).
- Componentes reutilizables y escalables (Design System accesible).
- Documentación de implementación accesible para criterios que no se validan solo desde diseño.

## Formato de cada hallazgo (campos mínimos)

Cada hallazgo debe documentar:

1. Descripción del hallazgo.
2. Criterio WCAG asociado (ej. 1.1.1 Texto Alternativo, Nivel A).
3. Principio POUR afectado.
4. Nivel de conformidad afectado (A / AA / AAA).
5. Justificación (por qué incumple).
6. Recomendación práctica (ejemplo de código, ajuste visual o de contenido).
7. Severidad (ver `[severity-and-findings](severity-and-findings.md)`).
