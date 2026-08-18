# Kiro Agent Profiles

The Mobile chapter declares Kiro-native execution profiles in each source
agent's YAML frontmatter. The renderer must preserve those fields when it
exports `*.agent.md` files under `.kiro/agents/`.

This is a capability contract, not workflow state. Runtime configuration,
approvals, evidence and Spec Packets remain under the resolved project's
`.sopp/` directory.

## Identity

Every agent declares a canonical `name` equal to its source agent id. Kiro uses
that field to identify an explicitly named agent, independently of the exported
filename. For example, an exported file named
`workspace-discovery.agent.md` with `name: workspace-discovery` is invoked as
`@workspace-discovery`; it does not need to be renamed to
`workspace-discovery.agent`.

## Capability Model

All profiles grant `read`. Write and shell permissions are limited to the role
contract. Figma access is granted only to `figma-analyzer`, `ds-orchestrator`
and `feature-builder`, through both `@figma` and `figma/*` MCP permission.

Only workflow controllers may use native delegation:

| Controller | Approved subagents |
|---|---|
| `mobile-orchestrator` | `workspace-discovery`, `ds-orchestrator`, `feature-builder`, `refactoring-advisor`, `test-coverage-engineer` |
| `feature-builder` | `figma-analyzer`, `ds-orchestrator`, `test-engineer`, `golden-test-engineer`, `code-auditor`, `delivery-manager` |
| `ds-orchestrator` | `figma-analyzer`, planning, architecture, implementation, test, audit and delivery specialists required by DS workflows |
| `refactoring-advisor` | `code-auditor`, `ds-orchestrator` |

The `subagent` permission rule, `availableAgents` and `trustedAgents` carry
the same list. Specialist profiles do not register subagents. This avoids a
delegation permission being inferred from a mere `@agent` reference.

## Skill Resources

Kiro custom agents load Skills only when the agent declares them as
`resources`. Every specialist therefore lists its exact `Active Skills` using
the exported Skill id:

```yaml
resources:
  - skill://flutter-clean-feature
  - skill://mobile-sdd-spec-validation
```

The `resources` list and the readable `## Active Skills` section must remain
identical. Do not use a wildcard for all chapter Skills: Kiro receives their
metadata at startup, so an exact list limits irrelevant discovery context and
avoids accidental activation. Kiro loads a Skill's full instructions only when
it becomes relevant.

Every exported `.kiro/skills/<id>/SKILL.md` must declare `name: <id>` and a
non-empty `description`; these are required for Kiro Skill discovery.

`workspace-discovery` declares only `mobile-sdd-spec-validation` and
`flutter-melos-management`. The first governs its deterministic packet and
SOPP validation; the second is necessary to identify legacy and modern Melos
workspaces. It intentionally excludes feature, architecture and UI-generation
Skills because bootstrap configures topology rather than implementing product
code.

## Portable Paths

Profiles never grant a blanket workspace write. Paths are relative glob
patterns so the same profile supports a single repository, a package in a
Melos workspace, a modular application, or a multi-root workspace:

- `.sopp/**` permits the resolved project root.
- `**/.sopp/**` permits a nested project root selected by the packet target.
- Product roles add only their relevant paths, such as `**/lib/**`,
  `**/test/**`, `**/assets/**` or `**/docs/**`.

The exact artifact target still comes from the approved Spec Packet and is
checked by the existing SOPP gate. A broad filesystem permission is never a
substitute for an approved `artifact_plan`.

## Persistence And Cost

A response returned by a subagent is not completion. The controller requires
the existing SOPP gate to find the planned files and evidence on disk before a
phase or checkpoint succeeds.

`docs/scripts/validate_mobile_kb.rb` checks the entire profile matrix,
canonical names, Figma access, delegation registration, portable `.sopp`
boundaries, Kiro Skill metadata and the exact agent-to-Skill mapping. This is
local static validation; it does not invoke an LLM or add runtime token/AI-credit
usage.

Run it after changing an agent profile:

```bash
ruby docs/scripts/validate_mobile_kb.rb
```
