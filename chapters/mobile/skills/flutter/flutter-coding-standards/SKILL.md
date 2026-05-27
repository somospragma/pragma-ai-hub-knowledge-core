---
name: flutter-coding-standards
description: Dart and Flutter coding standards, naming conventions, formatting rules, linting configuration, and import organization. Use this skill ALWAYS when developers ask about code naming (files, classes, methods, variables, constants, booleans, enums, mixins, extensions), code formatting (line length, indentation, trailing commas, string interpolation), linting rules and violations, import organization and dependencies, comments and code documentation, or edge cases in Dart/Flutter code. Provides strict standards based on the `very_good_analysis` package (also compatible with `flutter_lints` and `lint`) and Clean Architecture layer patterns. Always include ✅ CORRECT and ❌ INCORRECT examples. Apply to ANY Dart or Flutter project — mobile, web, desktop, CLI, or packages.
license: Complete terms in LICENSE.txt
metadata:
  id: flutter-coding-standards
  version: 1.0.0
  scope: stack
  type: skill
  chapter: mobile
  stack: [flutter]
  category: productivity
---

# Coding Standards

## Quick Reference

| Category | Standard | Example |
|----------|----------|---------|
| **Files** | `snake_case.dart` | `user_repository.dart` |
| **Classes** | `PascalCase` | `UserRepository` |
| **Methods** | `camelCase()` | `getUserById()` |
| **Variables** | `camelCase` | `userId`, `userName` |
| **Constants** | `camelCase` (local) | `defaultTimeout` |
| **Global Constants** | `SCREAMING_SNAKE_CASE` | `API_BASE_URL` |
| **Enums** | `PascalCase` | `UserRole`, `ApiStatus` |
| **Booleans** | `isXXX`, `hasXXX`, `canXXX` | `isLoading`, `hasUser` |
| **Imports** | Organized by category | dart, flutter, packages, relative |

---

## Naming Conventions

### Files and Directories

```dart
// ✅ CORRECT
lib/src/domain/usecases/get_user_usecase.dart
lib/src/data/models/user_model.dart
lib/src/presentation/blocs/user_cubit.dart
lib/src/presentation/pages/user_detail_page.dart
lib/src/presentation/widgets/user_card.dart

// ❌ INCORRECT
lib/src/domain/usecases/GetUserUseCase.dart    // PascalCase
lib/src/data/models/user.dart                  // No suffix
lib/src/presentation/bloc/UserBloc.dart        // Wrong pattern
```

### Classes and Types

```dart
// Entities
class UserEntity extends BaseEntity { }

// Models
class UserModel extends BaseResponseModel { }

// Repositories
class UserRepository { }
class UserRepositoryImpl { }

// UseCases
class GetUserUseCase { }
class CreateUserUseCase { }

// Cubits and BLoCs
class UserCubit extends Cubit { }
class UserBloc extends Bloc { }

// States
class UserState extends Equatable { }
class UserSuccess extends UserState { }

// Pages and Widgets
class UserDetailPage extends StatelessWidget { }
class UserCard extends StatelessWidget { }
```

### Variables and Functions

```dart
// Variables - camelCase
String userName = 'John';
int userId = 123;
bool isActive = true;

// Functions - camelCase
void loadUser() { }
Future<void> fetchData() { }

// Boolean naming - descriptive prefixes
bool isLoading = false;
bool hasError = false;
bool canDelete = true;
```

### Constants

```dart
// Local constants - camelCase
const int maxRetries = 3;
// Global constants - SCREAMING_SNAKE_CASE
const String API_BASE_URL = 'https://api.example.com';
```

### Edge Cases: Enums, Mixins, Extensions, Typedefs

```dart
// Enums - PascalCase
enum UserRole { admin, editor, viewer }

// ❌ INCORRECT
enum userRole { admin, editor, viewer }        // camelCase
enum USER_ROLE { ADMIN, EDITOR, VIEWER }       // SCREAMING_SNAKE_CASE

// Typedefs - PascalCase
typedef UserCallback = void Function(UserEntity user);
typedef JsonMap = Map<String, dynamic>;

// ❌ INCORRECT
typedef userCallback = void Function(UserEntity user);  // camelCase

// Mixins - PascalCase
mixin LoggableMixin { }

// ❌ INCORRECT
mixin loggable_mixin { }     // snake_case

// Extensions - PascalCase
extension StringExtension on String { }
extension ListExtension<T> on List<T> { }
```

