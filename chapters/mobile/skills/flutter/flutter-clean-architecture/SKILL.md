---
id: flutter-clean-architecture
version: 2.3.0
scope: stack
chapter: mobile
stack: [flutter]
tags: [flutter, mobile, clean architecture]
type: skill
name: flutter-clean-architecture
description: >
  Clean Architecture patterns for Flutter/Dart — 3-layer dependency flow (Domain, Data, Presentation), Result pattern, BLoC/Cubit state management, cross-feature communication via Mediator. USE when implementing features, designing architecture, understanding layer responsibilities, working with entities/repositories/usecases, or reviewing code violations. Activate for: structuring Flutter features, business logic placement, avoiding HTTP calls in widgets, Result vs try-catch patterns, repository design, state management scope, layer dependencies, migrating to Clean Architecture, cross-feature communication. Trigger even if user doesn't say "Clean Architecture" explicitly—applies to any Flutter/Dart project: single-app, monorepo, or packages. Stack: Flutter >=3.32.0, Dart >=3.8.0, BLoC 9.1.1, GetIt 9.2.1, Injectable 3.0.0, go_router 17.2.2, Freezed 3.2.5, fpdart 1.2.0.
license: Complete terms in LICENSE.txt
metadata:
  category: productivity
---

# Clean Architecture in Flutter

Canonical reference for layers, boundaries, and dependency rules.
Based on Uncle Bob's Clean Architecture, adapted for Flutter.

## Project Adaptation

Code examples use these base classes from `package:commons/commons.dart`. Substitute with your own:

| Example Class | Description | Alternatives |
|---|---|---|
| `BaseEntity` | Base for domain entities with Equatable | `Equatable` directly |
| `BaseUseCase<I,O>` | Typed use case contract | Plain `abstract interface class` with `call()` |
| `Result<T, E>` | Success/failure union type | Custom sealed class |
| `BaseResponseModel` | Base DTO for JSON serialization | Plain class with `fromJson`/`toJson` |

## Two Modes of Use

| Mode | Starting point | Strategy |
|---|---|---|
| **Greenfield** | New project, blank slate | Apply the full structure from day one. Use folder templates and contracts in reference files directly. |
| **Refactoring** | Existing codebase with violations | Apply incrementally — one feature at a time. Run the violation checklist to prioritize. Never rewrite everything at once. |

### Incremental Refactoring Order

When migrating an existing project, follow this order to minimize risk:

```
1.  Introduce Failure type               (core/error/failure.dart)
2.  Introduce UseCase base interfaces    (core/usecase/usecase.dart)
3.  Extract domain models                remove fromJson from existing models
4.  Create repository interfaces         in domain/
5.  Move HTTP calls behind DataSource    implementations
6.  Create RepositoryImpl                map exceptions to Failure
7.  Replace DataSource calls in BLoC     with UseCase calls
8.  Extract UIModels                     move formatting/color logic out of domain
9.  Introduce AppMediator               replace direct feature imports
10. Migrate to Melos monorepo           (if needed)
```

Each step can be done per feature without breaking the rest of the app.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER  (Flutter)                                  │
│  Page · BLoC · UIModel · Organism · Template                    │
├─────────────────────────────────────────────────────────────────┤
│  DOMAIN LAYER  (pure Dart — no Flutter, no JSON)                │
│  UseCase · Repository (interface) · DomainModel · Failure       │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                     │
│  RepositoryImpl · RemoteDataSource · LocalDataSource            │
│  DataModel · Mapper · ApiClient · CacheStore                    │
└─────────────────────────────────────────────────────────────────┘
         ↑ everything wired by the COMPOSITION ROOT (GetIt + Injectable)
