# Mobile Workflows

Use the explicit entry agent and workflow command shown below. This is the
portable, deterministic invocation contract for this chapter. A bare slash
command is only a supported shortcut when the active tool surface has a tested
workflow-to-agent routing adapter.

Each invocation below is copyable. Replace values between `<...>` and remove
optional lines that do not apply.

## Choose The Entry Point

Invoke the entry agent shown for a known workflow. That agent is the workflow
controller: it creates and resumes the packet, asks for required human
checkpoints, owns each required outcome, and records the final state.

## Portable Role Execution

Specialist agents such as `@test-engineer` describe role contracts. Native
agent-to-agent delegation is optional. At runtime, the controller records
`execution_capabilities.subagent_delegation`:

- `available`: it may delegate a focused phase and validates the returned
  evidence.
- `unavailable`: the invoked controller executes the specialist role contract
  itself, with the same planned artifacts, commands, permissions, blockers and
  evidence, under `fallback_policy: delegate_or_controller_executes`.

This makes the workflows portable across Copilot and Kiro. A missing subagent
capability never permits a mandatory phase to be skipped. If the controller
lacks a needed permission or tool, it records `blocked_input` instead.

For Kiro fallback execution, the active entry-agent profile needs `read`,
`write`, and `shell` access. Add `subagent` only when native delegation is
desired; it is not required for correctness. A Figma-driven fallback also
needs the configured Figma MCP tool. Missing runtime access is
`blocked_input: PLATFORM_CONTROLLER_ROLE_CAPABILITY_MISSING`.

Use `@mobile-orchestrator` only when the request is ambiguous or the user does
not know which workflow applies. It classifies intent and delegates once; it
never controls workflow execution. For example:

```text
@mobile-orchestrator I need to implement a Figma design, but I do not know whether it is a view or a reusable component.
```

Do not invoke `@mobile-orchestrator` in addition to an explicit entry-agent
command. For example, use `@ds-orchestrator /new-view`, not both agents.

## Summary

| Workflow | Entry Agent | Spec Level | Use When | Figma MCP |
|---|---|---:|---|---|
| `/bootstrap-workspace` | `@workspace-discovery` | bootstrap | Discover workspace topology and create `.sopp/config` files. | No |
| `/new-component` | `@ds-orchestrator` | mini | Create or update a reusable Design System component from Figma. | Required |
| `/new-view` | `@ds-orchestrator` | standard | Build an app screen that composes DS components. | Required |
| `/new-feature` | `@feature-builder` | full | Build domain, data, presentation, wiring and mandatory tests. | Optional when Figma is supplied. |
| `/refactor-component` | `@ds-orchestrator` | mini | Refactor an existing DS component. | No |
| `/refactor-feature` | `@refactoring-advisor` | full | Refactor an existing feature across layers. | No |
| `/test-plan` | `@test-coverage-engineer` | full | Generate or improve tests for an existing feature. | No |
| `/fix-pr-comments` | `@ds-orchestrator` | mini | Resolve accessible PR review comments. | No |

## Evidence Mode

Every workflow accepts `evidence_mode: <minimal|standard>` as an optional
parameter. It defaults to `minimal`, which preserves all gates and stores
compact phase results in the packet. Use `standard` only when detailed phase
reports are needed for investigation, audit or handoff outside the pipeline.
`/bootstrap-workspace` follows its existing uppercase input convention:
`EVIDENCE_MODE: <minimal|standard>`.

```text
evidence_mode: <minimal|standard>  # optional, default minimal
```

## `/bootstrap-workspace`

Purpose: discover app, Design System, core packages, topology and initial
configuration files.

| Parameter | Required | Expected Value |
|---|---:|---|
| `WORKSPACE_ROOT` | Yes | Absolute path to the IDE/workspace root. |
| `WORKSPACE_FILE` | No | Absolute path to `.code-workspace` when available. |
| `EXPECTED_APP_REPO_ROOT` | No, recommended | Absolute path to the app repository that will own `.sopp/config`. |
| `EXPECTED_APP_PACKAGE` | No | App package name when known. |
| `EXPECTED_DS_PACKAGE` | No | Design System package name when known. |
| `EXPECTED_CORE_PACKAGE` | No | Shared core package name when known. |
| `EXPECTED_REPO_MODE` | No | `single_repo`, `monorepo_melos` or `multi_repo`. |
| `APPLY_MODE` | No | `propose_then_apply` by default. |
| `FORCE_RECONFIGURE` | No | `false` by default. Set `true` only for an explicit migration or repair proposal. |

