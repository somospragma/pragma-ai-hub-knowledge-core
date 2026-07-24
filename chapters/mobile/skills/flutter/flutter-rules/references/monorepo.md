# Flutter Rules — Monorepo Support

This file contains the detailed logic for evaluating Flutter projects organized as
monorepos. Load it when Step 1 detects multiple `pubspec.yaml`.

---

## Why monorepos need special treatment

In a Flutter monorepo, code is split into independent projects that may share packages.
Evaluating a monorepo as a single project produces incorrect results: wrong paths, missed
shared packages, and lost cross-impact of findings. The key is to evaluate each project
with its own scope and then aggregate the results into a unified view.

---

## Detection Algorithm

### Step 1: Look for monorepo indicators

```bash
# Strongest indicator: melos.yaml at the root
ls melos.yaml 2>/dev/null

# Strong indicator: multiple nested pubspec.yaml
find . -name "pubspec.yaml" -not -path "./pubspec.yaml" -maxdepth 5

# Strong indicator: canonical monorepo folders
ls -d apps/ features/ packages/ shared/ 2>/dev/null
```

### Step 2: Classify each project found

| Type | Tandpical root folder | Characteristics |
|------|---------------------|-----------------|
| **App** | `apps/{name}/` | Has its own `android/`, `ios/`, and `lib/` |
| **Feature package** | `features/{name}/` | Only `lib/`, no native platforms |
| **Shared package** | `packages/{name}/` | Only `lib/`, consumed by others |
| **Shared code** | `shared/` | Pure Dart code shared by multiple projects |

**Clear app signal**: the `pubspec.yaml` contains `flutter:` with `uses-material-design` or
has `android/` and `ios/` folders as siblings.

**Clear package signal**: the `pubspec.yaml` has `flutter:` only for assets/fonts or has
no `flutter:` section at all.

### Step 3: Read melos.yaml if it exists

`melos.yaml` defines exactly which packages are part of the workspace and which are
excluded. Use it as the source of truth instead of inferring from the filesystem:

```yaml
# Ejemplo de melos.yaml
packages:
  - apps/**
  - features/**
  - packages/**
  - shared/**
```

If `melos.yaml` excludes a directory, do not evaluate it.

---

## Evaluation Scope by Project Type

### App (`apps/{name}/`)

| What to evaluate | Paths |
|------------------|-------|
| Dart code | `apps/{name}/lib/**/*.dart` |
| Tests | `apps/{name}/test/**/*.dart` |
| Dependencies | `apps/{name}/pubspec.yaml` |
| Linters | `apps/{name}/analysis_options.yaml` (or root if inherited) |
| Android | `apps/{name}/android/app/src/main/AndroidManifest.xml` |
| iOS | `apps/{name}/ios/Runner/Info.plist` |
| README | `apps/{name}/README.md` |

### Feature package (`features/{name}/`)

| What to evaluate | Paths |
|------------------|-------|
| Dart code | `features/{name}/lib/**/*.dart` |
| Tests | `features/{name}/test/**/*.dart` |
| Dependencies | `features/{name}/pubspec.yaml` |
| Linters | `features/{name}/analysis_options.yaml` (or root) |
| README | `features/{name}/README.md` |
| **N/A** | android/, ios/ → mark as N/A |

### Shared package (`packages/{name}/` or `shared/`)

Same as feature package. Android/iOS criteria are N/A.

---

## Analysis Options: root vs per-project

In well-configured monorepos, there is an `analysis_options.yaml` at the root that is
inherited by child projects. A project can have its own that extends the root:

```yaml
# packages/mi_package/analysis_options.yaml
include: ../../analysis_options.yaml  # inherits from the root
```

When evaluating a project:
1. Check if `{project}/analysis_options.yaml` exists
2. If not, check if there is one at the monorepo root
3. If there is none at all, it is ❌ Fails for the linters rule

---

## Cross-Impact Analysis

When you find a finding in a shared package, that finding has a transitive impact
on all apps that consume it. This matters because a problem in
`packages/network_client/` could affect all apps simultaneously.

### Cross-impact algorithm

For each package with finding `{package_name}`:

```
For each app in apps/:
  1. Read apps/{app_name}/pubspec.yaml
  2. Search for {package_name} in the dependencies: or dev_dependencies: section
  3. If found → that app is affected
```

### How to report the impact

```markdown
### ⚠️ Finding with cross-impact
- **Affected package:** packages/network_client
- **Criterion:** HTTP:// URLs without TLS detected
- **Evidence:** `packages/network_client/lib/src/client.dart:42`
- **Affected apps:** app_client, app_admin (consume network_client)
```

---

## Report Template for Monorepo

The monorepo report has two levels: first the per-project results, then a consolidated
summary with the cross-impact view.

```markdown
# Flutter Rules Report — {date YYYY-MM-DD}

> Type: Flutter Monorepo ({orchestrator: Melos | Nx | custom})
> Projects evaluated: {N apps} apps, {M packages} packages
> Rules source: MCP Pragma | local references v1.0

---

## Consolidated Summary

| Project | Type | ✔️ | ❌ | ⚠️ | Debt |
|---------|------|----|----|----|------|
| app_client | App | 12 | 3 | 2 | Medium |
| app_admin | App | 10 | 5 | 1 | High |
| shared_auth | Package | 8 | 1 | 0 | Low |
| **TOTAL** | — | 30 | 9 | 3 | — |

> **Project with most technical debt:** app_admin (5 criteria failing)

---

## Cross-Impact Findings

> Issues in shared packages that affect multiple apps.

| Package | Criterion | Severity | Affected apps |
|---------|-----------|----------|---------------|
| shared_auth | No typed exceptions | ⚠️ | app_client, app_admin |

---

## Results by Project

### app_client (App)

#### Maintainability
| Criterion | Status | Recommendation |
|-----------|--------|----------------|
| ... | ... | ... |

[... sections by domain ...]

---

### shared_auth (Package)

> **Note:** Android/iOS criteria marked N/A (package without native platforms)

#### Maintainability
| Criterion | Status | Recommendation |
|-----------|--------|----------------|
| ... | ... | ... |
| ... | ... | ... |

---

## Suggested Steps (Prioritized)

1. **[app_admin - High debt]** {concrete action}
2. **[Cross-impact - shared_auth]** {concrete action}
3. ...
```
