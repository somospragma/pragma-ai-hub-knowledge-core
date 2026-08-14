---
id: calidad-visual-regression
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Política transversal de regresión visual para suites del chapter calidad: cuándo correr, gestión de baselines, manejo de dinamismo, match levels, tags y anti-patrones. Aplica a web (Playwright) y móvil (Appium); enlaza a la implementación por stack."
tags: [visual-regression, screenshots, baselines, transversal, web, mobile, all-stacks, design-baseline]
verification:
  - check: "todo escenario etiquetado @visual ejecuta una comparación de imagen contra un baseline y adjunta baseline, actual y diff"
    failure_message: "Bloqueado: hay escenarios marcados como visuales que no comparan imágenes. Afirmar texto no es validación visual: duplica lo que ya verifica el humo y reporta cobertura que no existe."
  - check: "cada baseline declara su origen (design o previous_run) y su entorno de captura"
    failure_message: "Bloqueado: hay baselines sin origen declarado. Un diff contra un recorte de diseño no se interpreta igual que uno contra una corrida previa."
---

# Regresión visual — Política transversal de pruebas

## Instrucción

Define **qué** y **cuándo** en regresión visual para cualquier suite del chapter. El
**cómo** específico (herramienta, API) vive en la reference del stack. No dupliques la
política en un stack: enlázala.

## Regla dura: `@visual` obliga a comparar imágenes

Un escenario etiquetado `@visual` **debe** producir una comparación imagen contra baseline
y adjuntar los tres artefactos: **baseline, actual y diff**.

**Afirmar texto, atributos o presencia de elementos no es validación visual.** Si el
escenario no compara imágenes, no lleva el tag. Verificado en campo: se entregó un
escenario presentado como validación contra el diseño que solo afirmaba texto — exactamente
lo que ya verificaba el escenario de humo. Cero valor añadido y cobertura visual reportada
que no existía.

Corolario para el diseño de escenarios: si el criterio de aceptación habla de **contenido**
(qué dice, qué campos aparecen), es un escenario funcional. Si habla de **presentación**
(cómo se ve, disposición, estilo, fidelidad al diseño), es un escenario visual y compara
imágenes. Un mismo criterio rara vez es ambos.

## Baseline desde diseño

Cuando no existe un baseline histórico —caso típico de una funcionalidad nueva— el recorte
del diseño es un **baseline válido de primera generación**:

- Se declara `baseline_source: design`, frente a `baseline_source: previous_run`. El origen
  cambia cómo se interpreta el diff: contra diseño se esperan diferencias de renderizado
  legítimas; contra corrida previa, cualquier diferencia es un cambio.
- **Match level tolerante** (layout o estructura), nunca estricto: el diseño y el render
  real difieren en tipografía, antialiasing y densidad sin que eso sea un defecto.
- Las zonas de contenido volátil se excluyen antes de comparar
  (`[[calidad-data-volatility-and-assertion-anchoring]]`): el contenido de una maqueta es
  muestra, no dato.
- El recorte se toma de los artefactos persistidos por `[[calidad-figma-mcp-integration]]`
  en `.evidence/design/`, con su manifiesto. Si el hash del diseño cambió, se avisa antes
  de comparar contra un baseline obsoleto.
- Un diff contra diseño que revela una diferencia real de presentación es un hallazgo que
  pasa por `[[calidad-failure-triage-and-classification]]` como cualquier otro, con la
  cadena de evidencia si se va a reportar como defecto.

## Cuándo aplicar

- Una captura por pantalla/página priorizada (`CRITICAL`, `HIGH`) según
  `[[calidad-business-driven-prioritization]]`.
- En un **job dedicado** del pipeline, filtrado por tag, en cada PR a `main` y en cada
  release candidate — **no** en cada test del pipeline (costo y tiempo de captura).
- Greenfield genera la suite desde el inicio; brownfield la agrega sin tocar baselines
  ni tests preexistentes (`[[calidad-brownfield-vs-greenfield]]`).

## Gestión de baselines

- Los baselines se versionan (web: en el repo) o se gestionan en la herramienta
  (móvil: cloud del proveedor). La primera corrida genera el baseline; las siguientes comparan.
- **Todo baseline declara su origen** (`design` o `previous_run`) y su entorno de captura.
  Un baseline sin origen no se puede interpretar cuando falla.
- **Un entorno de captura estable y único** por baseline: mismo navegador/engine (web) o
  mismo `(platform, deviceModel, platformVersion, orientation)` (móvil). No mezclar
  fuentes de captura en un mismo baseline.

## Manejo del dinamismo

- Excluir/recortar zonas que cambian a cada corrida (status bar, hora, batería, notch en
  móvil; widgets con datos dinámicos en web).
- **Match level** acorde al contenido: estricto en pantallas estáticas; layout/ignorar
  contenido en pantallas con datos dinámicos. Evitar comparación pixel-perfect frágil.

## Tags y evidencia

- Etiquetar los escenarios con `@visual` además de los tags del chapter.
- Anexar el resultado del match como evidencia según
  `[[calidad-test-evidence-and-traceability]]` y `[[calidad-execution-metadata-schema]]`.

## Anti-patrones

- **Escenario `@visual` que no compara imágenes**: es el anti-patrón más caro porque
  reporta cobertura visual inexistente. Si solo afirma texto, es un escenario funcional
  mal etiquetado.
- Comparar screenshots byte-a-byte en disco con `assertEquals`: rompe ante cualquier
  cambio de DPI/antialiasing.
- Comparar contra un baseline de diseño con match level estricto: produce diffs falsos en
  cada corrida por diferencias de renderizado que no son defectos.
- Usar un baseline de diseño cuyo hash cambió sin volver a exportarlo: se compara contra
  una versión que el equipo ya descartó.
- Mezclar baselines de distintos engines/devices en un mismo conjunto.
- No recortar la zona dinámica (hora/notch): genera diffs falsos en cada corrida.
- Subir claves de API del proveedor al repo: solo vía secret del CI.

## Implementación por stack

- **Web (Playwright):** `toHaveScreenshot` (solo Chromium), baselines en
  `tests/__screenshots__/`. Ver
  [[calidad-playwright-greenfield]] (consultar `references/visual-regression.md` en su subfolder).
- **Móvil (Appium/Screenplay):** Applitools Eyes / Percy, baselines por device profile.
  Ver
  [[calidad-appium-screenplay-android]] (consultar `references/mobile-visual-regression.md` en su subfolder).

## Cross-links

`[[calidad-figma-mcp-integration]]`, `[[calidad-data-volatility-and-assertion-anchoring]]`,
`[[calidad-business-driven-prioritization]]`, `[[calidad-test-evidence-and-traceability]]`,
`[[calidad-execution-metadata-schema]]`, `[[calidad-failure-triage-and-classification]]`,
`[[calidad-brownfield-vs-greenfield]]`.
