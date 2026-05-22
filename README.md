# SOPP AI Hub — Knowledge Core

Repositorio central de conocimiento de IA para todos los pragmáticos de Pragma. Este es el **core** — contiene los assets base que aplican a toda la empresa. Los repos de cuenta (`pragma-ai-hub-knowledge-{cuenta}`) pueden extender o sobrescribir estos assets.

## IDEs soportados

| IDE | Tipos de asset soportados |
|---|---|
| **Kiro** | steering, skill, workflow, prompt, agent |
| **GitHub Copilot** | steering, skill, prompt |
| **Amazon Q (IDE)** | steering, skill, prompt |
| **Amazon Q (CLI)** | steering, skill, agent |
| **Claude Code** | steering, skill, workflow |

## Tipos de asset

| Tipo | Qué es | Ejemplo |
|---|---|---|
| `steering` | Instrucciones de comportamiento para el AI | "Siempre responde en español técnico" |
| `skill` | Instrucción para una tarea concreta | "Genera PR descriptions con este formato" |
| `workflow` | Secuencia de pasos para un proceso | "Flujo de code review en 5 pasos" |
| `guardrail` | Restricciones que el AI nunca debe violar | "Nunca expongas secrets en código" |
| `prompt` | Plantilla con variables para invocar | "Template para generar tests unitarios" |
| `persona` | Modo con rol y restricciones específicas | "Senior backend reviewer" |
| `agent` | Definición de agente especializado | "Agente de refactoring" |
| `convencion` | Estándares de código y naming | "Convenciones Java Spring en Pragma" |
| `doc` | Documentación consultable | "Guía de arquitectura hexagonal" |
| `adr` | Decisión de arquitectura | "ADR: Usar WebFlux para servicios reactivos" |

## Estructura del repositorio

```
_config/                      ← Configuración del sistema (solo equipo de plataforma)
├── taxonomy.json             ← Chapters, plataformas y stacks soportados
├── ides.json                 ← IDEs, capacidades y paths de escritura
└── templates/                ← Plantillas de renderizado por IDE
    ├── kiro/
    ├── github-copilot/
    ├── amazon-q-ide/
    ├── amazon-q-cli/
    └── claude-code/

chapters/                     ← Assets organizados por chapter
├── backend/
│   ├── steering/             ← Comportamiento base para backend
│   ├── skills/
│   │   ├── _all/             ← Aplica a todo backend sin distinción de stack
│   │   ├── java-spring/
│   │   ├── java-webflux/
│   │   ├── node-express/
│   │   ├── node-lambda/
│   │   └── dotnet/
│   ├── workflows/
│   ├── guardrails/
│   ├── prompts/
│   ├── personas/
│   └── convenciones/
├── calidad/
│   └── skills/automation/
├── mobile/
│   └── skills/flutter/, android-native/, apple-native/
├── frontend/
│   └── skills/react/, angular/
└── arquitectura/

shared/                       ← Assets globales (aplican a TODOS)
├── steering/                 ← Steering global de Pragma
├── guardrails/               ← Restricciones globales
├── docs/
└── adrs/
```

## Cómo contribuir

### 1. Crear un asset

Cada archivo `.md` requiere un frontmatter YAML:

```yaml
---
id: nombre-en-kebab-case       # Único en todo el repo
version: 1.0.0                 # Semver
scope: stack                   # global | chapter | stack
type: skill                    # Ver tabla de tipos arriba
chapter: backend               # Requerido si scope != global
stack: [java-spring]           # Requerido si scope = stack
tags: [pr, git]                # Opcional
description: Qué hace en una línea  # Recomendado
---

## Contenido del asset en markdown...
```

### 2. Ubicar el archivo en la carpeta correcta

| Scope | Dónde va |
|---|---|
| `global` | `shared/{type}/` |
| `chapter` | `chapters/{chapter}/{type}/` o `chapters/{chapter}/{type}/_all/` |
| `stack` | `chapters/{chapter}/{type}/{stack}/` |

