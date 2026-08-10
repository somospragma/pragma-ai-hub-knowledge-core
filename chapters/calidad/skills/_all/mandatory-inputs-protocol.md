---
id: calidad-mandatory-inputs-protocol
version: 1.4.0
scope: chapter
type: skill
chapter: calidad
description: Define los inputs obligatorios y opcionales que el usuario debe entregar antes de generar cualquier prueba automatizada.
tags: [inputs, protocol, spec, firma, user-story, enforcement, mandatory]
enforcement: mandatory
verification:
  - check: "los 4 inputs base (intent, project_name, output_path, spec/ui_source/apk_path) + modo de operación confirmados explícitamente por el usuario"
    failure_message: "Bloqueado: faltan inputs obligatorios o el modo de operación no fue confirmado. No se puede generar sin contrato de entrada completo."
  - check: "project_name matchea ^[a-z][a-z0-9-]*[a-z0-9]$ y output_path es ruta absoluta verificada"
    failure_message: "Bloqueado: project_name u output_path no cumplen las reglas formales del protocolo."
  - check: "spec entregado como contenido completo, no como ruta de archivo"
    failure_message: "Bloqueado: se requiere el contenido completo del spec, no la ruta del archivo."
  - check: "risk_map confirmado por usuario o default HIGH reportado explícitamente para revisión"
    failure_message: "Bloqueado: no se puede priorizar sin risk_map confirmado o default HIGH declarado al usuario."
  - check: "sut_available, data_available y (front/mobile) locator_map resueltos vía SUT readiness gate antes de validar spec"
    failure_message: "Bloqueado: no se resolvió si el desarrollo/datos/mapeo de locators están disponibles. Aplicar el SUT readiness gate."
---

# Mandatory Inputs Protocol — Contrato de Entrada Antes de Generar

## Cuándo aplicar

Aplica este skill **al inicio** de cualquier solicitud (paso 1 de `[[calidad-route-test-generation]]`). Su objetivo es asegurar que todos los insumos necesarios están presentes y bien formados antes de invocar `[[calidad-spec-validation]]` o cualquier workflow de generación.

## Inputs comunes y su semántica

| Input          | Obligatoriedad                                  | Qué es                                                                                            | Cómo se usa                                                                                                  |
|----------------|-------------------------------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `intent`       | Obligatorio                                     | Texto en lenguaje natural que describe qué quiere el usuario                                      | Insumo de `[[calidad-intent-detection]]` para elegir framework                                               |
| `project_name` | Obligatorio                                     | Nombre del proyecto en **kebab-case**                                                             | Nombre de carpetas, artefactos Maven/npm, identificadores en reportes                                        |
| `output_path`  | Obligatorio                                     | Ruta **absoluta** del directorio donde se escriben los archivos                                   | Destino del streaming de archivos (`[[calidad-streaming-files-protocol]]`)                                   |
| `spec`         | Obligatorio (Karate/K6)                         | **Contenido COMPLETO** del OpenAPI/Swagger/WSDL (no la ruta del archivo)                          | Input de `[[calidad-spec-validation]]`; fuente única para endpoints, schemas y auth                          |
| `base_url`     | A veces obligatorio                             | Base URL del servicio                                                                             | Necesario si el spec **no** lo declara (algunos Swagger 2.0 sin `host`, WSDL sin `<soap:address>` accesible) |
| `user_story`   | Opcional (recomendado · obligatorio en Karate brownfield cuando el cliente impone convenciones cliente-específicas) | Historia de usuario (formato Gherkin libre o As-a/I-want/So-that) con criterios de aceptación   | Naming de escenarios, prioridad de endpoints, criterios negativos                                            |
| `firma`        | Opcional (altamente recomendado)                | Documento técnico del servicio: reglas de negocio, ejemplos de datos reales, terminología, SLAs   | Enriquecimiento de payloads, escenarios `@negative`, vocabulario en nombres de escenarios                    |
| `extra_params` | Opcional                                        | JSON con parámetros framework-specific                                                            | Ej.: `{"include_login_case": true}` para Appium, `{"thresholds": {"http_req_duration": "p(95)<500"}}` para K6 |
| `sut_available` | Obligatorio (pregunta sí/parcial/no)           | ¿El desarrollo está desplegado y accesible?                                                       | Resuelve `execution_target: real | hybrid | mock` vía `[[calidad-sut-readiness-gate]]` (paso 1.5 del router)  |
| `data_available` | Obligatorio (pregunta sí/no)                   | ¿Existen datos de prueba en el ambiente (o catálogo de datasets del cliente)?                     | Resuelve `data_strategy: real | synthetic` (`[[calidad-test-data-management]]`)                               |
| `locator_map`  | Condicional (front/mobile; **obligatorio** si `execution_target != real`) | Mapeo acordado QA+dev de identificadores UI (`data-testid` / accessibility ids)  | Fuente única de selectores pre-desarrollo; formato y contrato en `[[calidad-ui-locator-map-contract]]`        |

