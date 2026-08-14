# Bug vs Test Design — Decision Tree

Árbol de decisión obligatorio para clasificar un fallo determinista. Su propósito es evitar el anti-patrón más caro del chapter: **"corregir" un test para que pase, escondiendo un bug real del SUT**.

> **Precondición del árbol:** todo nodo que termina en "BUG en el SUT" exige además la cadena de evidencia completa de `sut-defect-evidence-chain.md`. El árbol clasifica; la cadena demuestra. Llegar al nodo no autoriza a reportar.

## Pseudocódigo del árbol

```
¿el preflight de esta corrida está verde? (app alcanzable, sesión apuntando al
 destino correcto, aplicación abierta, con salida de comando y captura)
  NO  → NO hay nada que clasificar: la corrida no demostró tocar el SUT.
        Corregir el preflight y re-ejecutar. Ver calidad-execution-preflight.
  SÍ  ↓

¿el SUT está corriendo y respondiendo a un smoke básico (health-check)?
  NO  → environment issue. Escalar a plataforma cliente.
        NO clasificar como bug ni como test design issue.
        Suspender triage hasta restablecer el ambiente.
  SÍ  ↓

¿el test pasaba antes con la MISMA versión del SUT (mismo commit/tag/build)?
  SÍ  → cambió algo en el SUT desde entonces.
        ↓
        ¿el cambio es breaking? (campo requerido eliminado, tipo cambiado,
         status code modificado, endpoint movido, contrato roto)
          SÍ  → BUG deterministic en el SUT.
                Reportar al equipo dev del cliente con evidencia completa.
                **NO modificar el test.**
          NO  → cambio no-breaking (ej. campo opcional añadido, payload extra).
                ↓
                ¿el test puede tolerarlo sin perder valor de validación?
                  SÍ  → Ajustar el test para tolerar (ej. `##optional` en Karate,
                        `objectContaining` en Playwright).
                        Loggear como "schema-drift no-breaking" en evidencia.
                  NO  → Escalar a humano. Decisión ambigua que requiere review:
                        el cambio podría introducir comportamiento no documentado.

  NO  → el test NUNCA pasó con esta versión del SUT (test nuevo o nueva versión).
        ↓
        ¿el test está bien diseñado para la especificación?
         (selectors correctos, asserts contra la spec, datos válidos, flujo coherente)
          SÍ  → BUG en el SUT. Puede ser regresión o feature no implementada.
                Reportar al equipo dev con evidencia.
                **NO modificar el test.**
          NO  → TEST DESIGN ISSUE.
                Habilitar `[[calidad-test-self-correction-loop]]` para auto-corregir
                bajo guardrails del chapter.
```

## Casos límite documentados

### Caso A: nueva feature no documentada en spec

El SUT tiene un campo/flujo nuevo que no está en la spec entregada al chapter.

- **NO** auto-tolerar.
- Escalar al humano del chapter; pedir al cliente actualizar la spec.
- Sin spec actualizada, el test es ambiguo y se queda en quarantine.

### Caso B: spec ambigua

La spec dice "el sistema debe responder rápido"; el test asume `<200ms`. El SUT responde `350ms`.

- **NO** ajustar el threshold del test ni reportar bug.
- Escalar al humano; pedir clarificación cuantitativa de "rápido".
- Calibrar con `[[calidad-calibrate-k6-thresholds]]` si aplica.

### Caso C: cambio de UX que rompe selector pero funcionalidad sigue válida

El botón "Comprar" se renombró a "Confirmar pedido". Misma URL, mismo backend, misma redirección.

- Clasificar como `flaky + locator stale` (o `deterministic + locator stale` si el cambio es estable).
- Auto-healing vía `[[calidad-test-self-healing]]` con multi-locator fallback.
- **NO** reportar como bug (la funcionalidad no cambió).
- Si el cambio de UX implica cambio de copy en aserciones (`expect(page.locator('h1')).toHaveText('Comprar')`), pedir al cliente confirmar el nuevo copy oficial **antes** de ajustar el test.

### Caso D: feature flag toggleada entre el último pass y el fail

El SUT activó un feature flag que cambia el comportamiento (`new_checkout_v2 = true`).

- Clasificar como `environment` (config drift; ver patrón #11 en `failure-pattern-catalog.md`).
- Escalar al cliente; coordinar si el flag debe estar `on` o `off` en el entorno de tests.
- **NO** modificar el test sin decisión del cliente.

### Caso E: el SUT empezó a devolver datos correctos pero el test esperaba datos incorrectos (fixture viejo)

El test asume `precio: 100` pero el SUT cobra `120` (precio actualizado por negocio).

- **TEST DESIGN ISSUE** disfrazado. El test usa un fixture obsoleto.
- Auto-corregir el fixture vía `[[calidad-test-self-correction-loop]]` solo si la lista de precios oficial confirma el cambio.
- Si no hay fuente de verdad accesible, escalar a humano.

## Reglas de oro

1. **En la duda, NO modificar el test**. Reportar y esperar decisión humana es siempre más barato que esconder un bug.
2. **Toda decisión del árbol se documenta en la evidencia** del run con: nodo final alcanzado, justificación, evidencia que soporta cada ramificación.
3. **El árbol NO se aplica a tests flaky**: para flaky, usar el `failure-pattern-catalog.md` y la matriz de acción del SKILL.md.
4. **"No encontré el elemento" no es un nodo del árbol.** Es un síntoma que primero recorre los descartes de `sut-defect-evidence-chain.md`: localizador, ancla volátil, espera, contexto, visibilidad real, estado y datos, y pantalla correcta. Solo lo que sobrevive a los siete descartes entra al árbol.
5. **Llegar a un nodo de BUG no autoriza a reportar**: hay que completar la cadena de evidencia y emitir su bloque de reporte, y la publicación en el ALM pasa por `[[calidad-alm-write-authorization-gate]]`.
