# Design: {feature_name}

> **Spec context** — Read `.specs/{feature_name}/context.json` for phase state.
> This document covers **Phase 2 (Design)**. Requirements must be approved before this phase.
> Subagents: read `requirements.md` (approved) first, then continue this document.

---

## Architecture Overview

High-level description of how the system is organized. Include:
- Major components and how they interact
- Data flow at a high level
- Any diagrams (ASCII or Mermaid is fine)

Example:
```
User Request → API Gateway → Service Layer → Database
                              ↓
                        (async queue for async work)
                              ↓
                        Background Worker
```

## Technical Design Decisions

For each major decision, explain:
- **Decision**: What are we doing?
- **Why**: What problem does this solve? What alternatives did we consider?
- **Trade-offs**: What are we gaining and losing?

### Decision 1: {Architecture Decision}
- **What**: [Describe the choice]
- **Why**: [Rationale; what alternatives did we consider and why did we reject them?]
- **Trade-offs**: [What do we gain? What do we trade off?]

Example:
- **What**: Use async message queue for processing notifications
- **Why**: Synchronous delivery would block user requests. Async allows us to decouple, scale independently, and retry gracefully.
- **Trade-offs**: Notification sending is delayed (not immediate); we must handle duplicate messages; added infrastructure complexity.

### Decision 2: {Another Decision}
- **What**: ...
- **Why**: ...
- **Trade-offs**: ...

## Data Model / Contracts

How will data flow through the system?

### Key Entities
- **User**: [fields]
- **{Entity 2}**: [fields]
- **{Entity 3}**: [fields]

### API Contracts (if applicable)
```
POST /api/feature
Request: { ... }
Response: { ... }
Errors: [404, 409, ...]
```

### Data Transformations
- Step 1: Request arrives → Validation
- Step 2: Validated data → Service logic
- Step 3: Result → Response (or queue for async processing)

## Affected Components

What parts of the codebase will we touch?

- **Component A**: [What's changing? What's new?]
- **Component B**: [What's changing?]
- **New Component**: [Brief description]

## Implementation Approach

Rough outline of how development will happen. This frames the tasks that come in Phase 3.

1. [Foundation step]: Set up schemas, entities, repositories
2. [Core step]: Implement main service logic
3. [Integration step]: Hook into existing systems
4. [Polish step]: Testing, optimization, documentation

## Risks & Mitigation

What could go wrong? How will we prevent or handle it?

- **Risk**: {Description}
  - **Mitigation**: [How we'll address it]

- **Risk**: Race conditions during concurrent updates
  - **Mitigation**: Use database locks + atomic transactions; test under load

- **Risk**: Third-party API failures
  - **Mitigation**: Implement retry logic with exponential backoff; cache responses

## Testing Strategy

How will we validate this feature works as specified?

- **Unit Tests**: [Specific components/functions to test]
- **Integration Tests**: [System interactions to test]
- **Manual Tests**: [User scenarios to verify]
- **Performance Tests**: [If applicable]

## Definition of Done

For this design to be approved, all of these must be true:

- [ ] Design has been reviewed and understood by the team
- [ ] All technical decisions have clear rationale
- [ ] No open technical questions remain
- [ ] Affected components are clearly identified
- [ ] Data flow is documented
- [ ] Trade-offs have been discussed and accepted
- [ ] Risk mitigations are realistic and feasible
- [ ] Ready to translate into Phase 3 (Tasks)

---

**Status**: ⏳ Pending approval. Does this design direction make sense? Any concerns about the approach or alternative ideas?