```text
@workspace-discovery /bootstrap-workspace
WORKSPACE_ROOT: <absolute/path/to/workspace>                 # required
WORKSPACE_FILE: <absolute/path/to/workspace.code-workspace>  # optional
EXPECTED_APP_REPO_ROOT: <absolute/path/to/app-repo>          # optional, recommended
EXPECTED_APP_PACKAGE: <app_package_name>                     # optional
EXPECTED_DS_PACKAGE: <design_system_package_name>            # optional
EXPECTED_CORE_PACKAGE: <core_package_name>                   # optional
EXPECTED_REPO_MODE: <single_repo|monorepo_melos|multi_repo>  # optional
APPLY_MODE: propose_then_apply                              # optional
FORCE_RECONFIGURE: false                                    # optional; explicit repair/migration only
```

When a valid final `.sopp/config` triplet already exists for the resolved app
repository, bootstrap returns `reused_existing_config` and creates no proposal.
When the triplet is partial or invalid, it blocks instead of replacing it. Run
again with `FORCE_RECONFIGURE: true` only after reviewing the diagnosis.

Expected proposal:

```text
<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/
├── bootstrap-spec.yaml
├── context.json
├── review.md
├── proposed/project.config.yaml
├── proposed/architecture-contract.yaml
├── proposed/dependencies-contract.yaml
└── evidence/
```

Expected applied result after approval:

```text
<APP_REPO_ROOT>/.sopp/config/project.config.yaml
<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml
<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml
```

## `/new-component`

Purpose: create or update a reusable Design System atom, molecule or organism
from Figma.

| Parameter | Required | Expected Value |
|---|---:|---|
| `component_name` | Yes | Snake case component name, usually with DS intent but without file extension. |
| `figma_url` | Yes | Figma URL with file key and node id. |
| `user_story` | No | Inline acceptance context or short user need. |
| `user_story_path` | No | Markdown file with acceptance criteria or DoD. |
| `atomic_hint` | No | `atom`, `molecule` or `organism` when the level is already known. |
| `golden_tests` | No | Boolean, default `false`. Runs DS golden tests only when `true`. |

```text
@ds-orchestrator /new-component
component_name: <ds_component_name>                         # required, e.g. ds_status_badge
figma_url: <https://www.figma.com/file/...?...node-id=...>  # required
user_story: <short acceptance context>                      # optional
user_story_path: <docs/user-stories/story-123.md>           # optional
atomic_hint: <atom|molecule|organism>                       # optional
golden_tests: <true|false>                                  # optional, default false
```

Expected result: DS source files, tests, optional goldens, Widgetbook use case,
audit evidence and delivery summary under the `design_system` target.

## `/new-view`

Purpose: generate an app screen/view from Figma, including DS/App separation.

| Parameter | Required | Expected Value |
|---|---:|---|
| `view_name` | Yes | Snake case view name. |
| `figma_url` | Yes | Figma URL with file key and node id. |
| `user_story` | Yes | Inline user story or acceptance criteria. |
| `user_story_path` | No | Markdown file with acceptance criteria or DoD. |
| `route_name` | No | Existing or proposed route name/path. |
| `target_id` | No | App target id. Defaults to `active_target_defaults.app_target_id`, then `active_target_defaults.app`. |
| `project_root` | No | Absolute app repository root when the IDE opens a multi-root workspace. |
| `golden_tests` | No | Boolean, default `false`. Runs DS and complete-view goldens only when `true`. |
| `evidence_mode` | No | `minimal` by default; `standard` keeps detailed phase reports. |

```text
@ds-orchestrator /new-view
view_name: <view_name>                                      # required, e.g. product_catalog_view
figma_url: <https://www.figma.com/file/...?...node-id=...>  # required
user_story: <user story or acceptance criteria>             # required
user_story_path: <docs/user-stories/story-123.md>           # optional
route_name: <route name or path>                            # optional
target_id: <app_target_id>                                  # optional; must resolve to kind app
project_root: <absolute/path/to/app-repo>                    # optional; needed only for multi-root ambiguity
golden_tests: <true|false>                                  # optional, default false
evidence_mode: <minimal|standard>                            # optional, default minimal
```

Expected result: app view code, DS component inventory, DS artifacts when
needed, mandatory widget tests, optional goldens, Widgetbook screen use case
when configured, audit evidence and delivery summary. When goldens are
disabled, the packet records `golden_tests: skipped_by_input`. The app-view
checkpoint also requires `evidence/figma-fidelity-report.json` with exact
text/hierarchy/assets/typography/shape checks and the `1 dp` / `2%` / `4%`
tolerances.

