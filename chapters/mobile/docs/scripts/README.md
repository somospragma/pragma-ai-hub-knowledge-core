# Mobile KB Validation Scripts

## `validate_mobile_kb.rb`

Local integrity checker for the mobile knowledge base. It is intentionally
lightweight and does not require CI.

Run the default validation:

```bash
ruby docs/scripts/validate_mobile_kb.rb
```

Default checks:

- YAML and JSON parseability.
- Legacy references and unstructured permission blocks.
- Agent, prompt and skill references.
- Workflow invocation and Kiro/Copilot distribution paths.
- Spec packet template consistency.
- Required agent permissions.
- Figma MCP preflight requirements.
- Bootstrap anti-drift requirements.
- Deterministic legacy and modern Melos workspace resolution.
- Documentation target permissions.
- **Workflow Response Contract integrity** — every workflow markdown must
  declare the `Workflow Execution Contract`, `Instructions to the executing
  agent` and `Response Contract Violations` sections, plus a per-phase
  Response Contract block, the Spanish approval prompt, and matching
  `pragma-ai workflow report` telemetry calls (`--status started` +
  terminal) whose `--step-id` and `--workflow-id` values resolve against
  the `Step IDs` table. Prevents runtime drift where a phase silently drops
  its telemetry contract.

Run the strict internal-language audit:

```bash
ruby docs/scripts/validate_mobile_kb.rb --strict-language
```

Strict language mode enforces the policy that internal KB assets are written in
English while human-facing review templates and user responses remain Spanish.
Use it during the English migration pass or before publishing a new mobile KB
version.

## `sopp_gate.rb`

Executable state machine for full Mobile Spec Packet approvals. It validates
schema references, evidence, artifact hashes, approval records and phase order.
It also owns the deterministic change-request loop; agents must not edit
approval fields in `context.json` directly.

Typical layer flow:

```bash
ruby .kiro/docs/scripts/sopp_gate.rb open-initial --packet "$PACKET"
# Stop. The human repeats the emitted approval challenge in a later turn.
ruby .kiro/docs/scripts/sopp_gate.rb approve-initial --packet "$PACKET" \
  --spec-hash sha256:<reviewed-hash> --approval-id human-turn:<challenge>
ruby .kiro/docs/scripts/sopp_gate.rb can-enter --packet "$PACKET" --phase domain_layer
ruby .kiro/docs/scripts/sopp_gate.rb open-checkpoint --packet "$PACKET" --layer domain
# Stop. A later human turn repeats the emitted challenge and approves the hash.
ruby .kiro/docs/scripts/sopp_gate.rb approve --packet "$PACKET" --layer domain \
  --artifact-hash sha256:<reviewed-hash> --approval-id human-turn:<challenge>
```

Change-request flow:

```bash
ruby .kiro/docs/scripts/sopp_gate.rb request-changes --packet "$PACKET" \
  --layer domain --message "<verbatim human request>"
ruby .kiro/docs/scripts/sopp_gate.rb propose-adjustment --packet "$PACKET" \
  --layer domain --proposal "$PACKET/revisions/domain/001/proposal.md"
# Stop. Apply only after a later human turn authorizes the proposal hash.
```

The command uses only Ruby standard-library packages and therefore does not
consume AI tokens. Target roots are resolved from `spec.target_roots` or the
nearest `.sopp/config/project.config.yaml`.

## `melos_workspace.rb`

Read-only resolver for Melos package targets. It accepts legacy Melos 6
`melos.yaml` and the Melos 7+ configuration in the root `pubspec.yaml`; an
absent `melos.yaml` is never a failure by itself.

```bash
ruby .github/docs/scripts/melos_workspace.rb resolve \
  --root "$MELOS_ROOT" \
  --package-path "$TARGET_PACKAGE_PATH"
```

The JSON result reports `config_source`, target membership and a package scope.
It exits with status 2 and a machine-readable error when the selected target is
not a valid Melos package. It does not contact the network, run `pub get`, or
require the `melos` executable.

## `test_validate_workflow_response_contract.rb`

Minitest suite for the workflow Response Contract validator helpers. It
exercises `workflow_step_ids_from_header`, `workflow_phase_sections`,
`workflow_bash_report_calls`, `workflow_response_contract_present?`,
`workflow_approval_prompt_present?` and `workflow_execute_now_before_started?`
against synthetic fixtures, plus a KB-integration test that runs
`validate_workflow_response_contract` against the real workflow markdowns and
fails if any finding is produced. Run it directly:

```bash
ruby chapters/mobile/docs/scripts/test_validate_workflow_response_contract.rb
```

Regression protection: whenever a workflow markdown is edited (or the
validator helpers are refactored), this suite locks in that the eight mobile
workflows continue to satisfy the Response Contract.
