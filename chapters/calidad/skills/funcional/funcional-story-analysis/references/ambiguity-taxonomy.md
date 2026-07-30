
# Taxonomía de ambigüedades y vacíos

Cada hallazgo se clasifica, se cita la frase que lo produce y se convierte en **pregunta concreta para el PO**. La pregunta es el entregable; la clasificación solo ordena.

## Ambigüedades (el texto dice algo interpretable de 2+ formas)

| Tipo | Descripción | Ejemplo y pregunta |
|---|---|---|
| **Léxica** | Término con múltiples sentidos en el dominio | "el usuario activo" — ¿sesión iniciada, cuenta no suspendida, o con actividad reciente? |
| **De referencia** | Pronombre/artículo cuyo antecedente no es único | "cuando falla, se le notifica" — ¿falla el pago o la validación? ¿se notifica al cliente o al comercio? |
| **De cuantificación** | Cantidades sin límite o alcance sin borde | "soporta múltiples archivos" — ¿2, 20, 2000? ¿tamaño máximo por archivo y total? |
| **Temporal** | Plazos y orden sin precisión | "se actualiza periódicamente" — ¿frecuencia? ¿en línea o batch nocturno? |
| **De alcance** | "etc.", "entre otros", "y similares" | "tarjetas Visa, Mastercard, etc." — lista cerrada exacta de franquicias soportadas |
| **Condicional incompleta** | If sin else | "si el cupo es suficiente, se aprueba" — ¿y si no lo es? ¿rechazo, oferta parcial, lista de espera? |

## Vacíos (lo que el texto no dice y las pruebas necesitan)

| Tipo | Descripción |
|---|---|
| **Regla implícita** | El comportamiento asume una regla de negocio nunca escrita (ej. "recalcula el interés" sin fórmula ni redondeo) |
| **Caso límite ausente** | Bordes obvios sin tratamiento: monto 0, lista vacía, primer/último elemento, mes de 28/31 días |
| **Camino negativo ausente** | Solo se describe el éxito (cruza con el checklist de acceptance-criteria-quality) |
| **Dependencia no declarada** | Servicios, catálogos, permisos o features previas que el flujo necesita y nadie mencionó |
| **Dato de prueba imposible** | El escenario requiere datos que nadie sabe cómo obtener/construir (conecta con [[calidad-test-data-management]]) |
| **Actor sin definir** | Roles mencionados sin permisos ni origen ("el supervisor aprueba" — ¿qué rol del sistema es "supervisor"?) |

## Reglas de reporte

1. Formato del hallazgo: `[tipo] "cita textual" → Pregunta: ...` — la pregunta debe poder responderse con un dato o una decisión, no con un ensayo.
2. NO responder las preguntas por el PO, ni siquiera con "probablemente". La respuesta asumida por el agente es exactamente el defecto que este análisis existe para prevenir.
3. Priorizar: marcar `bloqueante` (impide diseñar casos o estimar) vs `menor` (se puede avanzar con la pregunta abierta y el caso queda pendiente de confirmación).
4. Deduplicar: la misma ambigüedad repetida en narrativa y CA es un hallazgo, no dos.
5. Los hallazgos `bloqueante` fuerzan veredicto DoR `not_ready`.
