---
id: workspace-discovery
version: 1.1.0
scope: chapter
type: prompt
chapter: mobile
description: >
  Prompt for discovering Flutter workspace topology, resolving target roots, and proposing deterministic bootstrap configuration. Use when bootstrap needs reproducible app, Design System, core, and documentation paths.
---
# Workspace Bootstrap Discovery (Deterministic)

## Objective

Resolve reproducibly:

1. where the target app repo is (`PROJECT_ROOT`)
2. where external DS/core repos live locally, if they exist
3. which topology applies (`single_repo | monorepo_melos | multi_repo`)
4. how `project.config.yaml`, `architecture-contract.yaml`, and
   `dependencies-contract.yaml` must be shaped

## Required Inputs

- `WORKSPACE_ROOT`
- `APPLY_MODE` (`propose_then_apply` | `propose_only` | `apply_with_backup`)

## Optional Inputs

- `WORKSPACE_FILE` (`*.code-workspace`)
- hints:
  - `EXPECTED_APP_REPO_ROOT` (absolute path to the app repo)
  - `EXPECTED_APP_REPO_NAME` (folder name of the app repo)
  - `EXPECTED_APP_PACKAGE`
  - `EXPECTED_DS_PACKAGE`
  - `EXPECTED_CORE_PACKAGE`
  - `EXPECTED_REPO_MODE`
  - `FORCE_RECONFIGURE` (`false` by default; `true` only for an intentional
    repair/replacement proposal)

## Required Outputs

When B0 requires a proposal, generate in
`BOOTSTRAP_ROOT={APP_REPO_ROOT}/.sopp/bootstrap/{run_id}`:

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

When B0 reuses a valid configuration, return only
`reused_existing_config`, the resolved app root, and the three validated
canonical paths. Do not create a bootstrap run directory.

If `APPLY_MODE=apply_with_backup` and explicit user approval exists:

1. `<APP_REPO_ROOT>/.sopp/config/project.config.yaml`
2. `<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml`
3. `<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml`
4. `.bak` backups of the three files, if they existed
5. `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/apply-report.md`

## Required Sequence

### Phase B0 - Reuse Or Diagnose Existing Configuration

Run this gate immediately after `APP_REPO_ROOT` is deterministically resolved.
When the app root is not supplied explicitly, execute B1-B3 only to resolve it,
then return to this gate before B4 creates any proposal. Inspect only the
canonical final triplet in `<APP_REPO_ROOT>/.sopp/config/`.

1. If the complete triplet is valid, matches `APP_REPO_ROOT`, and resolves all
   target roots, return `reused_existing_config` immediately. Do not create a
   packet, proposal, backup, or configuration file.
2. If it is partial, return `CONFIG_BOOTSTRAP_INCOMPLETE`.
3. If it is complete but invalid/outdated, return
   `CONFIG_BOOTSTRAP_CONFIG_INVALID`.
4. Do not automatically repair either state. Continue only after an explicit
   reinvocation with `FORCE_RECONFIGURE: true`.
5. Ignore runtime-looking files under tool-specific KB folders completely as
   configuration sources. Report their presence as ignored evidence and use
   `CONFIG_NON_CANONICAL_TOOL_STATE_FOUND` when no canonical triplet exists.

### Phase B1 - Resolve Roots To Scan

1. Start with `WORKSPACE_ROOT`.
2. If `WORKSPACE_FILE` exists, include `folders[].path`.
3. Normalize absolute paths and remove duplicates.

If there are no roots, block with `BOOTSTRAP_SCAN_ROOTS_EMPTY`.

### Phase B2 - Discover Candidates

Search each root for:

1. `pubspec.yaml`
2. Melos configuration candidates: legacy `melos.yaml`, or a root `pubspec.yaml`
   with `workspace:` plus a Melos dependency or `melos:` section
