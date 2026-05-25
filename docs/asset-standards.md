# Estándar de Assets — SOPP AI Hub

## Capabilities soportadas por IDE

| Capability | Kiro | GitHub Copilot | Amazon Q IDE | Amazon Q CLI | Claude Code |
|---|---|---|---|---|---|
| `steering` | ✅ | ✅ (concatena) | ✅ | ✅ | ✅ (concatena) |
| `skill` | ✅ | ✅ | ✅ | ✅ | ✅ (concatena) |
| `workflow` | ✅ | ❌ | ❌ | ❌ | ✅ (concatena) |
| `prompt` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `agent` | ✅ | ❌ | ❌ | ✅ | ❌ |
| `guardrail` | ❌ | ❌ | ❌ | ❌ | ❌ |
| `convencion` | ❌ | ❌ | ❌ | ❌ | ❌ |

> `guardrail` y `convencion` se indexan y almacenan pero actualmente ningún IDE los renderiza como archivo separado. Se pueden incluir como parte de un steering.

---

## Frontmatter canónico (obligatorio)

Todo archivo `.md` que el Hub procesa **debe** tener este frontmatter:

```yaml
---
id: nombre-en-kebab-case          # Único en todo el repo
version: 1.0.0                    # Semver
scope: global | chapter | stack   # Determina a quién se entrega
type: skill | steering | workflow | prompt | agent | guardrail | convencion
chapter: mobile                   # Requerido si scope != global
stack: [flutter]                  # Requerido si scope = stack (array)
description: Una línea            # Recomendado
tags: [bloc, state]               # Opcional
---
```

### Campos obligatorios

| Campo | Tipo | Regla |
|---|---|---|
| `id` | string | kebab-case, único en el repo |
| `version` | string | Semver (1.0.0, no "1.0") |
| `scope` | enum | `global`, `chapter`, o `stack` |
| `type` | enum | Ver tabla de capabilities |

### Campos condicionales

| Campo | Cuándo es obligatorio |
|---|---|
| `chapter` | Siempre que `scope` != `global` |
| `stack` | Solo cuando `scope` = `stack` |

### Campos opcionales

| Campo | Propósito |
|---|---|
| `description` | Descripción corta (max 120 chars) |
| `tags` | Array de tags para búsqueda |

---

## Estructura de archivos

### Formato plano (un archivo por asset)

```
chapters/backend/skills/java-spring/api-design.md
```

Ideal para assets simples sin archivos de referencia.

### Formato subcarpeta (asset con referencias)

```
chapters/mobile/skills/flutter/flutter-bloc-pattern/
├── SKILL.md              ← Archivo principal (tiene el frontmatter)
├── references/           ← Archivos de referencia
│   ├── event-pattern.mmd
│   └── state-diagram.mmd
├── assets/               ← Diagramas, imágenes
│   └── architecture.png
└── scripts/              ← Scripts auxiliares
    └── audit.sh
```

**Reglas:**
- El archivo principal se llama `{TYPE}.md` en mayúsculas: `SKILL.md`, `AGENT.md`, `WORKFLOW.md`, `PROMPT.md`, `STEERING.md`
- Las subcarpetas pueden tener cualquier nombre (`references/`, `assets/`, `scripts/`, `examples/`, etc.)
- El webhook procesa el `.md` principal y concatena los archivos de referencia al contenido
- Los archivos `.mmd` (Mermaid), `.dart`, `.java`, `.ts`, etc. se incluyen como bloques de código

---

## Esqueleto por tipo de asset

### `skill` — Instrucción para una tarea concreta

```yaml
---
id: mi-skill
version: 1.0.0
scope: stack
type: skill
chapter: backend
stack: [java-spring]
description: Qué hace este skill en una línea
---

## Cuándo aplicar
Condiciones o triggers que activan este skill.

## Instrucción
Lo que el AI debe hacer paso a paso.

## Restricciones
Lo que el AI NO debe hacer.

## Ejemplo
(Opcional) Ejemplo de input/output esperado.
```

### `steering` — Comportamiento base del AI

```yaml
---
id: backend-steering
version: 1.0.0
scope: chapter
type: steering
chapter: backend
description: Comportamiento base del AI para pragmáticos de backend
---

## Rol
Descripción del rol que asume el AI.

## Principios
Lista de principios que guían el comportamiento.

## Lo que nunca debes hacer
Restricciones de comportamiento.
```

