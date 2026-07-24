---
id: bootstrap-workspace
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: workspace-discovery
input_contract: ../docs/templates/spec-packets/overlays/bootstrap-workspace.yaml
invocation_mode: explicit_agent
description: >
  SDD-aware workflow to discover workspace topology and paths, propose the initial configuration, and apply it only after human approval. Use when project roots or target configuration are missing, ambiguous, or multi-repo.
---
# Workflow: Bootstrap Workspace

## When To Use It

Use this workflow when:

1. the app, Design System, and/or core package live in different physical paths
2. the workspace is a Melos monorepo or a multi-repo setup without reliable configuration
3. the user wants to remove path ambiguity before creating a view or component

Do not use it to re-create a valid canonical `.sopp/config` triplet. Bootstrap
reuses a valid applied configuration by default. Use `FORCE_RECONFIGURE: true`
only for an explicit migration or repair proposal.

## Prerequisites

- Accessible `WORKSPACE_ROOT`.
- Optional `*.code-workspace` file for the IDE workspace.
- Optional expected package names for the app, Design System, and core package.
- Recommended for multi-repo workspaces: `EXPECTED_APP_REPO_ROOT`, so the workflow can explicitly identify where `.sopp/config` must be created.

## User Inputs

```text
@workspace-discovery /bootstrap-workspace
WORKSPACE_ROOT: /Users/user/dev/mobile-workspace
WORKSPACE_FILE: /Users/user/dev/mobile-workspace/mobile.code-workspace
EXPECTED_APP_REPO_ROOT: /Users/user/dev/mobile-workspace/mand-app-monorepo
EXPECTED_APP_PACKAGE: my_app
EXPECTED_DS_PACKAGE: design_system
EXPECTED_CORE_PACKAGE: core
EXPECTED_REPO_MODE: multi_repo
APPLY_MODE: propose_then_apply
FORCE_RECONFIGURE: false
```

## Canonical Sequence

### PHASE B0 — Reuse Or Diagnose Canonical Configuration

**Agent**: `@workspace-discovery`

Run this gate immediately after the app repository is deterministically
resolved. When the app root is not supplied explicitly, complete B1 discovery
first, then return to this gate before B2 creates a proposal. Inspect only the
final canonical files in `<APP_REPO_ROOT>/.sopp/config/`.

1. If the complete triplet is valid, matches `APP_REPO_ROOT`, and resolves all
   target roots, return `reused_existing_config` and stop. Do not create a
   bootstrap packet, proposal, backup, or replacement configuration.
2. If the triplet is partial, finish with
   `blocked_input: CONFIG_BOOTSTRAP_INCOMPLETE`.
3. If the triplet is complete but fails schema, ownership, root, or target
   validation, finish with `blocked_input: CONFIG_BOOTSTRAP_CONFIG_INVALID`.
4. Continue after either failure only when the human explicitly re-invokes with
   `FORCE_RECONFIGURE: true`; record a compact diff against the prior canonical
   configuration in the proposal.
5. `.copilot/config/` and `.kiro/config/` are legacy tool-specific state. They
   are never configuration inputs or write destinations. If no canonical
   triplet exists, report `CONFIG_LEGACY_COPILOT_CONFIGURATION_FOUND`.

### PHASE B1 — Discovery

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md`

Resolve:

1. app, Design System, core, and Melos candidates
2. `APP_REPO_ROOT`
3. `TOPOLOGY_REPO_MODE`
4. `targets.registry` with logical targets (`app`, `design_system`, `core`, `project_docs`, `feature_*`) and their resolved roots
5. `active_target_defaults`
6. ambiguity risks

If deterministic resolution fails, finish with `blocked_input`.

---

### PHASE B2 — Bootstrap Spec Packet + Proposal

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md`

Required output in `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`:

1. `bootstrap-spec.yaml`
2. `context.json`
3. `review.md`
4. `proposed/project.config.yaml`
5. `proposed/architecture-contract.yaml`
6. `proposed/dependencies-contract.yaml`
7. `evidence/workspace-discovery-report.md`
8. `evidence/candidates.json`
9. `evidence/validation-report.md`
10. `evidence/drift-analysis.md`

`bootstrap-spec.yaml` must declare `schema_ref: ../docs/templates/schemas/bootstrap-spec.schema.yaml` and is the machine-readable source for the proposal. `review.md` is the human-readable Spanish review.

