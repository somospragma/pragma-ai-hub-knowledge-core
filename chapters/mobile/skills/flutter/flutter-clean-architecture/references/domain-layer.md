# Domain Layer — Detailed Patterns

## Table of Contents

1. [Entities](#entities)
2. [Use Cases](#use-cases)
3. [Repositories](#repositories)
4. [Result Pattern Deep Dive](#result-pattern-deep-dive)
5. [Domain Exceptions](#domain-exceptions)
6. [Base Interfaces](#base-interfaces)

---

The Domain Layer is the core of your application. It contains pure business logic with no external dependencies.

## Entities

Entities are immutable representations of business objects. They hold the core data that your application manages.

### Entity Rules

- Extend `BaseEntity` from commons package
- All fields must be `final`
- Override `props` for equality comparison
- No business logic beyond simple data representation
- Immutable (use `const` constructor)

### Entity Example

```dart
// domain/entities/user_entity.dart
import 'package:commons/commons.dart';

class UserEntity extends BaseEntity {
  const UserEntity({
    required this.id,
    required this.name,
    required this.email,
  });

  final String id;
  final String name;
  final String email;

  @override
  List<Object?> get props => [id, name, email];
}
```

**Key Points:**
- Use `const` constructor for immutability
- Include all identifying fields in `props`
- No methods except getters and computed properties
- No Flutter imports allowed
- No dependencies on other layers

## Repositories (Interfaces)

Repository interfaces define contracts for accessing data. They hide the complexity of where data comes from (API, database, cache).

### Repository Rules

- Are abstract classes (interfaces)
- Define methods that return `Result<T, Exception>`
- One interface per entity or concept
- NO implementation details
- Methods describe business actions (getUser, createUser, deleteUser)

### Repository Example

```dart
// domain/repositories/user_repository.dart
import 'package:commons/commons.dart';
import '../entities/user_entity.dart';

abstract class UserRepository {
  /// Fetch a single user by ID
  Future<Result<UserEntity, Exception>> getUser(String id);

  /// Fetch all users
  Future<Result<List<UserEntity>, Exception>> getAllUsers();

  /// Create a new user
  Future<Result<UserEntity, Exception>> createUser(UserEntity user);

  /// Delete a user by ID
  Future<Result<bool, Exception>> deleteUser(String id);

  /// Update an existing user
  Future<Result<UserEntity, Exception>> updateUser(UserEntity user);
}
```

**Key Points:**
- Every method returns `Result<Success, Failure>`
- Methods are async and deterministic
- No implementation logic
- Methods use business terminology (create, fetch, delete, not request, response)
- Can have multiple repositories for different domains

## UseCases

Use cases implement specific business actions. Each use case represents one user action or system operation.

### UseCase Rules

- One UseCase per business action
- Implement `BaseUseCase<InputType, OutputType>` from commons
- Main interface is `call()` method
- Always return `Result<T, Exception>`
- Can use multiple repositories
- Can contain complex business logic

### UseCase Example

```dart
// domain/usecases/get_user_usecase.dart
import 'package:commons/commons.dart';
import 'package:injectable/injectable.dart';
import '../entities/user_entity.dart';
import '../repositories/user_repository.dart';

@LazySingleton()
class GetUserUseCase
    extends BaseUseCase<String, Result<UserEntity, Exception>> {

  const GetUserUseCase({required this.repository});

  final UserRepository repository;

  @override
  Future<Result<UserEntity, Exception>> call(String userId) {
    return repository.getUser(userId);
  }
}
```

### ComplexUseCase Example (Multiple Steps)

```dart
// domain/usecases/authenticate_user_usecase.dart
import 'package:commons/commons.dart';
import 'package:injectable/injectable.dart';

class AuthenticateUserUseCase
    extends BaseUseCase<AuthRequest, Result<AuthToken, Exception>> {

  AuthenticateUserUseCase({
    required this.authRepository,
    required this.sessionRepository,
    required this.log,
  });

  final AuthRepository authRepository;
  final SessionRepository sessionRepository;
  final Log log;

  @override
  Future<Result<AuthToken, Exception>> call(AuthRequest request) async {
    // Step 1: Validate input
    if (request.email.isEmpty || request.password.isEmpty) {
      return Failure(InvalidCredentialsException('Email and password required'));
    }

    // Step 2: Authenticate with API
    log.info('Authenticating user: ${request.email}');
    final authResult = await authRepository.authenticate(request);

    // Step 3: Handle result
    return authResult.fold(
      (token) async {
        // Step 4: Save session if authentication successful
        await sessionRepository.saveToken(token);
        log.info('User authenticated successfully');
        return Success(token);
      },
      (error) {
        log.error('Authentication failed: ${error.message}');
        return Failure(error);
      },
    );
  }
}
```

**Key Points:**
- Use `fold()` to handle repository results
- Can orchestrate multiple repositories
- Log important steps
- Keep business logic together
- Use `@LazySingleton()` annotation for DI

## Result Pattern Deep Dive

The `Result<Success, Failure>` pattern replaces exception handling and provides explicit success/failure paths.

### Why Result Pattern?

- **Explicit:** Success and failure are types, not hidden exceptions
- **Composable:** Easy to chain operations
- **Type-safe:** Compiler enforces handling both cases
- **Cleaner:** No try-catch blocks scattered everywhere

### Using Result

```dart
// Result is generic: Result<ValueType, ErrorType>
final result = await useCase.call(request);

// Always use fold to handle both paths
result.fold(
  (success) => handleSuccess(success),
  (failure) => handleError(failure),
);

// Or use getOrElse for default
final user = result.getOrElse(() => defaultUser);

// Or check type
if (result is Success) {
  print('Got user: ${result.value.name}');
} else if (result is Failure) {
  print('Error: ${result.error.message}');
}
```

## Domain Exceptions

Define domain-specific exceptions for better error handling.

```dart
// domain/exceptions/user_exceptions.dart
abstract class UserException implements Exception {
  String get message;
}

class UserNotFoundException extends UserException {
  UserNotFoundException(this.userId);
  final String userId;

  @override
  String get message => 'User $userId not found';
}

class InvalidUserException extends UserException {
  InvalidUserException(this.reason);
  final String reason;

  @override
  String get message => 'Invalid user: $reason';
}
```

Then use in repositories:

```dart
@override
Future<Result<UserEntity, Exception>> getUser(String id) async {
  if (id.isEmpty) {
    return Failure(InvalidUserException('ID cannot be empty'));
  }
  // ... rest of implementation
}
```

---

## Base Interfaces

Generic base classes for all use cases. These live in `core/usecase/usecase.dart`
and are shared across every feature.

```dart
// lib/core/usecase/usecase.dart
import 'package:commons/commons.dart';

/// Use case with parameters.
/// [T] = return type inside Result. [P] = Params class.
abstract interface class UseCase<T, P> {
  Future<Result<T, Exception>> call(P params);
}

/// Use case without parameters.
/// [T] = return type inside Result.
abstract interface class UseCaseNoParams<T> {
  Future<Result<T, Exception>> call();
}

/// Use case that returns a Stream of Results (e.g., real-time data).
abstract interface class StreamUseCase<T, P> {
  Stream<Result<T, Exception>> call(P params);
}
```

### Params Pattern

Always use a `@freezed` class for parameters — enables equality and copyWith for free.

```dart
// lib/{feature}/domain/usecases/get_user_usecase.dart
@freezed
class GetUserParams with _$GetUserParams {
  const factory GetUserParams({required String id}) = _GetUserParams;
}

@injectable
class GetUserUseCase implements UseCase<UserEntity, GetUserParams> {
  const GetUserUseCase(this._repository);
  final UserRepository _repository;

  @override
  Future<Result<UserEntity, Exception>> call(GetUserParams params) =>
      _repository.getUser(params.id);
}
```

### No-Params Pattern

```dart
// lib/{feature}/domain/usecases/get_current_user_usecase.dart
@injectable
class GetCurrentUserUseCase implements UseCaseNoParams<UserEntity> {
  const GetCurrentUserUseCase(this._repository);
  final UserRepository _repository;

  @override
  Future<Result<UserEntity, Exception>> call() =>
      _repository.getCurrentUser();
}
```

### Stream Pattern

```dart
// lib/{feature}/domain/usecases/watch_cart_usecase.dart
@freezed
class WatchCartParams with _$WatchCartParams {
  const factory WatchCartParams({required String userId}) = _WatchCartParams;
}

@injectable
class WatchCartUseCase implements StreamUseCase<Cart, WatchCartParams> {
  const WatchCartUseCase(this._repository);
  final CartRepository _repository;

  @override
  Stream<Result<Cart, Exception>> call(WatchCartParams params) =>
      _repository.watchCart(params.userId);
}
```

### Base Interface Rules

| Rule | Reason |
|---|---|
| One use case per operation | Testability and SRP |
| Always use `Result<T, Exception>` return type | Explicit error handling |
| `@injectable` on every UseCase class | GetIt auto-wires via Injectable |
| Params class is `@freezed` | Equality, copyWith, immutability |
| No Flutter imports in UseCase | Domain must be pure Dart |
