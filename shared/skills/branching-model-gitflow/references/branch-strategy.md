# Branch Strategy Details

## Complete GitFlow Diagram

```
                     main (production)
                        ↑    ↓
                       / \__/
                      /
            release-{version} (temporary)
                      \
                       \__
                          ↑
                        release (QA/staging)
                          ↑    ↓
                    feature/... ← develop
                     bugfix/...  (integration)
                    hotfix-{v}
```

## Detailed Merge Flow

### Full Path: feature → develop → release → main

```
1. Feature development (local)
   feature/{issue-id}_{task-id}
        ↓ PR to feature/{issue-id}

2. Feature branch ready
   feature/{issue-id}
        ↓ All tasks merged

3. Feature to develop
   feature/{issue-id}
        ↓ PR to develop
        ↓ Review + Approval

4. Develop to QA
   develop
        ↓ Merged to release

5. Release candidate
   release
        ↓ Create release-{version} branch

6. Final testing → Production
   release-{version}
        ↓ PR to main
        ↓ Tag version
        ↓ Merge to main

7. Production release
   main (v1.2.0)
```

## Pro Tips

### Keep Branches Synced

```bash
# Rebase local feature onto latest develop
git fetch origin
git rebase origin/develop

# Or merge if you prefer merge commits
git merge origin/develop
```

### View Branch Relationships

```bash
# See all branches and where they diverged
git log --all --graph --decorate --oneline

# Compare current branch with develop
git log --graph --oneline HEAD~10...origin/develop
```

### Force Push Safely (personal branches only)

```bash
# Safe only on branches you own exclusively
git push --force-with-lease origin feature/{issue-id}

# NEVER on shared branches: develop, main, release
```

### Delete Old Branches

```bash
# Clean up locally
git branch -d feature/{issue-id}   # Safe (requires merged)
git branch -D feature/{issue-id}   # Force delete

# Clean up on remote
git push origin --delete feature/{issue-id}

# Prune dead remote references
git fetch origin --prune
```

## Merge Conflicts

### Resolving During Rebase

```bash
# During rebase, if conflicts occur
git fetch origin
git rebase origin/develop
# Fix conflicts in editor
git add <fixed-files>
git rebase --continue

# Push rebased branch
git push --force-with-lease origin feature/{issue-id}
```

### Resolving During Merge

```bash
git pull origin develop
# Fix conflicts in editor
git add <fixed-files>
git commit -m "merge: resolve conflicts with develop"
git push origin feature/{issue-id}
```

## Release Checklist

Before creating `release-{version}`:

- [ ] `develop` branch is stable and all features merged
- [ ] Full test suite passing (include integration tests)
- [ ] No outstanding critical issues
- [ ] Version number agreed and finalized
- [ ] CHANGELOG updated with this release's entries
- [ ] Documentation up to date
- [ ] Dependencies up to date (no known vulnerabilities)

## Hotfix Checklist

Before creating `hotfix-{version}`:

- [ ] Issue confirmed as critical and affecting production
- [ ] Fix is minimal and focused (not a large feature)
- [ ] Tests written to cover the fix
- [ ] Verified in a production-like environment
- [ ] Plan to cherry-pick the fix to `develop`

## Branch Strategy Variants

### GitHub Flow (simplified)

Good for: continuous deployment, solo devs, small teams without a QA stage.

```
main ← feature/{issue-id}
     ← bugfix/{issue-id}_{desc}
     ← hotfix-{version}
```

No `develop` or `release` branches. Everything goes to `main` via PR.

### Trunk-Based Development

Good for: teams with strong CI/CD and feature flags.

```
main (trunk, always deployable)
  ← short-lived branches (< 2 days)
  ← direct commits (senior/solo only)
```

Use feature flags for incomplete work instead of long-lived branches.
