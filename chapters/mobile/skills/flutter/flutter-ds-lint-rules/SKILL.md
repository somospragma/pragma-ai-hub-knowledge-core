---
id: flutter-ds-lint-rules
version: 1.3.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-lint-rules
description: >
  Linting and code quality rules for Design System components.
  Use when writing code, auditing code quality, configuring analysis_options,
  or verifying compliance with Pragma coding standards.
---

# Lint Rules

> **Scope**: Este skill cubre reglas de linting **específicas del Design System** (tokens hardcodeados, prefijo DS, estructura de widgets). Para el estándar general de código Dart/Flutter (analysis_options, flutter_lints, orden de imports) → ver skill `flutter-dart-coding-standard`.

## DS-Specific Rules

| ID | Rule | Severity | Auto-fix |
|----|------|----------|----------|
| DS-001 | No hardcoded values (colors, spacing, radius) | 🔴 BLOCKER | No |
| DS-002 | No `Colors.*` direct usage | 🔴 BLOCKER | No |
| DS-003 | No manual `TextStyle` (fontSize, fontWeight) | 🔴 BLOCKER | No |
| DS-004 | No inline/block/doc comments unless fundamental and justified | 🟡 WARNING | No |
| DS-005 | 1 public widget per file | 🔴 BLOCKER | No |
| DS-006 | Const correctness | 🟡 WARNING | Yes |
| DS-007 | No unauthorized dependencies (allowed: `flutter` SDK, own DS package; dev: `alchemist`, `widgetbook`, `flutter_test`) | 🔴 BLOCKER | No |
| DS-008 | Named parameters always | 🟡 WARNING | No |
| DS-009 | Package imports (no relative) | 🟡 WARNING | Yes |
| DS-010 | No dead or commented code | 🟡 WARNING | No |
| DS-011 | ~200 lines per file max | ⚠️ INFO | No |
| DS-012 | ~30 lines per method max | ⚠️ INFO | No |
| DS-013 | Max 7 constructor params | ⚠️ INFO | No |
| DS-014 | No unnecessary `!` (null assertion) | 🟡 WARNING | No |
| DS-015 | Nullable callbacks (`VoidCallback?`) | 🟡 WARNING | No |

## Linting Package

Per `project.config.yaml` → `linting.package`:

### flutter_lints
```yaml
include: package:flutter_lints/flutter.yaml
linter:
  rules:
    prefer_const_constructors: true
    prefer_const_declarations: true
    avoid_dynamic_calls: true
    public_member_api_docs: false
```

### very_good_analysis
```yaml
include: package:very_good_analysis/analysis_options.yaml
linter:
  rules:
    public_member_api_docs: false
```

## Verification Commands

```bash
flutter analyze lib/src/{level}/{component}/
dart fix --apply
flutter test test/{level}/{component}/
```

## Pragma Rules (always apply)

- SOLID principles in all code
- Variables `camelCase`, classes `PascalCase`, files `snake_case`
- 2-space indentation
- Conditionals and loops with `{ }`
- No `print` — use `developer.log` if needed
- Immutable models (`final` on all properties)
- Conventional Commits

See [full checklist](references/LINT-CHECKLIST.md) for self-review.
