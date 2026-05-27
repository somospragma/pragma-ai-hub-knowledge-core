# Exception Handling Reference

Complete guide to exception hierarchies, catch patterns, and mapping to domain failures.

## Table of Contents

1. [Exception Hierarchy](#exception-hierarchy)
2. [Domain Exceptions](#domain-exceptions)
3. [Data Layer Exceptions](#data-layer-exceptions)
4. [Catch Patterns](#catch-patterns)
5. [Mapping to Domain Failures](#mapping-to-domain-failures)

---

## Exception Hierarchy

All exceptions extend `AppException` so callers can catch broadly or specifically:

```dart
// Base
abstract class AppException implements Exception {
  const AppException(this.message);
  final String message;

  @override
  String toString() => '$runtimeType: $message';
}

// Domain tier
abstract class DomainException extends AppException {
  const DomainException(super.message);
}

// Data tier
abstract class DataException extends AppException {
  const DataException(super.message);
}
```

---

## Domain Exceptions

```dart
class UserNotFoundException extends DomainException {
  UserNotFoundException(String userId)
      : super('User with id $userId not found');
  final String userId = '';
}

class UnauthorizedException extends DomainException {
  const UnauthorizedException() : super('Unauthorized access');
}

class ValidationException extends DomainException {
  ValidationException(String field, String reason)
      : super('Validation failed for $field: $reason');
}
```

---

## Data Layer Exceptions

```dart
class NetworkException extends DataException {
  NetworkException({required int statusCode, required String body})
      : super('Network error $statusCode: $body');
  final int statusCode = 0;
}

class TimeoutException extends DataException {
  const TimeoutException() : super('Request timed out');
}

class CacheException extends DataException {
  const CacheException(super.message);
}

class ParseException extends DataException {
  ParseException(Type expected, dynamic actual)
      : super('Cannot parse $actual as $expected');
}
```

---

## Catch Patterns

```dart
// ✅ CORRECT — catch specific, re-throw unknown
Future<UserEntity> fetchUser(String id) async {
  try {
    return await _remote.getUser(id);
  } on NetworkException catch (e) {
    log.error('Network error fetching user $id', e);
    rethrow;
  } on TimeoutException {
    throw NetworkException(statusCode: 408, body: 'Request timed out');
  }
  // Let unknown exceptions propagate — don't swallow them
}

// ✅ CORRECT — wrap at data layer boundary
Future<UserEntity> getUser(String id) async {
  try {
    final json = await _httpClient.get('/users/$id');
    return UserModel.fromJson(json).toEntity();
  } on http.ClientException catch (e) {
    throw NetworkException(statusCode: 0, body: e.message);
  } on FormatException catch (e) {
    throw ParseException(UserModel, e.source);
  }
}

// ❌ INCORRECT — swallowing exceptions
Future<UserEntity?> getUser(String id) async {
  try {
    return await _remote.getUser(id);
  } catch (_) {
    return null;  // Silent failure — caller can't distinguish errors
  }
}

// ❌ INCORRECT — generic exception
try {
  await _remote.getUser(id);
} catch (e) {
  throw Exception('Failed');  // Loses all context
}
```

---

## Mapping to Domain Failures

In repositories, map data exceptions to typed `Failure` objects for use in domain/presentation:

```dart
// With Result<T, Failure> pattern
typedef Result<T> = Either<Failure, T>;

abstract class Failure {
  const Failure(this.message);
  final String message;
}

class NetworkFailure extends Failure {
  const NetworkFailure(super.message);
}

class NotFoundFailure extends Failure {
  const NotFoundFailure(super.message);
}

// Repository implementation
class UserRepositoryImpl implements UserRepository {
  @override
  Future<Result<UserEntity>> getUser(String id) async {
    try {
      return Right(await _remote.getUser(id));
    } on UserNotFoundException catch (e) {
      return Left(NotFoundFailure(e.message));
    } on NetworkException catch (e) {
      return Left(NetworkFailure(e.message));
    }
  }
}
```

**Rule:** Data exceptions are _implementation details_. The domain layer only knows about `Failure` variants — never let `NetworkException` or `CacheException` leak past the repository boundary.
