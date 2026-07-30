
# Tablas de decisión y transición de estados

## Tablas de decisión

Para reglas de negocio combinadas ("si A y B pero no C, entonces..."). Procedimiento:

1. Listar **condiciones** (entradas booleanas o discretizadas) y **acciones** (comportamientos observables).
2. Construir la tabla completa (2^n columnas para n condiciones booleanas) y luego **simplificar**: colapsar columnas donde una condición es irrelevante (`-`), eliminar combinaciones imposibles justificando por qué son imposibles.
3. Un caso de prueba por columna de la tabla simplificada.

Ejemplo — aprobación de crédito rotativo:

| Condición | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| Score >= 650 | S | S | N | - |
| Antigüedad >= 6 meses | S | N | - | - |
| Mora activa | N | N | - | S |
| **Acción** | Aprueba | Revisión manual | Rechaza | Rechaza |

Valor doble de la técnica: además de derivar casos, **destapa vacíos** — si al armar la tabla aparece una combinación sin acción definida (score alto + mora activa + antigüedad alta: ¿revisión o rechazo?), eso es una pregunta para el PO vía `[[calidad-funcional-story-analysis]]`, no una celda que el diseñador rellena a criterio.

Combinar con BVA: cada condición numérica (score >= 650) genera sus propios casos de borde (650, 649) sobre la columna correspondiente.

## Transición de estados

Para entidades con ciclo de vida (orden: creada → pagada → despachada → entregada; usuario: registrado → verificado → activo → suspendido). Procedimiento:

1. Dibujar el modelo: estados, eventos, transiciones, guards y acciones. En texto:

```
[Creada] --pagar(pago OK)--> [Pagada]
[Creada] --pagar(pago falla)--> [Creada] + notificación de error
[Pagada] --despachar--> [Despachada]
[Creada|Pagada] --cancelar--> [Cancelada]
[Despachada] --cancelar--> RECHAZADO (transición inválida)
```

2. **Cobertura mínima (0-switch)**: un caso por cada transición válida.
3. **Transiciones inválidas**: los intentos prohibidos relevantes son casos negativos de primera clase (cancelar una orden despachada, pagar dos veces, despachar sin pagar). El resultado esperado debe estar en los CA — si no está, es vacío reportable.
4. **1-switch (secuencias de 2 transiciones)** solo para flujos de alto riesgo (dinero, estados regulatorios): detecta defectos de estado acumulado.

Si el CA describe estados pero el modelo no cierra (estados huérfanos, eventos sin origen), el modelo incompleto vuelve como hallazgo de análisis. El diagrama (mermaid o texto) se adjunta al entregable de diseño: es evidencia de la técnica y documentación viva del comportamiento.