3. executable app signals (`lib/main.dart`, `lib/main_*.dart`, `android/`, `ios/`)
4. canonical app signals (`lib/src/presentation`, `lib/src/features`)
5. legacy app signals (`lib/presentation`, `lib/features`) only to alert
   compatibility/migration risk
6. canonical DS signals (`lib/src/atoms`, `lib/src/molecules`, `lib/src/organisms`)
7. legacy DS signals (`lib/atoms`, `lib/molecules`, `lib/organisms`) only to
   alert compatibility/migration risk
8. shared/core signals (`core|shared|common` in name/path)

Classify `APP_CANDIDATE`, `DS_CANDIDATE`, `CORE_CANDIDATE`, and
`MONOREPO_ROOT_CANDIDATE`.

### Phase B3 - Infer Topology

Rules:

1. `monorepo_melos`: the deterministic Melos resolver succeeds and multiple
   Flutter packages are present.
2. `single_repo`: isolated app without Melos.
3. `multi_repo`: app/features live in separate repos outside Melos.

Resolve:

- `APP_REPO_ROOT`
- `topology.repo_mode`
- `topology.feature_location_mode`
- `topology.shared_core_mode`
- `workspace.roots`
- `targets.registry`
- `active_target_defaults`

Root Selection Rule:

- `APP_REPO_ROOT` must be the repository for the target app.
- Do not write final configuration in dependency repos (DS/core) or in the
  global workspace root.
- If `EXPECTED_APP_REPO_ROOT` is provided, use it as a strict pin and validate
  that it is an executable app; block if it does not pass.
- In `monorepo_melos`, `APP_REPO_ROOT` must be the repo containing the resolved
  app Melos configuration.
- If there is a tie or ambiguity between app candidates, block and do not apply.

Required decision order:

1. valid `EXPECTED_APP_REPO_ROOT` wins.
2. valid Melos app repo wins.
3. best candidate with executable app signals and without DS/core signals wins.
4. conflict -> `BOOTSTRAP_APP_REPO_AMBIGUOUS`.

### Phase B4 - Build Bootstrap Spec Packet + Config Proposal

Rules:

1. `project.repository_local_path` must be absolute and point to the app repo.
2. `targets.registry` must include resolved logical targets:
   `app`, `design_system`, `core`, `project_docs`, and packaged features when
   they exist. `project_docs` uses `kind=docs` and resolves documentation and
   reports under `docs/`.
3. Each target must declare `kind`, `location_strategy`, `repo_root`,
   `package_path`, `root`, and `package_name` when applicable.
4. Local DS/core/features are represented in dependencies as
   `source=target` + `target_id`; physical paths are not duplicated in
   `dependencies-contract.yaml`.
5. Remote DS/core dependencies use `source=git|hosted` and do not declare local paths.
6. Build `proposed/architecture-contract.yaml` consistently with the discovered
   topology and make it suitable for `/new-view`.
7. Each `proposed/*.yaml` must include `schema_version`, `schema_ref`, and an
   `ownership` block:
   - `project.config.yaml`: owns workspace roots, target registry, topology,
     pipeline, target structure, naming, tokens, and testing.
   - `architecture-contract.yaml`: owns layer rules, generation policies,
     constraints, and domain/data contracts.
   - `dependencies-contract.yaml`: owns the dependency catalog, imports,
     dependency `target_id`, and the allowed matrix.
8. Use `lib/src` as the default for production code:
   - `targets.registry.app.structure.features_path: lib/src/features`
   - DS `targets.registry.design_system.structure.*_path` entries under `lib/src`
   - presentation/domain/data under `lib/src`
9. If legacy structure is detected outside `lib/src`, include an alert in
   `evidence/workspace-discovery-report.md`; do not change new-code defaults
   to legacy paths unless the user explicitly requests it.
