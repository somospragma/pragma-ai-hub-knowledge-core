---
id: delivery-review
version: 1.0.0
scope: chapter
type: prompt
chapter: mobile
description: Prompt for the final delivery phase. Use when implementation and testing are complete and delivery documentation must be prepared.
---
# Delivery And Final Review

## Reference Skills

- flutter-ds-folder-structure
- flutter-ds-naming-conventions
- flutter-ds-markdown-docs
- flutter-ds-lint-rules
- commit-conventions
- changelog-management

## Minimum Required Context

1. `workflow`.
2. `project_root`.
3. `topology`.
4. `target`.
5. `execution_context`.
6. `PIPELINE_SPEC_PATH`.
7. `PIPELINE_LOG_PATH`.
8. `spec_context` when the workflow uses Mobile Spec Packet.

If context is missing, return `blocked_input`.

## Instruction

After testing is complete, prepare the final delivery for the component or view.

## SDD Contract

When `spec_context` exists, validate `spec_ref`, verify that delivered
artifacts are declared in `artifact_plan` or approved in `context_ref`, record
`{SPEC_PACKET_PATH}/evidence/delivery-report.md`, and use `PIPELINE_SPEC_PATH`
only as the human report.

## Process

### 1. Structure Review

- Verify file location against `flutter-ds-folder-structure`.
- Confirm that new/modified production code lives under `lib/src`, except
  `lib/main*.dart` entrypoints and public `lib/<package>.dart` barrels.
- Validate naming conventions.
- Validate barrel files.
- Validate that external consumers use public barrels and not
  `package:<package>/src/...`.
- In `/new-view`, do not export app views in the DS barrel.

### 2. Scope Validation

- Confirm that changes belong to `target.target_root`.
- In `monorepo_melos`, confirm that no packages outside `target.package_path`
  were modified.

### 3. Documentation

- Verify the code comment policy:
  - no inline, block, or Dartdoc comments by default
  - exceptions only when they are fundamental and justified
- Generate README when applicable.

### 4. Branch And Commits

- DS branch: `naming.branch_prefix`.
- View branch: `naming.view_branch_prefix` (fallback `naming.branch_prefix`).
- Commits follow Conventional Commits.

### 5. PR

Include:

- user story
- Figma reference
- inventory file
- test summary
- DoD checklist

### 6. Final Report

```markdown
## Delivery Report

### Execution Context
- **Repo mode**: ...
- **Target package**: ...
- **Target root**: ...
- **Melos scope**: ...

### Summary
- **Branch**: ...
- **PR**: ...
- **Created/modified files**: ...
- **Tests**: ...
- **Audit**: ...

### Acceptance Criteria
- [x] ...
```

## Final Verification (topology-aware)

### `single_repo` or `multi_repo`

```bash
flutter analyze
flutter test
flutter test --tags golden
dart run build_runner build --delete-conflicting-outputs
```

### `monorepo_melos`

```bash
melos exec --scope={target_scope} -- flutter analyze
melos exec --scope={target_scope} -- flutter test
melos exec --scope={target_scope} -- flutter test --tags golden
melos exec --scope={target_scope} -- dart run build_runner build --delete-conflicting-outputs
```
