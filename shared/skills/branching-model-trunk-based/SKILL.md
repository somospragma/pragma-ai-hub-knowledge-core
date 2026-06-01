---
name: branching-model-trunk-based
description: |
  Trunk-Based Development (TBD) branch strategy, naming conventions, commit rules,
  release strategies, and hotfix procedures for ANY project type, tech stack, or Git
  hosting platform (GitHub, GitLab, Bitbucket, Azure DevOps, Gitea, etc.).

  Use this skill ALWAYS when the user asks about: trunk-based development, committing
  to main/trunk, short-lived feature branches, release from trunk, "always releasable"
  codebase, continuous delivery branching, how to avoid merge hell, or comparing TBD
  vs GitFlow. Also activate when the user says things like "I want to commit directly
  to main", "how do I keep trunk always green", "our branches live too long", "we're
  doing continuous deployment and need a branching model", "cherry-pick to release
  branch".
  Trigger even if the user doesn't say "Trunk-Based Development" explicitly.
license: Complete terms in LICENSE.txt
metadata:
  id: branching-model-trunk-based
  version: 1.0.0
  scope: global
  type: skill
  category: productivity
---

# Branching Model — Trunk-Based Development

Universal Trunk-Based Development (TBD) workflow based on the canonical reference
**trunkbaseddevelopment.com** — adaptable to any team size, project type, or tech stack.

> **Related skill:** For GitFlow-based workflows, see
> [branching-model-gitflow](../branching-model-gitflow/SKILL.md).

---

## Configuring for Your Context

At the start of a session, gather context if not already known:

| Setting | Options | Default |
|---------|---------|---------|
| **Team size** | 1–2, 3–15, 16–100, 100+ | 3–15 |
| **Release cadence** | Continuous / weekly / monthly | Continuous |
| **Issue tracker** | Jira `PROJ-123`, GitLab `#42`, GitHub `#42`, Linear `ABC-123`, none | project-specific |
| **Versioning** | SemVer `1.2.3`, CalVer `2024.05`, custom | SemVer |
| **Main branch name** | `main`, `trunk`, `master` | `main` |
| **Git platform** | GitHub, GitLab, Bitbucket, Azure DevOps, Gitea | platform-agnostic |

Use the defaults when context is unclear and note the assumption.

---

## Core Principles

Six rules that define TBD — every practice below flows from these:

1. **Single integration point.** All developers commit to one shared branch (`main`). No long-lived parallel branches — ever.
2. **Always releasable.** Every commit to `main` must be in a state that *could* go to production. The trunk is never frozen.
3. **Small, atomic increments.** Commits are deliberately small — the smallest independently releasable change. Separate refactoring commits from functional commits.
4. **Don't break the build.** A red trunk blocks the entire team. Run the full build locally before every push.
5. **Commit at least daily.** High-performing teams commit to trunk several times per day. Stale branches die in merge hell.
6. **Common ownership.** Every developer is empowered to change any part of the codebase. No "ownership silos."

---

## Branch Strategy

| Branch | Purpose | Max Lifetime | Who Works On It |
|--------|---------|-------------|----------------|
| **`main`** | Production-ready integration point | Permanent | Everyone (via merge/direct) |
| **`feat/…` / `fix/…`** | Short-lived feature or bug work | **2 days max** | 1 developer (or pair) |
| **`release/…`** | Just-in-time stabilization for a release | Until release shipped | Merge Meister (cherry-picks only) |

**Key rules:**
- `main` is always green — never commit broken code.
- Short-lived branches receive `main → branch` syncs freely; `branch → main` only when done, then delete immediately.
- Release branches are cut from `main` just before a release. Developers **never commit directly** to them.
- CD teams skip release branches entirely and **release from a tag on `main`**.

---

## Branch Naming Conventions

Lowercase, kebab-case. Prefix with issue ID when available:

```bash
# Short-lived feature / bug branches
feat/TICKET-123-payment-gateway     # Jira
feat/42-add-one-click-purchase      # GitLab / GitHub issue number
fix/TICKET-456-null-pointer-checkout
refactor/extract-purchasing-abstraction
chore/upgrade-dependencies
docs/update-api-readme

# Release branches (just-in-time, cut from main)
release/1.2.0
release/2024.05
rel/1.1.1

# Tags for release-from-trunk strategy
v1.2.0
v2024.05.27
```

> No issue tracker? Use a short, descriptive slug: `feat/user-authentication`.

**Git platform note:** Branch naming rules apply identically across GitHub, GitLab, Bitbucket, and Azure DevOps. The only difference is the MR/PR creation UI — the `git` commands are the same everywhere.

---

## Commit Frequency by Team Size

| Team Size | Recommended Style |
|-----------|-------------------|
| **1–2 devs** | Commit straight to `main` — no branches needed |
| **3–15 devs** | Direct-to-main OR short-lived feature branches with fast PR review |
| **16–100 devs** | Short-lived feature branches with mandatory pre-commit CI |
| **100+ devs** | Coupled patch-review system (Gerrit-style) + short-lived branches |

**Target frequency:** at least once every 24 hours per developer. High-performing XP teams commit 10+ times per day per pair.

---

## Short-Lived Feature Branch Workflow

```bash
# 1. Start from updated main
git checkout main && git pull origin main

# 2. Create short-lived branch (max 2 days)
git checkout -b feat/TICKET-123-add-payment

# 3. Work in small, atomic commits
git commit -m "refactor(payment): extract PaymentService interface"
git commit -m "feat(payment): add payment adapter"

# 4. Sync with main frequently
git pull origin main  # or: git rebase origin/main

# 5. Push and open a small, focused MR/PR
git push origin feat/TICKET-123-add-payment
# CI runs on the branch; human review happens here (GitHub PR / GitLab MR / Bitbucket PR)

# 6. Merge to main (squash or merge commit — team decision)
# Branch is deleted immediately after merge

# 7. CI runs again on main — verify still green
```

