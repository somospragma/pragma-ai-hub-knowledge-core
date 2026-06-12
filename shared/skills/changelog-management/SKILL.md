---
id: changelog-management
version: 1.3.0
scope: global
type: skill
name: changelog-management
description: >
  Manage CHANGELOG.md following the Keep a Changelog and Semantic Versioning (semver) standards.
  Use this skill to create or update CHANGELOG.md entries, classify changes under the standard
  Keep a Changelog categories (Added, Changed, Deprecated, Removed, Fixed, Security), determine
  the correct version bump type (MAJOR, MINOR, PATCH) specifically when writing changelog entries
  or preparing a release of a project, prepare a release by moving entries from [Unreleased] to a
  numbered version section, or review the format and structure of an existing CHANGELOG.md file.
  Trigger phrases: release notes, notas de versión, entradas de changelog, preparar release,
  bump de versión, categorizar cambios en CHANGELOG, validar CHANGELOG, generar release notes
  desde CHANGELOG. Do NOT trigger for general API versioning strategy, URL versioning, or
  architectural decisions unrelated to maintaining a CHANGELOG file.
permissions:
  - file_read   # reads CHANGELOG.md to validate format and extract entries
  - file_write  # edits CHANGELOG.md when the user requests updates to entries
metadata:
  category: productivity
---

# Changelog Management Skill

Maintain clear, organized release notes following Keep a Changelog and Semantic Versioning standards. This skill ensures your changelog communicates changes effectively to users and developers.

## Quick Reference

| What | Where | When |
|------|-------|------|
| **Unreleased changes** | `[Unreleased]` section | As you develop |
| **Release version** | Version header with date | When releasing |
| **Section headers** | Added, Changed, Deprecated, Removed, Fixed, Security | Always use these 6 categories |
| **Entry format** | Bullet points with brief description | Each change |
| **Breaking changes** | Mark clearly in description or use BREAKING CHANGE footer | Major versions |
| **Release notes** | Create from Unreleased section | Before version tag |

## Essential Rules

### 1. **Unreleased Section Always Comes First**

```markdown
## [Unreleased]
### Added
- New feature description

### Changed
- Behavior change description

### Fixed
- Bug fix description
```

The `[Unreleased]` section captures all changes since the last release.

### 2. **Use Only These 6 Categories**

- **Added** - New features or functionality
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Previously deprecated features now removed
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes or security improvements

Not all categories need to appear in every release.

### 3. **Version Format: [X.Y.Z] - YYYY-MM-DD**

```markdown
## [1.2.0] - 2011-04-08
### Added
- New authentication module
### Fixed
- Login page crash on slow networks
```

- Use semantic versioning: MAJOR.MINOR.PATCH
- Include full date in ISO format
- Bracketed version with links at bottom

### 4. **Write Clear, User-Focused Descriptions**

```markdown
# ✅ GOOD - User understands the impact
### Added
- Added full-text search across all products
- Implemented dark mode support for iOS

# ❌ BAD - Too vague or technical
### Added
- Refactored search component
- Updated dependencies
```

### 5. **Group Related Changes**

```markdown
### Added
- User authentication system
- Two-factor authentication
- Email verification flow

# Better organization than scattered entries
```

### 6. **Mark Breaking Changes Explicitly**

```markdown
## [2.0.0] - 2021-02-19
### Changed
- **BREAKING CHANGE**: Removed deprecated `getUserData()` method
- **BREAKING CHANGE**: Changed API response format from XML to JSON
- Changed default cache TTL from 5 minutes to 2 minutes

### Removed
- Removed support for API v1 endpoints
```

## Development Workflow

### When Developing

> These are instructions for **you, the developer**, to follow in your own repository. The agent guides you through these steps on request — it reads and suggests edits to your files, but does not write to disk, persist state, or schedule any recurring actions autonomously.

1. **Add a new entry to the `[Unreleased]` section of your `CHANGELOG.md`**

   Open your `CHANGELOG.md` and add a bullet under the appropriate category inside `[Unreleased]`:

   ```markdown
   ## [Unreleased]
   ### Added
   - New comprehensive user profile page
   ```

2. **Use the appropriate category** based on the type of change (see the 6 categories above)

3. **Write from the user's perspective** — describe what changed for them, not what you did internally
   - "Users can now export data as CSV" ✅
   - "Refactored export module" ❌

4. **Keep entries brief** — save implementation details for pull request descriptions, not the changelog

### Before Release

1. **Review all `[Unreleased]` entries**
   - Remove duplicates
   - Ensure clarity
   - Group related items