## Todo insumo entregado se lee COMPLETO y se declara qué se extrajo

Un insumo que el usuario entrega es una instrucción, no un adorno. Antes de generar nada, emitir una **tabla de extracción** —una fila por insumo— con: qué es, qué se extrajo de él y dónde se usará.

| Insumo | Qué se extrajo | Dónde se usa |
|---|---|---|
| `locator-map.json` | 13 pantallas, 173 identificadores, convención `semantics_identifier`, bloque `resolution_verified` con la estrategia Android | Targets, prototipo, gate de paridad |
| Prototipo interactivo (HTML) | 82 textos exactos, modelo de datos, formato de moneda, grafo de navegación | Catálogo de textos, datos del prototipo, orden de pantallas |
| … | … | … |

Reglas duras:

- **Leer el archivo entero**, no su primera pantalla. Los bloques que resuelven el trabajo suelen estar al final (verificado en campo: el `locator-map.json` traía el bloque con la estrategia de locators correcta y el agente pasó cinco turnos redescubriéndola por ensayo y error).
- **Un insumo sin fila en la tabla es un insumo ignorado** → blocker. Si de verdad no aporta, se declara explícitamente por qué.
- **Volver a los insumos durante el trabajo**, no solo al inicio: ante un fallo de datos, textos, montos o navegación, el insumo original manda sobre la inferencia. En campo, un prototipo interactivo entregado como insumo se abrió una sola vez, antes de escribir la estrategia, y nunca más — contenía la respuesta a cinco de los diecinueve problemas que costaron la sesión.
- Los valores del insumo **se copian, no se recuerdan**: montos, textos y rutas se transcriben del archivo, no de memoria.

## Reglas de uso

1. **Lee la `firma` ANTES de analizar el spec.** La firma te da el dominio, las reglas de negocio y los valores reales para construir payloads creíbles. Sin ese contexto, las pruebas terminan siendo "happy-path inventado".
2. **Si `user_story` está presente, los escenarios deben nombrarse con su lenguaje de negocio.** Ejemplo: si la historia habla de "cliente Pyme", el escenario es `"Cliente Pyme consulta su saldo disponible"`, no `"GET /accounts/{id} returns 200"`.
3. **Si la `firma` define reglas no presentes en el spec** (ej.: "un cliente no puede tener más de 3 direcciones activas") → **genera escenarios `@negative` aunque el spec no las indique**. La firma es fuente de verdad de negocio incluso cuando el contrato técnico no la refleja.
4. **NUNCA inventes** reglas, headers, valores enum, mensajes de error o flujos que no estén ni en el spec ni en la firma. Si falta información crítica, **pregunta**; no rellenes.
5. **Validación de `project_name`**: debe matchear `^[a-z][a-z0-9-]*[a-z0-9]$`. Si trae espacios, mayúsculas o snake_case, rechaza y solicita corrección.
6. **Validación de `output_path`**: debe ser absoluta. Si es relativa, rechaza. Antes de escribir, verifica que el directorio padre existe.
7. **Validación de `spec`**: si el usuario pasa una ruta de archivo en lugar de contenido, rechaza con: *"se requiere el contenido completo del spec, no la ruta del archivo."*

## Flujo de recolección

