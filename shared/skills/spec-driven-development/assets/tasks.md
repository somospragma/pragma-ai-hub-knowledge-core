# Tasks: {feature_name}

> **Spec context** — Read `.specs/{feature_name}/context.json` for phase state.
> This document covers **Phase 3 (Tasks)**. Requirements and Design must be approved before this phase.
> Subagents: read `requirements.md` and `design.md` (both approved) before executing any task.

---

## Execution Plan

Break down the implementation into atomic, actionable tasks. Each task should be:
- **Atomic**: Can be completed and tested independently (or have clear, documented dependencies)
- **Sized**: Completable in 1–8 hours (not days)
- **Actionable**: Clear what "done" means

Use checkboxes to track progress as you work through Phase 3.

### Phase 1: Foundation
Foundation work: schema, entities, repositories, setup.

- [ ] **Task 1.1**: {Description}
  - *What it produces*: [Schema files, migration, etc.]
  - *How to test*: [Manual test or unit test]

- [ ] **Task 1.2**: {Description}
  - *What it produces*: [Entity, repository, etc.]
  - *How to test*: [Unit test coverage, etc.]

### Phase 2: Core Implementation
Main feature logic and functionality.

- [ ] **Task 2.1**: {Description}
  - *Depends on*: Task 1.1, Task 1.2
  - *What it produces*: [Service class, business logic]
  - *How to test*: [Unit tests for each method]

- [ ] **Task 2.2**: {Description}
  - *What it produces*: [API endpoints, handlers]
  - *How to test*: [Integration tests with mock data]

- [ ] **Task 2.3**: {Description}

### Phase 3: Integration & Testing
Hook into existing systems, integration tests, performance validation.

- [ ] **Task 3.1**: {Description}
  - *Depends on*: Phase 2 complete
  - *What it produces*: [Integration with existing system]
  - *How to test*: [Integration tests]

- [ ] **Task 3.2**: {Description}
  - *What it produces*: [Full test coverage]
  - *How to test*: [Run test suite; check coverage > 80%]

### Phase 4: Polish & Validation
Documentation, monitoring, cleanup.

- [ ] **Task 4.1**: {Description}
  - *What it produces*: [Monitoring, logging, alerting setup]

- [ ] **Task 4.2**: {Description}
  - *What it produces*: [User-facing docs, API docs, runbooks]

## Task Dependencies

Document any dependencies between tasks to ensure correct execution order:

```
Task 1.1 (Schema)
    ↓
Task 1.2 (Entity) → Task 2.1 (Service) → Task 2.2 (API endpoints) → Task 3.1 (Integration)
                                                                            ↓
                                                                    Task 3.2 (Tests)
                                                                            ↓
                                                                    Task 4.1 (Monitoring)
                                                                            ↓
                                                                    Task 4.2 (Docs)
```

**Key Dependency Rule**: Don't start a task before its dependencies are complete.

## Implementation Notes

Gotchas, helpful context, and code pointers:

- **Where to find relevant code**: [Path to existing similar features]
- **Key utilities/libraries to use**: [Common patterns in this codebase]
- **Tricky parts**: [What might be confusing? How to handle it?]
- **Local testing**: [How to test locally before committing?]
- **Deployment concerns**: [Any database migrations? Backward compatibility?]

Example:
```
- The User service is in src/services/UserService.ts; follow that pattern
- We have a base ValidationError class; use that for validation failures
- Payment API has rate limits—cache responses in Redis
- Remember to handle nil/null cases in the data transformation step
- Run `npm test` after each task to ensure nothing breaks
```

## Validation Checklist

Before marking each task as complete, check:

- [ ] Code follows project style + conventions
- [ ] Tests pass (unit, integration, all relevant suites)
- [ ] No new compiler warnings or linting errors
- [ ] Relevant documentation updated (comments, docs, runbooks)
- [ ] No performance regressions (check metrics if applicable)
- [ ] Security review passed (for auth/data-handling tasks)
- [ ] Deployed to staging and verified working (if applicable)

## Feature-Level Validation Checklist

Once all tasks are done, validate the complete feature:

- [ ] All tasks completed and validated
- [ ] Entire feature tested end-to-end (manual walkthrough)
- [ ] Feature meets all requirements from Phase 1
- [ ] Performance meets all RNF targets
- [ ] No new bugs in existing functionality (regression testing)
- [ ] All acceptance criteria from Phase 1 met
- [ ] Documentation complete and up-to-date
- [ ] Code review approved
- [ ] Ready for production deployment

---

**Status**: ⏳ Pending your approval. Does this plan look solid? Should we reorganize anything, or break any tasks down further?

Once approved ✅, which task would you like to tackle first?

