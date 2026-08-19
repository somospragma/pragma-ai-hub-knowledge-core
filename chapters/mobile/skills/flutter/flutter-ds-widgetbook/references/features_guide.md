# Feature Screen Use Cases

Use this guide when cataloging full screens or feature pages in Widgetbook.

## When To Catalog A Screen

| Situation | Action |
|---|---|
| A new screen was created | Create a use case in `widgetbook_[appname]/lib/features/` |
| An existing screen changed | Update the existing use case |
| The screen has loading/empty/error/content states | Expose those states as knobs or use cases |

## Analyze The Screen

Before writing code, identify:

- state management dependency (`Bloc`, `Cubit`, `Provider`, `Riverpod`, etc.)
- injected services/repositories
- navigation calls
- constructor arguments
- loading, empty, error, success, logged-out, first-time, and default states

## Isolation Rule

A screen must render in Widgetbook without depending on the real app widget tree, real navigation, remote services, or global registrations.

Use one of these strategies:

- wrapper providers with mock state
- constructor injection with mock data
- callbacks that log actions instead of navigating
- mocktail only when the screen cannot be reasonably refactored

## Recommended Variants

| Screen type | Recommended states |
|---|---|
| List/home/catalog/history | default, loading, empty, error |
| Detail/profile/order | default, loading, error |
| Form/login/checkout | default, prefilled, submitting/loading, error |
| Dashboard/summary | default, loading, empty |

## Location

Mirror the feature structure from the main project:

```text
widgetbook_[appname]/lib/features/<feature>/<screen>.use_case.dart
```

Keep screen use cases out of `ui_system/`; those belong under `features/`.