The Spec Packet, evidence and pipeline reports are always created under the
resolved app target. DS phases may write planned DS artifacts in a separate
target, but they must not move packet state away from the app.

Before creating a packet, `/new-view` resolves and validates exactly one
canonical `.sopp/config` triplet. It never runs bootstrap automatically. A
missing, partial, invalid, ambiguous, or legacy-only configuration ends as
`blocked_input` with a configuration code and no YAML proposal.

The initial invocation is plan-only: it creates and completes the Spec Packet,
then presents `review.md` in Spanish and stops. No Flutter code or tests may be
generated in that response. Approve the named pending packet in a later turn
to allow Phase 3 and later phases to resume.

Before that approval, the plan must reconcile every visible Figma asset, icon,
text style, screen-chrome decision, hierarchy/order and geometry in
`visual_manifest` plus `layout_manifest`. Every visible
icon, image, illustration and logo is downloaded from Figma MCP into the
packet `source-assets/figma/` archive with its node id, format and SHA-256;
the implementation copies that source without replacement. Cropped SVG/image
sources are retained as reusable assets and rendered with an
`explicit_clip_transform`; the workflow must not export a containing frame as
a flattened substitute. A DS icon is permitted only when it is an exact
declared match and its Figma source export remains archived. Otherwise the
archived Figma SVG is used. Typography must resolve the exact Figma family and
weight to a registered project font; a close fallback blocks the run. When Figma displays
bottom navigation, the plan determines whether an existing app shell provides
it, this view owns it, or it is not part of the target view.

After app-view code generation, `/new-view` performs an app-view audit and a
required human checkpoint. It always writes
`evidence/figma-fidelity-report.json` from the canonical Figma screenshot and
a deterministic Flutter rendering at the manifest viewport. Text, hierarchy,
assets, typography and declared shape values must match exactly; geometry may
differ by at most `1 dp`, global pixels by `2%`, and regional pixels by `4%`.

Use the explicit `@ds-orchestrator /new-view` form shown above. A bare
`/new-view` is not the canonical invocation and must not start implementation.

## `/new-feature`

Purpose: generate a complete feature across domain, data, presentation, wiring
and mandatory automated tests. Golden tests and project documentation are
opt-in to control AI token consumption.

You must provide `feature_name` and `description`, plus one of these input
strategies:

1. `api_contract`, or
2. manual `entity_name` + `fields`.

| Parameter | Required | Expected Value |
|---|---:|---|
| `feature_name` | Yes | Snake case feature name. |
| `description` | Yes | One to three sentences describing the feature. |
| `api_contract` | Conditional | File path, URL, inline OpenAPI/GraphQL/JSON/cURL, or manual endpoint list. |
| `entity_name` | Conditional | Required only when `api_contract` is not provided. |
| `fields` | Conditional | Required only when `api_contract` is not provided. |
| `api_endpoints` | No | Manual endpoints when there is no formal API contract. |
| `user_story` | No | Inline user story, acceptance criteria or path to a Markdown file. |
| `figma_url` | No | Figma URL; triggers Figma MCP preflight and DS inventory. |
| `figma_scope` | No | `view` (default when `figma_url` is present) runs the shared screen-fidelity gate; `component_inventory` performs only the DS inventory. |
| `ui_components` | No | Existing or expected DS components when there is no Figma URL. |
| `sequence_diagram` | No | Mermaid file path or inline Mermaid sequence diagram. |
| `target_location` | No | `app_folder` or `melos_package`. |
| `package_name` | Conditional | Required when `target_location: melos_package` creates or targets a package. |
| `workspace_root` | Conditional | Required when `target_location: melos_package` and the workspace is ambiguous. |
| `golden_tests` | No | Boolean, default `false`. Runs feature golden tests only when `true`. |
| `documentation` | No | Boolean, default `false`. Updates project documentation only when `true`. |

When `figma_url` is present, `figma_scope` defaults to `view`. This runs the
same screen-fidelity planning and Presentation checkpoint used by `/new-view`:
Figma assets, `visual_manifest`, `layout_manifest`, exact text/order and the
compact fidelity report. Select `component_inventory` only when the Figma link
is not a screen that the feature must render; it avoids the screen comparison
and retains only the DS-inventory analysis.

With API contract:

