---
id: calidad-migrate-selectors-to-testdata
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [appium-wdio]
description: Migra selectores hardcodeados en código a archivos de test-data por plataforma, sin cambiar comportamiento.
tags: [appium, webdriverio, selectores, refactor, test-data, mantenibilidad]
---

# Migrar selectores hardcodeados a test-data

## Cuándo usar este workflow

Cuando un arquetipo existente tiene selectores literales en definiciones de steps u objetos de pantalla, y el cliente pide poder mantener la suite sin tocar código. Es el prerequisito para que un agente pueda reparar selectores con seguridad: mientras vivan en código, cada reparación es una modificación de lógica con riesgo de regresión.

Se ejecuta como trabajo propio, acordado y acotado. **No se hace de paso durante otra tarea**: es un refactor que toca muchos archivos y necesita su propia revisión.

## Precondición

La suite debe estar **verde antes de empezar**. Migrar sobre una suite roja hace imposible distinguir los fallos que la migración introdujo de los que ya estaban. Si hay escenarios fallando, se acuerda con el cliente excluirlos del alcance o arreglarlos antes.

Se registra el resultado de la corrida previa —qué escenarios pasan, cuáles no, cuánto tarda— como línea base de comparación.

## Pasos

### Paso 1 — Inventariar

```bash
grep -rnE "//android\.|//XCUIElement|\[@content-desc|\[@resource-id|\[aria-label|:has-text\(" \
  src --include='*.ts' | grep -v '/test-data/' > inventario-selectores.txt
wc -l inventario-selectores.txt
```

El inventario se agrupa por archivo y por pantalla. Su tamaño define si la migración se hace de una vez o por lotes: por encima de un centenar de selectores, se acuerda un orden por épica y se entrega en varios cambios revisables.

### Paso 2 — Acordar el alcance y el orden

Se prioriza por dolor real, no alfabéticamente:

1. Pantallas que más han cambiado en los últimos meses (más reparaciones futuras).
2. Pantallas presentes en más plataformas (más duplicación).
3. El resto.

### Paso 3 — Definir la estructura destino

Aplica `references/selectors-in-testdata-json.md` de `[[calidad-appium-wdio-greenfield]]`. Un archivo por épica y plataforma base, grupos en camelCase, plataformas derivadas resueltas por el mapa.

Si el proyecto ya tiene algunos archivos de test-data, **se sigue su convención**, no la del chapter.

### Paso 4 — Migrar, una pantalla por vez

Por cada pantalla, en este orden:

1. Crear o ampliar el archivo de test-data de cada plataforma base afectada, con el grupo de selectores.
2. Copiar el selector **literal, sin reescribirlo**. Optimizarlo de paso mezcla dos cambios y hace imposible saber cuál rompió qué.
3. Reemplazar el literal en el código por la referencia al selector cargado.
4. Compilar.
5. Ejecutar los escenarios de esa pantalla.
6. Comparar contra la línea base.

El paso 2 es donde se pierde la disciplina. Un selector frágil que se detecta durante la migración se **anota como recomendación**; se mejora después, en un cambio aparte, con su propia verificación.

### Paso 5 — Consolidar duplicados

Terminada la migración de una épica, aparecen selectores idénticos declarados con nombres distintos en pantallas distintas. Se unifican **solo dentro de la misma plataforma base y la misma épica**, y solo cuando son idénticos carácter por carácter.

Dos selectores parecidos que apuntan a elementos distintos de pantallas distintas no se unifican: el ahorro es mínimo y el acoplamiento hace que un cambio en una pantalla rompa la otra.

### Paso 6 — Verificar

- [ ] `grep` del paso 1 devuelve vacío en el alcance migrado.
- [ ] `npx tsc --noEmit` sin errores.
- [ ] Todos los JSON parsean.
- [ ] La suite del alcance migrado da **exactamente el mismo resultado** que la línea base: mismos escenarios en verde, mismos en rojo.
- [ ] Ningún archivo de infraestructura tocado.

El criterio de éxito es que **nada cambie de comportamiento**. Un escenario que antes fallaba y ahora pasa es tan sospechoso como el caso contrario: significa que el selector se modificó durante la copia.

### Paso 7 — Entregar

Reporte con: selectores migrados por pantalla y plataforma, archivos de test-data creados, comparación contra la línea base, duplicados consolidados, y la lista de selectores frágiles detectados como recomendación para un trabajo posterior.

## Criterios de finalización

- [ ] Cero selectores en código dentro del alcance acordado.
- [ ] Resultado de la suite idéntico a la línea base.
- [ ] Cero cambios de comportamiento, incluidos los "para bien".
- [ ] Selectores copiados literalmente; ninguno reescrito durante la migración.
- [ ] Recomendaciones de mejora registradas aparte, sin aplicar.
