# Especificación de Templates por IDE

## Cómo funcionan los templates

Cada template es el formato final que el sync escribe para el pragmático. Tienen placeholders que el renderer reemplaza con datos del asset.

El renderer hace exactamente esto:
1. Lee el asset canónico de S3
2. Extrae `description` del frontmatter YAML
3. Stripea el frontmatter YAML (todo lo que está entre los `---`)
4. Lee el template del IDE correspondiente al tipo de asset
5. Reemplaza los placeholders con los valores del asset
6. Escribe el archivo resultante en el path que indica `ides.json`

Los templates viven en `pragma-ai-hub-knowledge-core/_config/templates/{ide}/{type}.{ext}`.

---

## Placeholders disponibles

| Placeholder | Qué contiene |
|---|---|
| `%%pragma-content%%` | Contenido markdown del asset sin el frontmatter canónico |
| `%%pragma-id%%` | El `id` del asset tal como está en el frontmatter |
| `%%pragma-description%%` | El `description` del asset del frontmatter (vacío si no existe) |

---

## Kiro

Kiro usa el estándar [Agent Skills](https://agentskills.io/) para skills y modos de inclusión (`auto`, `manual`, `always`, `fileMatch`) para steering.

### `kiro/steering.md`
```markdown
---
inclusion: auto
name: %%pragma-id%%
description: %%pragma-description%%
---

%%pragma-content%%
```

### `kiro/skill.md`
Skills siguen el Agent Skills standard con frontmatter `name` + `description`.
```markdown
---
name: %%pragma-id%%
description: %%pragma-description%%
---

%%pragma-content%%
```

### `kiro/workflow.md`
```markdown
---
inclusion: auto
name: %%pragma-id%%
description: %%pragma-description%%
---

%%pragma-content%%
```

### `kiro/prompt.md`
```markdown
---
inclusion: manual
name: %%pragma-id%%
description: %%pragma-description%%
---

%%pragma-content%%
```

### `kiro/agent.md`
```markdown
---
inclusion: manual
name: %%pragma-id%%
description: %%pragma-description%%
---

%%pragma-content%%
```

### `kiro/hook.json`
Los hooks de Kiro son JSON. Se activan manualmente por el usuario.
```json
{
  "name": "%%pragma-id%%",
  "version": "1.0.0",
  "description": "%%pragma-description%%",
  "when": {
    "type": "userTriggered"
  },
  "then": {
    "type": "askAgent",
    "prompt": "%%pragma-content%%"
  }
}
```

---

## GitHub Copilot

Copilot tiene un comportamiento especial:
- **`steering`** → `concatenate_all`: todos los steerings van en un solo archivo `.github/copilot-instructions.md`
- **`skill`** → Agent Skills standard en `.github/skills/{id}/SKILL.md`

### `github-copilot/steering.md`
Se aplica a cada steering individualmente antes de concatenar.
```
%%pragma-content%%
```

### `github-copilot/skill.md`
Skills siguen el Agent Skills standard.
```markdown
---
name: %%pragma-id%%
description: %%pragma-description%%
---

%%pragma-content%%
```

### `github-copilot/prompt.prompt.md`
```markdown
---
mode: ask
---

%%pragma-content%%
```

### `github-copilot/agent.md`
```
%%pragma-content%%
```

### `github-copilot/workflow.md`
```
%%pragma-content%%
```

---

## Claude Code

Claude Code concatena todo en archivos únicos.
- **`steering`** → `concatenate_all`: todo va en `CLAUDE.md`
- **`skill`** y **`workflow`** → archivos individuales en `.claude/rules/`

### `claude-code/steering.md`
```
%%pragma-content%%
```

### `claude-code/skill.md`
```
%%pragma-content%%
```

### `claude-code/workflow.md`
```
%%pragma-content%%
```

---

## Amazon Q (IDE)

Amazon Q IDE usa markdown plano en `.amazonq/rules/`.

### `amazon-q-ide/steering.md`
```
%%pragma-content%%
```

### `amazon-q-ide/skill.md`
```
%%pragma-content%%
```

### `amazon-q-ide/workflow.md`
```
%%pragma-content%%
```

### `amazon-q-ide/prompt.md`
```
%%pragma-content%%
```

---

## Amazon Q (CLI)

Amazon Q CLI soporta agents como JSON además de markdown.

### `amazon-q-cli/steering.md`
```
%%pragma-content%%
```

### `amazon-q-cli/skill.md`
```
%%pragma-content%%
```

### `amazon-q-cli/workflow.md`
```
%%pragma-content%%
```

### `amazon-q-cli/agent.json`
```json
{
  "name": "%%pragma-id%%",
  "prompt": "%%pragma-content%%",
  "mcpServers": []
}
```

---

## Resumen de templates por IDE y tipo

| Tipo | Kiro | GitHub Copilot | Amazon Q IDE | Amazon Q CLI | Claude Code |
|---|---|---|---|---|---|
| `steering` | `steering.md` (auto) | `steering.md` (concatena) | `steering.md` | `steering.md` | `steering.md` (concatena) |
| `skill` | `skill.md` (Agent Skills) | `skill.md` (Agent Skills) | `skill.md` | `skill.md` | `skill.md` |
| `workflow` | `workflow.md` (auto) | `workflow.md` | `workflow.md` | `workflow.md` | `workflow.md` |
| `prompt` | `prompt.md` (manual) | `prompt.prompt.md` | `prompt.md` | — | — |
| `agent` | `agent.md` (manual) | `agent.md` | — | `agent.json` | — |
| `hook` | `hook.json` | — | — | — | — |