### 3. Hacer PR a main

- El linter valida automáticamente el frontmatter y la estructura
- Un Chapter Lead o AI Steward aprueba el PR
- Al mergear, el webhook notifica al Hub y el contenido se distribuye

## Stacks soportados

| Chapter | Stacks |
|---|---|
| backend | `java-spring`, `java-webflux`, `node-express`, `node-lambda`, `dotnet` |
| frontend | `react`, `angular` |
| mobile | `flutter`, `android-native`, `apple-native` |
| calidad | `automation` |
| arquitectura | (sin stacks específicos) |

## Templates de assets

### Skill

```markdown
---
id: mi-skill
version: 1.0.0
scope: stack
type: skill
chapter: backend
stack: [java-spring]
description: Qué hace este skill
---

## Cuándo aplicar
Condición o contexto para activar este skill

## Instrucción
Lo que el AI debe hacer

## Restricciones
Lo que el AI NO debe hacer
```

### Steering

```markdown
---
id: backend-steering
version: 1.0.0
scope: chapter
type: steering
chapter: backend
description: Comportamiento base del AI para backend
---

## Rol
Descripción del rol que asume el AI

## Principios
Lista de principios guía

## Lo que nunca debes hacer
Restricciones de comportamiento
```

### Workflow

```markdown
---
id: feature-development-workflow
version: 1.0.0
scope: chapter
type: workflow
chapter: backend
description: Flujo para desarrollar una feature
---

## Cuándo usar este workflow
Condición para activar

## Pasos

### 1. Nombre del paso
Instrucción

### 2. Nombre del paso
Instrucción

## Criterios de finalización
Cómo saber que terminó correctamente
```

## Cómo funciona la distribución

```
1. Pragmático hace PR con un nuevo skill
2. Chapter Lead aprueba y mergea a main
3. GitHub webhook notifica al Hub
4. Hub procesa el archivo y lo guarda en S3
5. CLI del pragmático hace sync cada 4h
6. El skill aparece en su IDE automáticamente
```

## Quién puede contribuir

- **Cualquier pragmático** puede abrir PR con nuevos assets
- **Chapter Leads** aprueban PRs de su chapter
- **AI Stewards** aprueban PRs de cuentas específicas
- **Equipo de Plataforma** mantiene `_config/` y la infraestructura

## Flujo de ramas y ambientes

```
feature/* → PR a develop → merge
                              ↓
                          develop (push)
                              ↓
                    GitHub Action webhook.yml
                              ↓
              ┌───────────────┼───────────────┐
              ▼                               ▼
    Hub TEMPORAL                      Hub DEV (oficial)
    (se elimina después)              cuenta 700693144401
              
develop → PR a main → merge
                          ↓
                      main (push)
                          ↓
                GitHub Action webhook.yml
                          ↓
                    Hub PROD (oficial)
                    cuenta 258975980616
```

| Rama | Ambientes que notifica | Propósito |
|---|---|---|
| `develop` | Temporal + DEV oficial | Validar cambios antes de producción |
| `main` | PROD oficial | Contenido en producción para los pragmáticos |

### Environments de GitHub (Settings → Environments)

| Environment | Secrets | Cuándo se usa |
|---|---|---|
| `temporal` | URL/key/secret del ambiente temporal | Push a develop (⚠️ se elimina cuando se retire) |
| `dev` | URL/key/secret del Hub DEV oficial | Push a develop |
| `prod` | URL/key/secret del Hub PROD oficial | Push a main |

### Eliminar el ambiente temporal

Cuando el ambiente temporal se retire:
1. Borrar el job `notify-hub-temporal` de `.github/workflows/webhook.yml`
2. Borrar el environment `temporal` en GitHub Settings
3. No se toca nada más

## Contacto

- **Equipo**: Plataforma Pragma AI
- **Slack**: #sopp-ai-hub
