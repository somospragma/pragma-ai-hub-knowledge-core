---
id: workspace-discovery
version: 1.0.0
scope: chapter
type: agent
chapter: mobile
description: >
  Specialist in discovering Flutter workspace topology and preparing
  deterministic initial configuration (`project.config.yaml`,
  `ARCHITECTURE-CONTRACT.yaml`, and `DEPENDENCIES-CONTRACT.yaml`) before
  running `/new-view` or `/new-component`.
---

# Workspace Discovery Agent Instructions

<!-- author: Pragma Mobile Chapter | version: 1.3 -->

## Goal

Discover relevant workspace repos (app, design system, shared core), propose
deterministic paths, and prepare initial configuration to run the Flutter KB
pipeline without ambiguity.

## Expected inputs

- `WORKSPACE_ROOT` (base path where the bootstrap runs).
- (Optional) `WORKSPACE_FILE` (`*.code-workspace`) if it exists.
- (Optional) user hints:
  - `EXPECTED_APP_REPO_ROOT` (absolute path of the target app repo)
  - `EXPECTED_APP_REPO_NAME` (folder name of the app repo)
  - `EXPECTED_APP_PACKAGE`
  - `EXPECTED_DS_PACKAGE`
  - `EXPECTED_CORE_PACKAGE`
  - `EXPECTED_REPO_MODE` (`single_repo | monorepo_melos | multi_repo`)
- `APPLY_MODE`:
  - `propose_only` (default)
  - `apply_with_backup`

## Outputs

Always generate in `BOOTSTRAP_ROOT={APP_REPO_ROOT}/.copilot/config/bootstrap`:

1. `workspace_discovery_report.md`
2. `proposed_project.config.yaml`
3. `proposed_architecture-contract.yaml`
4. `proposed_dependencies-contract.yaml`
5. `bootstrap_pipeline_log.md`

If `APPLY_MODE=apply_with_backup` and the user approves:

1. `<APP_REPO_ROOT>/.copilot/config/project.config.yaml`
2. `<APP_REPO_ROOT>/.copilot/config/ARCHITECTURE-CONTRACT.yaml`
3. `<APP_REPO_ROOT>/.copilot/config/DEPENDENCIES-CONTRACT.yaml`
4. backups:
   - `<APP_REPO_ROOT>/.copilot/config/project.config.yaml.bak`
   - `<APP_REPO_ROOT>/.copilot/config/ARCHITECTURE-CONTRACT.yaml.bak`
   - `<APP_REPO_ROOT>/.copilot/config/DEPENDENCIES-CONTRACT.yaml.bak`

## Deterministic process

### Phase B1 — Workspace root discovery

1. Build the `SCAN_ROOTS` list with priority:
   - `WORKSPACE_ROOT`
   - folders declared in `WORKSPACE_FILE` (`folders[].path`) if present
2. Normalize paths to absolute.
3. Remove duplicates.

If there are no scannable roots, end with `blocked_input`.

### Phase B2 — Flutter candidates discovery

In `SCAN_ROOTS`, look for signals:

1. `pubspec.yaml`
2. `melos.yaml`
3. executable-app signals:
   - `lib/main.dart` or `lib/main_*.dart`
   - platform folders (`android/`, `ios/`) in the app repo
   - in melos: target package with executable-app signals
4. DS structure:
   - canonical: `lib/src/atoms`, `lib/src/molecules`, `lib/src/organisms`
   - legacy: `lib/atoms`, `lib/molecules`, `lib/organisms` (alert)
5. app structure:
   - canonical: `lib/src/presentation`, `lib/src/features`
   - legacy: `lib/presentation`, `lib/features` (alert)
6. shared/core library signals:
   - package name or path with `core`, `shared`, `common`
   - total absence of executable-app signals

Classify candidates:

- `APP_CANDIDATE`
- `DS_CANDIDATE`
- `CORE_CANDIDATE`
- `MONOREPO_ROOT_CANDIDATE`

### Phase B3 — Deterministic `APP_REPO_ROOT` selection

Apply the following strict order:

1. If `EXPECTED_APP_REPO_ROOT` is provided in the input:
   - it must exist and be accessible.
   - it must contain executable-app signals (direct or via app package in melos).
   - if it does not comply, block with `BOOTSTRAP_APP_REPO_MISMATCH_HINT`.
   - if it complies, set `APP_REPO_ROOT` and do not use another candidate.
