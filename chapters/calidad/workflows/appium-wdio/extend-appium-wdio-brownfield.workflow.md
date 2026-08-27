---
id: calidad-extend-appium-wdio-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [appium-wdio]
description: Extiende un arquetipo Appium WebdriverIO existente con escenarios, pantallas, selectores o plataformas nuevas sin tocar su infraestructura.
tags: [appium, webdriverio, typescript, cucumber, brownfield, mobile]
---

# Extender arquetipo Appium WebdriverIO

## Cuándo usar este workflow

Cuando el router `[[calidad-route-test-generation]]` resolvió intent mobile sobre stack Node/TypeScript y el `output_path` ya contiene un arquetipo Appium standalone (mobile-only) — no un arquetipo `serenity-wdio` multiplataforma, que aunque también es Node/WebdriverIO se extiende con `[[extend-serenity-wdio-brownfield]]`. Es la ruta habitual con clientes que ya tienen suite: se agrega cobertura, no se reemplaza nada.

## Pasos

### Paso 0 — Verificar que `appium-core` está instalado

Este stack **depende de `appium-core`**, que se instala aparte. Antes de cualquier otra cosa, comprueba que el workspace tiene los tres bundles del core: `[[calidad-mobile-locator-resolution]]`, `[[calidad-mobile-interactions]]` y `[[calidad-appium-apk-auto-discovery]]`.

Si faltan, **detente y díselo al usuario** con el comando exacto:

```
pragma-ai init --ide <ide> --chapter calidad --stack appium-core
```

No es una recomendación: sin el protocolo de resolución de locators se generan selectores plausibles en vez de verificados, y eso produce una suite verde que no prueba nada. Si el usuario decide continuar sin el core, déjalo declarado en la traza del pipeline y en el delivery gate como una carencia asumida.

### Paso 1 — Recolectar inputs

Obligatorios: `project_root`, `change_type` (`new-scenario`, `new-screen`, `selector-update`, `new-platform`, `refactor`) y `change_description`. Condicionales: `user_story` o `test_cases`, `new_selectors`, `platform`.

### Paso 2 — Inventariar el arquetipo

Aplica `references/convention-detection.md` de `[[calidad-appium-wdio-brownfield]]` completo y **emite el objeto de convenciones en el turno**. Todo lo que se genere después se valida contra él.

Este paso no es opcional ni se resume. Generar antes de inventariar produce archivos correctos en abstracto e incorrectos para el proyecto, que es lo que se rechaza en revisión.

### Paso 3 — Establecer la línea base

Corre las 12 propiedades de `[[calidad-cucumber-bdd-conventions]]` sobre el árbol completo **antes de tocar nada** y guarda el resultado. Separa lo que ya estaba roto de lo que uno rompa; sin ella, cualquier fallo posterior se atribuye al cambio.

Los hallazgos preexistentes se registran para el reporte. **No se corrigen.**

### Paso 4 — Catálogo de steps

Si el proyecto tiene catálogo, se consulta. Si no lo tiene, se genera desde el código antes de agregar escenarios: es lo único que evita duplicar steps que ya existen en otra épica y provocar ambigüedades en features que nadie estaba tocando.

### Paso 5 — Clasificar y declarar

Clasifica cada step candidato en `reuse`, `extend-platform`, `new-local` o `new-shared`, y **emite la tabla en el turno** antes de generar. Es la traza de que el paso 4 se hizo.

### Paso 6 — Generar solo lo solicitado

Según `change_type`, siguiendo la instrucción de `[[calidad-appium-wdio-brownfield]]`. Los archivos se persisten con `[[calidad-streaming-files-protocol]]`.

No se tocan configuración del runner, `package.json`, `tsconfig.json`, hooks, gestor del servidor Appium ni motor de drivers. Si el cambio pedido exige tocar alguno, **detente y explica por qué** antes de hacerlo.

### Paso 7 — Verificar contra la línea base

- [ ] `npx tsc --noEmit` sin errores.
- [ ] Linter limpio sobre los archivos tocados.
- [ ] `--dry-run` del perfil afectado: ni `undefined` ni `ambiguous`.
- [ ] Las 12 propiedades **comparadas contra la línea base del paso 3**. Cualquiera que empeore es blocker.

### Paso 8 — Ejecutar lo generado

Solo los escenarios nuevos o afectados, con el perfil de su plataforma. Triage con `[[calidad-failure-triage-and-classification]]` y corrección con `[[calidad-test-self-correction-loop]]` si aplica.

Si el entorno no permite ejecutar (sin dispositivo, sin credenciales, sin macOS para iOS), se reporta `partial` con el motivo y el comando exacto para que lo corra el cliente. **No se declara éxito sin ejecución.**

### Paso 9 — Reportar

- Archivos tocados, uno por uno.
- Steps reutilizados contra steps creados, con la tabla del paso 5.
- Resultado de la ejecución.
- **Hallazgos preexistentes detectados y no corregidos**, con evidencia y fix sugerido para cada uno.
- Bloque de `[[calidad-delivery-gate-contract]]`.

## Criterios de finalización

- [ ] El objeto de convenciones se emitió antes de generar y todo lo generado lo cumple.
- [ ] La línea base de propiedades se estableció antes de tocar nada y no empeoró.
- [ ] La tabla de clasificación de steps se emitió antes de generar.
- [ ] Cero archivos de infraestructura modificados, o modificación explicada y acordada.
- [ ] Cero selectores nuevos en código.
- [ ] Cero steps existentes modificados.
- [ ] Cero escenarios de suites protegidas tocados.
- [ ] Lo generado se ejecutó, o el motivo de no poder ejecutarlo está declarado con su comando de remediación.
- [ ] Los hallazgos preexistentes están reportados y ninguno fue corregido sin permiso.
