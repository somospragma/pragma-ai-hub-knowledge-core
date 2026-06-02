# Release Strategies — Deep Dive

Reference for the `branching-model-trunk-based` skill.

---

## Table of Contents

1. [Strategy A: Branch for Release](#strategy-a-branch-for-release)
2. [Strategy B: Release from Trunk](#strategy-b-release-from-trunk)
3. [Choosing Your Strategy](#choosing-your-strategy)
4. [Cherry-Pick Discipline (Strategy A)](#cherry-pick-discipline-strategy-a)
5. [The Merge Meister Role](#the-merge-meister-role)

---

## Strategy A: Branch for Release

**Best for:** monthly or less-frequent releases; formal QA stages; regulated environments.

### Timeline

```
day 1              day N-3           day N           after N
main ──●──●──●──●──●──────────────────────────────────►
                  │
                  └── release/1.2.0 ──[QA]──●(hotfix cherry-pick)──► v1.2.0 TAG
                                                                       │
                                                                  (deployed)
```

### Step-by-Step

```bash
# 1. Cut the release branch from main (just-in-time, 2–5 days before release)
git checkout main && git pull origin main
git checkout -b release/1.2.0
git push origin release/1.2.0

# 2. Developers continue working on main (no slowdown, no freeze)

# 3. If a QA bug is found during stabilization:
#    a. Fix on main first
git checkout main
git commit -m "fix(checkout): fix race condition on concurrent orders (TICKET-890)"
git push origin main          # CI must pass

#    b. Cherry-pick to the release branch
git checkout release/1.2.0
git cherry-pick <commit-sha>
git push origin release/1.2.0  # CI must pass

# 4. Release
git tag v1.2.0
git push origin v1.2.0
# Deploy from tag v1.2.0

# 5. Cleanup — delete release branch when it's no longer in production
git push origin --delete release/1.2.0
```

### Non-Negotiable Rules

| Rule | Consequence of violation |
|------|--------------------------|
| Fix on `main` first, then cherry-pick | Forgetting the cherry-pick causes regression in next release |
| Never merge `release/x.y.z` back to `main` | Brings in release-only commits; confuses history |
| Delete release branch when retired | Stale branches cause confusion; may be re-cut for a patch if needed |
| CI must pass on BOTH `main` and `release/x.y.z` | A cherry-pick can introduce conflicts; CI catches them |

---

## Strategy B: Release from Trunk

**Best for:** continuous deployment; weekly or more-frequent releases; high CI maturity.

### Timeline

```
main ──●──●──[tag v1.1.0 → deploy]──●──●──[tag v1.2.0 → deploy]──►
```

### Step-by-Step

```bash
# 1. All development happens on main (or via short-lived branches)
# CI passes on every commit

# 2. Decide the release point (passing commit)
git checkout main && git pull origin main

# 3. Tag the commit
git tag v1.2.0
git push origin v1.2.0

# 4. Deploy from the tag (not from main HEAD — pin the tag)
# Your CI/CD pipeline deploys artifacts built from tag v1.2.0

# 5. If a production bug emerges — fix forward
git checkout main
git commit -m "fix(checkout): handle gateway timeout correctly"
git push origin main         # CI must pass
git tag v1.2.1
git push origin v1.2.1
# Deploy v1.2.1
```

### When a patch release is needed retroactively

If a serious bug is found in `v1.1.0` but `main` has already moved far ahead:

```bash
# Create a retroactive branch from the release tag
git checkout -b release/1.1.1 v1.1.0
git push origin release/1.1.1

# Apply the fix (either cherry-pick from main or write directly)
# Proceed with Strategy A rules from here
```

### Prerequisites for Strategy B

| Prerequisite | Why it matters |
|---|---|
| Fast, reliable CI (< 10 min) | Confidence that every commit is releasable |
| High unit + integration test coverage | Without it, broken code silently deploys |
| Small, independent commits (max 2-day branches) | Prevents half-done features accumulating in trunk |
| One-command deployment pipeline | Long deployment procedures create pressure to batch releases |
| Observability / alerting | Detect regressions in production within minutes |

---

## Choosing Your Strategy

Use this decision flowchart:

```
Q: Do you deploy to production more than once a week?
   Yes → Are you comfortable with "fix forward" on failures?
         Yes → Strategy B (Release from Trunk)
         No  → Strategy A (but work toward Strategy B)
   No  → Strategy A (Branch for Release)

Q: Do you have formal QA / regulatory sign-off before each release?
   Yes → Strategy A
   No  → Both work; Strategy B preferred for simplicity
```

---

## Cherry-Pick Discipline (Strategy A)

Cherry-picking is the only safe way to move fixes from `main` to a release branch.

**Why not `git merge`?**
- `git merge release/1.2.0 into main` pulls in all release-specific commits (version bumps, QA hotfixes that don't apply to current development state).
- It pollutes `main` history.
- It creates a false sense that the release branch is "merged" — it isn't; it's just receiving fixes.

**Cherry-pick best practices:**
- Cherry-pick commits by SHA, not by range, to avoid accidentally picking unrelated commits.
- If the cherry-pick produces conflicts (common when `main` has diverged), resolve them carefully — the release branch may have an older code state.
- Always run CI on the release branch after cherry-picking.
- Log cherry-picks: maintain a simple table in your team wiki or ticketing system.

---

## The Merge Meister Role

On teams with active release branches, designate a **Merge Meister** (rotating or permanent):

**Responsibilities:**
- Owns the cherry-pick process for the active release branch.
- Maintains an audit log of what was cherry-picked, when, and from which commit.
- Monitors CI on the release branch.
- Communicates release-branch status to QA and stakeholders.
- Deletes the release branch after the production version is retired.

**Audit log format (simple wiki table):**

| Date | Fix | Main commit | Release branch commit | Cherry-picked by |
|------|-----|-------------|----------------------|-----------------|
| 2026-05-15 | fix(checkout): timeout | `a1b2c3d` | `e4f5g6h` | @dev-name |

This log prevents the "did we fix this on the release branch?" question that causes
production regressions.
