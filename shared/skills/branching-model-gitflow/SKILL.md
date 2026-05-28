---
name: branching-model-gitflow
description: Git branch strategy, naming conventions, PR/MR workflows, and branch protection rules for ANY project type or tech stack. Use this skill ALWAYS when the user asks about creating or naming branches, merging strategies, release workflows, hotfix procedures, PR/MR templates, branch protection rules, choosing GitFlow vs GitHub Flow, rebasing vs merging, handling production bugs, versioning releases, or establishing Git conventions — in ANY technology (web, mobile, backend, data, infrastructure, monorepos). Also activate when users describe a Git problem in non-technical terms "I need to fix a bug on prod", "we need to release tomorrow", "how do I start a new feature", "someone merged to main by mistake". Trigger even if the user doesn't explicitly say "GitFlow" or "branch strategy."
license: Complete terms in LICENSE.txt
metadata:
  id: branching-model-gitflow
  version: 1.0.0
  scope: global
  type: skill
  category: productivity
---

# Branching Model — GitFlow

Universal Git workflow based on **GitFlow** — adaptable to any team size, project type, or tech stack.

## Configuring for Your Project

At the start of a workflow session, gather context if not already known:

| Setting | Options | Default |
|---------|---------|---------|
| **Issue tracker** | Jira `PROJ-123`, GitHub Issues `#42`, Linear `ABC-123`, none | GitHub `#42` |
| **Versioning** | SemVer `1.2.3`, CalVer `2024.03.26`, custom | SemVer `1.2.3` |
| **Main branch name** | `main`, `master` | `main` |
| **Test command** | `npm test`, `pytest`, `go test ./...`, `flutter test` | project-specific |
| **Lint command** | `npm run lint`, `ruff check .`, `dart analyze`, etc. | project-specific |

If context is unclear, use the defaults and note the assumption.

## Branch Strategy

**GitFlow** with named long-lived branches (recommended for teams and releases):

| Branch | Purpose | Protection | Merges From |
|--------|---------|-----------|-------------|
| **`main`** | Production releases | ✅ Protected | `release-{version}` |
| **`release`** | QA / staging integration | ✅ Protected | `develop` |
| **`develop`** | Active development integration | ✅ Protected | `feature/*`, `bugfix/*` |
| **`feature/*`** | New functionality | ❌ Not protected | Sub-task branches |
| **`bugfix/*`** | Bug fixes | ❌ Not protected | `develop` or `release` |
| **`release-{version}`** | Pre-release stabilization branch | ✅ Protected | `release` |
| **`hotfix-{version}`** | Critical production fixes | ❌ Not protected | `main` |

> **Simplified alternative (GitHub Flow)**: For solo devs or small teams without a QA stage, skip `release` and `develop` — work directly with `feature/*` → `main`.

## Branch Naming Conventions

Lowercase, kebab-case. Adapt `{issue-id}` to your tracker:

```bash
# Features (new functionality)
feature/{issue-id}                    # feature/PROJ-123, feature/gh-42
feature/{issue-id}_{short-desc}       # feature/PROJ-123_user-auth
feature/{issue-id}_{task-id}          # feature/PROJ-123_task-456  (sub-tasks)

# Bugfixes
bugfix/{issue-id}_{short-desc}        # bugfix/PROJ-234_fix-login-crash

# Releases and hotfixes
release-{version}                     # release-1.2.0, release-2024.03
hotfix-{version}                      # hotfix-1.2.1

# Maintenance (no issue tracker)
chore/{short-desc}                    # chore/update-dependencies
```

> No issue tracker? Use a short, descriptive slug: `feature/user-authentication`.

## Feature Development Workflow

```bash
# 1. Start from updated develop
git checkout develop && git pull origin develop

# 2. Create feature branch
git checkout -b feature/{issue-id}

# 3. For large features: create a task branch
git checkout -b feature/{issue-id}_{task-id}

# 4. Work and commit (conventional commits)
git commit -m "feat(scope): implement X"

# 5. Push and open PR: task → feature branch
git push origin feature/{issue-id}_{task-id}
# CI: lint + tests

# 6. After approval, merge task into feature and clean up
git checkout feature/{issue-id}
git pull origin feature/{issue-id}
git merge feature/{issue-id}_{task-id}
git push origin feature/{issue-id}
git branch -d feature/{issue-id}_{task-id}
git push origin --delete feature/{issue-id}_{task-id}

# 7. When all tasks done, open PR: feature → develop
# Full CI pipeline runs

# 8. After approval, merge to develop and clean up
git checkout develop
git merge --no-ff feature/{issue-id}
git push origin develop
git branch -d feature/{issue-id}
git push origin --delete feature/{issue-id}
```

## Release Workflow

