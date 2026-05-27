# Troubleshooting: SDD Common Issues

## Issue: Spec is Too Vague; Can't Write Design

**Problem**: Approval happened on requirements, but when trying to write design, too many unknowns.

**Solution**:
1. Identify the unknowns specifically
2. Go back to Phase 1 and update requirements with answers
3. Restart Phase 2 once unknowns are resolved
4. Better to fix this now than in code

**Example**:
- Requirement says: "Users can update their profile"
- During design, realize: "Do we need versioning? Audit trails? Rollback? Hard to design without knowing"
- Go back to Phase 1, ask user: "Should we track change history?"
- Update requirements, then Phase 2 becomes clear

---

## Issue: Design is Too Technical; Feels Like Code

**Problem**: Design is sneaking into implementation details ("Use Redis for caching", "Create 5 functions").

**Solution**:
1. Strip out technology choices
2. Keep it at the level of "what" and "why", not "how"
3. Leave implementation to Phase 3

**Good Design**: "We'll cache user preferences to reduce database load."  
**Bad Design**: "Create a Redis instance with 10GB memory, use Lua scripts for atomic updates."

---

## Issue: User Says "This Spec is Too Long"

**Problem**: Too many requirements, design decisions, or tasks. Feels overwhelming.

**Solution**:
1. This is often a signal that the feature is **too big**
2. Break the feature into smaller pieces
3. Spec each piece separately

**Example**:
- User: "This payment system spec has 40 requirements"
- You: "Yeah, this is really two features: subscription billing + one-time purchases. Let's spec those separately."
- Creates two `.specs/` folders: `subscription_billing` and `one_time_purchase`
- Each becomes manageable

---

## Issue: Approval Gate Stalls; User Won't Approve

**Problem**: User keeps saying "mostly looks good but..." and won't fully approve.

**Solution**:
1. List out the specific blockers: "What's the one thing that needs to change for approval?"
2. Fix that one thing
3. Ask again for approval with a smaller ask
4. Sometimes "good enough to proceed" is better than perfect

**Example**:
- Your spec has 10 points; user approves 9/10
- You: "The only thing left is [X]. Should I fix that, or is it OK as-is for moving to design?"
- User: "OK, leave it for now"
- Move forward (you can always update later)

---

## Issue: Halfway Through Phase 3, Discover Major Gap in Design

**Problem**: Task 2.3 reveals a design flaw no one caught before.

**Solution**:
1. Stop implementing
2. Go back to Phase 2
3. Update design
4. Adjust Phase 3 tasks
5. Resume from updated tasks

This is **why** approval gates exist—much cheaper to fix in design than in code.

---

## Issue: Requirements Pass Approval, But Later Seem Wrong

**Problem**: During design or coding, realize a requirement doesn't make sense.

**Solution**:
1. This is normal—you often learn as you go
2. Update the requirement
3. Update the associated design/tasks
4. Notify the approver of the change
5. Get re-approval if it's significant

---

## Issue: Tasks Are Too Big; Can't Finish in 8 Hours

**Problem**: Task says "Implement the payment service" but it's actually 40 hours of work.

**Solution**:
1. Break that task into subtasks
2. Update Phase 3 with finer-grained tasks
3. Keep each task to 1–8 hours

**Example**:
- Too Big: "Implement payment service" (40 hours)
- Right Size:
  - Task 2.1: Create Payment entity + repository (2 hours)
  - Task 2.2: Implement Stripe API wrapper (3 hours)
  - Task 2.3: Implement retry logic + error handling (2 hours)
  - Task 2.4: Add unit tests (2 hours)

---

## Issue: Specs Aren't Being Used; Teams Ignore Them

**Problem**: You write great specs, but implementers just code without looking.

**Solution**:
1. Make specs **visible**—put them where code happens (PR description, code review checklist)
2. Reference specs in code comments: "See `.specs/checkout_flow/design.md` for rationale"
3. Use spec as part of code review: "Does code match spec?\\"
4. Make spec approval a gate before implementation

Many teams treat specs as documentation, not *constraints*. Be explicit: "Code that doesn't match the spec gets sent back."

---

## Issue: Feature is Exploratory; Too Uncertain for Full Spec

**Problem**: Don't know enough to spec it out properly.

**Solution**:
1. Do a **spike** or **proof-of-concept** first (unspecced exploration)
2. Once you know what you're building, write the spec
3. Then implement from spec

Don't force specs onto exploratory work—it slows you down.

---

## Issue: Requirements Keep Changing

**Problem**: User approves Phase 1, but halfway into Phase 2 says "Actually, we also need X."

**Solution**:
1. New requirements = go back to Phase 1
2. Update Phase 1 docs
3. Get re-approval
4. Update Phase 2 if needed
5. This is **normal**—specs aren't meant to be static predictions

**Prevention**: During Phase 1, ask: "Is this complete? Any other requirements we're missing?" Hard. Better to add now than surprise later.

---

## Issue: Design Doesn't Match Codebase Patterns

**Problem**: Your design proposes something different from how the codebase normally works.

**Solution**:
1. Explore the codebase patterns more carefully
2. Update design to match existing conventions (usually better for consistency)
3. If there's a good reason to deviate, document the trade-off explicitly

**Example**:
- Codebase uses Redux for state management
- Your design proposes MobX
- Better to stick with Redux unless there's a strong reason not to

---

## Checklist: "Is My Spec Spec-Ready?"

Before declaring a spec complete:

- [ ] Requirements are clear and unanimous
- [ ] No unknown blockers in the design
- [ ] Design has been walked through (with codebase context)
- [ ] Tasks are sized to 1–8 hours each
- [ ] Task dependencies are explicit
- [ ] Team has approved all three phases
- [ ] No major risks unaddressed
- [ ] Ready to implement (or hand to AI agent)

If any of these are unchecked, iterate that phase before moving forward.
