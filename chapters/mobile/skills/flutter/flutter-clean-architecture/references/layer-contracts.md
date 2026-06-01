# Layer Contracts — Base Classes and Shared Abstractions

## Table of Contents

1. [UseCase — Base Contract](#1-usecase--base-contract)
2. [Failure — Sealed Error Type](#2-failure--sealed-error-type)
3. [Repository — Domain Contract](#3-repository--domain-contract)
4. [DataSource — Data Layer Contracts](#4-datasource--data-layer-contracts)
5. [CacheStore — Local Storage Abstraction](#5-cachestore--local-storage-abstraction)
6. [Mapper — Cross-Layer Conversion](#6-mapper--cross-layer-conversion)
7. [UIMapper — Domain → Presentation Conversion](#7-uimapper--domain--presentation-conversion)
8. [ApiClient — HTTP Abstraction](#8-apiclient--http-abstraction)
9. [BLoC — Presentation Contract](#9-bloc--presentation-contract)
10. [Contract Summary Table](#10-contract-summary-table)
11. [Dependency Direction — Full Diagram](#11-dependency-direction--full-diagram)

Canonical reference for the interfaces and generic classes that define layer boundaries.
All abstractions live in `core/` (single project) or `packages/core/` (monorepo).

---

## 1. UseCase — Base Contract

Every use case implements one of these interfaces. The domain **never** returns
raw types — always `Result<T, E>` to force explicit error handling.

```dart
// lib/core/usecase/usecase.dart
import 'package:commons/commons.dart';

/// Use case with parameters.
abstract interface class UseCase<T, P> {
  Future<Result<T, Exception>> call(P params);
}

/// Use case without parameters.
abstract interface class UseCaseNoParams<T> {
  Future<Result<T, Exception>> call();
}

/// Use case that returns a Stream instead of a Future.
abstract interface class StreamUseCase<T, P> {
  Stream<Result<T, Exception>> call(P params);
}
```

### Rules

- One `UseCase` = **one single business operation**.
- If multiple parameters are needed, create a `@freezed` Params class:

```dart
@freezed
class GetProductParams with _$GetProductParams {
  const factory GetProductParams({
    required String id,
    required String locale,
  }) = _GetProductParams;
}

@injectable
class GetProductUseCase implements UseCase<Product, GetProductParams> {
  const GetProductUseCase(this._repository);
  final ProductRepository _repository;

  @override
  Future<Result<Product, Exception>> call(GetProductParams params) =>
      _repository.getProduct(id: params.id, locale: params.locale);
}
```

- **Forbidden**: presentation logic, Flutter imports, Data layer imports.

---

## 2. Failure — Sealed Error Type

A single `Failure` type shared across the entire app. Features can extend it
if they need specific errors.

```dart
// lib/core/error/failure.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'failure.freezed.dart';

@freezed
sealed class Failure with _$Failure {
  /// No internet connection.
  const factory Failure.network({String? message}) = NetworkFailure;

  /// Server error (5xx).
  const factory Failure.server({String? message, int? statusCode}) = ServerFailure;

  /// Resource not found (404).
  const factory Failure.notFound({String? message}) = NotFoundFailure;

  /// Unauthorized (401) — expired or invalid token.
  const factory Failure.unauthorized({String? message}) = UnauthorizedFailure;

  /// Local cache error.
  const factory Failure.cache({String? message}) = CacheFailure;

  /// Data validation error.
  const factory Failure.validation({
    String? message,
    Map<String, List<String>>? fieldErrors,
  }) = ValidationFailure;

  /// Unexpected error.
  const factory Failure.unexpected({String? message, Object? error}) = UnexpectedFailure;
}
```

### Exception → Failure Mapping in RepositoryImpl

```dart
@LazySingleton(as: ProductRepository)
class ProductRepositoryImpl implements ProductRepository {
  const ProductRepositoryImpl(this._remote, this._local);
  final ProductRemoteDataSource _remote;
  final ProductLocalDataSource _local;

  @override
  Future<Result<Product, Exception>> getProduct({required String id}) async {
    try {
      final cached = await _local.getCachedProduct(id);
      if (cached != null) return Success(ProductMapper.fromDataModel(cached));

      final model = await _remote.getProduct(id);
      await _local.cacheProduct(model);
      return Success(ProductMapper.fromDataModel(model));
    } on DioException catch (e) {
      return Failure(_mapDioError(e));
    } on CacheException catch (e) {
      return Failure(CacheFailure(message: e.message));
    } on Exception catch (e) {
      return Failure(UnexpectedFailure(error: e));
    }
  }

  Exception _mapDioError(DioException e) => switch (e.type) {
        DioExceptionType.connectionTimeout ||
        DioExceptionType.receiveTimeout ||
        DioExceptionType.connectionError =>
          NetworkFailure(message: e.message),
        _ => switch (e.response?.statusCode) {
            401 => UnauthorizedFailure(message: e.message),
            404 => NotFoundFailure(message: e.message),
            _ => ServerFailure(message: e.message, statusCode: e.response?.statusCode),
          },
      };
}
```

---

## 3. Repository — Domain Contract

The interface lives in `domain/repositories/`. The implementation lives in `data/repositories/`.
The domain **never** knows the implementation.

```dart
// lib/{feature}/domain/repositories/product_repository.dart
import 'package:commons/commons.dart';

abstract interface class ProductRepository {
  /// Fetches a product by ID.
  Future<Result<Product, Exception>> getProduct({required String id});

  /// Fetches a paginated list of products.
  Future<Result<List<Product>, Exception>> getProducts({
    required int page,
    required int limit,
  });

  /// Observes real-time changes to a product.
  Stream<Result<Product, Exception>> watchProduct({required String id});
}
```

### Rules

- Only domain types in the signature: `Product` (DomainModel), `Exception`, primitives.
- **Forbidden**: `Response`, `DataModel`, `Map<String, dynamic>`, HTTP types.
- Write methods return `Result<Unit, Exception>` (not `void`).

```dart
abstract interface class CartRepository {
  Future<Result<Unit, Exception>> addToCart({required CartItem item});
  Future<Result<Unit, Exception>> removeFromCart({required String itemId});
  Future<Result<Cart, Exception>> getCart();
  Future<Result<Unit, Exception>> clearCart();
}
```

---

## 4. DataSource — Data Layer Contracts

DataSource interfaces live in `data/data_sources/`. They define the contract
for raw data access (HTTP, local cache, database).

```dart
// lib/{feature}/data/data_sources/remote/product_data_source.dart
abstract interface class ProductRemoteDataSource {
  /// Calls GET /products/{id}.
  /// Throws [DioException] on failure.
  Future<ProductModel> getProduct(String id);

  /// Calls GET /products?page={page}&limit={limit}.
  Future<List<ProductModel>> getProducts({
    required int page,
    required int limit,
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
    return (response.data as List).cast<Map<String, dynamic>>().map(ProductModel.fromJson).toList();
  }
}
```

```dart
// lib/{feature}/data/data_sources/local/product_data_source.dart
abstract interface class ProductLocalDataSource {
  Future<ProductModel?> getCachedProduct(String id);
  Future<void> cacheProduct(ProductModel model);
  Future<void> clearProductCache();
}
```

### DataSource Rules

| Type | Returns | Throws | Must NOT |
|---|---|---|---|
| Remote | `DataModel` | `DioException` | Return DomainModel, handle Failure |
| Local | `DataModel?` | `CacheException` | Call HTTP, contain business logic |

---

## 5. CacheStore — Local Storage Abstraction

Generic interface for cache. Implementation can use Drift, Isar, SharedPreferences, etc.

```dart
// lib/core/storage/cache_store.dart
abstract interface class CacheStore {
  Future<Map<String, dynamic>?> get(String key);
  Future<void> put(String key, Map<String, dynamic> value);
  Future<void> remove(String key);
  Future<void> removeByPrefix(String prefix);
  Future<void> clear();
}
```

---

## 6. Mapper — Cross-Layer Conversion

Mappers convert between DataModel and DomainModel. They are `abstract final` classes
with static methods (no state, no injection).

```dart
// lib/{feature}/data/data_models/product_mapper.dart
abstract final class ProductMapper {
  /// DataModel → DomainModel
  static Product fromDataModel(ProductModel model) => Product(
        id: model.id,
        name: model.name,
        price: Money(amount: model.priceInCents, currency: model.currency),
        isAvailable: model.stock > 0,
      );

  /// DomainModel → DataModel (for writes)
  static ProductModel toDataModel(Product product) => ProductModel(
        id: product.id,
        name: product.name,
        priceInCents: product.price.amount,
        currency: product.price.currency,
        stock: product.isAvailable ? 1 : 0,
      );
}
```

### Mapper Rules

- Live in `data/` because they know both `DataModel` and `DomainModel`.
- **Forbidden** in Domain — the domain does not know DataModels exist.
- Simple transformation logic only: rename fields, convert units, derive booleans.
- If the transformation requires complex business logic, move it to the UseCase.

---

## 7. UIMapper — Domain → Presentation Conversion

UIMappers convert DomainModels to UIModels for display in the UI.
They live in `presentation/`.

```dart
// lib/{feature}/presentation/ui_models/product_uimodel.dart
class ProductUIModel {
  const ProductUIModel({
    required this.id,
    required this.displayName,
    required this.formattedPrice,
    required this.availabilityLabel,
    required this.availabilityColor,
  });

  final String id;
  final String displayName;
  final String formattedPrice;
  final String availabilityLabel;
  final Color availabilityColor;
}

abstract final class ProductUIMapper {
  static ProductUIModel toUIModel(Product product) => ProductUIModel(
        id: product.id,
        displayName: product.name.toUpperCase(),
        formattedPrice: '\$${(product.price.amount / 100).toStringAsFixed(2)}',
        availabilityLabel: product.isAvailable ? 'Available' : 'Out of stock',
        availabilityColor: product.isAvailable ? Colors.green : Colors.red,
      );
}
```

### UIMapper Rules

- Live in `presentation/` — knows DomainModel (allowed) and Flutter types (Color, etc.).
- **Forbidden** in Domain.
- String formatting, color calculation, localized labels — all here.
- The BLoC calls the UIMapper **before** emitting the state.

---

## 8. ApiClient — HTTP Abstraction

```dart
// lib/core/network/api_client.dart
abstract interface class ApiClient {
  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters, Options? options});
  Future<Response<T>> post<T>(String path, {Object? data, Options? options});
  Future<Response<T>> put<T>(String path, {Object? data, Options? options});
  Future<Response<T>> delete<T>(String path, {Options? options});
}
```

```dart
// lib/core/di/modules/network_module.dart
@module
abstract class NetworkModule {
  @lazySingleton
  Dio dio() => Dio(BaseOptions(
        baseUrl: const String.fromEnvironment('API_BASE_URL'),
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
      ))
        ..interceptors.addAll([
          AuthInterceptor(getIt<TokenRepository>()),
          LogInterceptor(requestBody: true, responseBody: true),
        ]);

  @LazySingleton(as: ApiClient)
  ApiClientImpl apiClient(Dio dio) => ApiClientImpl(dio);
}
```

---

## 9. BLoC — Presentation Contract

```dart
// lib/{feature}/presentation/bloc/product_bloc.dart
@injectable
class ProductBloc extends Bloc<ProductEvent, ProductState> {
  ProductBloc(this._getProduct) : super(const ProductState.initial()) {
    on<LoadProductEvent>(_onLoad);
  }

  final GetProductUseCase _getProduct;

  Future<void> _onLoad(LoadProductEvent event, Emitter<ProductState> emit) async {
    emit(const ProductState.loading());
    final result = await _getProduct(GetProductParams(id: event.id));
    result.fold(
      (failure) => emit(ProductState.error(failure: failure)),
      (product) => emit(ProductState.success(product: ProductUIMapper.toUIModel(product))),
    );
  }
}

// product_event.dart
@freezed
class ProductEvent with _$ProductEvent {
  const factory ProductEvent.load({required String id}) = LoadProductEvent;
}

// product_state.dart
@freezed
class ProductState with _$ProductState {
  const factory ProductState.initial() = ProductInitial;
  const factory ProductState.loading() = ProductLoading;
  const factory ProductState.success({required ProductUIModel product}) = ProductSuccess;
  const factory ProductState.error({required Exception failure}) = ProductError;
}
```

---

## 10. Contract Summary Table

| Contract | Location | Layer | Knows |
|---|---|---|---|
| `UseCase<T, P>` | `core/usecase/` | Domain | Domain types only |
| `UseCaseNoParams<T>` | `core/usecase/` | Domain | Domain types only |
| `StreamUseCase<T, P>` | `core/usecase/` | Domain | Domain types only |
| `{Feature}Repository` | `{feature}/domain/repositories/` | Domain | Domain types only |
| `Failure` | `core/error/` | Domain | Nothing external |
| `{Feature}RemoteDataSource` | `{feature}/data/data_sources/remote/` | Data | DataModel, ApiClient |
| `{Feature}LocalDataSource` | `{feature}/data/data_sources/local/` | Data | DataModel, CacheStore |
| `CacheStore` | `core/storage/` | Data | Nothing (generic interface) |
| `ApiClient` | `core/network/` | Data | Dio (implementation) |
| `{Name}Mapper` | `{feature}/data/data_models/` | Data | DataModel + DomainModel |
| `{Name}UIMapper` | `{feature}/presentation/ui_models/` | Presentation | DomainModel + Flutter |

---

## 11. Dependency Direction — Full Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    COMPOSITION ROOT                          │
│              (GetIt + Injectable modules)                     │
│  Wires: Repository(impl) → interface, UseCase → BLoC        │
└──────────┬───────────────────────────────┬───────────────────┘
           │                               │
           ▼                               ▼
┌─────────────────────┐         ┌─────────────────────────────┐
│   PRESENTATION      │         │         DATA                │
│                     │         │                             │
│ Page ──► BLoC       │         │ RepositoryImpl              │
│           │         │         │   ├── RemoteDataSource      │
│     UIMapper        │         │   ├── LocalDataSource       │
│      │    │         │         │   └── Mapper                │
│  UIModel  │         │         │                             │
│           ▼         │         │                             │
│       ┌─────────────┼─────────┼──────────────┐              │
│       │     DOMAIN  │         │              │              │
│       │             │         │              │              │
│       │  UseCase ◄──┘         └──► Repository (interface)  │
│       │     │                        ▲                      │
│       │     ▼                        │                      │
│       │  DomainModel            Failure                     │
│       └─────────────────────────────────────────────────────┘
```

**Arrows = dependency direction.** Domain depends on nothing.
Presentation and Data depend on Domain. Only the Composition Root connects them.
