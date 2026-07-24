# Feature Development Checklist

Use this checklist when developing a new feature to ensure all requirements are met before submitting to code review.

## Pre-Development

- [ ] Feature requirements are clear and well-defined
- [ ] Feature scope is documented
- [ ] Data models and API contract are defined
- [ ] Feature package structure planned

## Domain Layer

- [ ] All entities created (extending `BaseEntity`)
- [ ] All repository interfaces defined (abstract classes)
- [ ] All required use cases implemented
- [ ] Use cases return `Result<T, Exception>`
- [ ] Barrel exports created (`entities.dart`, `repositories.dart`, `usecases.dart`)
- [ ] Domain tests written (>80% coverage)
- [ ] No Flutter imports in domain layer
- [ ] No business logic in entities (only data holders)

## Data Layer

### Models & Serialization
- [ ] All models created (extending `BaseResponseModel`)
- [ ] `fromJson()` factory constructors implemented
- [ ] `toJson()` methods implemented
- [ ] `copyWith()` methods implemented
- [ ] Default values for nullable fields

### DataSources
- [ ] Remote DataSource interface defined
- [ ] Remote DataSource implementation complete
- [ ] Local DataSource interface defined
- [ ] Local DataSource implementation complete
- [ ] Error handling with specific exceptions

### Repositories
- [ ] Repository implementation extends `BaseRepository`
- [ ] All abstract methods implemented
- [ ] Caching strategy implemented (Local → Remote fallback)
- [ ] Result pattern used for returns

### Mappers
- [ ] Mappers extend `BaseResponseMapper`
- [ ] `from()` method converts Model → Entity
- [ ] `fromList()` method for multiple conversions
- [ ] Inverse mapping (`toModel()`) if needed
- [ ] No business logic in mappers

### Testing
- [ ] Model serialization tests
- [ ] DateSource mock tests
- [ ] Repository implementation tests
- [ ] Mapper conversion tests
- [ ] Error handling tests
- [ ] Data layer test coverage >80%

### Organization
- [ ] Barrel exports created (`models.dart`, `datasources.dart`, `mappers.dart`, `repositories.dart`)
- [ ] File naming follows conventions

## Presentation Layer

### States
- [ ] Initial state created
- [ ] Loading state created
- [ ] Success state created (with data)
- [ ] Error state created (with message)
- [ ] Additional states if needed
- [ ] All states extend `Equatable`
- [ ] `props` override properly implemented
- [ ] `const` constructors used

### Cubit/BLoC
- [ ] Cubit/BLoC properly extends parent class
- [ ] Dependencies injected in constructor
- [ ] All public methods correspond to user actions
- [ ] States emitted for each action
- [ ] Error handling with `fold()` pattern
- [ ] Logging at important steps
- [ ] Tests written for all state transitions
- [ ] BLoC test coverage >80%

### Pages
- [ ] Page extends `StatelessWidget`
- [ ] `BlocBuilder` wraps content
- [ ] `BlocListener` handles side effects (snackbars, navigation)
- [ ] Loading state shows spinner
- [ ] Success state displays data
- [ ] Error state shows error message with retry
- [ ] Initial state handled
- [ ] Page has `Key` parameter
- [ ] Page initializes data in `didChangeDependencies()`

### Widgets
- [ ] All widgets extend `StatelessWidget`
- [ ] All widgets have `Key` parameter
- [ ] Widgets use `const` constructors
- [ ] No state management in widgets
- [ ] No business logic in widgets
- [ ] Widgets receive data via constructor
- [ ] Reusable and composable

### Routing
- [ ] Routes enum created
- [ ] Route paths defined
- [ ] Navigation implemented

### Testing
- [ ] Cubit/BLoC state transition tests
- [ ] Error state tests
- [ ] Widget tree tests
- [ ] Page integration tests
- [ ] Presentation layer test coverage >80%

### Organization
- [ ] Barrel exports created (`blocs.dart`, `pages.dart`, `widgets.dart`)
- [ ] File naming follows conventions

## Dependency Injection

- [ ] DI module created (`feature_register_module.dart`)
- [ ] All datasources registered (with proper names if multiple)
- [ ] Mapper registered
- [ ] Repository implementation registered
- [ ] All UseCases registered
- [ ] Cubit/BLoC registered (if using @injectable)
- [ ] Provider annotations correct (`@lazySingleton`, `@singleton`)
- [ ] DI module is properly annotated (`@module`)
- [ ] Injector generated (`dart run build_runner build`)

## Public API

- [ ] Barrel export created (`// lib/{feature_name}.dart`)
- [ ] Public exports include:
  - [ ] Entities
  - [ ] Repository interfaces
  - [ ] UseCases
  - [ ] Cubit/BLoC
  - [ ] Pages
  - [ ] Routes
  - [ ] DI module

## Code Quality

### Formatting & Linting
- [ ] All files formatted: `dart format .`
- [ ] No linting errors: `dart analyze`
- [ ] No linting warnings in feature files

### Naming Conventions
- [ ] Files: `snake_case.dart`
- [ ] Classes: `PascalCase`
- [ ] Methods/Variables: `camelCase`
- [ ] Constants: `SCREAMING_SNAKE_CASE` (global) or `camelCase` (local)
- [ ] Proper suffixes: `Entity`, `Model`, `Repository`, `UseCase`, `Cubit`, `State`, `Page`, `Widget`

### Documentation
- [ ] Classes documented with `///`
- [ ] Public methods documented with `///`
- [ ] Complex logic explained with comments
- [ ] Example usage in complex classes
- [ ] README.md for feature (optional but recommended)

### Testing Coverage
- [ ] Overall feature test coverage >80%
- [ ] Domain layer >85%
- [ ] Data layer >80%
- [ ] Presentation layer >75%
- [ ] Integration tests for critical flows

## Integration

- [ ] Feature imports work correctly
- [ ] Feature compiles without errors
- [ ] Feature integrates with main app
- [ ] DI registration works with main app DI
- [ ] No circular dependencies
- [ ] No unused imports

## Code Review Readiness

- [ ] Commits are well-structured
- [ ] PR template filled completely
- [ ] No debugging code (print, debugPrint)
- [ ] No hardcoded values (use constants/config)
- [ ] No magic numbers or strings
- [ ] Architecture follows Clean Architecture principles
- [ ] No code duplication
- [ ] Performance is acceptable
- [ ] Edge cases handled

## Final Validation

- [ ] Run all tests locally: `melos test`
- [ ] Run analysis: `melos analyze`
- [ ] Generate code: `melos exec -- "dart run build_runner build -d"`
- [ ] Format all files: `dart format .`
- [ ] Verify no git conflicts
- [ ] Verify branch is up to date with develop
- [ ] Create PR with proper template

## Additional Notes/Task

- [ ] Accessibility (a11y) checked if UI feature
- [ ] Performance tested if data-heavy feature
- [ ] Error logging is appropriate level
- [ ] Offline functionality if applicable
- [ ] Caching strategy validated
- [ ] API contract matches actual API
- [ ] Error messages are user-friendly
- [ ] Loading states have proper UX

---

**Feature Name:** ________________________
**Date Started:** ________________________
**Date Completed:** ________________________
**Reviewer:** ________________________
**Notes:**

