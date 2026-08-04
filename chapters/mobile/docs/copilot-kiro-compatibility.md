# Copilot And Kiro Compatibility

The mobile KB must run in GitHub Copilot and Kiro without changing the workflow
semantics. Renderer-specific files may differ, but the source assets and runtime
state stay portable.

## Core Rule

Execution-critical behavior belongs in workflows, agents, prompts, skills,
templates and the executable gates under `docs/scripts/`. Other docs explain
the model and are not required runtime context. Renderers must export
`docs/scripts/` recursively without flattening or relocating it.

## Renderer Mapping

| Asset | Copilot | Kiro | Requirement |
|---|---|---|---|
| Steering | `.github/copilot-instructions.md` | `.kiro/steering/*.md` | Must be self-contained and order-independent. |
| Workflows | `.github/instructions/*.instructions.md` | `.kiro/workflows/*.md` | Must be plain Markdown with explicit steps. |
| Skills | `.github/skills/{id}/SKILL.md` | `.kiro/skills/{id}/SKILL.md` or equivalent | Must avoid IDE-only assumptions. |
| Agents | `.github/agents/{id}.md` | Kiro agent/steering assets | Must describe permissions and outputs. |
| Executable gates | `.github/docs/scripts/*.rb` | `.kiro/docs/scripts/*.rb` | Must preserve the canonical `docs/scripts/` relative path and executable content. |
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

`.github/` and `.kiro/` are renderer/export locations for KB resources. They
may coexist in one repository, but they are not configuration, evidence, log
or execution-state sources for functional workflows.

Only `<APP_REPO_ROOT>/.sopp/` owns runtime configuration, evidence, logs,
approvals and execution state. Tool-specific KB folders must never contain or
provide runtime state. If the canonical `.sopp/config` triplet is missing,
partial, or invalid, the workflow blocks and requires an explicit bootstrap or
forced migration; it must not select a renderer-specific fallback.

## Required Agent Behavior

1. Use compact handoffs with `spec_ref`, `context_ref`, `phase` and
   `read_sections`.
2. Persist approvals, blockers and evidence on disk, not only in chat memory.
3. Keep Figma MCP checks explicit before workflows that depend on Figma.
4. For Figma-driven work, grant the preferred analyzer role and the entry
   controller fallback `write` access to the Spec Packet and Figma MCP
   asset-export capability. The fallback applies only when native delegation is
   unavailable and must otherwise stop with
   `PLATFORM_CONTROLLER_ROLE_CAPABILITY_MISSING`.
5. The active executor must persist exports under
   `source-assets/figma/`; a screenshot or temporary URL is insufficient.
6. Avoid mandatory Kiro hooks or Copilot-only commands.
7. Keep human-facing review content in Spanish by default.

## Executable Script Export

The canonical source is `docs/scripts/` in the exported chapter. Workflows and
skills resolve gates only from that location; renderer-root script directories
must not be generated. Synchronization must remove previously managed legacy
copies so an agent cannot execute a stale gate. After rendering, run
`ruby docs/scripts/validate_mobile_kb.rb --strict-language` from the exported
chapter root.

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
