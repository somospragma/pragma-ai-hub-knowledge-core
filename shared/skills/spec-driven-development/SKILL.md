---
id: spec-driven-development
version: 2.1.0
scope: global
type: skill
name: spec-driven-development
description: >
  Spec-Driven Development workflow: intercept every change request BEFORE any code is
  written — features, fixes, improvements, hotfixes, refactors, or modifications.
  Trigger on any signal of change: "feat", "fix", "hotfix", "mejora", "modificación",
  "refactor", "nueva funcionalidad", "llega un nuevo feat", "quiero agregar", "hay que
  implementar", "hay un bug", "necesito arreglar", "add support for", "agregar soporte",
  "implementa esto", "quiero que soporte", or any description of something to build,
  change, or fix. Also: planning, writing requirements/design docs, breaking tasks into
  subtasks. Guides through Requirements → Design → Tasks with human approval gates.
  Handles ambiguous requests via diagnostic gates. Technology-agnostic: delegates to
  implementation skills. INTERCEPTS before any code generator — when both apply,
  spec-driven-development goes first. Exception: user says "skip planning" or "just implement".
license: Complete terms in LICENSE.txt
metadata:
  category: productivity
---

# Spec-Driven Development Skill

> **Idioma / Language**: Este skill funciona en español e inglés. Los ejemplos de uso incluyen versiones en ambos idiomas.

---

## Table of Contents