10. Create `bootstrap-spec.yaml` with:
    - `workflow: bootstrap-workspace`
    - `mode: propose_then_apply`
    - `status: proposed`
    - received inputs
    - resolved topology
    - references to `proposed/*.yaml`
    - `schema_ref` per proposed file
    - ownership of each contract to prevent drift
11. Create `review.md` in Spanish with a short summary for human approval.
12. Create `context.json` with `run_id`, state, main paths, and pending approval.
13. Create evidence in `evidence/`, separating discovery, candidates,
    validation, and anti-drift analysis.

### Phase B5 - Validation

1. `APP_REPO_ROOT` exists.
2. Each `targets.registry.*.root` exists.
3. If a target uses `location_strategy=melos_package`, run
   `docs/scripts/melos_workspace.rb resolve` with `repo_root` and
   `package_path`; require `ok=true` and persist the returned source metadata.
4. Local dependencies use `source=target` and an existing `target_id`.
5. `.sopp/bootstrap/{run_id}` is writable in the app repo.
6. The proposed architecture contract is parseable.
7. `APP_REPO_ROOT` does not point to DS/core.
8. The target `app` has an executable app signal.
9. `BOOTSTRAP_ROOT={APP_REPO_ROOT}/.sopp/bootstrap/{run_id}` is writable.
10. There are no anti-drift violations:
    - `project.config.yaml` contains workspace roots, target registry, pipeline,
      naming, tokens, and testing helpers. It does not contain layer rules or a
      complete dependency catalog.
    - `architecture-contract.yaml` contains layer rules, generation policies,
      and architectural constraints. It does not contain physical topology,
      targets, or pipeline paths.
    - `dependencies-contract.yaml` contains the dependency catalog, imports,
      dependency `target_id`, and the allowed matrix. It does not contain
      physical topology, local physical paths, or layer rules.

If validation fails, block with an explicit code.

### Phase B6 - Controlled Apply

Only with explicit user approval:

1. reread `bootstrap-spec.yaml`, `context.json`, and `proposed/*.yaml`
2. validate `status=proposed`
3. back up destination files
4. write final files
5. record a summarized diff in `apply-report.md`

Without approval, finish in `propose_only`.

Strict Write Rule:

- With `APPLY_MODE=propose_then_apply` or `propose_only`, write only in
  `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.
- Do not write final files in `.sopp/config/*`.

## Minimum Report Format

`review.md` must briefly include, in Spanish:

1. **Topology proposal summary**
2. **Final proposed paths (app/ds/core)**
3. **Proposed files**
4. **Ownership decisions between contracts**
5. **Alerts**
6. **Action required to apply**

`evidence/workspace-discovery-report.md` must include the complete table of
candidates, confidence, executed validations, and the recommended next step.

## Block Codes

- `BOOTSTRAP_WORKSPACE_ROOT_MISSING`
- `BOOTSTRAP_SCAN_ROOTS_EMPTY`
- `BOOTSTRAP_APP_REPO_NOT_RESOLVED`
- `BOOTSTRAP_APP_REPO_AMBIGUOUS`
- `BOOTSTRAP_APP_REPO_MISMATCH_HINT`
- `BOOTSTRAP_APP_REPO_POINTS_TO_LIBRARY`
- `BOOTSTRAP_APP_PACKAGE_NOT_FOUND`
- `BOOTSTRAP_TOPOLOGY_AMBIGUOUS`
- `BOOTSTRAP_MELOS_INVALID`
- `BOOTSTRAP_PROPOSAL_ROOT_UNWRITABLE`
- `BOOTSTRAP_ARCH_CONTRACT_PROPOSAL_INVALID`
- `BOOTSTRAP_PATH_DEPENDENCY_MISSING`
- `BOOTSTRAP_APPLY_NOT_APPROVED`
- `CONFIG_BOOTSTRAP_INCOMPLETE`
- `CONFIG_BOOTSTRAP_CONFIG_INVALID`
- `CONFIG_NON_CANONICAL_TOOL_STATE_FOUND`
