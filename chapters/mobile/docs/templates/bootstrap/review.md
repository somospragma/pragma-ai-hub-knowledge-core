# Bootstrap Proposal

## Detected Topology

- Mode: `{{REPO_MODE}}`
- App repo: `{{APP_REPO_ROOT}}`

## Detected Targets

{{TARGET_REGISTRY_SUMMARY}}

## Proposed Files

- `proposed/project.config.yaml`
- `proposed/architecture-contract.yaml`
- `proposed/dependencies-contract.yaml`

## Ownership

- `project.config.yaml`: workspace roots, target registry, physical topology, target structure, pipeline, naming, tokens, testing.
- `architecture-contract.yaml`: layer rules, generation policies, constraints, and domain/data contracts.
- `dependencies-contract.yaml`: dependency catalog, imports, `target_id`, and allowed matrix.

## Alerts

{{ALERTS}}

## Required Action

Reply `approve apply` to write final configuration with backup.
