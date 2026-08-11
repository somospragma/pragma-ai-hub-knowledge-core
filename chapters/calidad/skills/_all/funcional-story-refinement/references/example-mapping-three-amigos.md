
# Example Mapping y Tres Amigos

Técnicas de sesión para descubrir reglas, ejemplos y preguntas ANTES de escribir criterios definitivos o casos de prueba. El agente prepara el material y facilita la estructura; las decisiones son de la sesión humana.

## Example Mapping (estructura de 4 colores)

Por cada HU se construye el mapa:

| Color | Elemento | Regla |
|---|---|---|
| Amarillo | **La historia** | Una sola por mapa |
| Azul | **Reglas** | Cada regla de negocio que gobierna el comportamiento, en una frase declarativa |
| Verde | **Ejemplos** | Casos concretos con datos que ilustran cada regla — mínimo un ejemplo por regla, ideal incluir el contraejemplo |
| Rojo | **Preguntas** | Todo lo que nadie en la sesión puede responder; se registra y se sigue |

Formato de trabajo del agente (markdown):

```markdown
## Example map — HU-123: Transferencia entre cuentas
### Regla R1: El monto no puede exceder el saldo disponible
- Ejemplo E1.1: saldo 100.000, transferencia 100.000 → aprobada (borde exacto)
- Ejemplo E1.2: saldo 100.000, transferencia 100.001 → rechazada con mensaje "saldo insuficiente"
### Regla R2: ...
### Preguntas
- P1: ¿el saldo "disponible" descuenta las transferencias programadas del día? (bloqueante)
```

Señales de la sesión: muchas rojas → HU no está lista, volver al PO; muchas azules (>6-7 reglas) → candidata a splitting (patrón Rules de `story-splitting-patterns.md`); reglas sin ejemplo → la regla probablemente no se entiende de verdad.

## Derivación hacia el diseño de casos

Los ejemplos verdes son la semilla directa de `[[calidad-funcional-test-design]]`: cada ejemplo se convierte en al menos un caso de alto nivel, y las reglas azules definen las particiones/tablas de decisión. Por eso los ejemplos deben tener **datos concretos** (montos, fechas, estados), no descripciones ("un monto alto").

## Tres Amigos

La conversación mínima: **negocio** (PO — qué problema), **desarrollo** (cómo se construye, qué es viable), **pruebas** (qué puede salir mal, qué falta para verificar). El rol del agente del chapter es el tercer amigo estructurado:

1. Llega con el análisis (`[[calidad-funcional-story-analysis]]`) y el example map borrador hechos.
2. Aporta la mirada destructiva: bordes, negativos, estados raros, dependencias caídas.
3. Registra los acuerdos y las preguntas rojas con dueño y fecha.
4. Sale con el material listo para formalizar el refinamiento (`refinement-proposal-format.md`).

Anti-patrón: convertir la sesión en revisión de un documento terminado. El material del agente es borrador para discutir, y así se presenta.
