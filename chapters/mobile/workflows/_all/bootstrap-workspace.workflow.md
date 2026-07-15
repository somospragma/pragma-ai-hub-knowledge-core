---
id: bootstrap-workspace
version: 1.2.0
scope: chapter
type: workflow
chapter: mobile
description: Bootstrap workflow to discover workspace topology/paths and prepare `project.config.yaml` + `ARCHITECTURE-CONTRACT.yaml` +
  `DEPENDENCIES-CONTRACT.yaml` before execute `/new-view` o
  `/new-component`.
---

# Workflow: Workspace Bootstrap

## When to use it

Use this workflow when:

1. the app, the DS and/or the core live in different physical paths
2. there is a Melos monorepo or multi-repo and there is no reliable configuration yet
3. the user wants to avoid ambiguity before creating a view/component

## Prerequisites

- `WORKSPACE_ROOT` accessible.
- Optional: `*.code-workspace` file from the VSCode workspace.
- Optional: hints for expected names (app, DS, core).
- Recommended in multi-repo workspaces: `EXPECTED_APP_REPO_ROOT` to explicitly
  pin the app repo where `.copilot/config` must be created.

## User inputs (example)

```text
@ds-orchestrator /bootstrap-workspace
WORKSPACE_ROOT: /Users/user/dev/mobile-workspace
WORKSPACE_FILE: /Users/user/dev/mobile-workspace/mobile.code-workspace
EXPECTED_APP_REPO_ROOT: /Users/user/dev/mobile-workspace/my-app-monorepo
EXPECTED_APP_PACKAGE: my_app
EXPECTED_DS_PACKAGE: design_system
APPLY_MODE: propose_only
```

## Canonical sequence

### PHASE B1 — Discovery + Proposal

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md`

Mandatory output in `<APP_REPO_ROOT>/.copilot/config/bootstrap`:

1. `workspace_discovery_report.md`
2. `proposed_project.config.yaml`
3. `proposed_architecture-contract.yaml`
4. `proposed_dependencies-contract.yaml`
5. `bootstrap_pipeline_log.md`

---

### HUMAN CHECKPOINT (mandatory)

The orchestrator presents:

1. proposed topology
2. proposed app/ds/core paths
3. key differences against current configuration (if any)
4. explicit confirmation that `APP_REPO_ROOT` is not DS/shared/core

Exact question:

"I have generated the workspace configuration proposal. Do you approve applying the changes with backup?"

Without explicit approval, end in `propose_only`.
In this mode, no final files must be written outside
`<APP_REPO_ROOT>/.copilot/config/bootstrap`.

---

### PHASE B2 — Apply with backup (if approved)

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md` with `APPLY_MODE=apply_with_backup`

Mandatory output:

1. `<APP_REPO_ROOT>/.copilot/config/project.config.yaml`
2. `<APP_REPO_ROOT>/.copilot/config/ARCHITECTURE-CONTRACT.yaml`
3. `<APP_REPO_ROOT>/.copilot/config/DEPENDENCIES-CONTRACT.yaml`
4. `.bak` backups for the 3 files (if they existed)

---

### PHASE B3 — Post-bootstrap validation

**Agent**: `@workspace-discovery`

Validations:

1. `project.repository_local_path` exists
2. in melos mode: `melos.yaml` + `target_scope`
3. DS/core with `source=path` exist
4. final `<APP_REPO_ROOT>/.copilot/config/ARCHITECTURE-CONTRACT.yaml` exists
5. final `<APP_REPO_ROOT>/.copilot/config/DEPENDENCIES-CONTRACT.yaml` exists
6. `<APP_REPO_ROOT>/.copilot/flow_result` can be created

If it fails, end with `blocked_input` and an explicit code.

## Expected result

If B1-B3 succeed:

1. the project is ready for `/new-view` or `/new-component`
2. the configuration no longer depends on `cwd`
3. the main pipeline operates with deterministic paths

## Rules

- Do not overwrite files without backup.
- Do not infer low-confidence paths without human approval.
- If the resolved root points to a DS/shared/core library, block with an
  explicit code and do not apply.
- Do not run `/new-view` or `/new-component` if bootstrap ended in `blocked_input`.