```

## The Golden Rule — Dependency Direction

**Dependencies point ONLY inward:**

```
Presentation → Domain ← Data
```

| From | Can import | CANNOT import |
|---|---|---|
| Domain | Nothing (pure Dart only) | Presentation, Data, Flutter, JSON |
| Data | Domain (interfaces, domain models, failures) | Presentation |
| Presentation | Domain (domain models, use cases, failures) | Data directly |
| GetIt modules | Everything | (it is the composition root) |

## Layer Responsibilities & Rules

### Domain Layer

**Rules:** ✅ Pure Dart + Equatable · ✅ UseCases return `Result<T, Exception>` · ✅ Repositories are `abstract interface class` · ❌ NO Flutter · ❌ NO HTTP · ❌ NO UI logic

| Component | Responsibility | Must NOT |
|---|---|---|
| UseCase | One business operation | Import Flutter, Data layer, JSON |
| DomainModel | Business concept + domain logic | Have `fromJson`/`toJson` |
| Repository (interface) | Data access contract | Have implementation details |
| Failure | Sealed error type | Have HTTP-specific fields |

### Data Layer

**Rules:** ✅ Implements Domain interfaces · ✅ DataSources throw exceptions · ✅ RepositoryImpl returns `Result<T, Exception>` · ❌ NO business logic · ❌ NO Presentation knowledge

| Component | Responsibility | Must NOT |
|---|---|---|
| RepositoryImpl | Orchestrate sources, map exceptions to Failure | Contain business rules |
| RemoteDataSource | HTTP calls, returns DataModels | Return domain models |
| LocalDataSource | Cache read/write, returns DataModels | Return domain models |
| DataModel | Reflects API JSON (`@freezed` + `fromJson`) | Be used in Domain/Presentation |
| Mapper | DataModel ↔ DomainModel conversion | Contain business logic |

### Presentation Layer

**Rules:** ✅ Depends on Domain only · ✅ BLoC/Cubit for state · ✅ UIMapper before emitting state · ❌ NO business logic · ❌ NO Data Layer direct access

| Component | Responsibility | Must NOT |
|---|---|---|
| Page | BlocProvider + route entry point | Contain business logic |
| BLoC | Handle events, call UseCases, emit states | Call DataSources directly |
| UIModel | Values ready to display in the UI | Contain business logic |
| Organism | Reusable composed widgets for the feature | Import Data layer |
| Template | Mobile/web layout for the Page | Contain business logic |

## Result Pattern (Error Handling)

Instead of try-catch, use `Result<Success, Failure>` and `.fold()`:

```dart
// ✅ CORRECT: fold handles both paths explicitly
final result = await getUserUseCase.call(userId);
result.fold(
  (user)  { emit(UserSuccess(user: user)); },
  (error) { emit(UserError(message: error.message)); },
);

// ❌ WRONG: try-catch hides the failure path
try {
  final user = await getUserUseCase.call(userId);
  emit(UserSuccess(user: user));
} catch (e) {
  emit(UserError(message: e.toString()));
}
```

## Stack Versions (2026)

```yaml
dependencies:
  flutter_bloc: ^9.1.1
  get_it: ^9.2.1
  injectable: ^3.0.0
  go_router: ^17.2.2
  freezed_annotation: ^3.1.0
  dio: ^5.9.2
  # Result<T, E>, BaseEntity, BaseUseCase — from your commons package

dev_dependencies:
  build_runner: ^2.14.1
  freezed: ^3.2.5
  injectable_generator: ^3.0.2
  mocktail: ^1.0.5