```text
@feature-builder /new-feature
feature_name: <feature_name>                                # required, e.g. product_catalog
description: <short feature description>                    # required
api_contract: <path|url|inline contract>                    # required for this strategy
user_story: <story text or docs/user-stories/story-123.md>  # optional
figma_url: <https://www.figma.com/file/...?...node-id=...>  # optional
figma_scope: <view|component_inventory>                     # optional; default view with figma_url
ui_components: <DSComponentA, DSComponentB>                 # optional
sequence_diagram: <docs/diagrams/feature_flow.mmd>          # optional
target_location: <app_folder|melos_package>                 # optional, default app_folder
package_name: <package_name>                                # conditional
workspace_root: <absolute/path/to/workspace>                # conditional
golden_tests: <true|false>                                  # optional, default false
documentation: <true|false>                                # optional, default false
```

Without API contract:

```text
@feature-builder /new-feature
feature_name: <feature_name>                                # required
description: <short feature description>                    # required
entity_name: <DomainEntityName>                             # required without api_contract
fields:                                                     # required without api_contract
  - <fieldName>: <DartType>
  - <fieldName>: <DartType?>
api_endpoints:                                              # optional
  - GET /<resource> -> List<<DomainEntityName>>
  - GET /<resource>/{id} -> <DomainEntityName>
user_story: <story text or docs/user-stories/story-123.md>  # optional
figma_url: <https://www.figma.com/file/...?...node-id=...>  # optional
figma_scope: <view|component_inventory>                     # optional; default view with figma_url
ui_components: <DSComponentA, DSComponentB>                 # optional
sequence_diagram: <docs/diagrams/feature_flow.mmd>          # optional
golden_tests: <true|false>                                  # optional, default false
documentation: <true|false>                                # optional, default false
```

Expected result: domain entities, use cases, repository contracts, DTOs, data
sources, repository implementation, presentation state, page/UI model,
DI/routing notes, passed unit/widget/integration tests, audit evidence and a
final delivery summary. When requested, it also includes passed golden tests
and updated project documentation. A missing or failed mandatory test blocks
audit completion and delivery; optional stages are recorded as
`skipped_by_input` when disabled.

The `feature-builder` always owns the required unit, widget and integration
test outcomes. It uses `@test-engineer` when the active tool surface can
delegate; otherwise it executes that role contract directly. The three stages
keep their order and evidence requirements in either mode.

### `/new-feature` approval and revision flow

`/new-feature` always uses the same executable sequence; there is no fast mode
that removes checkpoints:

```text
initial spec approval
→ Domain → human checkpoint
→ Data → human checkpoint
→ Presentation → human checkpoint
→ Wiring → mandatory tests → audit → delivery
```

Before showing the initial review, `feature-builder` runs `sopp_gate.rb
open-initial`, presents the spec hash and challenge, and stops. Before each
layer it runs `can-enter`; after each layer it generates the corresponding
evidence and runs `open-checkpoint`. The next layer cannot begin until a later
human turn repeats the challenge and approves the reviewed artifact hash.

If a layer is not satisfactory, describe the desired change instead of
approving it. The controller records the request without modifying code and
returns a bounded proposal such as:

```text
Domain adjustment proposal — revision 1
- Change ReviewsQuery pagination contract.
- Update ReviewsRepository and LoadReviewsUseCase.
- Update four Domain tests.
- Earliest affected layer: Domain.
```

After the developer authorizes that proposal in a later turn, the controller
applies only its declared scope, regenerates evidence and asks for a fresh
approval. If feedback during Presentation requires a Domain change, Domain,
Data and Presentation approvals become `stale` and those gates are replayed in
order. Questions and ambiguous comments leave the current checkpoint pending.

The gate and revision records are local deterministic operations and consume
no AI tokens. Human checkpoint messages remain compact and refer to packet
files instead of repeating the full spec or generated code.

## `/refactor-component`

Purpose: refactor an existing Design System component while preserving behavior
and visual contracts.

| Parameter | Required | Expected Value |
|---|---:|---|
| `component_path` | Yes | Path to the DS component file or component folder. |
| `refactor_goal` | No, recommended | Desired improvement or constraint. |
| `compatibility_policy` | No | `additive_only`, `no_public_api_change` or `allow_public_api_change`. |

```text
@ds-orchestrator /refactor-component
component_path: <lib/src/.../component_file.dart>           # required
refactor_goal: <what should improve and why>                # optional, recommended
compatibility_policy: <additive_only|no_public_api_change|allow_public_api_change> # optional
```

Expected result: approved refactor plan, scoped code changes, updated
tests/goldens when needed, audit evidence and delivery summary.

## `/refactor-feature`

Purpose: refactor an existing feature across architecture layers.

