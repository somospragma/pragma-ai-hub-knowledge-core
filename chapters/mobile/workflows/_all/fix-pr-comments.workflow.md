---
id: fix-pr-comments
version: 1.2.0
scope: chapter
type: workflow
chapter: mobile
description: Deterministic workflow to address Pull Request comments in a traceable way. Use it when concrete feedback already exists
---

# Workflow: Address PR Comments

## Prerequisites

- PR URL.
- Comments accessible via conversation, exported file, or integration.
- Valid `.copilot/config/project.config.yaml`.
- Context resolved by orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_ROOT`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`

If no comments are accessible, end with `blocked_input`.

## Topology Gate

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT`, `TARGET_ROOT`).
3. In `monorepo_melos`, validate `melos.yaml`, scope, and target package.

## Canonical Sequence

### PHASE 1 — Analyze comments and build the plan

**Agent**: `@component-planner`

Steps:
1. Classify comments by type: `[VISUAL]`, `[LOGIC]`, `[DOCS]`, `[TESTS]`, `[STYLE]`.
2. Map comment → affected file/area.
3. Create a prioritized plan.

Mandatory output: plan in `PIPELINE_SPEC_PATH`.

---

### PHASE 2 — Apply code fixes

**Agent**: `@widget-developer`

Category coverage:
- `[VISUAL]`, `[LOGIC]`, `[STYLE]` → Phase 2
- `[TESTS]` → Phase 4a/4b
- `[DOCS]` → Phase 5

---

### PHASE 3 — Comment coverage audit

**Agent**: `@code-auditor`

- Verify comment→fix matrix.
- If coverage is missing, loop with `@widget-developer`.
- Write report in `§5`.

---

### PHASE 4a — Update Widget Tests (if functional impact)

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)

---

### PHASE 4b — Update Golden Tests (if visual impact)

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)

---

### PHASE 5 — Delivery

**Agent**: `@delivery-manager`

- Apply `[DOCS]` fixes from the plan.
- Commits per fix type.
- Comment coverage summary.
- Final topology-aware verification.

Mandatory output: `§7` in `PIPELINE_SPEC_PATH` + log.
