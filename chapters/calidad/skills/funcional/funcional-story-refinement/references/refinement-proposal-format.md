
# Formato de la propuesta de refinamiento

La propuesta es el entregable que el PO aprueba, ajusta o rechaza. Debe poder leerse sin haber visto el análisis (autocontenida) y decidirse ítem por ítem.

## Estructura

```markdown
# Propuesta de refinamiento — {ID}: {título}

**Basada en**: análisis {fecha} ({n} hallazgos: {b} bloqueantes, {m} menores)
**Estado esperado tras aprobar**: ready

## 1. Narrativa
| | Texto |
|---|---|
| Actual | Como usuario quiero transferir dinero para mover mi plata |
| Propuesta | Como cliente autenticado con cuenta de ahorros activa, quiero transferir dinero a cuentas de terceros del mismo banco, para pagar sin efectivo |
| Motivo | A-1 (rol vago), A-4 (alcance sin borde: ¿terceros? ¿interbancaria?) |

## 2. Criterios de aceptación
### CA-1 [SIN CAMBIO] ...
### CA-2 [MODIFICADO]
- Actual: "El sistema valida el monto correctamente"
- Propuesto (Gherkin):
  Dado un cliente con saldo disponible de 100.000 COP
  Cuando intenta transferir 100.001 COP
  Entonces la transferencia se rechaza con el mensaje "Saldo insuficiente"
- Motivo: A-2 (no decidible), habilita BVA
### CA-7 [NUEVO] (camino negativo: servicio de destino no disponible) ...

## 3. Splitting propuesto (si aplica)
HU-123a "..." / HU-123b "..." — orden sugerido y qué hereda cada una.

## 4. Preguntas abiertas (sin respuesta, bloquean ready)
| # | Pregunta | Dueño sugerido | Severidad |

## 5. Decisión del PO
| Ítem | aprobar / ajustar / rechazar | Comentario |
|---|---|---|
| Narrativa | | |
| CA-2 | | |
| CA-7 | | |
| Splitting | | |
```

## Reglas

1. **Antes/después siempre visible** — el PO nunca aprueba a ciegas un reemplazo.
2. Todo ítem `[NUEVO]`/`[MODIFICADO]` trae su motivo trazado al hallazgo del análisis.
3. Las preguntas abiertas van en la propuesta aunque incomoden: aprobar la propuesta NO cierra las preguntas, y así se dice.
4. **Aplicación post-aprobación**: solo los ítems aprobados; los `ajustar` se iteran y se re-presentan; los `rechazar` se registran con el comentario del PO (es información de negocio valiosa).
5. En ALM (vía [[calidad-alm-mcp-integration]]): actualizar descripción/CA del work item con lo aprobado, dejar comentario `[QA refinamiento {fecha}] aplicado según aprobación de {quién}`, crear hijos del splitting con links parent-child. Guardar copia local en `refinement/{HU-ID}-refined-{fecha}.md`.
