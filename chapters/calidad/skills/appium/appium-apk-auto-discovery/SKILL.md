---
id: calidad-appium-apk-auto-discovery
version: 1.1.0
scope: stack
type: skill
chapter: calidad
stack: [appium]
enforcement: mandatory
description: "Auto-descubre selectores reales recorriendo una app Android desde su APK: arranca emulador/device, instala APK, captura view hierarchy con Appium Inspector REST API, extrae selectores reales (resource-id > content-desc > xpath) y los inyecta en los Page Objects en vez de TODOs."
tags: [appium, mobile, android, apk, auto-discovery, view-hierarchy, selector-extraction, runtime]
verification:
  - check: "Pregunta al usuario antes de activarse (auto vs deferred-locators)"
    failure_message: "Bloqueado: auto-discovery requiere consentimiento explícito del usuario"
  - check: "Verifica capacidades previas (adb, appium server, emulator/device, APK válido)"
    failure_message: "Bloqueado: faltan capacidades; degradar a deferred-locators"
  - check: "Genera .evidence/locators-discovered.json con score de confianza por locator"
    failure_message: "Bloqueado: sin auditoría de locators no se puede declarar success"
---

# Skill — Appium APK Auto-Discovery

## Cuándo aplicar

Cuando se genera un proyecto Appium Android greenfield Y el usuario provee APK Y existen capacidades de runtime (adb, appium, emulator/device). Es una **alternativa opcional** al deferred-locators-strategy: el usuario debe elegir explícitamente entre las dos opciones.

## Cómo encaja en el workflow

Invocado desde `[[calidad-generate-appium-screenplay-android]]` en su paso (después de pre-flight) cuando se verifican capacidades. Si el usuario acepta auto-discovery → este skill toma el control de la generación de Page Objects con selectores reales. Si rechaza → se sigue con `[[calidad-appium-screenplay-android]] (consultar `references/deferred-locators-strategy.md` en su subfolder)` (comportamiento default actual).

## Instrucción

1. **Validar capacidades runtime** — `adb devices` ≥1, `appium --version` presente, `aapt dump badging $APK_PATH` legible. Si algo falta → reportar al usuario y caer a deferred. Ver `references/adb-and-emulator-bootstrap.md`.
2. **Preguntar al usuario explícitamente**: "Detecto APK + emulador + Appium server. Puedo: (a) Auto-descubrir selectores reales recorriendo la app (~3-5 min). (b) Continuar con locators diferidos (TODO). ¿Cuál prefieres?" Default sugerido: (a). NUNCA proceder sin respuesta.
3. **Arrancar Appium server local** en `127.0.0.1:4723` si no está corriendo. Ver `references/adb-and-emulator-bootstrap.md`.
4. **Instalar APK y lanzar app** con `adb install` + `am start -n {appPackage}/{appActivity}`. Pre-flight ya extrajo appPackage/appActivity de `aapt dump badging`.
5. **Crear session Appium** vía REST con `automationName=UiAutomator2`, capabilities apropiadas.
6. **Crawling sistemático**: usar `references/crawler-strategy.md` — heurísticas conservadoras (tap en cada Button/clickable, swipe vertical para scroll, back para volver), capturar `getPageSource()` por pantalla, identificar pantallas únicas por hash del XML, evitar loops, limit de profundidad 5.
7. **Extracción de selectores** según `references/selector-extraction-rules.md`: priorizar `resource-id` (más estable) > `content-desc` (accessibility) > `text` (frágil) > `xpath` (último recurso). Score de confianza por locator según `references/locator-confidence-scoring.md`.
8. **Generar Page Objects** con selectores reales (no TODOs). Persistir `.evidence/locators-discovered.json` con pantalla, selector elegido, alternativas descartadas, score. Cleanup según `references/safety-and-cleanup.md`.


**Verificación obligatoria de cada locator descubierto** (`[[calidad-appium-screenplay-android]]`, consultar `references/locator-resolution-protocol.md`): un identificador encontrado en la jerarquía da **identidad, no capacidad**. Antes de fijarlo en un Page Object: contar cuántos nodos resuelve (**único válido = 1**), identificar el nodo realmente capaz (el contenedor del identificador suele no ser clickeable ni editable) y validar por **efecto externo** (la interacción produce navegación o una petición al backend). Un locator "descubierto" que nunca se ejerció es una hipótesis, no un hallazgo.

## Restricciones

- NUNCA proceder sin consentimiento explícito del usuario (paso 2 obligatorio).
- NUNCA dejar el device en estado dirty: uninstall APK al terminar, kill appium server si lo arrancamos, no dejar emulador colgado.
- Si crawl falla en >30% de pantallas detectadas → fallback a deferred-locators con razón documentada.
- NUNCA modificar selectores ya descubiertos sin re-correr crawl completo.
- Tiempo máximo: 10 minutos por sesión. Después → reportar parcial.

## Cross-links

`[[calidad-generate-appium-screenplay-android]]`, `[[calidad-appium-screenplay-android]] (consultar `references/deferred-locators-strategy.md` en su subfolder)` (alternativa), `[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-test-self-healing]]`.
