# Linting Rules Reference

This document explains the most important linting rules enforced by the `very_good_analysis` package.

## Table of Contents

1. [Immutability and Performance](#immutability-and-performance)
2. [Style and Readability](#style-and-readability)
3. [Dart and Flutter Best Practices](#dart-and-flutter-best-practices)
4. [Avoidance Rules](#avoidance-rules)

## Immutability and Performance

### prefer_const_constructors

**Rule:** Use `const` keyword whenever possible.

**Why:** Const constructors enable compiler optimizations and reduce memory usage.

```dart
// ✅ CORRECT
class UserCard extends StatelessWidget {
  const UserCard({Key? key, required this.user}) : super(key: key);

  final UserEntity user;

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Text('User'),
      ),
    );
  }
}

// ❌ INCORRECT - Missing const
class UserCard extends StatelessWidget {
  UserCard({Key? key, required this.user}) : super(key: key);

  final UserEntity user;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Text('User'),
      ),
    );
  }
}
```

### prefer_final_fields

**Rule:** Fields should be `final` when they are not reassigned.

**Why:** Prevents accidental mutations and clarifies intent.

```dart
// ✅ CORRECT
class UserRepository {
  const UserRepository({required this.remoteDataSource});

  final UserDataSource remoteDataSource;  // final

  Future<UserEntity> getUser(String id) async {
    return await remoteDataSource.getUser(id);
  }
}

// ❌ INCORRECT - Missing final
class UserRepository {
  UserRepository({required this.remoteDataSource});

  UserDataSource remoteDataSource;  // Not final
}
```

### prefer_final_locals

**Rule:** Local variables should be `final` when not reassigned.

**Why:** Makes intent clear and prevents accidental reassignments.

```dart
// ✅ CORRECT
void processUser(String userId) {
  final user = await getUserUseCase.call(userId);  // final
  final name = user.name.toUpperCase();             // final
  print(name);
}

// ❌ INCORRECT - Missing final
void processUser(String userId) {
  var user = await getUserUseCase.call(userId);     // var (could be reassigned)
  var name = user.name.toUpperCase();               // var
  print(name);
}
```

### sized_box_for_whitespace

**Rule:** Use `SizedBox` instead of `Container` for empty space.

**Why:** `SizedBox` is more efficient for the rendering engine.

```dart
// ✅ CORRECT - Use SizedBox for spacing
Column(
  children: [
    const Text('Title'),
    const SizedBox(height: 16),  // Efficient
    const Text('Subtitle'),
  ],
)

// ❌ INCORRECT - Container for spacing
Column(
  children: [
    const Text('Title'),
    Container(height: 16),  // Less efficient
    const Text('Subtitle'),
  ],
)
```

## Style and Readability

### require_trailing_commas

**Rule:** Add trailing commas to multi-line collections and function calls.

**Why:** Enables auto-formatting to work properly and improves readability.

```dart
// ✅ CORRECT - Trailing commas
final result = await useCase.call(
  userId: 'user-123',
  includeDetails: true,  // <- Trailing comma
);

const colors = [
  Colors.red,
  Colors.blue,
  Colors.green,  // <- Trailing comma
];

// ❌ INCORRECT - No trailing commas
final result = await useCase.call(
  userId: 'user-123',
  includeDetails: true  // Missing comma
);
```

### always_declare_return_types

**Rule:** Always specify return types for functions and methods.

**Why:** Makes code more self-documenting and enables better IDE support.

```dart
// ✅ CORRECT - Type declared
Future<List<UserEntity>> getAllUsers() async {
  return await repository.getUsers();
}

String getUserName(UserEntity user) {
  return user.name.toUpperCase();
}

// ❌ INCORRECT - Type missing
getAllUsers() async {  // No return type
  return await repository.getUsers();
}

getUserName(UserEntity user) {  // No return type
  return user.name.toUpperCase();
}
```

### prefer_single_quotes

**Rule:** Use single quotes (`'`) instead of double quotes (`"`).

**Why:** Consistency and reduced escaping needs.

```dart
// ✅ CORRECT - Single quotes
final message = 'Hello World';
final name = 'John Doe';

// ❌ INCORRECT - Double quotes
final message = "Hello World";
final name = "John Doe";

// Exception: Double quotes when single quote in string
final quote = "It's a beautiful daand";  // ✅ Acceptable
final quote = 'It\'s a beautiful daand';  // ✅ Also acceptable
```

### curland_braces_in_flow_control_structures

**Rule:** Always use braces for if, else, for, while, even for single statements.

**Why:** Prevents subtle bugs and improves readability.

```dart
// ✅ CORRECT - Always use braces
if (user != null) {
  processUser(user);
}

for (var i = 0; i < 10; i++) {
  print(i);
}

// ❌ INCORRECT - Missing braces
if (user != null)
  processUser(user);

for (var i = 0; i < 10; i++)
  print(i);
```

### prefer_interpolation_to_compose_strings

**Rule:** Use string interpolation (`$variable`) instead of concatenation (`+`).

**Why:** More readable and efficient.

```dart
// ✅ CORRECT - Interpolation
final greeting = 'Hello, $name!';
final info = 'User $id is $age andears old';

// ❌ INCORRECT - Concatenation
final greeting = 'Hello, ' + name + '!';
final info = 'User ' + id + ' is ' + age.toString() + ' andears old';
```

### unnecessary_brace_in_string_interps

**Rule:** Avoid unnecessary braces in string interpolation.

**Why:** Simpler and more readable code.

```dart
// ✅ CORRECT - No braces needed
final message = 'User: $name is active';

// ❌ INCORRECT - Unnecessary braces
final message = 'User: ${name} is active';
```

### prefer_collection_literals

**Rule:** Use collection literals (`[]`, `{}`) instead of constructors.

**Why:** More concise and idiomatic Dart.

```dart
// ✅ CORRECT - Literals
final list1 = [1, 2, 3];
final list2 = <String>['a', 'b'];
final map = {'key': 'value'};

// ❌ INCORRECT - Constructors
final list1 = List.from([1, 2, 3]);
final list2 = List<String>();
final map = Map<String, String>();
```

### sort_constructors_first

**Rule:** Define constructors before other methods in a class.

**Why:** Standard convention, easier to locate and understand object creation.

```dart
// ✅ CORRECT - Constructor first
class UserEntity extends BaseEntity {
  const UserEntity({
    required this.id,
    required this.name,
  });

  final String id;
  final String name;

  @override
  List<Object?> get props => [id, name];

  String getDisplayName() => name.toUpperCase();
}

// ❌ INCORRECT - Methods before constructor
class UserEntity extends BaseEntity {
  String getDisplayName() => name.toUpperCase();

  @override
  List<Object?> get props => [id, name];

  const UserEntity({
    required this.id,
    required this.name,
  });

  final String id;
  final String name;
}
```

## Dart and Flutter Best Practices

### avoid_print

**Rule:** Never use `print()` in production code.

**Why:** Use proper logging instead. Print goes to stdout, not to app logs.

```dart
// ✅ CORRECT - Use logging
log.debug('User loaded: ${user.name}');
log.info('Starting sync process');
log.error('Error occurred: ${error.message}');

// ❌ INCORRECT - Using print
print('User: $user');
debugPrint('Loading...');
```

### use_key_in_widget_constructors

**Rule:** All widgets should accept a `Key` parameter.

**Why:** Enables proper widget state management and testing.

```dart
// ✅ CORRECT - Key parameter included
class UserCard extends StatelessWidget {
  const UserCard({
    Key? key,
    required this.user,
  }) : super(key: key);

  final UserEntity user;

  @override
  Widget build(BuildContext context) {
    return Card(child: Text(user.name));
  }
}

// ❌ INCORRECT - Missing Key parameter
class UserCard extends StatelessWidget {
  const UserCard({required this.user});

  final UserEntity user;

  @override
  Widget build(BuildContext context) {
    return Card(child: Text(user.name));
  }
}
```

### use_build_context_synchronously

**Rule:** Don't use `BuildContext` after asynchronous operations without checking if widget is still mounted.

**Why:** Prevents runtime errors if widget is disposed before async completes.

> **Note on `dart fix --apply`:** The commands shown in this file (`dart fix --apply`,
> `dart format`, `dart analyze`) modify source files. Always review changes
> interactively before applying them to production code — confirm with your team
> before running bulk auto-fixes on a shared branch.

```dart
// Good — check mounted before using context
void _loadUser() async {
  final result = await loadUserData();

  if (!mounted) return;

  Navigator.of(context).pushReplacementNamed('/home');
}

// Avoid — uses context after await without mounted check
void _loadUser() async {
  final result = await loadUserData();
  Navigator.of(context).pushReplacementNamed('/home'); // unsafe
}
```

### prefer_is_empty / prefer_is_not_empty

**Rule:** Use `.isEmpty` and `.isNotEmpty` instead of checking length.

**Why:** More readable and idiomatic.

```dart
// ✅ CORRECT
if (users.isEmpty) {
  return CircularProgressIndicator();
}

if (message.isNotEmpty) {
  showSnackBar(message);
}

// ❌ INCORRECT
if (users.length == 0) {
  return CircularProgressIndicator();
}

if (message.length > 0) {
  showSnackBar(message);
}
```

### cascade_invocations

**Rule:** Use cascade operator (`..`) for multiple operations on same object.

**Why:** More concise and expressive.

```dart
// ✅ CORRECT - Cascade
final user = UserEntity(id: '1', name: 'John')
  ..email = 'john@example.com'
  ..phone = '555-0123';

// ❌ INCORRECT - Multiple line assignments
final user = UserEntity(id: '1', name: 'John');
user.email = 'john@example.com';
user.phone = '555-0123';
```

### avoid_redundant_argument_values

**Rule:** Don't pass arguments if they match the default value.

**Why:** Reduces noise, makes intentional overrides clear.

```dart
// ✅ CORRECT
ListView(
  children: items,
);

// ❌ INCORRECT - Using default value explicitly
ListView(
  scrollDirection: Axis.vertical,  // Default, don't specify
  children: items,
);
```

## Avoidance Rules

### avoid_empty_else

**Rule:** Don't have empty else blocks.

**Why:** Unnecessary code that adds no value.

```dart
// ✅ CORRECT
if (isValid) {
  processData();
}

// ❌ INCORRECT
if (isValid) {
  processData();
} else {
  // Do nothing
}
```

### avoid_null_checks_in_equality_operators

**Rule:** Use `Equatable` mixin instead of custom equality checks.

**Why:** Better, more consistent equality handling.

```dart
// ✅ CORRECT - Use Equatable
class UserEntity extends Equatable {
  const UserEntity({required this.id, required this.name});

  final String id;
  final String name;

  @override
  List<Object?> get props => [id, name];
}

// ❌ INCORRECT - Custom equality
class UserEntity {
  const UserEntity({required this.id, required this.name});

  final String id;
  final String name;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserEntity &&
      runtimeType == other.runtimeType &&
      id == other.id &&
      name == other.name;
}
```

### unnecessary_this

**Rule:** Don't use `this.` unless necessary for clarity.

**Why:** Reduces noise, unless clarifying shadowed names.

```dart
// ✅ CORRECT - No unnecessary this
class UserRepository {
  UserRepository({required UserDataSource dataSource}) {
    remoteDataSource = dataSource;
  }

  late final UserDataSource remoteDataSource;
}

// ❌ INCORRECT - Unnecessary this
class UserRepository {
  UserRepository({required UserDataSource dataSource}) {
    this.remoteDataSource = dataSource;
  }

  late final UserDataSource remoteDataSource;
}
```