```

**Key decisions:** `abstract interface class` for all contracts · `@freezed` for domain models, data models, BLoC events and states · `@injectable` / `@lazySingleton` for DI registration.

## Where Does X Go?

| What | Where | Why |
|---|---|---|
| `fromJson` / `toJson` | `data/data_models/` only | Domain must not know about JSON |
| `Color`, `TextStyle`, `Widget` | `presentation/` only | Domain must not import Flutter |
| Error mapping (DioException → Failure) | `data/repositories/` | RepositoryImpl is the boundary |
| String formatting for display | `presentation/ui_models/` (UIMapper) | Presentation concern |
| Business validation (e.g. min age) | `domain/domain_models/` or `domain/usecases/` | Business rule |
| HTTP base URL | `core/di/modules/network_module.dart` | Infrastructure config |
| Navigation after action | `presentation/bloc/` or `presentation/pages/` via BlocListener | Presentation concern |
| Shared `Failure` type | `core/error/failure.dart` | Used by all layers |
| Feature-specific `Failure` | `{feature}/domain/` | Scoped to the feature |
| `SharedPreferences` / `Hive` | `data/data_sources/local/` | Infrastructure detail |
| Analytics event | `presentation/bloc/` (after state change) | Triggered by user action |
| Cross-feature notification | `core/mediator/events/` | Neutral contract, no feature owns it |
| Cross-feature subscription | `presentation/bloc/` via `AppMediator.on<T>()` | Presentation/application concern |
| Shared domain concept (2+ features) | `packages/core/domain/` (monorepo) | Extract to shared package |

## Violation Detection

Run on every PR review:

```bash
# Detect base path (single project vs monorepo)
FEATURES_PATH="lib/src/features/*/"; [[ ! -d "lib/src/features" ]] && FEATURES_PATH="lib/features/*/"

# ❌ Domain importing Flutter
grep -r "import 'package:flutter" ${FEATURES_PATH}domain/ && echo "VIOLATION: Domain imports Flutter"

# ❌ Domain importing Data layer
grep -r "import.*data.*model\|import.*data.*mapper\|import.*repository_impl" ${FEATURES_PATH}domain/ && echo "VIOLATION: Domain imports Data"

# ❌ Presentation importing Data directly
grep -r "import.*data_source\|import.*data_models\|import.*_model\.dart" ${FEATURES_PATH}presentation/ && echo "VIOLATION: Presentation imports Data"

# ❌ Domain model with fromJson
grep -rn "fromJson\|toJson" ${FEATURES_PATH}domain/domain_models/ && echo "VIOLATION: DomainModel has JSON"

# ❌ BLoC with DataSource injected
grep -rn "DataSource" ${FEATURES_PATH}presentation/bloc/ && echo "VIOLATION: BLoC has DataSource"

# ❌ Repository interface returning DataModel
grep -rn "Model>" ${FEATURES_PATH}domain/repositories/ && echo "VIOLATION: Repository returns DataModel"

# ❌ Features importing each other directly
grep -rn "import.*features/[^/]*/[^/]*/features" lib/ && echo "VIOLATION: Direct cross-feature import"
```

## Data Flow Summary

```
User taps button
  → BLoC emits Loading → calls UseCase(params)
    → UseCase calls Repository.method(params)
      → RepositoryImpl tries LocalDataSource (cache)
      → [miss] calls RemoteDataSource → returns DataModel
      → Mapper: DataModel → DomainModel → cache locally
      ← RepositoryImpl returns Result.success(DomainModel)
    ← UseCase returns Result.success(DomainModel)
  → BLoC maps DomainModel → UIModel via UIMapper
  → BLoC emits Success(UIModel)
← Page rebuilds with UIModel data
```

## References

| File | Read when |
|---|---|
| [domain-layer.md](./references/domain-layer.md) | Implementing Entities, Repository interfaces, UseCases, base interfaces |
| [data-layer.md](./references/data-layer.md) | Implementing DataSources, Models, RepositoryImpl, Mappers |
| [presentation-layer.md](./references/presentation-layer.md) | Implementing BLoC/Cubit, States, UIModels, Pages |
| [data-flow.md](./references/data-flow.md) | Understanding the complete request/response cycle step by step |
| [folder-structure.md](./references/folder-structure.md) | Deciding between single project vs monorepo, setting up Melos |
| [mediator-pattern.md](./references/mediator-pattern.md) | Implementing cross-feature communication without direct imports |
| [violations-guide.md](./references/violations-guide.md) | Fixing architectural violations — before/after examples with detection |
| [layer-contracts.md](./references/layer-contracts.md) | Base interfaces, Failure type, DataSource contracts, UIMapper pattern |

## Evals

See `evals/evals.json` for test cases covering layering violations, Result pattern, dependency direction, cross-feature communication, and incremental refactoring.
