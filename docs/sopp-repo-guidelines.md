# SOPP AI — Lineamientos de Repositorios de Conocimiento

> Este documento es la referencia completa para crear y mantener un repositorio de conocimiento SOPP AI.
> Aplica tanto a `pragma-ai-knowledge-core` como a cualquier `pragma-ai-knowledge-{cuenta}`.
> Entrégalo a quien vaya a crear el repo, el linter y los GitHub Actions — contiene todo lo necesario.

---

## Tabla de Contenidos

1. [Repositorios existentes y sus roles](#1-repositorios-existentes-y-sus-roles)
2. [Estructura de carpetas](#2-estructura-de-carpetas)
3. [Templates de assets](#3-templates-de-assets)
4. [Reglas de validación — el linter](#4-reglas-de-validación--el-linter)
5. [GitHub Actions](#5-github-actions)
6. [Contrato del webhook hacia el Hub](#6-contrato-del-webhook-hacia-el-hub)
7. [Cómo crear un repo de cuenta desde el template](#7-cómo-crear-un-repo-de-cuenta-desde-el-template)

---

## 1. Repositorios existentes y sus roles

| Repo | Propósito | Dueño | Quién puede hacer PR |
|---|---|---|---|
| `pragma-ai-knowledge-core` | Conocimiento transversal de toda Pragma | Equipo Central Pragma AI | Cualquier pragmático |
| `pragma-ai-knowledge-{cuenta}` | Conocimiento específico o overrides por cuenta | AI Steward de la cuenta | Pragmáticos de esa cuenta |
| `sopp-ai-hub` | Código del Hub (Lambdas, CLI) | Equipo de Plataforma | Equipo de Plataforma |

`pragma-ai-knowledge-core` y todos los `pragma-ai-knowledge-{cuenta}` siguen **exactamente la misma estructura** de carpetas y las mismas reglas. Un repo de cuenta no necesita replicar toda la estructura — solo define lo que quiere agregar o sobrescribir.

---

## 2. Estructura de carpetas

> **Nota:** La carpeta `_config/` solo existe en `pragma-ai-knowledge-core`. Los repos de cuenta **no la tienen**. Es mantenida exclusivamente por el Equipo de Plataforma.

```
/
├── _config/                  ← SOLO en pragma-ai-knowledge-core
│   ├── taxonomy.json         ← chapters, plataformas, stacks y señales de detección
│   ├── ides.json             ← IDEs soportados, capacidades y path templates
│   └── templates/            ← plantillas de renderizado por IDE y tipo de asset
│       ├── kiro/
│       ├── github-copilot/
│       ├── amazon-q-ide/
│       └── amazon-q-cli/
│
├── .github/
│   ├── workflows/
│   │   ├── lint.yml          ← linter en cada PR
│   │   └── webhook.yml       ← notifica al Hub en cada push a main
│   └── CODEOWNERS            ← quién aprueba qué carpeta
│
├── chapters/
│   ├── backend/
│   │   ├── steering/
│   │   ├── skills/
│   │   │   ├── _all/         ← aplica a todo backend sin distinción de stack
│   │   │   ├── n/
│   │   │   ├── node/
│   │   │   └── dotnet/
│   │   ├── agents/
│   │   ├── workflows/
│   │   ├── guardrails/
│   │   ├── prompts/
│   │   ├── personas/
│   │   └── convenciones/
│   │       ├── _all/
│   │       ├── java-spring/
│   │       └── node/
│   │
│   ├── calidad/
│   │   ├── steering/
│   │   ├── skills/
│   │   │   ├── _all/
│   │   │   └── automation/
│   │   ├── workflows/
│   │   ├── guardrails/
│   │   └── prompts/
│   │
│   ├── mobile/
│   │   ├── steering/
│   │   ├── skills/
│   │   │   ├── _all/
│   │   │   ├── flutter/
│   │   │   └── android/
│   │   ├── workflows/
│   │   ├── guardrails/
│   │   └── prompts/
│   │
│   ├── frontend/
│   │   ├── steering/
│   │   ├── skills/
│   │   │   ├── _all/
│   │   │   ├── react/
│   │   │   └── angular/
│   │   ├── workflows/
│   │   ├── guardrails/
│   │   └── prompts/
│   │
│   └── arquitectura/
│       ├── steering/
│       ├── skills/
│       │   └── _all/
│       ├── workflows/
│       ├── guardrails/
│       └── adrs/
│
└── shared/
    ├── steering/             ← aplica a TODOS los pragmáticos
    ├── guardrails/           ← restricciones globales
    ├── docs/                 ← documentación consultable
    └── adrs/                 ← decisiones de arquitectura transversales
```

### Reglas de estructura

- Cada archivo va en la carpeta que corresponde a su `type` y su `scope`
- `_all/` dentro de `skills/` o `convenciones/` indica que aplica a todo el chapter sin distinción de stack
- No crear carpetas de stack que no estén en la lista de stacks soportados
- No crear carpetas de chapter fuera de los cinco definidos
- Un repo de cuenta **no necesita** tener todas las carpetas — solo las que tiene contenido

### Reglas de estructura

- Cada archivo va en la carpeta que corresponde a su `type` y su `scope`
- `_all/` dentro de `skills/` indica que aplica a todo el chapter sin distinción de stack
- No crear carpetas de stack que no estén en el listado canónico de `taxonomy.json`
- No crear carpetas de chapter fuera de los cinco definidos
- Un repo de cuenta **no necesita** tener todas las carpetas — solo las que tiene contenido

### Stacks canónicos por chapter

Estos ids son los únicos valores válidos en las carpetas de los repos y en el frontmatter de los assets. La fuente de verdad es `_config/taxonomy.json` en `pragma-ai-knowledge-core`.

| Stack id | Chapter | Plataforma | Carpeta en repo |
|---|---|---|---|
| `java-spring` | backend | java | `chapters/backend/skills/java-spring/` |
| `java-webflux` | backend | java | `chapters/backend/skills/java-webflux/` |
| `node-express` | backend | node | `chapters/backend/skills/node-express/` |
| `node-lambda` | backend | node | `chapters/backend/skills/node-lambda/` |
| `dotnet` | backend | dotnet | `chapters/backend/skills/dotnet/` |
| `react` | frontend | react | `chapters/frontend/skills/react/` |
| `angular` | frontend | angular | `chapters/frontend/skills/angular/` |
| `flutter` | mobile | flutter | `chapters/mobile/skills/flutter/` |
| `android-native` | mobile | android | `chapters/mobile/skills/android-native/` |
| `apple-native` | mobile | apple | `chapters/mobile/skills/apple-native/` |
| `automation` | calidad | automation | `chapters/calidad/skills/automation/` |

---

## 3. Archivos de configuración — `_config/` (solo en core)

La carpeta `_config/` en `pragma-ai-knowledge-core` contiene la configuración que hace funcionar todo el sistema. No es conocimiento — es infraestructura. Solo el Equipo de Plataforma la modifica.

### `taxonomy.json`

**Qué es:** el catálogo oficial de chapters, plataformas y stacks soportados por SOPP AI.

**Para qué sirve:**
- El CLI lo usa para detectar automáticamente el stack de un workspace al correr `pragma-sopp-cli init`, leyendo los archivos del proyecto y comparando contra las señales de detección definidas aquí
- El CLI lo usa para mostrar al pragmático solo las opciones válidas durante el init
- El Hub lo usa para validar que los stacks enviados en un request de sync sean reconocidos
- El linter lo usa para validar que las carpetas de stack en los repos sean válidas

**Dónde vive:** `pragma-ai-knowledge-core/_config/taxonomy.json`

**Cómo se distribuye:** el Hub lo expone en `GET /taxonomy`. El CLI lo descarga en el `install` y lo cachea en `~/.pragma-sopp/taxonomy.json`. Se refresca en cada sync si el Hub tiene una versión más nueva.

**Cuándo se actualiza:** cuando Pragma adopta un nuevo stack o tecnología. El equipo de plataforma abre PR en `pragma-ai-knowledge-core`, actualiza el JSON, y todos los CLIs existentes reciben el cambio sin recompilarse.

**Estructura resumida:**
```json
{
  "version": "1.0.0",
  "chapters": {
    "{chapter}": {
      "platforms": {
        "{platform}": {
          "stacks": ["{stack-id}"],
          "detection": {
            "{stack-id}": {
              "signals": ["archivo1", "*.ext"],
              "requires_signal": { "file": "archivo", "contains": "texto" }
            }
          }
        }
      }
    }
  }
}
```

---

### `ides.json`

**Qué es:** el catálogo de IDEs soportados por SOPP AI con sus capacidades y los path templates donde el CLI debe escribir cada tipo de asset.

**Para qué sirve:**
- El CLI lo usa para saber exactamente en qué ruta del filesystem del pragmático debe escribir cada asset según el IDE activo del workspace — sin lógica hardcodeada en el binario
- El CLI lo usa para omitir silenciosamente los tipos de asset que el IDE no soporta (ej: hooks solo los soporta Kiro)
- El Hub lo usa para saber qué template de renderizado aplicar a cada asset antes de firmarlo
- Cuando Pragma adopte un IDE nuevo, basta con agregarlo aquí — el CLI lo soporta sin recompilarse

**Dónde vive:** `pragma-ai-knowledge-core/_config/ides.json`

**Cómo se distribuye:** el Hub lo expone en `GET /config`. El CLI lo descarga en el `install` y lo cachea en `~/.pragma-sopp/ides.json`. Se refresca en cada sync.

**Cuándo se actualiza:** cuando Pragma adopta un IDE nuevo, cuando un IDE cambia sus paths de configuración, o cuando se agrega soporte para un nuevo tipo de asset en un IDE existente.

**Estructura resumida:**
```json
{
  "version": "1.0.0",
  "ides": [
    {
      "id": "cursor",
      "name": "Cursor",
      "capabilities": ["steering", "skill", "workflow", "guardrail", "persona", "prompt", "convencion"],
      "global_paths": {
        "steering":  "~/.cursor/rules/{id}.mdc",
        "guardrail": "~/.cursor/rules/{id}.mdc"
      },
      "workspace_paths": {
        "steering":   ".cursor/rules/{id}.mdc",
        "skill":      ".cursor/rules/skills/{id}.mdc",
        "workflow":   ".cursor/rules/workflows/{id}.mdc",
        "guardrail":  ".cursor/rules/{id}.mdc",
        "persona":    ".cursor/rules/personas/{id}.mdc",
        "prompt":     ".cursor/rules/prompts/{id}.mdc",
        "convencion": ".cursor/rules/convenciones/{id}.mdc"
      },
      "special_behaviors": {
        "steering": "one_file_per_asset"
      }
    }
  ]
}
```

Los path templates usan `{id}` como placeholder que el CLI reemplaza con el id del asset.

`special_behaviors` indica comportamientos especiales del IDE que el renderer debe aplicar. Por ejemplo, Copilot requiere `concatenate_all` en steering porque todo va en un solo archivo `.github/copilot-instructions.md`.

**IDEs soportados:**

| id | Nombre real | Tipos soportados |
|---|---|---|
| `cursor` | Cursor | steering · skill · workflow · guardrail · persona · prompt · convencion |
| `kiro` | Kiro | steering · skill · workflow · guardrail · persona · prompt · hook · agent |
| `github-copilot` | GitHub Copilot | steering · skill · prompt |
| `amazon-q-ide` | Amazon Q (IDE) | steering · skill · prompt · guardrail |
| `amazon-q-cli` | Amazon Q (CLI) | steering · skill · agent · hook |

---

### `templates/`

Plantillas de renderizado por IDE y tipo de asset. El Hub las usa para transformar el markdown canónico de S3 al formato nativo de cada herramienta. La especificación completa de cada template está en `templates-definitions-ides.md`.

```
_config/templates/
  cursor/
    steering.mdc
    skill.mdc
    workflow.mdc
    guardrail.mdc
    persona.mdc
    prompt.mdc
    convencion.mdc
  kiro/
    steering.md
    skill.md
    workflow.md
    hook.json
    agent.md
  github-copilot/
    steering.md
    skill.prompt.md
  amazon-q-ide/
    steering.md
    skill.md
  amazon-q-cli/
    steering.md
    skill.md
    agent.json
```

---

## 4. Templates de assets

Cada tipo de asset tiene un template obligatorio. El linter valida que el frontmatter sea correcto y que el contenido tenga la estructura mínima esperada.

### Template base — todos los assets comparten este frontmatter

```markdown
---
id: {kebab-case-unico-global}
version: {semver}
scope: {global|chapter|stack}
type: {skill|steering|agent|workflow|guardrail|prompt|persona|doc|adr|convencion}
chapter: {backend|calidad|mobile|frontend|arquitectura}   # omitir si scope=global
stack: [{java-spring|node|dotnet|flutter|android|react|angular}]  # solo si scope=stack
tags: []
description: {una línea}

# Solo en repos de cuenta, cuando el archivo hace override de core:
# pragma_extends: {path en core del asset que extiende}
# pragma_override: {full|merge}
---
```

---

### `steering` — instrucciones de comportamiento global

```markdown
---
id: {chapter}-steering
version: 1.0.0
scope: chapter
type: steering
chapter: {chapter}
description: Comportamiento base del AI para pragmáticos de {chapter}
---

## Rol
{Descripción del rol que asume el AI para este chapter}

## Principios
{Lista de principios que guían el comportamiento del AI}

## Lo que nunca debes hacer
{Lista de restricciones de comportamiento}
```

---

### `skill` — instrucción para una tarea concreta

```markdown
---
id: {verbo-sustantivo-contexto}
version: 1.0.0
scope: {chapter|stack}
type: skill
chapter: {chapter}
stack: [{stack}]   # omitir si scope=chapter
tags: []
description: {qué hace este skill en una línea}
---

## Cuándo aplicar
{Condición o contexto en el que el AI debe activar este skill}

## Instrucción
{Instrucción detallada de lo que debe hacer el AI}

## Restricciones
{Lo que el AI NO debe hacer al ejecutar este skill}
```

---

### `guardrail` — restricciones explícitas

```markdown
---
id: {contexto}-guardrails
version: 1.0.0
scope: {global|chapter|stack}
type: guardrail
chapter: {chapter}   # omitir si scope=global
description: Restricciones para {contexto}
---

## Nunca hagas esto
{Lista explícita de lo que el AI nunca debe hacer en este contexto}
```

---

### `workflow` — secuencia de pasos

```markdown
---
id: {nombre-del-proceso}-workflow
version: 1.0.0
scope: {chapter|stack}
type: workflow
chapter: {chapter}
tags: []
description: Flujo para {qué proceso cubre}
---

## Cuándo usar este workflow
{Condición para activar este workflow}

## Pasos

### 1. {Nombre del paso}
{Instrucción del paso}

### 2. {Nombre del paso}
{Instrucción del paso}

### N. {Nombre del paso}
{Instrucción del paso}

## Criterios de finalización
{Cómo saber que el workflow terminó correctamente}
```

---

### `agent` — definición de agente especializado

```markdown
---
id: {rol}-agent
version: 1.0.0
scope: {chapter|stack}
type: agent
chapter: {chapter}
description: Agente especializado en {rol}
---

## Rol
{Descripción del rol del agente}

## Cómo operar
{Pasos o comportamiento del agente al activarse}

## Criterios de evaluación
{Cómo mide el agente la calidad de su output}
```

---

### `prompt` — plantilla con variables

```markdown
---
id: {tarea}-prompt
version: 1.0.0
scope: {chapter|stack}
type: prompt
chapter: {chapter}
stack: [{stack}]   # omitir si scope=chapter
description: Plantilla para {qué tarea}
---

## Template

{Instrucción con marcadores [VARIABLE] para que el pragmático reemplace}
```

---

### `persona` — modo con rol y restricciones distintas

```markdown
---
id: {nombre}-persona
version: 1.0.0
scope: {chapter|stack}
type: persona
chapter: {chapter}
description: Modo {nombre} para {contexto de uso}
---

## Activación
{Cuándo el AI debe adoptar esta persona}

## Comportamiento en este modo
{Cómo se comporta el AI en este modo}
```

---

### `doc` — documentación consultable

```markdown
---
id: {tema}-doc
version: 1.0.0
scope: {global|chapter|stack}
type: doc
chapter: {chapter}   # omitir si scope=global
tags: []
description: {de qué trata este doc}
---

{Contenido libre del documento}
```

---

### `adr` — decisión de arquitectura

```markdown
---
id: {decision}-adr
version: 1.0.0
scope: {global|chapter}
type: adr
chapter: {chapter}   # omitir si scope=global
tags: []
description: {decisión tomada en una línea}
---

## Contexto
{Por qué se tomó esta decisión — el problema que existía}

## Decisión
{Qué se decidió hacer}

## Consecuencias
{Qué implica esta decisión — ventajas, desventajas, restricciones}
```

---

### `convencion` — estándares de código y naming

```markdown
---
id: {lenguaje|contexto}-conventions
version: 1.0.0
scope: stack
type: convencion
chapter: {chapter}
stack: [{stack}]
description: Convenciones de {qué} para {stack} en Pragma
---

{Secciones libres describiendo las convenciones}
```

---

### Override desde repo de cuenta

Cuando un archivo de cuenta hace override de core, agrega estas líneas al frontmatter:

**Override completo** — reemplaza el asset de core completamente:

```markdown
---
id: {mismo id que en core}
version: 1.0.0
...campos normales...
pragma_extends: {path relativo en core, ej: chapters/backend/skills/java-spring/generate-pr-description}
pragma_override: full
---

{Contenido completamente nuevo — el de core se ignora}
```

**Override parcial por secciones** — solo declara las secciones `##` que cambia o agrega:

```markdown
---
id: {mismo id que en core}
version: 1.0.0
...campos normales...
pragma_extends: {path relativo en core}
pragma_override: merge
---

## {Nombre exacto de sección a reemplazar}
{Nuevo contenido de esa sección}

## {Nueva sección que no existe en core}
{Contenido nuevo que se agrega al final}
```

---

## 5. Reglas de validación — el linter

El linter corre en cada PR como GitHub Action. Si falla, el PR no se puede mergear.

> **`_config/` está excluido del linter.** Los archivos de `_config/` (taxonomy.json, ides.json, templates/) son infraestructura, no contenido. No tienen frontmatter de assets ni siguen las reglas de estructura de carpetas. El linter no los toca — su validación es responsabilidad del Equipo de Plataforma al hacer PR en ese directorio.

### Implementación recomendada

Crear como script Node.js o Go que se instala como dev dependency del repo:

```
sopp-lint/
  index.js (o main.go)
  rules/
    frontmatter.js     ← valida campos del frontmatter
    structure.js       ← valida ubicación del archivo en la carpeta correcta
    ids.js             ← valida unicidad de IDs en el repo
    override.js        ← valida consistencia de overrides
    content.js         ← valida estructura mínima del contenido
```

### Reglas completas

#### FR — Frontmatter

| Código | Regla | Severidad |
|---|---|---|
| `FR-001` | El archivo debe tener frontmatter YAML delimitado por `---` | ERROR |
| `FR-002` | `id` es obligatorio | ERROR |
| `FR-003` | `id` debe estar en kebab-case | ERROR |
| `FR-004` | `id` debe ser único dentro del repo | ERROR |
| `FR-005` | `version` es obligatorio | ERROR |
| `FR-006` | `version` debe ser semver válido (ej: `1.0.0`) | ERROR |
| `FR-007` | `scope` es obligatorio | ERROR |
| `FR-008` | `scope` debe ser `global`, `chapter` o `stack` | ERROR |
| `FR-009` | `type` es obligatorio | ERROR |
| `FR-010` | `type` debe ser uno de: `skill`, `steering`, `agent`, `workflow`, `guardrail`, `prompt`, `persona`, `doc`, `adr`, `convencion` | ERROR |
| `FR-011` | Si `scope=chapter` o `scope=stack`, `chapter` es obligatorio | ERROR |
| `FR-012` | `chapter` debe ser uno de: `backend`, `calidad`, `mobile`, `frontend`, `arquitectura` | ERROR |
| `FR-013` | Si `scope=stack`, `stack` es obligatorio y no puede estar vacío | ERROR |
| `FR-014` | Cada valor en `stack` debe ser un stack válido para el chapter declarado | ERROR |
| `FR-015` | `description` es obligatorio | WARNING |
| `FR-016` | `description` no debe superar 120 caracteres | WARNING |
| `FR-017` | `tags` debe ser un array (puede estar vacío) | WARNING |

#### ST — Estructura de carpetas

| Código | Regla | Severidad |
|---|---|---|
| `ST-001` | El archivo debe estar en la carpeta que corresponde a su `type` | ERROR |
| `ST-002` | El archivo debe estar bajo el chapter declarado en `chapter` | ERROR |
| `ST-003` | Si `scope=stack`, el archivo debe estar bajo la carpeta del stack (`java-spring/`, `node/`, etc.) | ERROR |
| `ST-004` | Si `scope=chapter`, el archivo debe estar bajo `_all/` o directamente en la carpeta del chapter | ERROR |
| `ST-005` | Si `scope=global`, el archivo debe estar bajo `shared/` | ERROR |
| `ST-006` | No se permiten archivos `.md` fuera de la estructura de carpetas definida | ERROR |
| `ST-007` | No se permiten carpetas de stack fuera de los valores soportados por ese chapter | ERROR |

#### OV — Override (solo aplica en repos de cuenta)

| Código | Regla | Severidad |
|---|---|---|
| `OV-001` | Si `pragma_extends` está presente, `pragma_override` es obligatorio | ERROR |
| `OV-002` | Si `pragma_override` está presente, `pragma_extends` es obligatorio | ERROR |
| `OV-003` | `pragma_override` debe ser `full` o `merge` | ERROR |
| `OV-004` | El `id` del archivo debe coincidir con el `id` del asset en `pragma_extends` | ERROR |
| `OV-005` | Si `pragma_override=merge`, el archivo debe tener al menos una sección `##` | ERROR |
| `OV-006` | Si `pragma_override=merge`, cada sección `##` debe tener contenido | WARNING |

#### CT — Contenido mínimo

| Código | Regla | Severidad |
|---|---|---|
| `CT-001` | El archivo no puede tener solo frontmatter — debe tener contenido después del `---` | ERROR |
| `CT-002` | `steering` debe tener al menos las secciones `## Rol` y `## Lo que nunca debes hacer` | WARNING |
| `CT-003` | `skill` debe tener al menos la sección `## Instrucción` | WARNING |
| `CT-004` | `workflow` debe tener al menos la sección `## Pasos` | WARNING |
| `CT-005` | `guardrail` debe tener al menos la sección `## Nunca hagas esto` | WARNING |
| `CT-006` | `adr` debe tener al menos las secciones `## Contexto` y `## Decisión` | WARNING |
| `CT-007` | El contenido no debe exceder 10.000 caracteres | WARNING |

### Output del linter

```
$ sopp-lint ./chapters/backend/skills/java-spring/mi-skill.md

✓ FR-001  Frontmatter presente
✓ FR-002  id: "mi-skill" presente
✓ FR-003  id en kebab-case
✗ FR-004  ERROR: El id "mi-skill" ya existe en chapters/backend/skills/node/mi-skill.md
✓ FR-005  version: "1.0.0" presente
✓ FR-006  version es semver válido
⚠ FR-015  WARNING: description ausente
✓ ST-001  Archivo en carpeta correcta para type=skill
✓ ST-003  Archivo bajo carpeta de stack java-spring
⚠ CT-003  WARNING: skill sin sección ## Instrucción

2 errores · 2 advertencias

PR bloqueado — resuelve los errores antes de continuar.
```

### Comando del linter

```bash
# Valida un archivo específico
sopp-lint ./chapters/backend/skills/java-spring/mi-skill.md

# Valida todos los archivos modificados (para el GitHub Action)
sopp-lint --changed

# Valida todo el repo
sopp-lint --all

# Solo errores, ignora warnings (para decisión de bloqueo del PR)
sopp-lint --changed --errors-only
```

---

## 6. GitHub Actions

### 5.1 `lint.yml` — validación en cada PR

Se ejecuta en cada PR hacia `main`. Bloquea el merge si hay errores.

```yaml
# .github/workflows/lint.yml
name: SOPP Lint

on:
  pull_request:
    branches: [main]
    paths:
      - 'chapters/**/*.md'
      - 'shared/**/*.md'
      # _config/ está excluido — no es contenido, no pasa por el linter

jobs:
  lint:
    name: Validar assets
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Instalar sopp-lint
        run: npm install -g @pragma/sopp-lint

      - name: Obtener archivos modificados
        id: changed
        run: |
          echo "files=$(git diff --name-only origin/main...HEAD | grep '\.md$' | tr '\n' ' ')" >> $GITHUB_OUTPUT

      - name: Ejecutar linter
        run: sopp-lint --changed --errors-only
        env:
          CHANGED_FILES: ${{ steps.changed.outputs.files }}

      - name: Comentar resultado en el PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ **SOPP Lint falló.** Revisa los errores en los logs antes de continuar.'
            })
```

### 5.2 `webhook.yml` — notifica al Hub en cada push a main

Se ejecuta cuando un PR llega a `main`. Notifica al Hub qué archivos cambiaron. Incluye `_config/` porque la Lambda webhook tiene un code path separado para esos archivos — los copia directamente a S3 sin lógica de merge.

```yaml
# .github/workflows/webhook.yml
name: Notificar Hub

on:
  push:
    branches: [main]
    paths:
      - 'chapters/**/*.md'
      - 'shared/**/*.md'
      - '_config/**'          # taxonomy.json, ides.json y templates — la Lambda los copia directo a S3

jobs:
  notify-hub:
    name: Notificar cambios al Hub
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Obtener archivos modificados
        id: changed
        run: |
          echo "files=$(git diff --name-only HEAD~1 HEAD | grep -E '\.(md|json)$' | jq -R -s -c 'split("\n") | map(select(length > 0))')" >> $GITHUB_OUTPUT

      - name: Notificar al Hub
        run: |
          curl -X POST https://webhook.sopp.pragma.com.co/github \
            -H "Content-Type: application/json" \
            -H "x-api-key: ${{ secrets.SOPP_HUB_API_KEY }}" \
            -H "X-Hub-Signature-256: $(echo -n '${{ toJson(github.event) }}' | openssl dgst -sha256 -hmac '${{ secrets.SOPP_WEBHOOK_SECRET }}' | cut -d' ' -f2)" \
            -H "X-GitHub-Event: push" \
            -H "X-Repo-Name: ${{ github.repository }}" \
            -d '{
              "ref": "${{ github.ref }}",
              "repository": {
                "full_name": "${{ github.repository }}",
                "clone_url": "https://github.com/${{ github.repository }}.git"
              },
              "changed_files": ${{ steps.changed.outputs.files }},
              "pusher": "${{ github.actor }}",
              "commit_sha": "${{ github.sha }}"
            }'
```


---

## 7. Contrato del webhook hacia el Hub

Este es el payload que el GitHub Action envía a la Lambda `sopp-hub-webhook`.
La Lambda valida la firma `X-Hub-Signature-256` antes de procesar.

### Headers obligatorios

| Header | Descripción | Ejemplo |
|---|---|---|
| `Content-Type` | Siempre JSON | `application/json` |
| `x-api-key` | API Key del Hub embebida en el CLI y en el secret de Azure DevOps | `a1b2c3d4e5f6...` |
| `X-Hub-Signature-256` | HMAC-SHA256 del body firmado con `SOPP_WEBHOOK_SECRET` | `sha256=d57c68ca6f...` |
| `X-GitHub-Event` | Tipo de evento | `push` |
| `X-Repo-Name` | Nombre completo del repo | `somospragma/pragma-ai-knowledge-bancolombia` |

### Body del webhook

```json
{
  "ref": "refs/heads/main",
  "repository": {
    "full_name": "somospragma/pragma-ai-knowledge-bancolombia",
    "clone_url": "https://github.com/somospragma/pragma-ai-knowledge-bancolombia.git"
  },
  "changed_files": [
    "chapters/backend/skills/java-spring/webflux-error-handling.md",
    "chapters/backend/skills/java-spring/nueva-skill.md"
  ],
  "pusher": "david@pragma.com.co",
  "commit_sha": "abc123def456abc123def456abc123def456abc1"
}
```

### Respuestas de la Lambda

| Status | Cuándo | Body |
|---|---|---|
| `200` | Webhook procesado correctamente | `{ "received": true, "processed_files": 2 }` |
| `204` | Evento ignorado (no hay archivos .md en changed_files) | vacío |
| `401` | Firma inválida | `{ "error": "INVALID_SIGNATURE" }` |
| `404` | Repo no registrado en el Hub | `{ "error": "REPO_NOT_REGISTERED" }` |
| `422` | Payload malformado | `{ "error": "INVALID_PAYLOAD", "detail": "..." }` |

### El secret `SOPP_WEBHOOK_SECRET`

- Se genera una vez por repo al registrarlo en el Hub
- Se guarda como GitHub Actions secret bajo el nombre `SOPP_WEBHOOK_SECRET`
- El Hub guarda el secret en su Accounts Registry para validar la firma
- Si se rota, hay que actualizarlo en ambos lados (GitHub secret + Hub config)

---

## 8. Cómo crear un repo de cuenta desde el template

El repo `pragma-ai-knowledge-template` en la org de Pragma es el punto de partida.
Crear un nuevo repo de cuenta toma menos de 10 minutos.

### Paso 1 — Crear el repo desde el template

```bash
# Usando GitHub CLI
gh repo create somospragma/pragma-ai-knowledge-{cuenta} \
  --template somospragma/pragma-ai-knowledge-template \
  --private \
  --description "SOPP AI Knowledge — {Nombre de la cuenta}"
```

O desde la UI de GitHub: `Use this template` en el repo `pragma-ai-knowledge-template`.

### Paso 2 — Configurar el secret del webhook

```bash
# Generar el secret
SECRET=$(openssl rand -hex 32)

# Guardarlo en GitHub Actions secrets
gh secret set SOPP_WEBHOOK_SECRET \
  --repo somospragma/pragma-ai-knowledge-{cuenta} \
  --body "$SECRET"

echo "Secret generado: $SECRET"
echo "Compártelo con el equipo de plataforma para registrar el repo en el Hub."
```

### Paso 3 — Registrar el repo en el Hub

El equipo de plataforma agrega el repo al `Accounts Registry` del Hub:

```json
// En la config del Hub
{
  "cuenta": "{cuenta}",
  "repo": "somospragma/pragma-ai-knowledge-{cuenta}",
  "webhook_secret": "{secret generado en el paso 2}"
}
```

### Paso 4 — Configurar CODEOWNERS

Editar `.github/CODEOWNERS` con los equipos correctos de la cuenta.

### Paso 5 — Crear el primer asset

Ya está todo listo. El AI Steward o el Chapter Lead crean el primer PR con el primer asset.
El linter valida automáticamente. Si pasa, el merge dispara el webhook al Hub.

### Checklist de onboarding

```
[ ] Repo creado desde el template pragma-ai-knowledge-template
[ ] SOPP_WEBHOOK_SECRET configurado en GitHub Actions secrets
[ ] Repo registrado en el Hub por el equipo de plataforma
[ ] CODEOWNERS configurado con los equipos de la cuenta
[ ] AI Steward asignado con merge rights
[ ] Chapter Leads asignados con permisos de aprobación por carpeta
[ ] Primer asset creado y mergeado exitosamente
[ ] Verificado que el Hub recibió el webhook y procesó el asset
```