---

## const vs final vs late

Understanding when to use `const`, `final`, and `late` is critical for Dart code quality.

```dart
// const - Compile-time constant, deeply immutable
const String APP_VERSION = '1.0.0';
const int MAX_RETRIES = 3;

class ConfigDefaults {
  static const String apiEndpoint = 'https://api.example.com';
}

// final - Runtime-set immutable variable
class UserEntity {
  final String id;
  final String name;
  
  const UserEntity({required this.id, required this.name});
}

// late - Lazy initialization, set before first use
class UserRepository {
  late final UserLocalDataSource _localSource;
  late final UserRemoteDataSource _remoteSource;
  
  void initialize() {
    _localSource = UserLocalDataSourceImpl(database);
    _remoteSource = UserRemoteDataSourceImpl(httpClient);
  }
}
```

---

## Formatting Rules

### Line Length

Maximum **100 characters** per line. Use auto-formatting to handle wrapping.

```dart
// ✅ CORRECT - Wrapped nicely
final result = await getUserUseCase.call(
  userId,
  includeDetails: true,
);

// ❌ INCORRECT - Over 100 chars
final result = await getUserUseCase.call(userId, includeDetails: true, fetchAvatar: false);
```

### Indentation

Use **2 spaces**. Never tabs. Configure your IDE to enforce this automatically.

### Trailing Commas

Always use trailing commas in multi-line lists and function calls:

```dart
// ✅ CORRECT
final result = await useCase.call(
  userId: 'user-123',
  includeDetails: true,
);

// ❌ INCORRECT
final result = await useCase.call(
  userId: 'user-123',
  includeDetails: true
);
```

### String Interpolation

Always prefer interpolation over concatenation:

```dart
// ✅ CORRECT - Clear and readable
final message = 'User $userId logged in at $loginTime';
final interpolated = 'Value is ${value + 10} units';

// ❌ INCORRECT - Concatenation is hard to read
final message = 'User ' + userId + ' logged in at ' + loginTime;
```

**Rule:** `prefer_interpolation_to_compose_strings` — use `$variable` for identifiers, `${expression}` for property access or expressions.

---

## Private Members

Dart uses underscore `_` prefix for private visibility. Naming follows standard conventions with `late final` for fields:

```dart
// ✅ CORRECT
class UserRepository {
  late final UserRemoteDataSource _remoteSource;
  late final UserLocalDataSource _localSource;
  
  void _initialize() { }
  String _formatName(String raw) => raw.trim();
}

// ❌ INCORRECT
class UserRepository {
  late UserRemoteDataSource remoteSource;      // Missing underscore (public)
  late UserLocalDataSource localSource;        // Missing underscore (public)
  UserRemoteDataSource _remoteSource2;         // Missing final (mutable)
}
```

**Philosophy:** Private members signal "don't use from outside this library." Use `late final` for fields injected after construction (set exactly once; reassignment throws `LateInitializationError`).

---

## Linting Configuration

The recommended linter is `very_good_analysis` (strictest). Choose based on your project's tolerance:

| Package | Strictness | Typical Use |
|---------|-----------|-------------|
| `very_good_analysis` | High | Production apps, teams |
| `lint` | Medium | Open-source libraries |
| `flutter_lints` | Low | Getting started, small apps |

Essential rules (apply to all):

- `prefer_const_constructors` — `const` widgets skip rebuild
- `prefer_final_fields` / `prefer_final_locals` — prevents accidental mutation
- `require_trailing_commas` — enables consistent `dart format`
- `always_declare_return_types` — explicit types as documentation
- `avoid_print` — use `log.*` instead of `print` in production

```yaml
# analysis_options.yaml
include: package:very_good_analysis/analysis_options.yaml
# or: package:flutter_lints/flutter.yaml
# or: package:lint/analysis_options.yaml
```

```bash
dart analyze && dart fix --apply && dart format lib/
```

> Read [references/linting-rules.md](references/linting-rules.md) for full rule examples, rationale, and Flutter-specific rules (`use_key_in_widget_constructors`, `sized_box_for_whitespace`).

---

## Import Organization

Organize imports in this order:

1. **Dart imports** (`dart:xxx`)
2. **Flutter imports** (`package:flutter/xxx`)
3. **Package imports** (`package:xxx`)
4. **Relative imports** (`../`, `./`)

