# Copilot And Kiro Compatibility

The mobile KB must run in GitHub Copilot and Kiro without changing the workflow
semantics. Renderer-specific files may differ, but the source assets and runtime
state stay portable.

## Core Rule

Execution-critical behavior belongs in workflows, agents, prompts, skills and
templates. Docs explain the model; they are not required runtime context.

## Renderer Mapping

| Asset | Copilot | Kiro | Requirement |
|---|---|---|---|
| Steering | `.github/copilot-instructions.md` | `.kiro/steering/*.md` | Must be self-contained and order-independent. |
| Workflows | `.github/instructions/*.instructions.md` | Kiro workflow/steering assets | Must be plain Markdown with explicit steps. |
| Skills | `.github/skills/{id}/SKILL.md` | `.kiro/skills/{id}/SKILL.md` or equivalent | Must avoid IDE-only assumptions. |
| Agents | `.github/agents/{id}.md` | Kiro agent/steering assets | Must describe permissions and outputs. |
| Hooks | Optional | Optional | Must never be required for correctness. |

## Portable Runtime State

Both surfaces should use the same project runtime folder:

```text
<APP_REPO_ROOT>/.sopp/
├── config/
├── bootstrap/{run_id}/
└── flow_result/specs/{workflow_slug}/
```

This prevents separate Copilot/Kiro state from drifting.

## Deployment Boundary

`.copilot/`, `.github/`, and `.kiro/` are renderer/export locations for KB
resources. They may differ by tool and may coexist in one repository. They are
not configuration sources for functional workflows.

Only `<APP_REPO_ROOT>/.sopp/config/` owns the three runtime configuration
files. An agent must ignore `.copilot/config/` and `.kiro/config/`, even when
they contain old bootstrap outputs. If the canonical `.sopp/config` triplet is
missing, partial, or invalid, the workflow blocks and requires an explicit
bootstrap or forced migration; it must not select a renderer-specific fallback.

## Required Agent Behavior

1. Use compact handoffs with `spec_ref`, `context_ref`, `phase` and
   `read_sections`.
2. Persist approvals, blockers and evidence on disk, not only in chat memory.
3. Keep Figma MCP checks explicit before workflows that depend on Figma.
4. Avoid mandatory Kiro hooks or Copilot-only commands.
5. Keep human-facing review content in Spanish by default.

## Handoff Example

```yaml
handoff:
  workflow: new-feature
  phase: data_layer
  spec_ref: .sopp/flow_result/specs/product_catalog/spec.yaml
  context_ref: .sopp/flow_result/specs/product_catalog/context.json
  read_sections:
    - contracts.api
    - artifact_plan.planned[group=data]
    - success_criteria
```

## Test Order

1. `/bootstrap-workspace`
2. `/test-plan` or `/refactor-component`
3. `/new-feature` without Figma
4. `/new-component` or `/new-view` after confirming Figma MCP access