**Hard rules for SLFBs:**
- One developer per branch (pair-programming counts as one unit)
- One focused concern per branch — a user story can and should spawn multiple branches
- If after 2 days the work isn't done → break it into a smaller slice, merge what's complete, open a new branch for the rest

---

---

## Release Strategies

### Strategy A — Branch for Release (monthly or less-frequent releases)

```
main ──●──●──●──●──●──●──►  (development continues uninterrupted)
              │
              └── release/1.2.0 ──●(cherry-pick fix)──► tag v1.2.0
```

1. Cut `release/1.2.0` from `main` a few days before the release date.
2. Developers continue committing to `main` at full speed — no slowdown.
3. Bug fixes: **fix on `main` first** → CI verifies → cherry-pick to the release branch.
4. Tag the release branch commit with `v1.2.0` and deploy from that tag.
5. Delete the release branch once it's no longer in production.

**Critical rule:** Always cherry-pick `main → release/x.y.z`. **Never** merge the release branch back to `main`.

### Strategy B — Release from Trunk (CD teams)

```
main ──●──●──[tag v1.1.0]──●──●──[tag v1.2.0]──►
```

1. No release branches. Tag a passing commit on `main` and deploy from the tag.
2. If a production bug emerges: fix forward on `main`, tag the fix commit, deploy again.
3. Requires: robust CI, fast deployment pipeline, high test coverage.

**Choose your strategy:**
- Continuous deployment / weekly releases → **Strategy B**
- Monthly or less-frequent releases with formal QA → **Strategy A**

> Detailed runbooks for both strategies: [references/release-strategies.md](references/release-strategies.md).

---

## Hotfix Procedures

### With release branches (Strategy A)

```bash
# 1. Reproduce on main FIRST
git checkout main && git pull origin main
# Write a failing test, implement the fix
git commit -m "fix(checkout): handle payment gateway timeout (TICKET-789)"

# 2. Verify on main — CI MUST pass before cherry-picking
git push origin main  # wait for green CI

# 3. Cherry-pick to the release branch
git checkout release/1.2.0
git cherry-pick <fix-commit-sha>
git push origin release/1.2.0  # CI MUST pass on the release branch too

# 4. Tag and release only after CI is green on the release branch
git tag v1.2.1
git push origin v1.2.1
```

> ⚠️ **CI must pass twice**: once on `main` after the fix, and once on the release branch after the cherry-pick. Cherry-picks can introduce conflicts — CI is what catches them.

**Rule:** Fix on `main` first — always. If you forget the cherry-pick, the next production release will regress. Assign a **Merge Meister** to own this process on teams with active release branches.

### Without release branches (Strategy B — CD)

```bash
# Fix forward on main
git commit -m "fix(checkout): handle payment gateway timeout"
git tag v1.2.1 && git push origin v1.2.1
# Deploy the new tag
```

---

## CI/CD Requirements

TBD only works sustainably with a properly configured CI pipeline:

| Requirement | Why |
|-------------|-----|
| **CI on every commit to `main`** | Catch regressions instantly before the next commit compounds them |
| **CI on every short-lived branch** | Verify before merging, not after |
| **Build time < 10 minutes** | Slow builds push teams toward long-lived branches |
| **Same build script locally and in CI** | "Works on my machine" is eliminated |
| **Pre-commit local verification** | Pull latest, compile, run unit tests before every push |
| **Automatic revert on failure** | Best practice — broken commit is immediately reverted, trunk stays green |

**Developer pre-push checklist:**

```bash
git pull origin main          # sync with latest
# ... run full local build ... #
git push origin main          # only if green
```

---

## TBD vs GitFlow — Decision Guide

| Factor | Choose TBD | Choose GitFlow |
|--------|-----------|---------------|
| Release cadence | Continuous or weekly | Monthly or quarterly |
| CI maturity | Strong CI/CD in place | Optional / lightweight CI |
| Team discipline | High (small commits, always green) | Lower threshold |
| Merge complexity preference | Minimize merges | Structured merge workflow is acceptable |
| Concurrent version support | Release branches + tags | Explicit `release/*` branches |
| Regulatory / compliance gates | TBD + release branches work | Dedicated QA branch (`release`) |
| Goal | Continuous Delivery / DevOps | Batch releases with formal QA stages |

> **Note:** GitFlow's `develop` branch is a permanent long-lived branch — this is TBD's primary anti-pattern. The two models are fundamentally incompatible. Vincent Driessen (GitFlow's author) himself noted GitFlow is not appropriate for continuously-deployed software.

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Breaks TBD |
|---|---|
| Feature branches alive > 2 days | Merge hell; defeats the purpose of TBD |
| Multiple devs sharing one feature branch | Branch becomes de facto long-lived |
| Fixing bugs on the release branch first | Risk of regression if cherry-pick to `main` is forgotten |
| Merging `release/x.y.z` back into `main` | Use cherry-picks only; reverse merges bring in release-only commits |
| "Code freeze" near release | TBD has no code freeze — `main` is always releasable |
| One MR/PR per entire Agile story | Forces large, hard-to-review requests; stream multiple small MRs/PRs per story |
| Not running builds locally before pushing | CI confirms; it doesn't discover problems for you |
| Slow builds (> 10 min) | Developers start batching commits and opening long-lived branches |
| Peer-branch merges (feat/A → feat/B) | Bypasses `main` as the integration point |

---

## Deep Dives

For more detail, load the relevant reference file:

- **Release strategy runbooks:** [references/release-strategies.md](references/release-strategies.md)