| Parameter | Required | Expected Value |
|---|---:|---|
| `feature_name` | Yes | Snake case feature name. |
| `feature_path` | Yes | Path to feature source folder. |
| `refactor_goal` | Yes | Refactor intent. |
| `constraints` | No | Constraints such as route/API compatibility. |
| `user_story` | No | Inline acceptance criteria or Markdown path. |
| `target_location` | No | `same` or `melos_package`. |
| `package_name` | Conditional | Required for package extraction. |
| `sequence_diagram` | No | Mermaid file path or inline Mermaid sequence diagram. |
| `api_contract` | No | API change/addition to fold into the refactor. |
| `can_delete_files` | No | `true` only when delete actions are explicitly approved. |

```text
@refactoring-advisor /refactor-feature
feature_name: <feature_name>                                # required
feature_path: <lib/src/features/feature_name>               # required
refactor_goal: <refactor intent>                            # required
constraints: <constraints that must remain true>            # optional
user_story: <story text or docs/user-stories/story-123.md>  # optional
target_location: <same|melos_package>                       # optional, default same
package_name: <package_name>                                # conditional
sequence_diagram: <docs/diagrams/feature_flow.mmd>          # optional
api_contract: <inline endpoint changes or contract path>    # optional
can_delete_files: <true|false>                              # optional, default false
```

Expected result: risk analysis, approved refactor plan, layer-by-layer changes,
tests, docs artifact and audit report. Delete operations require explicit
`can_delete_files: true`, an `action: delete` artifact and human approval.

## `/test-plan`

Purpose: analyze an existing feature and generate or improve test coverage.

| Parameter | Required | Expected Value |
|---|---:|---|
| `feature_name` | Yes | Snake case feature name. |
| `feature_path` | Yes | Path to feature source folder. |
| `scope` | No | `full`, `domain`, `data` or `presentation`. |
| `focus` | No | Comma-separated files, classes or flows to prioritize. |
| `topology` | No | `single_repo`, `monorepo_melos` or `multi_repo` when useful. |
| `target_id` | No | Target id when not resolved from `feature_path`. |
| `target_root` | No | Target package/root path when topology is ambiguous. |

```text
@test-coverage-engineer /test-plan
feature_name: <feature_name>                                # required
feature_path: <lib/src/features/feature_name>               # required
scope: <full|domain|data|presentation>                      # optional, default full
focus: <file_or_flow_1, file_or_flow_2>                     # optional
topology: <single_repo|monorepo_melos|multi_repo>           # optional
target_id: <target_id>                                      # optional
target_root: <path/to/package-or-target-root>               # optional
```

Expected result: coverage plan, generated tests where allowed, command/evidence
summaries, known gaps and a docs/testing artifact.

## `/fix-pr-comments`

Purpose: address review comments without expanding scope.

| Parameter | Required | Expected Value |
|---|---:|---|
| `pr_comments_source.kind` | Yes | `pr_url`, `inline`, `exported_file` or `integration`. |
| `pr_comments_source.value` | Yes | PR URL, inline comments, exported file path or integration id. |
| `pr_comments_source.access_status` | Yes | `pending`, `available` or `blocked_input`. |
| `pr_id` | No | PR number or identifier used for the spec packet slug. |
| `target_branch` | No | Target branch if relevant to the review. |
| `allow_git_commands` | No | `true` only when git execution is explicitly allowed. |
| `allow_gh_commands` | No | `true` only when GitHub CLI execution is explicitly allowed. |

```text
@ds-orchestrator /fix-pr-comments
pr_comments_source:
  kind: <pr_url|inline|exported_file|integration>           # required
  value: <url|inline comments|path/to/comments.md|id>       # required
  access_status: available                                  # required
pr_id: <123>                                                # optional
target_branch: <branch_name>                                # optional
allow_git_commands: false                                   # optional, default false
allow_gh_commands: false                                    # optional, default false
```

Expected result: comment inventory, approved fix plan, scoped code/test/doc
changes, audit evidence and delivery summary. The workflow does not run `git`
or `gh` unless explicit permissions are granted.

## Compact Handoff Shape

Agent-to-agent handoffs must stay compact and file-reference based:

```yaml
spec_ref: "{SPEC_PACKET_PATH}/spec.yaml"
context_ref: "{SPEC_PACKET_PATH}/context.json"
phase: "data_layer"
read_sections:
  - contracts.api
  - artifact_plan.planned[group=data]
  - success_criteria
expected_outputs:
  - evidence/data-validation.md
```

Agents must read only the listed sections and write only approved artifacts.