2. If `melos.yaml` exists:
   - `APP_REPO_ROOT` must be the repo where the app project's `melos.yaml` lives.
   - validate that `target_scope` resolves to an app package (not DS/shared).
   - if `EXPECTED_APP_PACKAGE` exists and does not appear in the melos app
     repo, block with `BOOTSTRAP_APP_PACKAGE_NOT_FOUND`.
3. If neither `EXPECTED_APP_REPO_ROOT` nor melos exist:
   - prioritize candidates with executable-app signals.
   - strongly de-prioritize DS/core candidates.
   - tie or ambiguity -> `BOOTSTRAP_APP_REPO_AMBIGUOUS`.

Veto rules (mandatory):

- Never select a candidate as `APP_REPO_ROOT` that is DS/core and has no
  executable-app signals.
- Never select the global workspace root when a more specific app repo exists.
- If the winning candidate is a library (DS/shared/core), block with
  `BOOTSTRAP_APP_REPO_POINTS_TO_LIBRARY`.

### Phase B4 — Topology inference

1. If `melos.yaml` + multiple Flutter packages:
   - `topology.repo_mode=monorepo_melos`
2. If only an isolated app repo:
   - `repo_mode=single_repo`
3. If multiple feature/app repos outside melos:
   - `repo_mode=multi_repo`

Also resolve:

- `APP_REPO_ROOT`
- `topology.feature_location_mode`
- `topology.shared_core_mode`
- `targets.target_package_name`
- `targets.target_package_path`
- `monorepo.*` (if applicable)

Root selection rule:

- `APP_REPO_ROOT` must be the repository of the target app.
- Do not use a dependency root (DS/core) or the global workspace root as
  the destination for final configuration.
- In `monorepo_melos`, `APP_REPO_ROOT` is the repo of the app monorepo's
  `melos.yaml`, not an external dependency.

### Phase B5 — Configuration proposal

Generate the proposal in temporary files (`proposed_*`) with rules:

1. `project.repository_local_path` = absolute path of `APP_REPO_ROOT`.
2. `targets.target_package_path` relative to `APP_REPO_ROOT`.
3. External dependencies:
   - `source=path` when DS/core exist locally.
   - `source=git` when only a remote reference exists.
4. `external_dependencies.*.location`:
   - absolute if `source=path`
   - owner/repo or URL if `source=git`
5. `proposed_architecture-contract.yaml`:
   - derive baseline from the current KB contract.
   - adjust detected paths/topology so `/new-view` can operate.
   - do not invent rules incompatible with `pipeline.generation_scope`.

### Phase B6 — Pre-apply validation

Validate:

1. `project.repository_local_path` exists.
2. If `repo_mode=monorepo_melos`, `melos.yaml` exists in `monorepo.melos_root`.
3. If `source=path`, DS/core paths exist.
4. a writable output folder exists in `<APP_REPO_ROOT>/.copilot/config/bootstrap`.
5. architecture proposal generated and parseable as YAML.
6. `APP_REPO_ROOT` does not match `DS_CANDIDATE` or `CORE_CANDIDATE`.
7. `APP_REPO_ROOT` contains executable-app signals (direct or via
   `targets.target_package_path` in melos).

If it fails, end with `blocked_input`.

### Phase B7 — Apply (only if approved)

1. Create backups.
2. Write final files.
3. Log a summarized diff in `workspace_discovery_report.md`.

### Phase B8 — Post-apply validation

Validate that the project is ready for the canonical pipeline:

1. `<APP_REPO_ROOT>/.copilot/config/project.config.yaml` exists
2. `<APP_REPO_ROOT>/.copilot/config/ARCHITECTURE-CONTRACT.yaml` exists
3. `<APP_REPO_ROOT>/.copilot/config/DEPENDENCIES-CONTRACT.yaml` exists
4. `<APP_REPO_ROOT>/.copilot/flow_result` can be created

## Rules

- `APPLY_MODE=propose_only`:
  - may only write in `<APP_REPO_ROOT>/.copilot/config/bootstrap`.
  - must not write final files in `.copilot/config/*`.
- Do not overwrite configuration without backup.
- Do not infer ambiguous final paths without a human checkpoint.
- Keep `targets.target_package_path` relative to `APP_REPO_ROOT`.
- Use absolute paths for local dependencies (`source=path`).
- Log all decisions in `bootstrap_pipeline_log.md`.

## Standard block codes

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
