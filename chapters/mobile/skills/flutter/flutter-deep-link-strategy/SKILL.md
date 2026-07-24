---
id: flutter-deep-link-strategy
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-deep-link-strategy
description: >
  Comprehensive deep link implementation using go_router 17.2.2, fpdart functional programming, clean architecture patterns, route guards, dynamic parameters, and platform-specific configuration. Use when implementing deep links, configuring StatefulShellRoute for bottom nav, adding route guards with typed Either<DeepLinkFailure, T> error handling, or setting up Android App Links and iOS Universal Links.
---
# Deep Link Strategy

See `references/implementation_guide.md` for complete patterns and code examples.

## Quick Reference

This skill provides comprehensive deep link strategy implementation patterns for Flutter following
clean architecture with modern functional programming. All code examples use:

- Dart 3.5+ / Flutter 3.24+
- go_router 17.2.2 for declarative routing and deep links
- flutter_bloc 9.1.1 for state management
- GetIt 9.2.1 + Injectable 3.0.0 for dependency injection
- Freezed 3.2.5 for immutable data classes
- fpdart 1.2.0 for functional programming and error handling

## Core Features

### 1. Declarative Routing with go_router
- `ShellRoute` — simple shell (shared scaffold/drawer)
- `StatefulShellRoute.indexedStack` — bottom navigation with persistent tabs
- Deep links activate the correct tab inside the shell
- Route guards and authentication redirects
- Dynamic parameter handling (`/product/:id`)
- Query string support (`?tab=reviews&sort=date`)
- Error handling and fallback routes

### 2. Clean Architecture Implementation
```
Domain (Entities, UseCases, Repositories)
  ↓
Data (RepositoryImpl, DataSources)
  ↓
Presentation (BLoC, Pages)
```

### 3. Functional Error Handling
- `Either<DeepLinkFailure, T>` for all operations
- Comprehensive failure types with Freezed
- Proper error propagation through layers

### 4. Deep Link Types Supported
- **Product Links**: `/product/:productId?variant=color`
- **Share Links**: `/share/:token` with validation
- **Profile Links**: `/profile/:userId?tab=activity`
- **Dynamic Content**: `/content/:type/:id`
- **Authentication-aware routing**

### 5. Platform Configuration
- Android App Links with intent filters
- iOS Universal Links with associated domains
- Custom scheme support for both platforms

## Architecture Integration

```
ProcessDeepLinkUseCase → DeepLinkRepository → DeepLinkRepositoryImpl → DeepLinkDataSource
                                    ↓
                            DeepLinkBloc (Presentation)
                                    ↓
                            go_router Navigation
```

All dependencies injected via GetIt + Injectable. Errors returned as `Either<DeepLinkFailure, T>` using fpdart.

## Key Implementation Patterns

### Router Configuration
```dart
// Case A: Simple ShellRoute (shared scaffold)
ShellRoute(
  builder: (context, state, child) => MainShell(child: child),
  routes: [ /* paths protegidas */ ],
)

// Case B: StatefulShellRoute (bottom navigation with persistent tabs)
// Deep link activates the correct branch/tab automatically
StatefulShellRoute.indexedStack(
  builder: (context, state, navigationShell) =>
      MainScaffold(navigationShell: navigationShell),
  branches: [
    StatefulShellBranch(routes: [
      GoRoute(
        path: '/home',
        builder: (_, __) => const HomePage(),
        routes: [
          // Deep links anidados dentro de la tab
          GoRoute(path: 'product/:productId', ...),
        ],
      ),
    ]),
    StatefulShellBranch(routes: [
      GoRoute(path: '/profile/:userId', ...),
    ]),
  ],
)
```

| Scenario | Recommendation |
|---|---|
| Shared scaffold/AppBar without tabs | `ShellRoute` |
| Bottom navigation with persistent tabs | `StatefulShellRoute.indexedStack` |
| Deep link must activate a specific tab | `StatefulShellRoute` — route through the correct branch |
| Deep link opens a screen over the shell | Route outside the shell (root level) |

### Domain Layer
```dart
@freezed
class DeepLinkFailure with _$DeepLinkFailure {
  const factory DeepLinkFailure.invalidFormat({required String message}) = InvalidFormatFailure;
  const factory DeepLinkFailure.notFound({required String resource}) = NotFoundFailure;
  const factory DeepLinkFailure.unauthorized({required String message}) = UnauthorizedFailure;
}

abstract interface class DeepLinkRepository {
  Future<Either<DeepLinkFailure, DeepLinkResult>> processDeepLink(String url);
}
```

### BLoC State Management
```dart
@injectable
class DeepLinkBloc extends Bloc<DeepLinkEvent, DeepLinkState> {
  final ProcessDeepLinkUseCase _processDeepLinkUseCase;
  final GoRouter _router;

  DeepLinkBloc(this._processDeepLinkUseCase, this._router);
}
```

## Testing Strategy

- **Unit Tests**: UseCases and Repository logic
- **BLoC Tests**: State transitions with bloc_test
- **Integration Tests**: End-to-end deep link flow
- **Widget Tests**: Navigation behavior

## Security & Best Practices

- Parameter validation and sanitization
- Authentication checks before navigation
- Rate limiting for share links
- HTTPS enforcement for universal links
- Fallback routes for invalid links

## Reference Files

- `references/implementation_guide.md` — Complete implementation with code examples, platform setup, and testing strategies