### `workflow` — Secuencia de pasos

```yaml
---
id: feature-development
version: 1.0.0
scope: chapter
type: workflow
chapter: mobile
description: Flujo para desarrollar una feature completa
---

## Cuándo usar este workflow
Condiciones para activar.

## Pasos

### 1. Nombre del paso
Instrucción detallada.

### 2. Nombre del paso
Instrucción detallada.

## Criterios de finalización
Cómo saber que terminó correctamente.
```

### `prompt` — Plantilla con variables

```yaml
---
id: test-generation
version: 1.0.0
scope: chapter
type: prompt
chapter: calidad
description: Plantilla para generar tests unitarios
---

## Template

Genera tests unitarios para [COMPONENTE] siguiendo:
- Patrón AAA (Arrange, Act, Assert)
- Cobertura de happy path y edge cases
- Mocks para dependencias externas

## Variables
- `[COMPONENTE]`: Clase o función a testear
```

### `agent` — Agente especializado

```yaml
---
id: code-auditor
version: 1.0.0
scope: chapter
type: agent
chapter: mobile
description: Agente que audita código contra estándares
---

## Rol
Descripción del rol del agente.

## Cómo operar
Pasos o comportamiento al activarse.

## Herramientas
(Opcional) Herramientas o MCPs que usa.

## Criterios de evaluación
Cómo mide la calidad de su output.
```

### `guardrail` — Restricciones explícitas

```yaml
---
id: security-guardrails
version: 1.0.0
scope: global
type: guardrail
description: Restricciones de seguridad para todo Pragma
---

## Nunca hagas esto
Lista explícita de lo que el AI nunca debe hacer.
```

### `convencion` — Estándares de código

```yaml
---
id: java-spring-conventions
version: 1.0.0
scope: stack
type: convencion
chapter: backend
stack: [java-spring]
description: Convenciones de código Java Spring en Pragma
---

## Naming
Reglas de nomenclatura.

## Estructura de paquetes
Organización del código.

## Patrones
Patrones obligatorios.
```

---

## Cómo agregar un nuevo capability

Si necesitas un tipo de asset que no existe (ej: `hook`, `mcp-config`, `template`):

### 1. Agregar al `_config/ides.json`

```json
{
  "id": "kiro",
  "capabilities": ["steering", "skill", "workflow", "prompt", "agent", "NUEVO_TIPO"],
  "workspace_paths": {
    "NUEVO_TIPO": ".kiro/hooks/{id}.json"
  }
}
```

### 2. Crear el template de renderizado

```
_config/templates/kiro/NUEVO_TIPO.md    (o .json si es JSON)
```

El template usa `%%pragma-content%%` como placeholder:
```
%%pragma-content%%
```

Para templates JSON:
```json
{
  "name": "%%pragma-id%%",
  "content": "%%pragma-content%%"
}
```

### 3. Agregar al `_config/asset-schemas.json`

```json
{
  "NUEVO_TIPO": {
    "description": "Qué es este tipo",
    "required_sections": ["## Sección obligatoria"],
    "optional_sections": ["## Sección opcional"],
    "frontmatter_required": ["id", "version", "scope", "type"],
    "frontmatter_optional": ["chapter", "stack", "tags", "description"]
  }
}
```

### 4. Documentar en este archivo

Agregar el esqueleto del nuevo tipo en la sección anterior.

### 5. Push a main

El webhook procesa el cambio en `_config/` y lo sube a S3. Las lambdas lo leen en el siguiente cold start. No requiere redespliegue de lambdas.

---

## Scope y filtrado

| Scope | A quién se entrega | Dónde va en el repo |
|---|---|---|
| `global` | Todos los pragmáticos | `shared/` |
| `chapter` | Pragmáticos del chapter | `chapters/{chapter}/` |
| `stack` | Pragmáticos con ese stack | `chapters/{chapter}/skills/{stack}/` |

---

## Notas sobre IDEs específicos

### GitHub Copilot
- `steering` se concatena en un solo archivo `.github/copilot-instructions.md`
- `skill` y `prompt` van como `.prompt.md` individuales en `.github/prompts/`

### Claude Code
- Todo se concatena en un solo `CLAUDE.md` (steering + skills + workflows)

### Kiro
- Cada asset es un archivo `.md` separado
- Skills van en `.kiro/skills/`
- El resto en `.kiro/steering/`

### Amazon Q
- Todo va como `.md` en `.amazonq/rules/`
