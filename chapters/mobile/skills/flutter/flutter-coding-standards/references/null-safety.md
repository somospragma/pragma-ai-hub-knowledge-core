# Null Safety Reference

Extended patterns for Dart null safety (`sound null safety` — Dart 2.12+).

## Table of Contents

1. [Type Declarations](#type-declarations)
2. [Null-Aware Operators](#null-aware-operators)
3. [Null Narrowing](#null-narrowing)
4. [late vs Nullable](#late-vs-nullable)
5. [Common Anti-Patterns](#common-anti-patterns)

---

## Type Declarations

```dart
// Non-nullable — compiler guarantees never null
String userId = 'user-123';

// Nullable — must handle null explicitly
String? avatarUrl;

// Required in constructor (non-nullable field must be set)
class UserEntity {
  const UserEntity({required this.id, required this.name});
  final String id;
  final String name;
}

// Optional in constructor (nullable field can be omitted)
class UserProfile {
  const UserProfile({required this.userId, this.bio});
  final String userId;
  final String? bio;
}
```

---

## Null-Aware Operators

```dart
// ?? — null-coalescing (provide fallback)
final displayName = user.nickname ?? user.name;

// ??= — null-assignment (assign only if null)
String? cached;
cached ??= fetchFromNetwork();  // Only fetches if cached is null

// ?. — safe navigation (short-circuit on null)
final city = user?.address?.city;        // null if user or address is null
final upper = user?.name.toUpperCase();  // null if user is null

// !  — force-unwrap (ONLY when you're certain it's non-null)
// Use sparingly — prefer null checks instead
final id = user!.id;  // Throws if user is null
```

---

## Null Narrowing

Dart narrows nullable types inside null checks — use this instead of `!`:

```dart
// ✅ CORRECT — type narrowed inside if block
String? maybeName;
if (maybeName != null) {
  // maybeName is String (non-nullable) here
  print(maybeName.toUpperCase());
}

// ✅ CORRECT — early return to narrow
Future<void> loadUser(String? userId) async {
  if (userId == null) return;
  // userId is String (non-nullable) hereafter
  final user = await repository.getUser(userId);
}

// ✅ CORRECT — pattern matching (Dart 3+)
switch (user) {
  case UserEntity(:final name) when name.isNotEmpty:
    print('User: $name');
}

// ❌ INCORRECT — force-unwrap without check
void display(String? name) {
  print(name!.toUpperCase());  // Throws NullPointerException at runtime
}

// ❌ INCORRECT — null check that doesn't narrow (class field)
class UserController {
  String? name;
  void display() {
    if (name != null) {
      // In classes, 'name' could be set to null between the check and use
      // This won't compile without ! (but ! is still risky here)
    }
  }
}
// Fix: use local variable
void displayFixed() {
  final localName = name;
  if (localName != null) {
    print(localName);  // localName is narrowed
  }
}
```

---

## `late` vs Nullable

Choose based on whether the field is guaranteed to be assigned before use:

```dart
// late — field WILL be set (before first use), not null
// Throws LateInitializationError if read before set
class UserRepository {
  late final UserDataSource _dataSource;

  void initialize(UserDataSource ds) {
    _dataSource = ds;  // Set exactly once
  }
}

// Nullable — field MAY be null at any time
class UserCache {
  UserEntity? _cachedUser;

  UserEntity? get current => _cachedUser;

  void invalidate() {
    _cachedUser = null;  // Can be reset to null
  }
}

// Decision guide:
// - Must be non-null once initialized → late final
// - Can be null at any point → String?
// - Always non-null from construction → final (set in constructor)
```

---

## Common Anti-Patterns

```dart
// ❌ DON'T — assign null to non-nullable
String name = null;         // Compile error

// ❌ DON'T — use ! without a narrowing check
String? value = getOptional();
print(value!.length);       // Throws if null

// ❌ DON'T — use 'as String' to strip nullable
String? maybe = getOptional();
print((maybe as String).length);  // Throws if null — use narrowing instead

// ❌ DON'T — redundant null check on non-nullable
String name = 'John';
if (name != null) {         // Compiler warns: always true
  print(name);
}

// ✅ DO — prefer null-coalescing for defaults
final label = user.displayName ?? 'Anonymous';

// ✅ DO — prefer safe navigation for chains
final zip = user?.address?.zipCode ?? 'Unknown';

// ✅ DO — local variable narrowing for class fields
final email = this.email;
if (email != null) {
  sendConfirmation(email);
}
```
