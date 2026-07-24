---
id: fix-pr-comments
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/overlays/fix-pr-comments.yaml
invocation_mode: explicit_agent
description: Deterministic workflow to fix Pull Request comments in a traceable way. Use it when actionable review feedback already exists.
---
# Workflow: Fix PR Comments

## Prerequisites

- URL of the PR.
- Accessible comments through conversation, exported file or integration.
  Record the source in `spec.yaml.inputs.pr_comments_source` with:
  `kind: pr_url | inline | exported_file | integration`, `value` and
  `access_status`.
- `.sopp/config/project.config.yaml` valid.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID` per affected file
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {targets.registry[app].root}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {targets.registry[app].root}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {targets.registry[app].root}/{pipeline.output_dir}/specs/pr-comments-{pr_id}`

If there are no accessible comments, finish with `blocked_input`.

## User Inputs

```text
@ds-orchestrator /fix-pr-comments
pr_comments_source:
  kind: <pr_url|inline|exported_file|integration>
  value: <url|inline comments|path/to/comments.md|integration id>
  access_status: available
pr_id: <123>                         # optional
target_branch: <branch_name>         # optional
allow_git_commands: false            # optional, default false
allow_gh_commands: false             # optional, default false
```

## Topology Gate

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT` and each affected target).
3. In targets `location_strategy=melos_package`, validate `repo_root/melos.yaml`
   and `repo_root/package_path`.

## Canonical Sequence

### PHASE 0 — Mobile Spec Packet (`mini`)

**Agent**: `@ds-orchestrator`
**Skill**: `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: mini`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The spec records the PR URL/source, accessible comments, comment-to-action
matrix, success criteria, permissions per agent, and allowed categories.

---

### PHASE 1 — Analyze comments and build the plan

**Agent**: `@component-planner`

Steps:
1. Classify comments by type: `[VISUAL]`, `[LOGIC]`, `[DOCS]`, `[TESTS]`, `[STYLE]`.
2. Map comment → file/affected area.
3. Create a prioritized plan.

Required output: update `comment_inventory`, `correction_plan`,
`artifact_plan`, and `success_criteria` in `spec.yaml`.

---

### PHASE 1.5 — Validation + Human Review

**Skill**: `mobile-sdd-spec-validation`

Validate `spec.yaml` and present `review.md` in Spanish with:

1. comments grouped by category
2. affected files
3. proposed changes
4. required tests, goldens and documentation

Wait for explicit approval before applying fixes.

---

### PHASE 2 — Apply code fixes

**Agent**: `@widget-developer`
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: pr_comment_fixes
read_sections:
  - inputs.pr_comments_source
  - correction_plan
  - artifact_plan
  - success_criteria
```

Category coverage:
- `[VISUAL]`, `[LOGIC]`, `[STYLE]` → Phase 2
- `[TESTS]` → Phase 4a/4b
- `[DOCS]` → Phase 5

---

### PHASE 3 — Audit comment coverage

**Agent**: `@code-auditor`

- Verify matrix comment-to-fix.
- If missing coverage, loop with `@widget-developer`.
- Write `evidence/audit-report.md`.

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
- Suggest commit message text by fix type; do not run `git` or create commits.
- Coverage summary comments.
- Final Verification topology-aware.

Required output: `evidence/delivery-report.md`, human report and log.

`delivery-manager` does not run `git`, create branches, or open PRs unless
the user explicitly requests it and `agent_permissions.delivery-manager`
declares the required external tools.

## Rules

- Do not apply fixes before approving `review.md`.
- `spec.yaml` is the machine source of the comment-to-action matrix.
- Handoffs by reference; do not copy the entire feedback of the PR between agents.
- Validate `agent_permissions` before creating, modifying, or deleting files.