Generate the proposal from the canonical templates in `../docs/templates/`; do not rebuild the three configuration files from scratch when a template exists.

Minimum agent permissions:

- B1-B3: may read the workspace and write only inside `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.
- B4: may write inside `<APP_REPO_ROOT>/.sopp/config/` only after the human checkpoint is approved and backups are created.
- Must never delete existing configuration files.
- Must never apply changes if the resolved root points to a Design System, shared, or core package instead of the app repository.

---

### PHASE B3 — Pre-Apply Validation

**Agent**: `@workspace-discovery`
**Skill**: `mobile-sdd-spec-validation`

Validate:

1. `bootstrap-spec.yaml` is parseable and has `mode=propose_then_apply`.
2. The three files in `proposed/` exist.
3. Each `proposed/*.yaml` file declares `schema_version`, `schema_ref`, and `ownership`.
4. `project.repository_local_path` exists.
5. Each `targets.registry.*.root` resolves to an existing directory.
6. Each Dart/Flutter target declares `pubspec.yaml`.
7. If a target uses `location_strategy=melos_package`, `repo_root/melos.yaml` and `repo_root/package_path` exist.
8. `app` targets have executable app signals (`lib/main.dart`, `lib/main_*.dart`, `android/`, or `ios/`).
9. `design_system` targets have Design System signals (`atoms`, `molecules`, `organisms`, or a DS barrel file).
10. Dependencies with `source=target` reference an existing `target_id` in `project.config.yaml.targets.registry`.
11. `APP_REPO_ROOT` does not point to a Design System, shared, or core package.
12. No anti-drift rule is violated:
    - physical paths and pipeline settings live only in `project.config.yaml`
    - layer rules live only in `architecture-contract.yaml`
    - dependency catalog and import rules live only in `dependencies-contract.yaml`
    - `dependencies-contract.yaml` does not define physical target paths

If validation fails, finish with `blocked_input`.

---

### HUMAN CHECKPOINT (Required)

The orchestrator presents:

1. topology proposal
2. proposed app, Design System, and core paths
3. key differences from the current configuration, if any
4. explicit confirmation that `APP_REPO_ROOT` is not a Design System, shared, or core package
5. summary of `review.md`

Ask exactly:

"I generated the workspace configuration proposal. Do you approve applying the changes with backup?"

Without explicit approval, finish with state `proposed`. Do not write final files outside `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.

Operational note: this is not a second command. The same workflow remains paused in `proposed`; when the human approves, the orchestrator executes B4 atomically with backups.

---

### PHASE B4 — Apply With Backup (If Approved)

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md` with `APPLY_MODE=apply_with_backup`

Required output:

1. `<APP_REPO_ROOT>/.sopp/config/project.config.yaml`
2. `<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml`
3. `<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml`
4. `.bak` backups for the three files, if they existed
5. `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/apply-report.md`

---

### PHASE B5 — Post-Bootstrap Validation

**Agent**: `@workspace-discovery`
**Skill**: `mobile-sdd-spec-validation`

Validate:

1. `project.repository_local_path` exists.
2. Each target in the registry resolves and keeps its expected signals.
3. Dependencies with `source=target` point to existing targets.
4. Final `<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml` exists.
5. Final `<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml` exists.
6. `<APP_REPO_ROOT>/.sopp/flow_result` can be created.
7. `architecture.contract_path` and `dependencies.contract_path` resolve.
8. No anti-drift rule is violated across the three final YAML files.
9. Future `artifact_plan.planned[].target_id` values can resolve against `targets.registry`.

If validation fails, finish with `blocked_input` and an explicit code.

## Expected Result

If B0-B5 succeed:

1. the project is ready for `/new-view` or `/new-component`
2. the configuration no longer depends on `cwd`
3. the main pipeline operates with deterministic paths

## Rules

- Do not overwrite files without backup.
- Do not infer low-confidence paths without human approval.
- Validate agent permissions before writing in `bootstrap/` or `config/`.
- Default operation: `propose_then_apply`.
- `review.md` must be in Spanish.
- Handoffs must use references (`bootstrap-spec.yaml`, `context.json`); do not copy the full discovery into each phase.
- If the resolved root points to a Design System, shared, or core package, block with an explicit code and do not apply changes.
- Do not execute `/new-view` or `/new-component` if bootstrap ended in `blocked_input`.