1. [What is Spec-Driven Development?](#what-is-spec-driven-developmentelopment)
2. [When to Use This Skill](#when-to-use-this-skill)
3. [The Workflow: Three Phases](#the-workflow-three-phases)
   - [Phase 0: Complexity Assessment](#phase-0-complexity-assessment)
   - [Phase 1: Requirements](#phase-1-requirements)
   - [Phase 2: Design](#phase-2-design)
   - [Phase 3: Tasks](#phase-3-tasks)
   - [Phase 4: Execution (ai-dlc Integration)](#phase-4-execution-ai-dlc-integration)
4. [Handling Ambiguity & Vague Requests](#handling-ambiguity--vague-requests)
5. [Questioning Protocol](#questioning-protocol)
6. [Core Principles](#core-principles)
7. [Example Workflows](#example-workflows)
8. [Subagent Prompt Templates](#subagent-prompt-templates)
9. [Folder Structure](#folder-structure)
9. [Subagent Context Protocol](#subagent-context-protocol)
10. [Common Pitfalls](#common-pitfalls--how-to-avoid-them)
11. [Quick Checklist](#quick-checklist-am-i-using-this-skill-right)

---

## What is Spec-Driven Development?

Spec-Driven Development is a structured approach to planning and implementing features. The core idea: **align on requirements, design, and tasks *before* writing code**. This reduces rework, prevents misalignment, and gives AI coding agents clear guidance.

The workflow has three sequential phases, each with an approval gate:

1. **Requirements**: What are we building and why? (functional and non-functional)
2. **Design**: How will we build it? (architecture, technical decisions, data flow)
3. **Tasks**: What's the concrete execution plan? (atomic, checkable tasks)

This skill is **technology-agnostic**. It doesn't prescribe how to implement — that's delegated to other skills, agents, or your team's expertise. The spec just captures the *intent* and *constraints*.

## When to Use This Skill

Use this skill ALWAYS when:
- The user asks to "specify a new feature"
- The user says "I want to build..." followed by a description
- The user asks "How should I plan this feature?"
- The user needs to break down a feature into tasks
- The user wants to create a design document before coding
- The user is starting a new feature and wants a structured approach

**Note**: Don't wait for perfect clarity. This skill helps you *achieve* clarity through structured conversation.

### Priority Over Implementation Skills

When both this skill and an implementation skill (e.g. `mcp-tool-creator`, code generators, scaffolding tools) could apply to the same request, **this skill runs first — always**. The reason is simple: implementation skills generate code based on assumptions. This skill surfaces and validates those assumptions before any code is written, which is when course-correcting is cheapest.

Implementation skills are the **execution vehicle for Phase 3 Tasks** — they get invoked when you reach the "ready to implement" handoff, not as a shortcut around planning.

The only exception: the user explicitly says "just implement, skip the spec" or "no need for planning." In that case, hand off directly to the implementation skill.

---

## The Workflow: Three Phases

### Phase 0: Complexity Assessment

Before opening any spec file, classify the feature to select the execution mode:

**Assess these signals:**

| Signal | Weight |
|---|---|
| Involves a new module, service, or bounded domain | High complexity |
| Touches 3+ components or cross-cutting concerns | High complexity |
| Requires architectural decisions or new patterns | High complexity |
| Single file / single class change | Simple |
| CRUD operation on existing model | Simple |
| Minor UI tweak, label change, bug fix with clear scope | Simple |

**Decision rule:**

```
if (any High-complexity signal) → MULTI-AGENT MODE
else                            → SINGLE-AGENT MODE
```

### Execution Modes

> ⚠️ **The mode controls HOW the next phase is launched — not whether approval gates apply.**
> Approval gates are unconditional in both modes. Never self-approve or assume the user approved
> in order to produce "complete output." If there is no explicit user ✅, STOP.

- **⚡ SINGLE-AGENT MODE**: Used for simple tasks. The main agent handles all phases in the same conversation window, pausing at each approval gate for the user to respond.
- **🔀 MULTI-AGENT MODE**: Used for complex tasks. Employs a **Proposer-Critic loop** per phase using two dedicated agents:

| Agent | File | Responsibility |
|-------|------|---------------|
| Proposer | [`agents/sdd-proposer.agent.md`](agents/sdd-proposer.agent.md) | Draft the phase artifact — requirements, design, or tasks |
| Critic   | [`agents/sdd-critic.agent.md`](agents/sdd-critic.agent.md)     | Audit the draft for gaps, security risks, inconsistencies, and missing coverage |

**Loop per phase:**
1. **Gather context first** — before invoking the Proposer for Phase 1, ask the clarifying questions from Phase 1 Step 1 (existing architecture, integration points, constraints). This is the orchestrator's responsibility, not the Proposer's. Collect the user's answers, then proceed.
2. Invoke **Proposer** with the user description, clarifying answers, and any prior approved phases
3. Invoke **Critic** with the Proposer's draft — receives structured audit (✅ / ⚠️ / ❌ findings)
4. If Critic returns any ❌ Failures: Proposer incorporates fixes (one revision cycle max)
5. Present the refined, Critic-validated output to the user — they never see drafts or audit reports

**Announce the mode to the user before proceeding:**

> 🔀 **Running in multi-agent mode** — I'll launch a Proposer to draft the spec and a Critic to audit it for quality and risks before I present it to you.

or

> ⚡ **Running in single-agent mode** — This task is straightforward, so I'll handle it directly while still keeping the documentation in `.specs/{feature_name}/`.

---

### Phase 1: Requirements

**Goal**: Understand what we're building and why. What are the constraints?

**Your Steps**:

1. **Ask clarifying questions first** — regardless of execution mode (single-agent or multi-agent), ask at least 2–3 targeted questions before creating any files or launching any subagent. Focus on: existing architecture/system context, integration points, known constraints, and any open decisions. In MULTI-AGENT MODE this is especially critical — the orchestrator collects answers and passes them to the Proposer as enriched context.
2. **Check for ambiguity**: If the user is vague ("improve performance", "make it faster"), don't jump to Phase 1 yet. Instead, ask diagnostic questions to clarify the problem statement before creating specs.
3. Propose a feature name in `snake_case` (e.g., `user_authentication`, `payment_workflow`)
4. Create the spec folder structure: `.specs/{feature_name}/`
5. Copy the requirements template: `assets/requirements.md` → `.specs/{feature_name}/requirements.md`
6. Copy the context template: `assets/context.json` → `.specs/{feature_name}/context.json`; fill in `feature_name`, `spec_folder`, `created_at`, `updated_at`; set `phases.requirements.status = "in_progress"`
7. **Collaborate with the user** to capture:
   - Functional Requirements (RF): What behaviors must the system have?
   - Non-Functional Requirements (RNF): Quality attributes (performance, security, scalability)
   - Constraints: What limits are we operating within?
   - Assumptions: What are we assuming to be true?
   - Success Criteria: How do we know it's done?
   - Dependencies: What does this depend on?
8. Fill the requirements.md document incrementally, asking clarifying questions as you go
9. **Approval Gate** ✋ — STOP here regardless of mode. Show the user the requirements document and ask:
   > "Does this capture what you want to build? Any missing requirements, constraints, or open questions?"

   Wait for the user's explicit response before doing anything else.
   - Once the user confirms ✅:
     - Update `context.json`: `phases.requirements.status = "approved"`, `phases.requirements.approved_at = <now>`, `current_phase = "design"`, `updated_at = <now>`
     - Emit the **Subagent Handoff Block** (see *Subagent Context Protocol* section)
     - **If SUBAGENT MODE**: stop completely. The parent agent will launch a Phase 2 subagent using the prompt from *Subagent Prompt Templates* § Phase 2.
     - **If SINGLE-AGENT MODE**: continue to Phase 2 in this conversation window.
   - If the user requests changes ❌: iterate — update the document, show again, repeat the gate

**Conversation Tips**:
- Ask **"why"** for each requirement—it reveals hidden constraints
- Probe edge cases: "What happens if...?"
- Distinguish functional from non-functional early
- Surface dependencies explicitly
- Don't assume technology at this stage

**Example Trigger**:
```
User: "I want to add a referral system to the app"
Your response: "Perfect! Let's structure this with spec-driven development. 
I'll start with requirements—those are the behaviors and constraints we need to lock down.

Quick questions to clarify:
1. Do users earn rewards for successful referrals?
2. Can they see/track their referrals in real time?
3. Are there limits? (max referrals per user, cap on rewards?)
4. How do we verify someone was actually referred by a specific user?

Once we nail these down, I'll create a requirements document for your review."
```

---

### Phase 2: Design

**Goal**: Decide *how* we'll build it. Technical decisions, architecture, data flow.

**Your Steps**:

1. Once requirements are approved ✅, copy the design template: `assets/design.md` → `.specs/{feature_name}/design.md`; update `context.json`: `phases.design.status = "in_progress"`, `updated_at = <now>`
2. **Codebase Research**: If this is a brownfield project, explore:
   - Existing architectural patterns and conventions
   - How similar features are implemented
   - Affected components and systems
   - Any architectural constraints you should know about
3. **Schema lookup**: Before writing the Data Model section, check if `.specs/{feature_name}/` contains schema files (e.g. `inputSchema.json`, `outputSchema.json`, `schema.json`, `openapi.yaml`, or similar). If found, parse and render them — do NOT ask the user to re-share information that already exists in the spec folder.
4. **Keep it technology-agnostic**: The design should capture *intent* and *trade-offs*, not prescribe specific libraries/frameworks. Leave tech choices to the implementation phase.
5. Work with the user to document:
   - Architecture overview (text description or diagram)
   - Technical design decisions with rationale and trade-offs
   - Data model / contracts (how data flows through the system)
   - Affected components (what code areas change?)
   - Implementation approach (rough steps to build this)
   - Risks and how to mitigate them
   - Testing strategy
6. Complete the design.md document
7. **Approval Gate** ✋ — STOP here regardless of mode. Show the user the design and ask:
   > "Does this design direction make sense to you? Any concerns about the approach or alternative ideas?"

   Wait for the user's explicit response before doing anything else.
   - Once the user confirms ✅:
     - Update `context.json`: `phases.design.status = "approved"`, `phases.design.approved_at = <now>`, `current_phase = "tasks"`, `updated_at = <now>`
     - Emit the **Subagent Handoff Block**
     - **If SUBAGENT MODE**: stop completely. The parent agent will launch a Phase 3 subagent using the prompt from *Subagent Prompt Templates* § Phase 3.
     - **If SINGLE-AGENT MODE**: continue to Phase 3 in this conversation window.
   - If the user requests changes ❌: iterate — refine the design and show again

**Data Model rendering rules** (apply whenever input/output schemas exist):
- Render the **full tree** — never collapse or abbreviate nested objects with `{ field1, field2 }`. Every field gets its own line with indentation.
- Show **type** for every field using the target language's types (e.g. Java: `String`, `Integer`, `BigDecimal`, `Boolean`, `List<>`).
- Show **constraints** inline: `min=N max=N` and a representative `ex: value` when the schema provides one.
- Mark required vs. optional clearly: use `*` prefix for required fields, `°` for optional. Add a legend at the top: `` `*` = required | `°` = optional ``.
- For optional fields, note the nullability annotation (e.g. `@JsonInclude(NON_NULL)` in Java).
- If two schemas exist (input + output), render them as two separate trees with clear headers.

**Conversation Tips**:
- Explain *why* each design decision (don't just list options, explain the reasoning)
- Surface trade-offs: "We could do X (pros: ..., cons: ...) or Y (pros: ..., cons: ...)"
- Reference existing patterns in the codebase: "Based on how we did [similar feature], here's the pattern we'd follow"
- Don't over-engineer—keep it simple unless there's a good reason not to
- If designing something truly novel, acknowledge the exploration and propose an MVP approach

**Example Conversation**:
```
User: Approves requirements. Is the design ready?
Your response: "Great! I've outlined the design. Here's the approach:

**Decision**: We'll use an async queue system for processing notifications, rather than 
synchronous delivery. Why? It prevents blocking user actions, scales better, and isolates 
failures.

**Data Model**: Notification preferences live in a `user_notification_settings` table. 
When a user opts out of a type, we check that table before sending.

**Implementation**: Queue handler → Preference lookup → Send (async)

**Risk**: If preferences change while a message is queued, we might send unwanted 
notifications. Mitigation: Include preference snapshot in each queued message.

Does this approach fit with how you imagined it working?"
```

**When the user pushes back on the design:**

If the user says "I don't know the architecture yet" or "That's not how our system works," that's OK. This is a sign to:

1. Ask more clarifying questions about the codebase
2. Offer to do a quick codebase exploration (suggest using other skills/agents if needed)
3. Propose a simpler design and iterate

The spec should reflect *reality*, not wishful thinking.

---

### Phase 3: Tasks

**Goal**: Break the design into concrete, atomic, actionable tasks. Ready to implement.

**Your Steps**:

1. Once design is approved ✅, copy the tasks template: `assets/tasks.md` → `.specs/{feature_name}/tasks.md`; update `context.json`: `phases.tasks.status = "in_progress"`, `updated_at = <now>`
2. **Translate design into tasks**: Break down the design into discrete, atomic steps:
   - Each task should be completable in 1–8 hours (not days)
   - Each task should have a clear, testable outcome
   - Use clear, actionable language ("Create X", "Implement Y", "Write tests for Z")
   - Tasks should be as independent as possible (or have clear dependencies)
3. **Organize into phases**:
   - Foundation: Setup, scaffolding, schema changes
   - Core: Main implementation
   - Integration: Hooking systems together
   - Polish: Testing, documentation, cleanup
4. Document:
   - Task breakdown with descriptions
   - Task dependencies (which tasks must run in order?)
   - Implementation notes (where's the relevant code? any gotchas?)
   - Validation checklist (how do we verify each task is done correctly?)
5. Complete the tasks.md document
6. **Approval Gate** ✋ — STOP here regardless of mode. Show the user the task breakdown and ask:
   > "Does this plan look solid? Should we reorganize anything, or break any tasks down further?"

   Wait for the user's explicit response before doing anything else.
   - Once the user confirms ✅:
     - Update `context.json`: `phases.tasks.status = "approved"`, `phases.tasks.approved_at = <now>`, `current_phase = "execution"`, `updated_at = <now>`
     - Emit the **Execution Orchestrator Handoff Block** (see *Subagent Context Protocol* § Execution Orchestrator Handoff Block)
     - **If MULTI-AGENT MODE**: stop completely. The parent agent launches the Execution Orchestrator using the prompt from *Subagent Prompt Templates* § Phase 4.
     - **If SINGLE-AGENT MODE**: continue to Phase 4 (Execution) in this conversation window — act as the Execution Orchestrator directly.
   - If the user requests changes ❌: iterate — reorder tasks, split large ones, clarify ambiguous ones
**Conversation Tips**:
- Frame tasks for the person who will do them (human or AI agent)
- Anticipate questions: "Why does Task 1.2 come before Task 2.1? Because we need X in place first."
- Mention gotchas and tricky parts upfront
- Link each task back to the design/requirements if it's not obvious
- Sometimes it's helpful to provide a quick walkthrough of the task order

**Example Conversation**:
```
User: Approves design. Ready for tasks?
Your response: "Perfect! Here's the breakdown:

**Phase 1 - Foundation** (2 tasks)
- [ ] Create notification_settings table and migration
- [ ] Create NotificationPreference entity + repository

**Phase 2 - Core** (3 tasks)
- [ ] Implement NotificationService with preference checking
- [ ] Add opt-in/opt-out API endpoints
- [ ] Set up async queue worker for processing

**Phase 3 - Integration** (2 tasks)
- [ ] Hook notifications into existing event system
- [ ] Add integration tests

**Phase 4 - Polish** (2 tasks)
- [ ] Add monitoring + logging
- [ ] Update user-facing documentation

The order matters—we need the schema before writing the service. We need the service 
before hooking into events. Etc."
```

---

### Phase 4: Execution (ai-dlc Integration)

**Goal**: Implement the approved spec through parallel specialized agents, each running the ai-dlc Construction phase for their assigned unit.

> This phase only activates after Phase 3 (Tasks) is approved. It bridges the planning output
> of spec-driven-development into the structured construction workflow of ai-dlc.
>
> **Prerequisite**: The ai-dlc skill should be loaded in the same session for full Construction
> stage guidance. If unavailable, the Unit Executor falls back to the embedded stage mapping
> table in this skill — Phases 1–3 are unaffected regardless.

**Your Steps**:

1. Read `context.json` and confirm `phases.tasks.status = "approved"` before proceeding
2. **Parse the dependency DAG** from `tasks.md` to identify named execution units:
   - Default units: `foundation`, `core`, `integration`, `polish` (matching the four task phases)
   - Override: if `design.md` identifies distinct bounded components (services, modules), use those as units instead
3. **Build execution waves** — group units so that all units in a wave have their dependencies satisfied by prior waves:
   - Wave 1: units with no dependencies (run in parallel)
   - Wave N: units whose every dependency is in a completed wave
4. **Write wave plan to `context.json`** under the `execution` key (see *context.json Lifecycle* in *Subagent Context Protocol*)
5. **Present the wave plan** to the user and wait for explicit ✅ before launching any agents
6. **On user ✅**: emit one **Unit Executor Handoff Block** per unit in Wave 1 (units in the same wave launch as parallel agents)
7. After each wave completes, emit Unit Executor Handoff Blocks for the next wave
8. When all waves complete: update `execution.status = "complete"` and `current_phase = "complete"`

**Execution Mode behavior**:

- **⚡ SINGLE-AGENT MODE**: You act as both Orchestrator and Unit Executors in sequence. Work through each wave and each unit's ai-dlc stages without spawning separate agents. Announce each unit at the start.
- **🔀 MULTI-AGENT MODE**: Launch the Execution Orchestrator agent first (using the prompt in *Subagent Prompt Templates* § Phase 4 — Execution Orchestrator). The Orchestrator then launches Unit Executor agents per wave using the Unit Executor prompt.

**Unit Executor responsibilities per unit**:

Each Unit Executor runs the ai-dlc Construction stages appropriate for its tasks:

| Unit | ai-dlc Stages | Output path |
|---|---|---|
| `foundation` | Functional Design → Code Generation | `aidlc-docs/construction/foundation/` |
| `core` | NFR Requirements → NFR Design → Code Generation | `aidlc-docs/construction/core/` |
| `integration` | Infrastructure Design → Code Generation | `aidlc-docs/construction/integration/` |
| `polish` | Code Generation (build & test) | `aidlc-docs/construction/polish/` |

The Unit Executor maps SDD spec inputs to ai-dlc stage inputs as follows:

| ai-dlc stage expects | SDD source |
|---|---|
| Unit of work definition | Unit's task list from `tasks.md` |
| Business requirements | `requirements.md` |
| Component structure + data model | `design.md` |
| NFR targets | `requirements.md` § Non-Functional Requirements |

> 📖 See `agents/sdd-execution-orchestrator.agent.md` and `agents/sdd-unit-executor.agent.md`
> for the full agent definitions. See `references/subagent-protocol.md` for the
> Execution Orchestrator Handoff Block and Unit Executor Handoff Block templates.

---

## Handling Ambiguity & Vague Requests

> ⚠️ **Critical behavior** — do not skip this section. Jumping to Phase 1 on a vague request wastes everyone's time.

This is where the skill shines. When users say things like:
- "Improve performance" (but don't say what's slow)
- "Make it better" (vague improvement)
- "I'm not sure what we need" (uncertainty)
- "Fix the [system]" (unclear problem)

**Do NOT jump to Phase 1 Requirements**. Instead:

1. **Explicitly recognize the ambiguity**: "This is too vague to create a spec. Let's diagnose first."
2. **Ask diagnostic questions**:
   - For performance: Which operations? Which users? Current vs. target metrics?
   - For improvements: What problem are we solving? For whom? How big is the impact?
   - For fixes: What's broken? How do users experience the problem?
3. **Convert vagueness to clarity**:
   - "OK, so **dashboard loading takes 5 seconds** and you want it under 2 seconds. That's RF-1."
   - "**New users abandon after signup step 2**, and we want to reduce drop-off to <10%. That's RF-1."
4. **Then proceed to Phase 1** with a clear problem statement

This diagnostic gate prevents wasted time speccing the wrong thing.

---

## Questioning Protocol

> This protocol governs every moment the agent asks the user a question — at Phase 1
> Step 1 (initial clarification), during Handling Ambiguity (diagnostic gate), and at
> each Approval Gate follow-up. In MULTI-AGENT MODE, the Orchestrator owns this protocol
> exclusively; the Proposer never asks the user directly.

### Sequential Questioning Loop

Ask **exactly one question at a time**. Never queue or reveal upcoming questions — each
answer shapes what needs to be asked next.

When `vscode/askQuestions` (or an equivalent ask-user tool) is available, use it to
render the current question interactively. Fall back to Markdown only when no interactive
tool is available.

**For multiple-choice questions:**

1. Analyze all options against: best practices for the project type, common patterns in
   similar implementations, risk reduction (security, performance, maintainability), and
   any constraints already visible in the spec or conversation.
2. Identify the **recommended option** and state your reasoning concisely.
3. When the interactive tool is unavailable, render options as a Markdown table:

   | Option | Description |
   |--------|-------------|
   | A | `<Option A description>` |
   | B | `<Option B description>` |
   | C | `<Option C description>` (add D/E as needed, up to 5) |
   | Short | Provide a different short answer (≤5 words) *(include only when free-form is appropriate)* |

   Format: **`Recommended: Option [X] — <reasoning>`**

   Append: *"Reply with the option letter (e.g., "A"), accept the recommendation by
   saying "yes" or "recommended", or provide your own short answer."*

**For short-answer questions (no meaningful discrete options):**

1. Provide a **suggested answer** based on best practices and visible context.
2. Format: **`Suggested: <proposed answer> — <brief reasoning>`**
3. Append: *"Format: short answer (≤5 words). Accept by saying "yes" or "suggested", or
   provide your own answer."*

### Handling Replies

- **"yes" / "recommended" / "suggested"** → adopt your stated recommendation or
  suggestion verbatim.
- **Letter reply (e.g., "B")** → map to the corresponding option.
- **Free-form answer** → validate it fits the ≤5-word constraint if applicable. If
  ambiguous, ask one brief disambiguation — it belongs to the same question, do NOT
  advance the counter.
- Once the answer is satisfactory: record it in working memory (do not write to disk yet)
  and advance to the next queued question.

### Stop Conditions (enforced at every gate)

Stop asking further questions when **any** of the following is true:

1. All critical ambiguities for the current phase are resolved and remaining queued
   questions become unnecessary.
2. The user signals completion: *"done"*, *"good"*, *"no more"*, *"continue"*.
3. You have asked **5 questions** in this gate.

If no valid questions exist at the start of a gate, present a brief summary of what will happen next and ask the user to confirm before proceeding (e.g., "No clarifying questions needed — ready to move to Phase X. Shall I continue?").

---

## Core Principles

1. **Respect Approval Gates**: Don't skip them. They exist to catch misalignment when it's cheapest to fix. If user says "looks good", move forward. If they say "wait, we're missing X", iterate the docs. This is the core of SDD.

2. **One Phase At a Time**: Complete Phase 1 fully before opening Phase 2. This prevents "moving goalposts" and scope creep. If new requirements emerge during design, go back to Phase 1—don't hand-wave them into design.

3. **Technology-Agnostic at Spec Level**: Don't say "use PostgreSQL" or "use React" in the spec. The spec captures *intent and constraints*, not implementation. Let other skills/agents decide tech. Example bad: "RF: We need fast queries on user data." Example good: "RNF: User queries must return < 100ms including network latency."

4. **Collaborative, Not Prescriptive**: Ask questions, propose structures, but always defer to the user's judgment. If they say "that's not right," listen and adjust. You're a guide, not a boss.

5. **Clear Over Perfect**: Better a clear, simple spec that's ready to implement than a perfect one that takes forever. Specs can always be refined during implementation.

6. **Surface Assumptions & Constraints Early**: Hidden assumptions = rework. Ask "Why not?" for every design decision. Ask "What if?" for edge cases. Explicit is always better than implicit.

---

## Example Workflows

> 📖 Read `references/example-workflows.md` when you need a full conversation walkthrough.
> It contains two complete end-to-end examples — a notification system (EN) and a referrals
> system (ES) — showing exactly what each phase response should look like in practice.

---

## Subagent Prompt Templates

> 📖 Read `references/subagent-templates.md` when launching subagents in SUBAGENT MODE.
> It contains verbatim prompts for Phase 1 (Requirements), Phase 2 (Design), Phase 3 (Tasks),
> Phase 4 Execution Orchestrator, and Phase 4 Unit Executor.
> Copy the relevant prompt and substitute the placeholders with real values.

---

## Folder Structure

After running this skill, the folder structure looks like:

```
.specs/
└── {feature_name}/
    ├── context.json       ← machine-readable state (phase, approvals, execution waves)
    ├── requirements.md    (Phase 1)
    ├── design.md          (Phase 2)
    └── tasks.md           (Phase 3)

aidlc-docs/                ← created during Phase 4 (Execution)
└── construction/
    ├── plans/
    │   ├── {unit}-code-generation-plan.md
    │   └── ...
    ├── foundation/
    │   ├── functional-design/
    │   └── code/
    ├── core/
    │   ├── nfr-requirements/
    │   ├── nfr-design/
    │   └── code/
    ├── integration/
    │   ├── infrastructure-design/
    │   └── code/
    └── polish/
        └── code/
```

Spec files in `.specs/` are read-only after approval. Application code lives at the workspace root.

### Validating context.json

After writing or updating `context.json`, validate it against the JSON Schema and business rules:

```bash
# First-time setup — creates the Hatch environment and installs jsonschema
cd $SKILL_DIR/scripts
hatch env create

# Run the validator for a specific spec folder
hatch run validate .specs/{feature_name}/
```

Or validate all specs at once:

```bash
hatch run validate-all
```

Without Hatch (plain Python), the script still runs structural business-rule checks (phase ordering, approval timestamps, folder consistency) — only JSON Schema validation requires `jsonschema`.

---

## Subagent Context Protocol

**The problem**: Subagents run in isolated context windows with no memory of the parent
conversation. **The solution**: after every approval gate, write state to `context.json`
on disk and emit a **Subagent Handoff Block** so any downstream agent can resume exactly
where the workflow left off.

> 📖 Read `references/subagent-protocol.md` for the full protocol details:
> the Handoff Block template, how subagents must announce and resume state,
> the complete `context.json` lifecycle table, and `project_context` population rules.

---

## Common Pitfalls & How to Avoid Them

| Pitfall | What Happens | How to Avoid |
|---------|-------------|--------------|
| Skipping Requirements | You design for the wrong thing | Insist on the gate. "Let's lock in requirements first." |
| Over-detailed Requirements | Takes forever to write | Focus on *what*, not *how*. Requirements ≠ implementation. |
| Overly Complex Design | Tasks become huge and unclear | Ask: "Can we simplify this?" Break design into smaller pieces. |
| Bypassing Approval Gates | Misalignment with user | Always stop and present output to the user. Wait for explicit confirmation before moving to the next phase. |
| Mixing Technologies into Spec | Spec becomes prescriptive | Keep spec technology-agnostic. Delegate tech choices to implementation phase. |

---

## Hands-Off: What This Skill Does NOT Do

- **Implementation**: This skill plans the feature. Other skills/agents handle building it.
- **Technology Choice**: The spec doesn't say "use PostgreSQL" or "use React." Those are design/implementation details for other skills.
- **Code Review**: Once tasks are underway, that's outside this skill's scope.
- **Maintenance & Evolution**: The spec is for *this* feature. Evolving specs over time is handled separately (that's "spec-anchored" or "spec-as-source" territory — advanced SDD patterns).

---

## References

- `references/sdd-overview.md` — MLM Fowler's taxonomy (spec-first, spec-anchored, spec-as-source)
- `references/troubleshooting.md` — common questions and edge cases
- `references/example-workflows.md` — full end-to-end conversation examples (EN + ES)
- `references/subagent-templates.md` — verbatim subagent prompts for Phases 1–4 (including Orchestrator + Unit Executor)
- `references/subagent-protocol.md` — Handoff Block templates, Unit Executor Handoff Block, resume rules, context.json lifecycle
- `agents/sdd-proposer.agent.md` — Proposer agent definition (multi-agent mode, Phases 1–3)
- `agents/sdd-critic.agent.md` — Critic agent definition (multi-agent mode, Phases 1–3)
- `agents/sdd-execution-orchestrator.agent.md` — Execution Orchestrator agent definition (Phase 4)
- `agents/sdd-unit-executor.agent.md` — Unit Executor agent definition (Phase 4)

---

## Quick Checklist: Am I Using This Skill Right?

- [ ] User described a feature idea or asked for planning help
- [ ] Step 0: Complexity assessed → mode selected (single-agent or subagent)
- [ ] `context.json` created and updated after every approval gate
- [ ] Phase 1: Captured requirements with approval gate (subagent if complex)
- [ ] Phase 2: Designed architecture with approval gate (subagent if complex)
- [ ] Phase 3: Broke into tasks with approval gate (subagent if complex)
- [ ] Subagent Handoff Block emitted at every phase transition
- [ ] Step 0: Complexity assessed → mode selected (single-agent or subagent)
- [ ] `context.json` created and updated after every approval gate
- [ ] Phase 1: Captured requirements with approval gate (subagent if complex)
- [ ] Phase 2: Designed architecture with approval gate (subagent if complex)
- [ ] Phase 3: Broke into tasks with approval gate (subagent if complex)
- [ ] Phase 4: Execution wave plan built and confirmed by user
- [ ] Phase 4: Unit Executor agents launched per wave (parallel where dependency-safe)
- [ ] Phase 4: All units completed ai-dlc Construction stages
- [ ] Subagent Handoff Block (or Execution Handoff Block) emitted at every phase transition
- [ ] All spec files (context.json, requirements, design, tasks) live in `.specs/{feature_name}/`
- [ ] All construction artifacts live in `aidlc-docs/construction/`

✓ You've done your job. The feature is implemented.