```
1. Pedir al usuario los obligatorios faltantes, uno por uno o en bloque (preferir bloque para no fragmentar).
2. Si un input está incompleto → indicar exactamente QUÉ falta, no devolver "está incompleto".
3. Resolver el SUT readiness gate ([[calidad-sut-readiness-gate]]): sut_available, data_available y (front/mobile) locator_map. El resultado puede endurecer los inputs restantes.
4. Confirmar opcionales relevantes según framework detectado (firma, user_story, extra_params).
5. Para proyectos con convenciones cliente-específicas detectadas (ver `[[calidad-karate-brownfield]]` y su reference `client-specific-conventions.md`), aplicar reglas adicionales descritas allí.
6. Solo cuando TODOS los obligatorios están presentes → pasar el control a [[calidad-spec-validation]].
```

### Inputs para la ruta funcional

Los intents funcionales (análisis/refinamiento de HUs, diseño de casos, estrategia/plan) NO usan la tabla de arriba: su contrato de entrada lo define cada workflow funcional (`[[calidad-analyze-and-refine-stories]]`, `[[calidad-design-test-cases]]`, `[[calidad-build-test-strategy-and-plan]]`). Común a los tres: `stories_source`/`contexto_fuente` (IDs o queries del ALM vía `[[calidad-alm-mcp-integration]]`, o el contenido pegado) y `output_path`. `spec`, `sut_available` y `locator_map` no aplican salvo que el flujo derive en automatización (re-entrada al router).

Cruce con la `user_story` de esta tabla: si la HU entregada como input de automatización está visiblemente rota (sin CA, ambigua), ofrecer el análisis funcional (`[[calidad-funcional-story-analysis]]`) ANTES de generar código — mejora el insumo en vez de generar sobre él.

### K6-specific inputs

Para proyectos K6, además de los inputs base de la tabla anterior, el agente DEBE completar el checklist K6-específico (perfil de carga por escenario, dependencias externas, disponibilidad objetivo, data de prueba, endpoint objetivo vs auxiliares, volumen esperado, restricciones de ambiente). Ver [[calidad-k6-greenfield]] (consultar `references/k6-discovery-checklist.md`).

Sin este checklist, K6 no puede generar `options.stages` ni `options.thresholds` defendibles y debe degradar a `scaffold-only`.

## Overrides por convenciones cliente-específicas

Algunos clientes/proyectos imponen overrides sobre los inputs opcionales. Patrón típico: clientes con convenciones brownfield estrictas (ver `[[calidad-karate-brownfield]]` y su reference `client-specific-conventions.md`) elevan `user_story` y `firma` a obligatorios.

| Escenario                                                            | Skill / asset                      | Inputs que pasan a obligatorios                                                                                                                                       |
|----------------------------------------------------------------------|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Karate brownfield con convenciones cliente-específicas detectadas    | `[[calidad-karate-brownfield]]`            | `user_story` y `firma` son **obligatorios** (no opcionales). Convenciones genéricas detalladas en el reference `client-specific-conventions.md` dentro del skill `karate-brownfield`. |
| Pruebas antes del desarrollo (`execution_target: mock` o `hybrid`)   | `[[calidad-sut-readiness-gate]]`           | Karate/K6: `spec` con **response schemas completos y examples**. Playwright: fuente UI + `locator_map`. Appium: `locator_map` con accessibility ids. Matriz completa en el skill del gate. |

### Pattern para nuevos overrides

Cuando un cliente o proyecto necesite endurecer inputs:

1. Documentar la regla en el SKILL del framework correspondiente (por ejemplo `karate-brownfield/SKILL.md` o un reference de convenciones cliente-específicas).
2. Apuntar el override en la tabla de arriba con: escenario, skill o asset que lo define, lista de inputs que se vuelven obligatorios.
3. Si el override aplica también a la validación de spec o al flujo de generación, mencionarlo en el skill de framework, no acá: este documento sólo concentra el pointer.

## Restricciones

- **NUNCA proceder** sin los inputs obligatorios resueltos.
- **NUNCA mezclar** convenciones cliente-específicas detectadas en un proyecto con proyectos genéricos de otros clientes.
- **NUNCA asumir** valores por defecto para `base_url`, headers de auth o entornos: si falta, se pregunta.
- Encadena con `[[calidad-spec-validation]]` (paso siguiente) y con `[[calidad-intent-detection]]` (paso previo).
