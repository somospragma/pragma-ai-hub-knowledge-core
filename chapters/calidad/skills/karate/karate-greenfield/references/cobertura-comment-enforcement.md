# Cobertura comment enforcement (Karate)

Toda `.feature` generada por el agente DEBE declarar explícitamente su cobertura efectiva mediante un comentario en la cabecera del archivo. Este comentario es la fuente de verdad para auditoría rápida del `delivery_gate.coverage.declared` (ver `[[calidad-delivery-gate-contract]]`).

## Regla obligatoria

La primera línea no vacía del archivo `.feature` DEBE coincidir con:

```
# cobertura: <N>
```

donde `<N>` es el `effective_minimum` calculado mediante la fórmula descrita en ``negative-coverage-formula.md`` (con `risk_factor` aplicado).

Si el archivo coloca `Feature:` en la primera línea por restricción de un cliente, el comentario `# cobertura:` puede vivir en la segunda línea. No se acepta ninguna otra ubicación.

El número declarado debe corresponder al `effective_minimum` real para ese endpoint, NO a un round number cosmético, NO al `real_minimum` sin modulación de riesgo.

## Por qué importa

- Sin este comentario, la auditoría de cobertura requiere correr Karate o parsear todos los `Scenario:` del archivo. Cosmetic claims ("5 escenarios") son indistinguibles de cobertura real.
- El delivery gate cross-cutting consume este número directamente; un archivo sin el comentario rompe el contrato `[[calidad-delivery-gate-contract]]`.
- Hace que la cobertura sea greppable y trazable en code review, sin levantar Maven.

## Auditoría rápida

El comando siguiente debe retornar exactamente una línea por cada `.feature` generada:

```bash
grep -r "# cobertura:" src/test/java/com/testing/features/
```

Si el conteo de líneas devueltas es menor que el número de archivos `.feature`, la entrega es inválida y debe regenerarse.

## Snippet de validación shell

Incluir este snippet en el evidence pack (o ejecutarlo manualmente antes de cerrar la entrega):

```bash
for f in src/test/java/com/testing/features/**/*.feature; do
  grep -q "^# cobertura:" "$f" || echo "MISSING cobertura: $f"
done
```

Cualquier línea de salida `MISSING cobertura: ...` invalida la entrega para ese archivo. El agente debe regenerar el feature con la cabecera correcta antes de continuar.

## Política de modificación

- NO eliminar el comentario al refactorizar features.
- Al añadir/quitar escenarios, RECALCULAR `effective_minimum` y actualizar el comentario en el mismo commit.
- El número del comentario y el conteo real de `Scenario:` + `Scenario Outline:` (más filas de `Examples` si se cuentan por fila) deben ser consistentes entre sí. Cualquier divergencia es bug.

## Cross-links

- Fórmula y cálculo: ``negative-coverage-formula.md``.
- Consumo por el gate de entrega: `[[calidad-delivery-gate-contract]]`.
- Cómo se reporta en el evidence pack: `[[calidad-post-generation-protocol]]`.