2. **Create new version section**
   ```markdown
   ## [1.2.0] - 2011-04-08
   ### Added
   - Feature A
   ### Fixed
   - Bug fix B
   ```

3. **Move entries from `[Unreleased]` to version section**

4. **Update comparison links at bottom**
   ```markdown
   [unreleased]: https://github.com/org/repo/compare/v1.2.0...HEAD
   [1.2.0]: https://github.com/org/repo/releases/tag/v1.2.0
   ```

5. **Create git tag**

   > ⚠️ **WARNING — DESTRUCTIVE OPERATION**: The commands below permanently modify the remote repository. A pushed tag cannot be easily removed once other systems or CI pipelines have picked it up. **Do not run these automatically — copy and execute them manually in your terminal after verifying the version number.**

   Run these commands in your terminal:
   ```bash
   # Verify the version number before running
   git tag -a v1.2.0 -m "Release v1.2.0"

   # DESTRUCTIVE: The following push is permanent and cannot be undone on the remote.
   # Double-check the tag name matches the intended release version.
   git push origin v1.2.0
   ```

## Semantic Versioning Guide

> **Scope note**: This guide applies specifically to choosing the version number for a CHANGELOG entry or release. For general API versioning strategies (URL versioning, header versioning, etc.) consult your architecture team — that is outside the scope of this skill.

| Change Type | Version | Example |
|------------|---------|---------|
| **Breaking API change** | MAJOR | 1.0.0 → 2.0.0 |
| **New backward-compatible feature** | MINOR | 1.0.0 → 1.1.0 |
| **Bug fix, patch** | PATCH | 1.0.0 → 1.0.1 |

```
MAJOR: Removed old API, changed authentication method → v1.0.0 → v2.0.0
MINOR: Added new search feature, new export formats → v1.0.0 → v1.1.0
PATCH: Fixed login bug, improved performance → v1.0.0 → v1.0.1
```

## Common Mistakes

### ❌ Mixing Technical and User Details

```markdown
# BAD
### Added
- Refactored UserCubit using BLoC pattern
- Migrated to GetIt for dependency injection

# GOOD
### Added
- Improved user authentication reliability
```

### ❌ Forgetting Unreleased Section

```markdown
# BAD - Version jumps around
## [2.0.0]
## [1.9.0]

# GOOD - Unreleased always first
## [Unreleased]
## [2.0.0]
## [1.9.0]
```

### ❌ Inconsistent Categorization

```markdown
# BAD - Fixed goes under Added
### Added
- Fixed typo in welcome message
- Fixed memory leak

# GOOD
### Fixed
- Typo in welcome message
- Memory leak in data loader
```

### ❌ No Breaking Change Markers

```markdown
# BAD - Users don't see breaking change
### Changed
- Updated API response format

# GOOD
### Changed
- **BREAKING CHANGE**: API response format changed from XML to JSON
  Old format: <user><name>...</name></user>
  New format: {"user": {"name": "..."}}
```

## Tools & Validation

### Validate Changelog Format

Run these commands in your terminal:
```bash
# Simple check for structure
grep -E "^## \[" CHANGELOG.md

# Check for required sections in unreleased
grep -A 5 "## \[Unreleased\]" CHANGELOG.md | grep -E "### (Added|Changed|Deprecated|Removed|Fixed|Security)"
```

### Generate Release Notes

Run these commands in your terminal:
```bash
# Extract unreleased section for release notes
sed -n '/## \[Unreleased\]/,/## \[/p' CHANGELOG.md | head -n -1
```

### Link Version References

Add the following version comparison links manually at the bottom of `CHANGELOG.md`:

```markdown
[unreleased]: https://github.com/org/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/org/repo/releases/tag/v1.2.0
```

> Replace `v1.2.0` with the version you just released and adjust the URL to point to the previous version accordingly.

## See Also

- [Keep a Changelog Official](https://keepachangelog.com/) - Full specification
- [Semantic Versioning](https://semver.org/) - Version numbering system

## Additional References

- [keepachangelog-rules.md](references/keepachangelog-rules.md) — Detailed Keep a Changelog rules
- [changelog-examples.md](references/changelog-examples.md) — Content patterns and real-world examples
- [writing-guidelines.md](references/writing-guidelines.md) — Best practices for writing changelog entries
- [categories-guide.md](assets/categories-guide.md) — Guide for choosing the right category
- [changelog-template.md](assets/changelog-template.md) — Starter template for new changelogs
