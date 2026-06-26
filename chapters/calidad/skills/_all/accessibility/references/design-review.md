# Revisión de accesibilidad desde diseño (Product Designer)

Evaluación de accesibilidad **antes de código**, sobre pantallas, flujos, componentes,
textos, prototipos o especificaciones, desde la perspectiva de un Product Designer senior
en accesibilidad digital, inclusión financiera, UX Writing, research y tecnologías asistivas.

Dependencia obligatoria: fundamentar hallazgos en
`[regulatory-framework](regulatory-framework.md)` y `[wcag-pour](wcag-pour.md)`.

## Información mínima a solicitar

**Acceso y evidencia**: enlace de Figma, prototipo navegable, capturas/exportaciones,
variantes desktop/mobile/tablet, estados (error, vacío, loading, éxito, validación),
componentes interactivos, animaciones/transiciones/estados dinámicos, UX Writing y reglas
de validación de formularios.

**Contexto**: qué se revisa (pantalla / componente / flujo / Design System / prototipo),
funcionalidad y objetivo del usuario, dispositivos contemplados, alcance, etapa del diseño,
restricciones (técnicas/legales/negocio), uso del Design System, perfiles de usuario
prioritarios, y si se probó con tecnologías asistivas o usuarios reales.

Si un criterio no tiene evidencia suficiente, clasificarlo como *no verificable*, *evidencia
insuficiente* o *riesgo potencial* (ver `[severity-and-findings](severity-and-findings.md)`).

## Tipos de validación desde diseño

- **Validable desde diseño**: contraste, jerarquía visual, carga cognitiva, tamaños
  táctiles, claridad de contenido, espaciado, consistencia visual, legibilidad, prevención
  de errores.
- **Parcialmente verificable desde diseño** (requiere documentación/anotaciones/specs):
  orden de lectura, textos alternativos, labels accesibles, navegación esperada, cambios
  dinámicos, gestos, interacción por voz, motion, componentes complejos. Se clasifican como
  *parcialmente verificables* / *riesgo potencial* y generan *requerimiento de
  implementación accesible*.

## Alcance posible de la auditoría desde diseño

Auditoría heurística; auditoría WCAG bajo POUR; auditoría normativa; auditoría cognitiva y
de comprensión; auditoría de UX Writing; auditoría multidispositivo; auditoría de
formularios y errores; auditoría de flujos bancarios críticos. Nivel mínimo recomendado en
banca: **WCAG AA**.

## Validación multidispositivo

Contemplar desktop, mobile y tablet; orientación vertical y horizontal; distintas
resoluciones; zoom; touch, mouse y teclado; comportamiento responsive.

## Qué debe producir la revisión

- Identificar barreras y clasificarlas por severidad (crítica/alta/media/baja).
- Relacionar hallazgos con normativa aplicable y explicar el impacto en el usuario.
- Proponer mejoras de UX/UI y de UX Writing accionables.
- Recomendar validaciones con usuarios o tecnologías asistivas.
- Identificar evidencias faltantes y diferenciar hallazgos comprobados de riesgos potenciales.

## Mejora continua

Recomendar: frecuencia de auditorías, design reviews accesibles, integración de
accesibilidad en procesos y políticas internas, y métricas (contraste, ratio de
cumplimiento, tiempo de navegación con teclado).
