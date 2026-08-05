# Mobile SDD Configuration Guide

This guide describes the configuration templates used by `/bootstrap-workspace`
and by the mobile SDD workflows.

## Current Decision

The original three configuration files are kept, but simplified and protected by
explicit ownership:

| File | Responsibility | Must Not Define |
|---|---|---|
| `project.config.yaml` | Project identity, workspace roots, physical topology, target registry, pipeline, naming, tokens, testing and Figma. | Layer rules, generation policies, dependency catalog or import matrix. |
| `architecture-contract.yaml` | Layer rules, generation policies, architectural constraints, domain/data contracts and state/navigation/DI policies. | Physical topology, targets, pipeline, package sources or dependency catalog. |
| `dependencies-contract.yaml` | External/internal dependencies, target/git/hosted source, preferred imports and allowed dependency matrix. | Topology, targets, pipeline, layer rules or generation policies. |

This separation reduces drift without creating one oversized configuration file.

## Available Templates

```text
./
├── project.config.yaml
├── architecture-contract.yaml
├── dependencies-contract.yaml
├── bootstrap/
│   ├── bootstrap-spec.yaml
│   ├── context.json
│   └── review.md
├── schemas/
│   ├── project-config.schema.yaml
│   ├── architecture-contract.schema.yaml
│   ├── dependencies-contract.schema.yaml
│   ├── bootstrap-spec.schema.yaml
│   ├── mobile-spec.schema.yaml
│   └── mobile-context.schema.json
└── spec-packets/
    ├── mini-spec.yaml
    ├── standard-spec.yaml
    ├── full-spec.yaml
    ├── context.json
    ├── review.md
    ├── new-component.overlay.yaml
    ├── bootstrap-workspace.overlay.yaml
    ├── refactor-component.overlay.yaml
    ├── fix-pr-comments.overlay.yaml
    ├── new-view.overlay.yaml
    ├── new-feature.overlay.yaml
    ├── refactor-feature.overlay.yaml
    └── test-plan.overlay.yaml
```

## Recommended Bootstrap

If the project does not have consolidated configuration yet:

```text
@workspace-discovery /bootstrap-workspace
WORKSPACE_ROOT: /path/workspace
WORKSPACE_FILE: /path/workspace/mobile.code-workspace
EXPECTED_APP_REPO_ROOT: /path/workspace/app-monorepo
APPLY_MODE: propose_then_apply
```

The agent must:

1. Resolve `APP_REPO_ROOT` and `targets.registry`.
2. Create `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.
3. Copy/adapt templates from `./bootstrap/`.
4. Generate `proposed/*.yaml` from the three configuration templates.
5. Validate `schema_ref`, `ownership` and anti-drift rules.
6. Present `review.md` in Spanish.
7. Apply files into `.sopp/config/` only after explicit human approval.

## Path Model

```text
<APP_REPO_ROOT>/.sopp/config/project.config.yaml
<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml
<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml
```

Functional workflows resolve a packet owner before Phase 0. The owner is
immutable for the run and can differ from the active artifact target:

```text
{SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/specs/{workflow_slug}/
├── spec.yaml
├── context.json
├── review.md
└── evidence/
```

`spec.yaml` and `context.json` are the executable source of truth.
`PIPELINE_SPEC_PATH` is only a cumulative human report.

For `/new-view`, resolve the owner from `target_id` or the configured app
default. It must have `kind: app`; a DS phase may change `ACTIVE_TARGET_ID` for
its generated components but never the packet root, evidence or reports.

## Critical Fields

### `project.config.yaml`

- `project.repository_local_path`: app repo that owns `.sopp/config`.
- `workspace.roots`: IDE/workspace roots used for discovery.
- `topology.repo_mode`: `single_repo | monorepo_melos | multi_repo`.
- `targets.registry`: logical targets (`app`, `design_system`, `core`,
  `project_docs`, `feature_*`) with `kind`, `location_strategy`, `repo_root`,
  `package_path`, `root` and `package_name`.
- `targets.registry.<target_id>.structure`: target-relative folders such as
  feature paths, view paths, DS atomic paths and Widgetbook paths.
- `project_docs`: target pointing to the root where `docs/`, `docs/testing/`
  and `docs/refactoring/` live or will be created.
- `active_target_defaults`: default target per workflow/phase type.
- `pipeline.output_dir`: SDD artifact root.
- `pipeline.spec_file`: human report, not machine source.
- `architecture.contract_path`: architecture contract path.
- `dependencies.contract_path`: dependencies contract path.

`project.config.yaml` must not store package imports, dependency versions,
generation scope or contract policy. Those belong to
`dependencies-contract.yaml` and `architecture-contract.yaml`.

### `architecture-contract.yaml`

- `layers`: import rules by layer.
- `generation_policies`: contract and code generation scope.
- `constraints.source_of_truth`: declares `spec.yaml` as machine source.
- `constraints.layer_checkpoints`: layer checkpoint requirements.
- `constraints.stage_checkpoints`: stage checkpoints when the workflow does not
  map exactly to architecture layers.

### `dependencies-contract.yaml`

- `external_dependencies`: DS, shared core and other packages by `target_id`,
  import and availability rules. It does not define physical paths.
- `internal_dependencies`: internal core/shared packages when present.
- `allowed_dependency_matrix`: allowed dependencies by layer.

## Spec Packet Templates And Overlays

The base templates in `spec-packets/` are generative skeletons. The agent must:

1. Hydrate placeholders such as `{{WORKFLOW}}`, `{{PHASE}}`, `{{AGENT}}` and
   success criteria.
2. Apply the workflow overlay named `spec-packets/<workflow>.overlay.yaml` and use its
   `entry_agent` as the workflow entry point.
3. Complete `agent_permissions`.
4. Declare `external_access.figma_mcp`; `/new-component` and `/new-view` must
   hydrate `figma_mcp.required=true` before human review.
5. Complete every `artifact_plan.planned[]` entry with `target_id + path`.
6. Validate the hydrated YAML against
   `schemas/mobile-spec.schema.yaml`.
7. Validate `context.json` against `schemas/mobile-context.schema.json` and set
   `workflow_controller` to the overlay `entry_agent`.

Do not validate raw templates with placeholders as final specs.

## Coherence Rules

1. If a target uses `location_strategy=melos_package`, `melos.yaml` must exist
   at `repo_root` and the package must exist at `repo_root/package_path`.
2. If `shared_core_mode=external_core_package`,
   `dependencies-contract.yaml.external_dependencies.shared_core.enabled=true`.
3. Productive paths should point to `lib/src`.
4. `/new-view` blocks if `architecture_contract.generation_policies.view_generation.require_architecture_contract=true` and
   `architecture-contract.yaml` is missing.
5. Bootstrap must not apply changes when ownership drift is detected.
6. Workflows must not use `../..` to cross packages. They must declare
   `artifact_plan.planned[].target_id` and a path relative to that target.

## Local Validation

From the exported chapter root, run:

```bash
ruby docs/scripts/validate_mobile_kb.rb
```

The validator checks:

- YAML/JSON parseability.
- Legacy references.
- Agent, prompt and skill references.
- Workflow invocation and distribution-path validation.
- Template permissions for executing agents.
- Figma MCP requirements.
- Documentation/report artifacts under `artifact_plan.planned[group=docs]`.
- Bootstrap applied-state validation.