```bash
# 1. From updated QA/staging
git checkout release && git pull origin release

# 2. Create release stabilization branch
git checkout -b release-{version}          # e.g., release-1.2.0

# 3. Bump version in your manifest:
#   package.json    → "version": "1.2.0"
#   pubspec.yaml    → version: 1.2.0+1
#   pyproject.toml  → version = "1.2.0"
#   Cargo.toml      → version = "1.2.0"
git commit -m "chore(release): bump version to {version}"

# 4. Run full quality suite
{your-test-command}     # npm test / pytest / flutter test --coverage
{your-lint-command}     # npm run lint / ruff check . / dart analyze

# 5. Push and open PR: release-{version} → main
git push origin release-{version}

# 6. After approval and QA sign-off, merge and tag
git checkout main && git pull origin main
git merge --no-ff release-{version}
git tag v{version}
git push origin main && git push origin v{version}

# 7. Back-merge to develop (keep history in sync)
git checkout develop && git pull origin develop
git merge --no-ff release-{version}
git push origin develop

# 8. Clean up
git branch -d release-{version}
git push origin --delete release-{version}
```

## Hotfix Workflow

```bash
# 1. Branch from main (current production state)
git checkout main && git pull origin main
git checkout -b hotfix-{version}           # e.g., hotfix-1.2.1

# 2. Focused fix + version bump
git commit -m "fix(scope): resolve critical {description}"
git commit -m "chore(release): bump version to {version}"

# 3. Push and open urgent PR: hotfix → main
git push origin hotfix-{version}

# 4. After expedited review: merge, tag, push
git checkout main
git merge --no-ff hotfix-{version}
git tag v{version}
git push origin main && git push origin v{version}

# 5. Cherry-pick fix to develop to prevent regression
git checkout develop && git pull origin develop
git cherry-pick <fix-commit-hash>
git push origin develop

# 6. Clean up
git branch -d hotfix-{version}
git push origin --delete hotfix-{version}
```

## Bugfix Workflow

```bash
# Bug in develop → branch from develop
git checkout develop && git pull origin develop
git checkout -b bugfix/{issue-id}_{short-desc}

# Bug found in QA → branch from release
git checkout release && git pull origin release
git checkout -b bugfix/{issue-id}_{short-desc}

git commit -m "fix(scope): {description}"
git push origin bugfix/{issue-id}_{short-desc}

# After PR approval, merge and clean up
git checkout develop     # (or release)
git merge bugfix/{issue-id}_{short-desc}
git push origin develop
git branch -d bugfix/{issue-id}_{short-desc}
git push origin --delete bugfix/{issue-id}_{short-desc}
```

## Pull Request Template

```markdown
## [{source-branch} → {target-branch}] Brief description

## Description
<!-- What does this change and why? -->

## Type of Change
- [ ] Feature (new functionality)
- [ ] Bugfix (non-critical fix)
- [ ] Hotfix (critical production fix)
- [ ] Refactor (no functional change)
- [ ] Docs (documentation only)
- [ ] Chore (dependencies, tooling, maintenance)

## Related Issue
- Closes #{issue-id}: Brief description

## Checklist
- [ ] Code follows project conventions
- [ ] Tests added or updated
- [ ] No linting errors
- [ ] Code formatted
- [ ] Documentation updated (if applicable)
- [ ] No unintended breaking changes

## How to Test
<!-- Steps for the reviewer to verify -->

## Screenshots / Demo (if UI change)
```

## Common Git Commands

```bash
# Create and push branch
git checkout -b feature/{issue-id}
git push origin feature/{issue-id}

# Keep branch in sync with develop
git fetch origin && git rebase origin/develop

# Undo last local commit (not yet pushed)
git reset --soft HEAD~1

# View full branch graph
git log --all --graph --decorate --oneline

# Delete local + remote branch
git branch -d feature/{issue-id}
git push origin --delete feature/{issue-id}

# Cherry-pick a single commit
git cherry-pick <commit-hash>

# Squash commits before PR (interactive rebase)
git rebase -i HEAD~3

# Safe force-push (personal branches only — never shared branches)
git push --force-with-lease origin feature/{issue-id}
```

## Branch Protection Rules

Recommended for `main`, `release`, and `develop`:
- ✅ PR required with at least 1 approval
- ✅ CI pipeline must pass before merge
- ✅ No conflicts with base branch
- ✅ Dismiss stale approvals on new push
- ❌ Force push not allowed
- ❌ Direct commits not allowed

## Detailed Reference

For the full GitFlow diagram, merge flow visualization, and advanced git tips:
→ Read `references/branch-strategy.md`

## Related Skills
- Commit messages → `commit-conventions` skill
- Branching model reference → `references/branch-strategy.md`
