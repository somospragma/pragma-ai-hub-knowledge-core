# templates-definitions-ides.md
# Especificación de Templates por IDE

## Cómo funcionan los templates

Cada template es el formato final que el CLI escribe en disco para el pragmático. Tienen un único placeholder: `%%pragma-content%%`, donde el renderer inyecta el contenido markdown del asset (sin el frontmatter canónico — ese es solo metadata interna del Hub).

El renderer hace exactamente esto:
1. Lee el asset canónico de S3
2. Stripea el frontmatter YAML (todo lo que está entre los `---`)
3. Lee el template del IDE correspondiente al tipo de asset
4. Reemplaza `%%pragma-content%%` con el contenido stripeado
5. Escribe el archivo resultante en el path que indica `ides.json`

Los templates viven en `pragma-ai-knowledge-core/_config/templates/{ide}/{type}.{ext}`.

---

## Cursor

Los archivos de Cursor son `.mdc` con frontmatter YAML que controla cuándo el AI los aplica.

### `cursor/steering.mdc`
```
---
alwaysApply: true
---

%%pragma-content%%
```

### `cursor/skill.mdc`
```
---
alwaysApply: false
---

%%pragma-content%%
```

### `cursor/workflow.mdc`
```
---
alwaysApply: false
---

%%pragma-content%%
```

### `cursor/guardrail.mdc`
```
---
alwaysApply: true
---

%%pragma-content%%
```

### `cursor/persona.mdc`
```
---
alwaysApply: false
---

%%pragma-content%%
```

### `cursor/prompt.mdc`
```
---
alwaysApply: false
---

%%pragma-content%%
```

### `cursor/convencion.mdc`
```
---
alwaysApply: false
---

%%pragma-content%%
```

---

## Kiro

Kiro usa markdown plano. El steering va en `.kiro/steering/` y los hooks en `.kiro/hooks/` como JSON.

### `kiro/steering.md`
```
%%pragma-content%%
```

### `kiro/skill.md`
```
%%pragma-content%%
```

### `kiro/workflow.md`
```
%%pragma-content%%
```

### `kiro/guardrail.md`
```
%%pragma-content%%
```

### `kiro/persona.md`
```
%%pragma-content%%
```

### `kiro/prompt.md`
```
%%pragma-content%%
```

### `kiro/agent.md`
```
%%pragma-content%%
```

### `kiro/hook.json`

Los hooks de Kiro son JSON. El `%%pragma-content%%` en este caso es el campo `prompt` del JSON — el contenido del asset se inyecta ahí.

```json
{
  "name": "%%pragma-id%%",
  "trigger": "onUserMessage",
  "prompt": "%%pragma-content%%"
}
```

> **Nota:** El hook usa dos placeholders: `%%pragma-id%%` para el id del asset y `%%pragma-content%%` para el contenido. El renderer conoce ambos.

---

## GitHub Copilot

Copilot tiene dos comportamientos especiales definidos en `ides.json`:

- **`steering`** → `concatenate_all`: todos los steerings van en un solo archivo `.github/copilot-instructions.md`. El renderer los concatena separados por `\n\n---\n\n`
- **`skill` y `prompt`** → un archivo `.prompt.md` por asset con su propio frontmatter

### `github-copilot/steering.md`

Este template se aplica a cada steering individualmente antes de concatenar. El renderer une todos los resultados en `.github/copilot-instructions.md`.

```
%%pragma-content%%
```

### `github-copilot/skill.prompt.md`
```
---
mode: ask
---

%%pragma-content%%
```

### `github-copilot/prompt.prompt.md`
```
---
mode: ask
---

%%pragma-content%%
```

---

## Amazon Q (IDE)

Amazon Q IDE usa markdown plano. Las rules van en `.amazonq/rules/` y los prompts en `.amazonq/prompts/`.

### `amazon-q-ide/steering.md`
```
%%pragma-content%%
```

### `amazon-q-ide/skill.md`
```
%%pragma-content%%
```

### `amazon-q-ide/prompt.md`
```
%%pragma-content%%
```

### `amazon-q-ide/guardrail.md`
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

### `amazon-q-cli/agent.json`

El contenido del asset se inyecta en el campo `prompt` del JSON del agente.

```json
{
  "name": "%%pragma-id%%",
  "prompt": "%%pragma-content%%",
  "mcpServers": []
}
```

---

## Resumen de placeholders

| Placeholder | Qué contiene |
|---|---|
| `%%pragma-content%%` | Contenido markdown del asset sin el frontmatter canónico |
| `%%pragma-id%%` | El `id` del asset tal como está en el frontmatter (solo en templates JSON) |

---

## Resumen de templates por IDE y tipo

| Tipo | Cursor | Kiro | Copilot | Amazon Q IDE | Amazon Q CLI |
|---|---|---|---|---|---|
| `steering` | `steering.mdc` (alwaysApply: true) | `steering.md` | `steering.md` + concatena | `steering.md` | `steering.md` |
| `skill` | `skill.mdc` | `skill.md` | `skill.prompt.md` | `skill.md` | `skill.md` |
| `workflow` | `workflow.mdc` | `workflow.md` | — no soportado — | — no soportado — | — no soportado — |
| `guardrail` | `guardrail.mdc` (alwaysApply: true) | `guardrail.md` | — no soportado — | `guardrail.md` | — no soportado — |
| `persona` | `persona.mdc` | `persona.md` | — no soportado — | — no soportado — | — no soportado — |
| `prompt` | `prompt.mdc` | `prompt.md` | `prompt.prompt.md` | `prompt.md` | `prompt.md` |
| `convencion` | `convencion.mdc` | — no soportado — | — no soportado — | — no soportado — | — no soportado — |
| `agent` | — no soportado — | `agent.md` | — no soportado — | — no soportado — | `agent.json` |
| `hook` | — no soportado — | `hook.json` | — no soportado — | — no soportado — | — no soportado — |