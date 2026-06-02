# Spec-Driven Development: Overview

## What is Spec-Driven Development?

Spec-Driven Development (SDD) is a structured approach to planning and building features using AI assistance. The core premise: **write a specification before writing code**.

The specification becomes the source of truth for both human and AI, reducing ambiguity and cost of rework.

## Three Levels of SDD (Fowler Model)

Based on Martin Fowler's analysis (October 2025), there are three maturity levels of SDD:

### Level 1: Spec-First (This Skill)
- **What**: Write a spec *before* building
- **Feature lifecycle**: Spec → Code → Spec is deleted/abandoned
- **When to use**: Single features, one-off projects, feature branches
- **Maintenance**: When evolving the feature later, write a new spec for the change
- **Advantage**: Prevents false starts and rework
- **Challenge**: Specs aren't kept as living documents

This skill implements **Spec-First** by default.

### Level 2: Spec-Anchored
- **What**: Write a spec and keep it updated as the feature evolves
- **Feature lifecycle**: Spec → Code → Spec + Code both evolve together
- **When to use**: Long-lived features that change frequently
- **Maintenance**: Update spec when requirements/design change; keep it in sync with code
- **Advantage**: Spec serves as documentation + decision log over time
- **Challenge**: Requires discipline to keep spec in sync; can become stale

### Level 3: Spec-as-Source
- **What**: Spec is the primary artifact; code is generated from it
- **Feature lifecycle**: Spec → Generated Code (humans only edit spec, never code)
- **When to use**: Highly structured domains (CRUD operations, data pipelines, etc.)
- **Maintenance**: Humans edit spec only; code is regenerated on demand
- **Advantage**: Single source of truth; code is always in sync with spec
- **Challenge**: Requires tooling; only works for certain types of problems; LLM non-determinism is hard

## This Skill: Spec-First Implementation

This skill guides you through **Spec-First SDD**:

1. **Phase 1**: Capture requirements (functional, non-functional, constraints)
2. **Phase 2**: Design how you'll build it (architecture, decisions, trade-offs)
3. **Phase 3**: Break design into executable tasks

**After Phase 3**, the spec is ready for handoff to implementers (human developers or AI agents).

## Key Differences from Other Approaches

### SDD vs. BDD (Behavior-Driven Development)
- **BDD**: Write tests first that describe behavior, then code to pass tests
- **SDD**: Write specs that describe intent/design, then code to match spec
- **Overlap**: Both are "upfront planning," but SDD is higher-level (not test-focused)

### SDD vs. TDD (Test-Driven Development)
- **TDD**: Tests guide code structure
- **SDD**: Specs guide design, which then guides code
- **Overlap**: Both emphasize planning before coding

### SDD vs. Traditional Requirements/Design
- **Traditional**: Requirements → Design → Code (often with disconnect between layers)
- **SDD**: Specs are structured artifacts that bridge requirements + design + tasks
- **Difference**: SDD specs are explicitly AI-friendly (written in natural language)

## When SDD is Valuable

### ✅ Good Use Cases
- Complex features with unclear requirements
- Cross-system integrations (dependencies need explicit documentation)
- High-stakes features (architecture decisions matter)
- Team collaboration (shared understanding prevents rework)
- AI-assisted development (spec reduces ambiguity for AI)

### ❌ Poor Use Cases
- Simple bug fixes ("Add validation to field X")
- Tiny features ("Change button color from blue to red")
- Highly exploratory work (don't know what we're building yet)
- Emergency/firefighting situations (too slow; just code)

## Common Mistakes in SDD

1. **Writing specs for everything**: Save specs for features that warrant them
2. **Over-specifying**: Don't prescribe implementation details in specs
3. **Skipping approval gates**: Specs are only useful if stakeholders agree before coding
4. **Letting specs go stale**: If you're doing Spec-Anchored, keep specs in sync
5. **Not addressing ambiguity upfront**: Vague specs = vague implementations

## FAQ

**Q: How long does it take to write a spec?**  
A: Depends on complexity. Simple features: 30 min to 1 hour. Complex: 2–4 hours. Usually 10–20% of total development time.

**Q: What if requirements change mid-development?**  
A: Update the spec. Don't just code changes—keep the spec current. This is where Spec-Anchored helps.

**Q: Can I use SDD for maintenance/bug fixes?**  
A: Sometimes. Major fixes or refactors? Yes, spec it out. Tiny tweaks? No, just code.

**Q: Does SDD work with AI coding agents?**  
A: Excellently. AI agents love specs because they reduce ambiguity. That's why SDD is gaining traction in the AI-assisted coding world.

**Q: Can I skip phases?**  
A: Not really. Each phase builds on the previous. Skipping = rework later.

**Q: Who approves the spec?**  
A: Whoever "owns" the decision (product lead, tech lead, team consensus, etc.). The spec is the contract—make sure everyone agrees.

---

## Resources

- Martin Fowler's SDD article: https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- This skill's SKILL.md for hands-on guidance
