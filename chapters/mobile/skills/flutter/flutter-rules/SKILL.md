---
name: flutter-rules
description: >
  Evaluates Flutter projects against Pragma's best practices and rules across 5 domains:
  Maintainability, Traceability, Performance, Security, and Documentation.
  Generates an actionable Markdown report in reports/flutter_rules_report.md with a
  visual table (✔️/❌/⚠️/N/A), specific recommendations, and an executive summary.

  Use it ALWAYS when the user mentions: evaluate Flutter project, audit Flutter best practices,
  review Flutter rules, analyze Dart code quality, verify clean Flutter architecture,
  review BLoC state management, audit widget performance, review Flutter error handling,
  verify basic mobile security, review Flutter code against standards, analyze Pragma Flutter
  quality, or when they ask "does my app follow best practices?", "review my Flutter project",
  "how good is my Flutter code?", "audit my Dart/Flutter app", "run the Flutter rules",
  "evaluate my code against Pragma", "validate my Flutter project", "flutter rules report".
  Also activate for projects with pubspec.yaml, Flutter monorepos with Melos or Nx,
  analysis of multiple apps in apps/, features/, packages/, shared/, cross-impact between
  shared packages, or when the user attaches Dart files and requests a review.
license: Complete terms in LICENSE.txt
metadata:
  id: flutter-rules
  version: 1.0.0
  scope: stack
  type: skill
  chapter: mobile
  stack: [flutter]
  category: productivity
---

# Flutter Rules

Skill to evaluate Flutter projects against Pragma's best practices and rules.
Produces an actionable report organized into 5 domains: Maintainability, Traceability,
Performance, Security, and Documentation.

## References

Load the corresponding file before each phase:

| File | When to load |
|------|--------------|
| [references/monorepo.md](references/monorepo.md) | When Step 1 detects multiple `pubspec.yaml` or `melos.yaml` |
| [references/maintainability.md](references/maintainability.md) | When evaluating the Maintainability domain |
| [references/traceability.md](references/traceability.md) | When evaluating the Traceability domain |
| [references/performance.md](references/performance.md) | When evaluating the Performance domain |
| [references/security.md](references/security.md) | When evaluating the Security domain |
| [references/documentation.md](references/documentation.md) | When evaluating the Documentation domain |

---

## Step 0 — Fetching Rules

Attempt to retrieve updated rules from the Pragma MCP server:

```
getPragmaResources: 'mobile-flutter-rules.md'
```

If the MCP is unavailable or fails, use the local files in `references/` listed
in the table above. **Notify the user which source is being used.**

---

## Step 1 — Project Structure Detection

This step is critical because the evaluation scope (which paths to analyze, which criteria
to apply) changes completely between a single-app project and a monorepo. Determining this
correctly avoids false positives (non-existent paths) and false negatives (omitted projects).

### Detect the project type

```bash
# Strongest monorepo indicator: melos.yaml at the root
ls melos.yaml 2>/dev/null

# Detect multiple pubspec.yaml
find . -name "pubspec.yaml" -not -path "./pubspec.yaml" -maxdepth 5

# Detect canonical folders
ls -d apps/ features/ packages/ shared/ 2>/dev/null
```

### If single-app

Evaluate standard paths and continue with Step 2:
- Dart: `lib/**/*.dart` and `test/**/*.dart`
- Dependencies: `pubspec.yaml`, `analysis_options.yaml`
- Platforms: `android/`, `ios/`

### If monorepo

Load [references/monorepo.md](references/monorepo.md) — it contains the full classification
algorithm (apps vs packages vs features), how to read `melos.yaml`, the exact path scope
by project type, the cross-impact algorithm, and the consolidated report template.

Once all projects are identified:
- If the user didn't specify which one to evaluate, ask: *"I found {N} projects: [list]. Should I evaluate all of them or just one specific one?"*
- If they said "all", evaluate each project in its own scope and aggregate results using the monorepo report template from `references/monorepo.md`.

---

## Step 2 — Domain Evaluation

For each domain, load its reference file and verify compliance with each rule
in the repository's code and documentation. Use the available search tools
(`grep_search`, `file_search`, `read_file`) to gather concrete evidence.

**Evaluation strategy:**

- **Architecture** — look for `domain/`, `data/`, `presentation/` layers in the directory structure
- **Dependencies** — review `pubspec.yaml` for fixed versions and unnecessary dependencies
- **BLoC/UseCase** — verify that BLoC only imports from domain, never directly from data
- **Linters** — verify existence and content of `analysis_options.yaml`
- **Immutability** — look for `final` in models and states
- **Errors** — look for `try/catch` and exception subclasses
- **Performance** — look for `const`, `ListView.builder`, absence of `shrinkWrap: true`
- **Security** — look for `http://` (not https), `print(`, hardcoded credentials
- **README** — verify existence and minimum content of `README.md`

For each criterion, assign a status:
- ✔️ **Passes** — clear evidence of compliance
- ❌ **Fails** — clear evidence of non-compliance
- ⚠️ **Partial** — incomplete or inconsistent compliance
- **N/A** — the criterion does not apply to this project

---

## Step 3 — Report Generation

Generate or update the report in `reports/flutter_rules_report.md`.

**If it does not exist**, create the file. **If it exists**, append the results at the end with the date.

### Report structure — Single-app

```markdown
# Flutter Rules Report — {date YYYY-MM-DD}

> Project: {name}
> Type: single-app
> Rules source: MCP Pragma | local references v1.0

## Executive Summary

| Total | ✔️ Passes | ❌ Fails | ⚠️ Partial | N/A |
|-------|-----------|---------|------------|-----|
| N     | X         | Y       | Z          | W   |

## Maintainability

| Criterion | Status | Recommendation |
|-----------|--------|----------------|
| Clean architecture 3 layers | ✔️/❌/⚠️/N/A | {if applicable} |

## Traceability
[same structure]

## Performance / Security / Documentation
[same structure]

## Suggested Steps
1. {Priority finding with concrete action}
```

### Report structure — Monorepo

For monorepos, use the full template defined in [references/monorepo.md](references/monorepo.md)
which includes: consolidated summary, cross-impact table, and per-project results.

---

## Step 4 — Notification

Upon completion, notify the developer:

1. **Report location**: `reports/flutter_rules_report.md`
2. **Findings summary**: N criteria evaluated — X pass, Y fail, Z partial
3. **Top 3 priority actions** to improve compliance
4. If it is a monorepo with multiple projects, indicate which project has the most technical debt
