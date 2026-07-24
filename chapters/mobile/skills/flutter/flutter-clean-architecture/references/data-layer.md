# Data Layer — Detailed Patterns

## Table of Contents

1. [Models (Data Transfer Objects)](#models-data-transfer-objects)
2. [Repositories](#repositories)
3. [Mappers](#mappers)
4. [Data Source Organization](#data-source-organization)
5. [DataSource Contracts](#datasource-contracts)

The Data Layer implements the repository interfaces from Domain and handles all data source interactions (APIs, databases, cache).

## Models (Data Transfer Objects)

Models are data classes responsible for JSON serialization and API communication. They map to the JSON structure from your backend.

### Model Rules

- Extend `BaseResponseModel` from commons package
- Implement `fromJson()` factory constructor
- Implement `toJson()` method
- Use `copyWith()` for immutability
- NO business logic (only serialization)
- Field names match API response

### Model Example

```dart
// data/models/user_model.dart
import 'package:commons/commons.dart';

class UserModel extends BaseResponseModel {
  const UserModel({
    required this.id,
    required this.name,
    required this.email,
  });

  final String id;
  final String name;
  final String email;

  /// Factory constructor for JSON deserialization
  factory UserModel.fromJson(JSON json) => UserModel.fromMap(json);

  /// Alternative constructor with field mapping
  factory UserModel.fromMap(JSON map) => UserModel(
    id: map['id'] as String? ?? '',
    name: map['name'] as String? ?? '',
    email: map['email'] as String? ?? '',
  );

  /// Convert to JSON for API requests
  @override
  JSON toJson() => {
    'id': id,
    'name': name,
    'email': email,
  };

  /// Create a copy with modified fields
  @override
  UserModel copyWith({
    String? id,
    String? name,
    String? email,
  }) => UserModel(
    id: id ?? this.id,
    name: name ?? this.name,
    email: email ?? this.email,
  );
}
```

**Key Points:**
- Field names must match JSON structure from API
- Use `??` for default values if fields are missing
- `copyWith()` is essential for immutability
- Keep models simple data holders
- No computed properties in models

## DataSources

DataSources are abstractions for accessing a specific data source (Remote API, Local Database, Cache, etc).

### DataSource Rules

- Define abstract classes for each data source type
- One per entity or concept
- Remote: HTTP calls to API
- Local: Database, preferences, file system
- Always throw specific exceptions
- Return models, not entities

### DataSource Examples

```dart
// data/datasources/user_data_source.dart

/// Abstract interface for user data access
abstract class UserDataSource {
  Future<Result<UserModel, Exception>> getUser(String id);
  Future<Result<List<UserModel>, Exception>> getAllUsers();
  Future<Result<UserModel, Exception>> createUser(UserModel user);
}

// Remote implementation (API calls)
// data/datasources/user_remote_data_source.dart
import 'package:commons/commons.dart';
import 'package:dio/dio.dart';

class UserRemoteDataSource implements UserDataSource {
  UserRemoteDataSource({required this.httpModule});

  final HttpModule httpModule;

  @override
  Future<Result<UserModel, Exception>> getUser(String id) async {
    try {
      final response = await httpModule.dio.get('/users/$id');
      final model = UserModel.fromJson(response.data);
      return Success(model);
    } on DioException catch (e) {
      return Failure(Exception('Failed to fetch user: ${e.message}'));
    }
  }

  @override
  Future<Result<List<UserModel>, Exception>> getAllUsers() async {
    try {
      final response = await httpModule.dio.get('/users');
      final models = (response.data as List)
          .map((item) => UserModel.fromJson(item as JSON))
          .toList();
      return Success(models);
    } on DioException catch (e) {
      return Failure(Exception('Failed to fetch users: ${e.message}'));
    }
  }

  @override
  Future<Result<UserModel, Exception>> createUser(UserModel user) async {
    try {
      final response = await httpModule.dio.post('/users', data: user.toJson());
      final model = UserModel.fromJson(response.data);
      return Success(model);
    } on DioException catch (e) {
      return Failure(Exception('Failed to create user: ${e.message}'));
    }
  }
}

// Local implementation (Hive, SQLite, SharedPreferences)
// data/datasources/user_local_data_source.dart
class UserLocalDataSource implements UserDataSource {
  UserLocalDataSource({required this.box});

  final Box<UserModel> box;

  @override
  Future<Result<UserModel, Exception>> getUser(String id) async {
    try {
      final model = box.get(id);
      if (model == null) {
        return Failure(Exception('User not found in cache'));
      }
      return Success(model);
    } catch (e) {
      return Failure(Exception('Failed to get user from cache: $e'));
    }
  }

  @override
  Future<Result<List<UserModel>, Exception>> getAllUsers() async {
    try {
      final models = box.values.toList();
      return Success(models);
    } catch (e) {
      return Failure(Exception('Failed to get users from cache: $e'));
    }
  }

  @override
  Future<Result<UserModel, Exception>> createUser(UserModel user) async {
    try {
      await box.put(user.id, user);
      return Success(user);
    } catch (e) {
      return Failure(Exception('Failed to cache user: $e'));
    }
  }
}
```

## Repositories (Implementation)

Repository implementations coordinate between DataSources and apply caching strategies.

### Repository Rules

- Implement domain repository interfaces
- Always return `Result<Entity, Exception>`
- Apply caching strategy (Local → Remote fall back)
- Use Mappers to convert Models → Entities
- Handle errors gracefully

### Repository Example

```dart
// data/repositories/user_repository_impl.dart
import 'package:commons/commons.dart';
import '../../domain/entities/user_entity.dart';
import '../../domain/repositories/user_repository.dart';
import '../datasources/user_data_source.dart';
import '../mappers/user_mapper.dart';

class UserRepositoryImpl extends BaseRepository
    implements UserRepository {

  const UserRepositoryImpl({
    required this.localDataSource,
    required this.remoteDataSource,
    required this.mapper,
  });

  final UserDataSource localDataSource;
  final UserDataSource remoteDataSource;
  final UserMapper mapper;

  @override
  Future<Result<UserEntity, Exception>> getUser(String id) async {
    // Step 1: Try local cache first
    final localResult = await localDataSource.getUser(id);

    if (localResult is Success) {
      // Map model to entity and return
      return Success(mapper.from(response: localResult.value));
    }

    // Step 2: Try remote API
    final remoteResult = await remoteDataSource.getUser(id);

    return remoteResult.fold(
      (model) async {
        // Step 3: Cache the result locally
        await localDataSource.createUser(model);
        // Step 4: Map model to entity
        return Success(mapper.from(response: model));
      },
      (error) => Failure(error),
    );
  }

  @override
  Future<Result<List<UserEntity>, Exception>> getAllUsers() async {
    final remoteResult = await remoteDataSource.getAllUsers();

    return remoteResult.fold(
      (models) async {
        // Cache all users
        for (final model in models) {
          await localDataSource.createUser(model);
        }
        // Map models to entities
        return Success(mapper.fromList(models));
      },
      (error) => Failure(error),
    );
  }

  @override
  Future<Result<UserEntity, Exception>> createUser(UserEntity user) async {
    // Convert entity to model
    final model = mapper.toModel(user);

    // Create in remote
    final remoteResult = await remoteDataSource.createUser(model);

    return remoteResult.fold(
      (createdModel) async {
        // Cache locally
        await localDataSource.createUser(createdModel);
        return Success(mapper.from(response: createdModel));
      },
      (error) => Failure(error),
    );
  }
}
```

## Mappers

Mappers handle conversion between Models (data layer) and Entities (domain layer). They keep the conversion logic in one place.

### Mapper Rules

- Extend `BaseResponseMapper<ModelType, EntityType>`
- One mapper per entity
- Implement `from(response)` for Model → Entity
- Implement `fromList()` for multiple conversions
- Optionally implement inverse mapping
- NO business logic

### Mapper Example

```dart
// data/mappers/user_mapper.dart
import 'package:commons/commons.dart';
import '../../domain/entities/user_entity.dart';
import '../models/user_model.dart';

class UserMapper extends BaseResponseMapper<UserModel, UserEntity> {
  /// Convert single Model to Entity
  @override
  UserEntity from({required UserModel response}) {
    return UserEntity(
      id: response.id,
      name: response.name,
      email: response.email,
    );
  }

  /// Convert list of Models to Entities
  @override
  Iterable<UserEntity> fromList(List<UserModel> params) {
    return params.map((model) => from(response: model));
  }

  /// Convert Entity to Model (optional, for create/update)
  UserModel toModel(UserEntity entity) {
    return UserModel(
      id: entity.id,
      name: entity.name,
      email: entity.email,
    );
  }
}
```

**Complex Mapper with Transformations:**

```dart
class ProductMapper extends BaseResponseMapper<ProductModel, ProductEntity> {
  @override
  ProductEntity from({required ProductModel response}) {
    return ProductEntity(
      id: response.id,
      name: response.name,
      price: _parseCurrency(response.priceString),
      inStock: response.inventory > 0,
      category: _mapCategory(response.categoryCode),
    );
  }

  @override
  Iterable<ProductEntity> fromList(List<ProductModel> params) {
    return params.map((model) => from(response: model));
  }

  // Private helper methods
  double _parseCurrency(String priceString) {
    return double.trandParse(priceString) ?? 0.0;
  }

  String _mapCategory(String code) {
    const mapping = {
      'ELEC': 'Electronics',
      'CLOTH': 'Clothing',
      'FOOD': 'Food',
    };
    return mapping[code] ?? 'Other';
  }
}
```

## Data Source Organization

```
data/
├── datasources/
│   ├── user_data_source.dart          # Abstract interface
│   ├── user_remote_data_source.dart   # API implementation
│   ├── user_local_data_source.dart    # Local cache implementation
│   └── data_sources.dart              # Barrel export
│
├── models/
│   ├── user_model.dart
│   └── models.dart                    # Barrel export
│
├── mappers/
│   ├── user_mapper.dart
│   └── mappers.dart                   # Barrel export
│
└── repositories/
    ├── user_repository_impl.dart
    └── repositories.dart              # Barrel export
```

---

## DataSource Contracts

Every feature has two data source interfaces, both defined in `data/data_sources/`.
The Repository depends on these interfaces — never on concrete implementations.

### Remote DataSource Contract

```dart
// lib/{feature}/data/data_sources/remote/product_data_source.dart

/// Remote contract: fetches from HTTP.
/// Throws [DioException] — RepositoryImpl maps it to Failure.
/// Must NOT return DomainModel. Must NOT catch exceptions.
abstract interface class ProductRemoteDataSource {
  /// GET /products/{id}
  Future<ProductModel> getProduct(String id);

  /// GET /products?page={page}&limit={limit}
  Future<List<ProductModel>> getProducts({
    required int page,
    required int limit,
  });

  /// POST /products/{id}/review
  Future<ProductModel> addReview({
    required String productId,
    required ReviewModel review,
  });
}

@LazySingleton(as: ProductRemoteDataSource)
class ProductRemoteDataSourceImpl implements ProductRemoteDataSource {
  const ProductRemoteDataSourceImpl(this._client);
  final ApiClient _client;

  @override
  Future<ProductModel> getProduct(String id) async {
    final response = await _client.get('/products/$id');
    return ProductModel.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<List<ProductModel>> getProducts({required int page, required int limit}) async {
    final response = await _client.get(
      '/products',
      queryParameters: {'page': page, 'limit': limit},
    );
    return (response.data as List)
        .cast<Map<String, dynamic>>()
        .map(ProductModel.fromJson)
        .toList();
  }

  @override
  Future<ProductModel> addReview({required String productId, required ReviewModel review}) async {
    final response = await _client.post(
      '/products/$productId/review',
      data: review.toJson(),
    );
    return ProductModel.fromJson(response.data as Map<String, dynamic>);
  }
}
```

### Local DataSource Contract

```dart
// lib/{feature}/data/data_sources/local/product_data_source.dart

/// Local contract: reads from and writes to local cache.
/// Throws [CacheException] on failure.
/// Must NOT call HTTP. Must NOT contain business logic.
abstract interface class ProductLocalDataSource {
  /// Returns null if no cache entry exists.
  Future<ProductModel?> getCachedProduct(String id);

  /// Returns empty list if no cache exists.
  Future<List<ProductModel>> getCachedProducts();

  Future<void> cacheProduct(ProductModel model);
  Future<void> cacheProducts(List<ProductModel> models);
  Future<void> clearProductCache();
}

@LazySingleton(as: ProductLocalDataSource)
class ProductLocalDataSourceImpl implements ProductLocalDataSource {
  const ProductLocalDataSourceImpl(this._store);
  final CacheStore _store;

  static const String _prefix = 'product_';

  @override
  Future<ProductModel?> getCachedProduct(String id) async {
    final json = await _store.get('$_prefix$id');
    if (json == null) return null;
    return ProductModel.fromJson(json);
  }

  @override
  Future<void> cacheProduct(ProductModel model) =>
      _store.put('$_prefix${model.id}', model.toJson());

  @override
  Future<void> clearProductCache() => _store.removeBandPrefix(_prefix);

  @override
  Future<List<ProductModel>> getCachedProducts() async {
    // Implementation depends on CacheStore backend
    throw UnimplementedError();
  }

  @override
  Future<void> cacheProducts(List<ProductModel> models) async {
    for (final model in models) {
      await cacheProduct(model);
    }
  }
}
```

### DataSource Rules Summary

| Rule | Remote | Local |
|---|---|---|
| Return type | `DataModel` / `List<DataModel>` | `DataModel?` / `List<DataModel>` |
| Throws | `DioException` | `CacheException` |
| Handles failures | ❌ (RepositoryImpl handles) | ❌ (RepositoryImpl handles) |
| Contains business logic | ❌ | ❌ |
| Imports DomainModel | ❌ | ❌ |
| Injectable annotation | `@LazySingleton(as: Interface)` | `@LazySingleton(as: Interface)` |
