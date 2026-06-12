# Requirements: {feature_name}

> **Spec context** — Read `.specs/{feature_name}/context.json` for phase state.
> This document covers **Phase 1 (Requirements)**.
> Subagents: load this file if `phases.requirements.status = "approved"` before proceeding to Phase 2.

---

## Overview

**In one sentence**: What are we building?

**Why**: What problem does this solve? For whom?

Be concise — this is the north star.

## Functional Requirements (RF)

What behaviors must the system exhibit? Focus on observable actions and outcomes.

**Structure**: Each requirement should answer "What should the system do?"

- **RF-1**: {Behavior 1}
- **RF-2**: {Behavior 2}  
- **RF-3**: {Behavior 3}

**Good Example**: "Users can create an account using email or phone, and must verify their identity before accessing the app."

**Bad Example**: "Implement OAuth2 authentication." (Too prescriptive about technology.)

## Non-Functional Requirements (RNF)

Quality attributes: performance, scalability, security, maintainability, reliability, accessibility, etc.

**Structure**: Each requirement should be **measurable** or at least **verifiable**.

- **RNF-1**: {Quality Attribute} - {Measurable Target}
  - Example: "Response time < 100ms for user queries (including network latency)"
  - Example: "Support 10,000 concurrent users without performance degradation"
  - Example: "All data encrypted at rest and in transit (TLS 1.3+)"

- **RNF-2**: {Another Quality Attribute}

## Constraints

What limits are we operating within? (Resources, deadlines, dependencies, regulations, etc.)

- **C-1**: {Constraint}
- **C-2**: {Constraint}

Examples:
- "Must integrate with existing user authentication system"
- "Budget: $50k"
- "GDPR compliant (no PII in logs)"
- "Must work with iOS 12+"

## Assumptions

What are we assuming to be true?

- **A-1**: {Assumption}
- **A-2**: {Assumption}

Examples:
- "Assume user database can handle 1M records"
- "Assume email delivery service has 99.9% uptime"

## Success Criteria

How will we know this feature is complete and working correctly? (These are testable.)

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

Examples:
- User can successfully create 100 accounts without errors
- Performance tests show < 100ms response time for user queries
- All unit tests pass; code coverage > 80%
- Feature works on Chrome, Safari, Firefox (latest versions)

## Dependencies

**Internal** (existing systems/features we depend on):
- Auth system: [describe what we need from it]
- Database: [what schema do we assume exists?]
- Payment system: [integration points]

**External** (third-party services):
- Email service (e.g., SendGrid)
- Analytics platform
- Any APIs or webhooks needed

## Open Questions

Anything unclear that needs clarification before design?

- Q1: {Question}
- Q2: {Question}

Examples:
- "How do we handle failed transactions?"
- "What's the backoff strategy for retries?"
- "Do we need a UI for admins to manage this, or API-only?"

---

**Status**: ⏳ Pending approval. Does this capture what we're building? Any missing requirements, constraints, or questions for the team?