```dart
// ✅ CORRECT - Organized
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:commons/commons.dart';

import '../entities/user_entity.dart';
import '../repositories/user_repository.dart';
import 'user_state.dart';

// ❌ INCORRECT - Random order
import 'package:commons/commons.dart';
import 'dart:async';
import '../repositories/user_repository.dart';
```

---

## Control Flow and Structure

### Braces in Control Structures

```dart
// ✅ CORRECT
if (isActive) {
  log.debug('User is active');
}

// ❌ INCORRECT
if (isActive) log.debug('User is active');
```

### Prefer Cascades

```dart
// ✅ CORRECT
final user = UserEntity(name: 'John')
  ..id = 'user-123'
  ..isActive = true;
```

---

## Code Documentation

- **`//` comments** — explain *why*, not *what* (intent, non-obvious decisions)
- **`///` comments** — required on every public class, method, and property
- Always include: summary line, `[param]` references, exceptions thrown

```dart
// ✅ CORRECT
/// Loads a user by their unique identifier.
///
/// Throws [UserNotFoundException] if not found.
Future<UserEntity> getUserById(String id) async { }
```

> Read [references/documentation-patterns.md](references/documentation-patterns.md) for complete templates (class, method, property, enum, exception docs).

---

## Null Safety

```dart
// ✅ CORRECT
String name = 'John';                          // Non-nullable
String? nickname = null;                       // Nullable — explicit ?
String displayName = user.nickname ?? user.name; // Null-coalescing
String? safe = user?.profile?.name;             // Safe navigation
```

**Rules:** Never assign `null` to a non-nullable — use `?` type. Avoid `!` (force-unwrap) unless you've already narrowed the type with a null check.

> Read [references/null-safety.md](references/null-safety.md) for advanced patterns (null narrowing, late vs nullable, common anti-patterns).

---

## Equatable for Entity Comparison

Entities should extend `Equatable` for shallow equality:

```dart
class UserEntity extends Equatable {
  final String id;
  final String name;
  
  const UserEntity({required this.id, required this.name});
  
  @override
  List<Object> get props => [id, name];
}
```

---

## Custom Exceptions

Never throw generic `Exception`. Always create a typed hierarchy:

```dart
// ✅ CORRECT
abstract class AppException implements Exception {
  final String message;
  AppException(this.message);
}
class UserNotFoundException extends AppException {
  UserNotFoundException(String id) : super('User $id not found');
}

// ❌ INCORRECT
throw Exception('User not found');  // Too vague, untyped
```

> Read [references/exception-handling.md](references/exception-handling.md) for the full hierarchy (network, cache, auth exceptions), catch patterns, and mapping to domain failures.

---

## Pre-Commit Checklist

Before committing, ensure:

- [ ] **Formatting**: `dart format lib/` (clean)
- [ ] **Linting**: `dart analyze` (zero errors)
- [ ] **Auto-fixes**: `dart fix --apply`
- [ ] **Naming**: snake_case files, PascalCase classes, camelCase methods
- [ ] **Imports**: Organized (dart → flutter → packages → relative)
- [ ] **Trailing commas**: Multi-line calls have trailing commas
- [ ] **Null safety**: Explicit null types with `?`
- [ ] **Documentation**: Public APIs have `///` comments
- [ ] **Equatable**: Entities use `Equatable` + `props`
- [ ] **Logging**: Use `log.debug()`, not `print()`
- [ ] **Tests**: New functions have corresponding tests
- [ ] **CHANGELOG**: Updated for user-facing changes
- [ ] **Commit message**: Follows Conventional Commits

```bash
# Full verification (any Flutter/Dart project)
dart format lib/ && dart analyze && dart fix --apply && flutter test

# In a Melos monorepo
dart format lib/ && dart analyze && dart fix --apply && melos test

# Quick check only
dart format --output=none --set-exit-if-changed lib/ && dart analyze
```

---

## References

Load these files on demand — each focuses on one area of depth:

| File | Read when you need... |
|------|----------------------|
| [references/linting-rules.md](references/linting-rules.md) | Full rule list, Flutter-specific rules, `analysis_options.yaml` examples |
| [references/documentation-patterns.md](references/documentation-patterns.md) | Complete `///` templates for classes, methods, enums, exceptions |
| [references/null-safety.md](references/null-safety.md) | Null narrowing patterns, `late` vs nullable, anti-patterns |
| [references/exception-handling.md](references/exception-handling.md) | Exception hierarchy, network/cache/auth exceptions, catch + map to domain |
