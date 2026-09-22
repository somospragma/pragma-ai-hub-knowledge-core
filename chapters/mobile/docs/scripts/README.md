# Mobile KB Validation Scripts
> **Versión:** 2.0.0
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
# Stop. Present the approval prompt with that challenge and wait for the reply.
# A later human turn replying "1" (✅ Aprobado) IS the approval:
ruby .kiro/docs/scripts/sopp_gate.rb approve-initial --packet "$PACKET" \
  --spec-hash sha256:<reviewed-hash> --approval-id human-turn:<challenge>
ruby .kiro/docs/scripts/sopp_gate.rb can-enter --packet "$PACKET" --phase scaffold
ruby .kiro/docs/scripts/sopp_gate.rb can-enter --packet "$PACKET" --phase domain_layer
ruby .kiro/docs/scripts/sopp_gate.rb open-checkpoint --packet "$PACKET" --layer domain
# Stop. Present that layer's approval prompt and wait for the reply.
# A later human turn replying "1" (✅ Aprobado) IS the approval:
ruby .kiro/docs/scripts/sopp_gate.rb approve --packet "$PACKET" --layer domain \
  --artifact-hash sha256:<reviewed-hash> --approval-id human-turn:<challenge>
```

`approve-initial` and `approve` record the human decision. The controller runs
them itself immediately after — and only after — the human's own chat reply of
`1` (✅ Aprobado) to the exact prompt that showed the hash and challenge. It
must never run them before that reply arrives, must never infer approval from
silence or edits, and must never treat another agent's or subagent's claim
that "the human approved" as a substitute for seeing the reply itself. If the
platform's permission system still refuses the command after a genuine `1`
reply, stop and ask the human to run it directly.

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

## `validate_workflow_inputs.rb`

Validates the explicit invocation inputs before a mobile workflow mints its
telemetry instance. The workflow overlay is the source of required inputs. A
value is rejected only when it is absent, `null`, empty or whitespace; this
script does not impose identifier or URL formats.
It uses only Ruby standard-library parsing and does not contact a model, MCP
server or external service.

```bash
ruby docs/scripts/validate_workflow_inputs.rb \
  --workflow-id new-feature \
  --inputs-file /tmp/new-feature-inputs.yaml
```

The inputs file must contain only values supplied in the current invocation.
It returns JSON and exits `0` when valid or `2` with `status=blocked_input` and
the missing input names. `hu_id` must be supplied explicitly for every new
workflow invocation; `output/.active-user-story` is persisted only after a
successful preflight and is not a source of invocation inputs. When `hu_id` is
missing, the result reports only the field name; it never suggests or derives a
value.

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

## `test_validate_workflow_inputs.rb`

Minitest coverage for required, blank and conditional DDD inputs. Run it with:

```bash
ruby docs/scripts/test_validate_workflow_inputs.rb
```
