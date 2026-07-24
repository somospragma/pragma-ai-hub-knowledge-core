# Mocking Strategy

Use this reference when a Widgetbook use case needs external dependencies such as providers, services, repositories, or blocs.

## Choose A Strategy

| Situation | Strategy |
|---|---|
| Widget can receive data through constructor parameters | Extract dependency and pass data directly |
| Full screen depends on providers and cannot be refactored | Inject mock providers in the use case tree |
| Simple reusable component | Hardcode realistic values in the use case |

Prefer constructor data for reusable UI. Use provider/bloc mocks only for full screens or hard-to-isolate legacy code.

## Rules

- Declare mocks at file level when several variants reuse them.
- Connect useful mock values to knobs.
- Do not depend on the real app tree or global provider registrations.
- Keep every use case autonomous and deterministic.
- Use realistic domain values, not empty placeholders.
