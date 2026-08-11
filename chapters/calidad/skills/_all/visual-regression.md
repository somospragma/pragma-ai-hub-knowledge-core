---
id: calidad-visual-regression
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Política transversal de regresión visual para suites del chapter calidad: cuándo correr, gestión de baselines, manejo de dinamismo, match levels, tags y anti-patrones. Aplica a web (Playwright) y móvil (Appium); enlaza a la implementación por stack."
tags: [visual-regression, screenshots, baselines, transversal, web, mobile, all-stacks]
---

# Regresión visual — Política transversal de pruebas

## Instrucción

Define **qué** y **cuándo** en regresión visual para cualquier suite del chapter. El
**cómo** específico (herramienta, API) vive en la reference del stack. No dupliques la
política en un stack: enlázala.

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

- Comparar screenshots byte-a-byte en disco con `assertEquals`: rompe ante cualquier
  cambio de DPI/antialiasing.
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
