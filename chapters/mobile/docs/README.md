# Mobile Knowledge Base

This folder is the operating guide for the mobile chapter knowledge base. The
execution rules live in `workflows`, `agents`, `prompts`, `skills` and
`docs/templates`; docs explain how to use them without duplicating every rule.

## What This KB Does

The mobile KB helps agents and developers execute Flutter work through
lightweight Spec-Driven Development:

1. The human provides intent, links or project hints.
2. The agent creates a Mobile Spec Packet.
3. The human reviews a compact Spanish `review.md`.
4. Agents generate or refactor by phase using compact handoffs.
5. Audits, tests, blockers and approvals are stored as evidence.

For a known task, invoke the workflow entry agent directly. The optional
`mobile-orchestrator` only classifies an ambiguous request and delegates to that
controller; it does not own packet state or human checkpoints.

## Start Here

- [Workflows](workflows.md): canonical entry agents, invocation syntax,
  required inputs, checkpoints and expected results.
- [Mobile Spec Packet](mobile-spec.md): spec levels, initial files, config
  files, schemas and template locations.

## Runtime State

Generated project state is stored in the target app repository:

```text
<APP_REPO_ROOT>/.sopp/
├── config/
│   ├── project.config.yaml
│   ├── architecture-contract.yaml
│   └── dependencies-contract.yaml
├── bootstrap/{run_id}/
└── flow_result/specs/{workflow_slug}/
```

Tool-specific export folders such as `.github/` and `.kiro/` may contain
agents, workflows, prompts, skills, and docs. They never own project runtime
configuration; functional workflows use only `<APP_REPO_ROOT>/.sopp/`.

## Source Assets

- Templates: `./templates/`
- Schemas: `./templates/schemas/`
- Executable validation and gate scripts: `./scripts/`
- Workflows: `../workflows/`
- Agents: `../agents/`
- Examples: `./examples/` (non-normative samples only)
- Shared validation skill:
  `../skills/mobile-sdd-spec-validation/SKILL.md`

## Language Policy

The KB itself is written in English. Human-facing approval questions, summaries
and review files are written in Spanish by default unless the user asks for
another language.

## Local Validation

From the exported chapter root, run after changing workflows, agents, prompts,
templates, schemas or docs:

```bash
ruby docs/scripts/validate_mobile_kb.rb
ruby docs/scripts/validate_mobile_kb.rb --strict-language
```
