# Code Documentation Patterns

This guide explains how to write effective documentation for your code.

## Documentation Rules

1. **Always document public APIs** - Every class, method, function that's part of the public API
2. **Use `///` for documentation** - Not `//` comments
3. **Start with a summary line** - One line description of what this does
4. **Add details if not obvious** - Explain why, not just what
5. **Include examples for complex cases** - Show usage patterns
6. **Document parameters and returns** - Use `[param]` syntax
7. **Avoid obvious documentation** - Don't document what the code clearly shows

## Quick Reference

### Class Documentation

```dart
/// Represents a user in the system.
///
/// This class holds immutable user data and inherits equality
/// comparison from [BaseEntity].
///
/// Example:
/// ```dart
/// final user = UserEntity(
///   id: 'user-123',
///   name: 'John Doe',
///   email: 'john@example.com',
/// );
/// ```
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

### Method Documentation

```dart
/// Fetches a single user by ID.
///
/// Returns [Success] wrapped [UserEntity] if the user is found.
/// Returns [Failure] wrapped [Exception] if fetch fails.
///
/// Parameters:
/// - [userId]: The unique identifier of the user to fetch
///
/// Example:
/// ```dart
/// final result = await getUserUseCase.call('user-123');
/// result.fold(
///   (user) => print('User found: ${user.name}'),
///   (error) => print('Error: ${error.message}'),
/// );
/// ```
Future<Result<UserEntity, Exception>> call(String userId) {
  return repository.getUser(userId);
}
```

### Property Documentation

```dart
/// The unique identifier for this user in the system.
///
/// Format: 'user-{uuid}' or '{auth-provider}:{id}'
final String id;

/// Whether the user account is currently active.
///
/// Inactive accounts cannot log in.
bool isActive;

/// Optional URL to user's profile picture.
///
/// May be null if user hasn't uploaded an avatar.
String? avatarUrl;
```

## Documentation Examples

### Simple Class

```dart
/// Authenticates a user with email and password.
class AuthenticateUseCase {
  // ...
}
```

### Complex Class

```dart
/// Represents an application feature with dependency injection.
///
/// Features are self-contained packages that include:
/// - Domain layer (entities, repositories, usecases)
/// - Data layer (models, datasources, repositories)
/// - Presentation layer (cubits, pages, widgets)
///
/// Example:
/// ```dart
/// final feature = UserProfileFeature();
/// final userCubit = feature.getUserCubit();
/// ```
class Feature {
  // ...
}
```

### Simple Method

```dart
/// Logs a debug message.
void debug(String message) {
  // ...
}
```

### Complex Method

```dart
/// Fetches and caches user data from remote source.
///
/// This method implements a cache-first strategy:
/// 1. Checks local cache for user
/// 2. If not found, fetches from remote API
/// 3. Saves result to local cache
/// 4. Returns mapped entity
///
/// Parameters:
/// - [userId]: The ID of the user to fetch
/// - [forceRefresh]: If true, skip cache and fetch from remote
///
/// Returns:
/// - [Success] with [UserEntity] if fetch succeeds
/// - [Failure] with [Exception] if fetch fails
///
/// Throws:
/// - [CacheException] if unable to save to cache (not thrown, wrapped in Result)
/// - [NetworkException] if API call fails (not thrown, wrapped in Result)
///
/// Example:
/// ```dart
/// final result = await repository.getUser('user-123');
/// result.fold(
///   (user) => print('Loaded: ${user.name}'),
///   (error) => print('Failed: ${error.message}'),
/// );
/// ```
Future<Result<UserEntity, Exception>> getUser(
  String userId, {
  bool forceRefresh = false,
}) async {
  // Implementation...
}
```

### Exception Documentation

```dart
/// Thrown when a user is not found in the system.
///
/// This exception is raised in data layer and wrapped in [Failure]
/// before being returned to domain and presentation layers.
class UserNotFoundException implements Exception {
  UserNotFoundException(this.userId);

  /// The ID of the user that was not found.
  final String userId;

  @override
  String toString() => 'User not found: $userId';
}
```

### Enum Documentation

```dart
/// Defines the different roles a user can have in the system.
///
/// - [admin]: Full system access, can manage other users
/// - [editor]: Can create and edit content
/// - [viewer]: Read-only access
enum UserRole {
  /// Full system access, can manage all resources.
  admin,

  /// Can create and edit content.
  editor,

  /// Read-only access to resources.
  viewer,
}
```

## What NOT to Document

// ❌ Don't document obviouscode

```dart
// ❌ WRONG - Obvious from code
/// Sets the user's name.
void setName(String value) {
  name = value;
}

// ✅ CORRECT - No documentation needed for obvious methods
void setName(String value) {
  name = value;
}

// ❌ WRONG - Documenting local variables
void fetchUser() {
  // Get the user ID from the request
  var userId = request.params['id'];

  // Call the use case
  var result = await useCase.call(userId);
}

// ✅ CORRECT - No documentation for obvious local variables
void fetchUser() {
  final userId = request.params['id'];
  final result = await useCase.call(userId);
}
```

## Documentation Tips

### Use Cross-Reference Syntax

Link to related classes and methods:

```dart
/// Implements [UserRepository] to fetch data from remote API.
///
/// Uses [UserRemoteDataSource] for HTTP calls and [UserMapper]
/// to convert [UserModel] to [UserEntity].
///
/// See also:
/// - [UserLocalDataSource] for local caching
/// - [UserRepositoryImpl] for the main implementation
class UserRemoteDataSource {
  // ...
}
```

### Include Return Type Information

```dart
/// Processes all users and returns their display names.
///
/// Returns: [List<String>] containing user names in order
/// Returns: Empty list if no users exist
List<String> getUserDisplayNames() {
  // ...
}
```

### Document Null Safety

```dart
/// Gets the user's nickname if set.
///
/// Returns: `String` if user has set a nickname
/// Returns: `null` if no nickname is set
String? nickname();
```

### Document Async Behavior

```dart
/// Asynchronously loads user data from remote server.
///
/// This method requires network connectivity. Consider using
/// [loadFromCache] for offline scenarios.
///
/// Returns: [Future<UserEntity>] that completes when data loads
///
/// Throws: [TimeoutException] if network request takes >30 seconds
Future<UserEntity> loadFromRemote(String userId) async {
  // ...
}
```

### Document Callbacks

```dart
/// Builds a list item widget for each user.
///
/// Parameters:
/// - [itemBuilder]: Called for each user in the list
///   - Receives [BuildContext] and [UserEntity]
///   - Returns [Widget] to display for that user
///
/// Example:
/// ```dart
/// buildUserList(
///   users: users,
///   itemBuilder: (context, user) => UserCard(user: user),
/// )
/// ```
Widget buildUserList({
  required List<UserEntity> users,
  required Widget Function(BuildContext, UserEntity) itemBuilder,
}) {
  // ...
}
```

## Generating Documentation

Generate documentation HTML from your comments:

```bash
# Generate docs for entire project
dart doc

# Documentation is generated in doc/api/
# Open doc/api/index.html in browser to view
```

## IDE Support

Most IDEs use the documentation comments to provide:
- **Hover tooltips** - See docs when hovering over a symbol
- **Autocomplete hints** - See signature and docs in autocomplete
- **Parameter hints** - See docs for method parameters
- **Quick docs** - Keyboard shortcut to view full documentation

Take advantage of these IDE features by writing clear, concise documentation.
