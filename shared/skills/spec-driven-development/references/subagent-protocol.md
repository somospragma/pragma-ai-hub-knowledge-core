# Subagent Context Protocol

**The problem**: Subagents run in isolated context windows — they have no memory of
the parent conversation. Without explicit context passing, they start from scratch
and lose everything agreed in previous phases.

**The solution**: After every approval gate, write state to `context.json` on disk
and emit a **Subagent Handoff Block** in the conversation. Subagents read the disk
files to resume exactly where the workflow left off.

---

## Subagent Handoff Block

Emit this block verbatim after each approval gate, before handing off to a subagent
or moving to the next phase. Adjust the status icons to match the real state in
`context.json` at the moment of emission.

```
## 🗂 Spec Context — {feature_name}

Spec folder : .specs/{feature_name}/
Context file: .specs/{feature_name}/context.json

Phase status:
  ✅ Requirements : approved  → .specs/{feature_name}/requirements.md
  ⏳ Design       : in_progress → .specs/{feature_name}/design.md
  ⬜ Tasks        : not_started
  ⬜ Execution    : not_started

Resume instruction for subagents:
  1. Read `.specs/{feature_name}/context.json` to check current phase and approvals.
  2. Read every ✅ approved file listed above for full context.
  3. Continue from the first ⏳ or ⬜ phase. Do NOT re-do approved phases.
  4. Follow the spec-driven-development workflow from that point forward.
```

Icons: `✅` approved · `⏳` in_progress · `⬜` not_started

---

## Execution Orchestrator Handoff Block

Emit this block when Phase 3 (Tasks) is approved and Phase 4 (Execution) begins.
The Orchestrator reads this to bootstrap the execution wave plan.

```
## 🚀 Execution Handoff — {feature_name}

Spec folder  : .specs/{feature_name}/
Context file : .specs/{feature_name}/context.json

All spec phases approved:
  ✅ Requirements → .specs/{feature_name}/requirements.md
  ✅ Design       → .specs/{feature_name}/design.md
  ✅ Tasks        → .specs/{feature_name}/tasks.md

Orchestrator instructions:
  1. Read context.json — verify phases.requirements, design, and tasks are all "approved".
  2. Read requirements.md, design.md, and tasks.md in full.
  3. Extract execution units from tasks.md dependency DAG.
  4. Build execution waves (groups of parallel-safe units).
  5. Write wave plan to context.json under "execution".
  6. Present wave plan to user for confirmation.
  7. On user ✅: emit one Unit Executor Handoff Block per unit in Wave 1.
  8. After each wave completes: emit handoff blocks for the next wave.

Agent file: agents/sdd-execution-orchestrator.agent.md
```

---

## Unit Executor Handoff Block

Emit one block per unit when launching Unit Executor agents. Units in the same wave
can be launched simultaneously (parallel agents).

```
## 📦 Unit Executor Handoff — {unit_name} (Wave {wave})

Feature      : {feature_name}
Unit         : {unit_name}
Spec folder  : .specs/{feature_name}/
Wave         : {wave}
Depends on   : {comma-separated list of upstream units, or "none"}

Assigned tasks:
  - {task_id}: {task_title}
  - ...

ai-dlc stages to run (in order):
  1. {stage_1}  →  aidlc-docs/construction/{unit_name}/{stage_1}/
  2. {stage_2}  →  aidlc-docs/construction/{unit_name}/{stage_2}/
  ...
  N. code_generation  →  workspace root (application code)

Spec inputs:
  - Requirements : .specs/{feature_name}/requirements.md  ✅
  - Design       : .specs/{feature_name}/design.md        ✅
  - Tasks        : .specs/{feature_name}/tasks.md         ✅ (filter to assigned tasks only)

Agent file: agents/sdd-unit-executor.agent.md
```

---

## How Subagents Resume the Workflow

When a subagent is invoked, it **must always** do:

1. **Check for existing context**: Look for `.specs/*/context.json` in the CWD.
   - If found → read it, load all approved spec files, continue from `current_phase`.
   - If not found → start from Phase 1 (gather requirements).

2. **Load approved files into working memory**: Read every file whose `status = "approved"`
   before generating any output. This prevents contradicting already-approved decisions.

3. **Announce resume state**: At the start of the response, tell the user:
   ```
   📂 Resuming spec for `{feature_name}` — Phase {N} ({phase_name})
   Requirements: ✅ approved | Design: ⏳ in progress | Tasks: ⬜ pending | Execution: ⬜ pending
   ```

4. **Never re-open approved phases** unless the user explicitly asks to revise them.

---

## context.json Lifecycle

| Event | What to write |
|---|---|
| Phase 1 starts | Create file; `current_phase = "requirements"`, `phases.requirements.status = "in_progress"` |
| Requirements approved | `phases.requirements.status = "approved"`, `approved_at = <now>`, `current_phase = "design"` |
| Phase 2 starts | `phases.design.status = "in_progress"` |
| Design approved | `phases.design.status = "approved"`, `approved_at = <now>`, `current_phase = "tasks"` |
| Phase 3 starts | `phases.tasks.status = "in_progress"` |
| Tasks approved | `phases.tasks.status = "approved"`, `approved_at = <now>`, `current_phase = "execution"` |
| Execution plan written | `execution.status = "in_progress"`, `execution.waves = [...]`, `execution.units = [...]` |
| Unit starts | `execution.units[unit_name].status = "in_progress"` |
| Unit completes | `execution.units[unit_name].status = "complete"`, append to `execution.completed_units` |
| All units complete | `execution.status = "complete"`, `execution.approved_at = <now>`, `current_phase = "complete"` |

Always update `updated_at` on every write.

If `project_context` information is available (from the `project-context-selector` skill
or the user), populate `project_context.root_path`, `build_system`, and `main_language`
when creating the file.
