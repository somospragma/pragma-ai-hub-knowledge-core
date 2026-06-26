# Estructura del reporte de auditoría de accesibilidad

Entregable orientado a identificar, documentar y priorizar hallazgos de accesibilidad,
experiencia de usuario, inclusión financiera y cumplimiento normativo. Se entrega en dos
formatos.

## 1. Resumen ejecutivo en la conversación

Síntesis con: estado general de la revisión, resumen ejecutivo, principales hallazgos,
riesgos potenciales para tecnologías asistivas, evidencias faltantes relevantes,
recomendaciones prioritarias de diseño, recomendaciones prioritarias de contenido/UX
Writing, y criterios no verificables o parcialmente verificables.

## 2. Matriz de auditoría descargable (hoja de cálculo)

Clara, filtrable y ordenable. Estructura mínima:

### Hoja 1 — Matriz de hallazgos (una fila por hallazgo/criterio)

Columnas mínimas: ID (autogenerado, único) · Flujo bancario afectado · Pantalla/Flujo ·
Componente · Principio POUR · Criterio evaluado · Hallazgo · Evidencia · Estado de
validación · Severidad · Riesgo de exclusión financiera · Criterio WCAG asociado ·
Referencia normativa · Tipo de discapacidad o barrera afectada · Riesgo para tecnologías
asistivas · Evidencias faltantes · Recomendación de diseño · Recomendación de contenido/UX
Writing · Requerimiento de implementación accesible.

### Hoja 2 — Guía de interpretación

Diccionario de cada campo de la matriz: qué significa, cuándo aplica y cómo interpretarlo.

### Hoja 3 — Referencias WCAG y normativas

Todos los criterios considerados (con o sin hallazgo): Criterio WCAG · Nombre · Nivel de
conformidad · Principio POUR · Aplicación en productos bancarios · Relación con el marco
normativo (`[regulatory-framework](regulatory-framework.md)`).

### Hoja 4 — Resumen ejecutivo

Estado general · total de hallazgos · hallazgos por severidad · hallazgos por principio
POUR · riesgos altos de exclusión financiera · evidencias faltantes críticas ·
recomendaciones prioritarias.

## Codificación de estados (formato condicional sugerido)

- **Severidad**: Crítica (rojo oscuro) · Alta (rojo) · Media (amarillo) · Baja (verde).
- **Riesgo de exclusión financiera**: Alto (rojo) · Medio (amarillo) · Bajo (verde).
- **Estado de validación**: Comprobado (verde) · Parcialmente verificable (amarillo) ·
  Riesgo potencial (naranja) · Evidencia insuficiente (gris) · No verificable (azul).

## Listas controladas (valores permitidos)

Principio POUR · Severidad · Riesgo de exclusión financiera · Nivel de conformidad WCAG ·
Estado de validación · Tipo de discapacidad o barrera afectada.

## Reglas de validación del reporte

- Cada hallazgo en una fila independiente; ID único autogenerado.
- Ningún criterio se marca como cumplido sin evidencia suficiente.
- Criterios sin evidencia: *no verificable* / *evidencia insuficiente* / *riesgo potencial*.
- Criterios parcialmente verificables generan *requerimiento de implementación accesible*.
- En flujos bancarios críticos, escalar severidad cuando la barrera afecte acceso,
  autenticación, comprensión, autorización o ejecución segura de una operación.
- Toda recomendación debe ser accionable (diseño, contenido, interacción o accesibilidad).

> Este reporte se alinea con el esquema universal de evidencia del chapter; ver
> `[[calidad-test-evidence-and-traceability]]` y `[[calidad-executive-report-generator]]`
> para la generación del reporte ejecutivo.
