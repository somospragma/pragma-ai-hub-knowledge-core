# Complete Data Flow

## Table of Contents

1. [Happy Path: Fetching User Data](#happy-path-fetching-user-data)
2. [Error Path: Network Failure](#error-path-network-failure)
3. [Key Principles Demonstrated](#key-principles-demonstrated)
4. [Request/Response Sequence (Step-by-Step)](#requestresponse-sequence-step-by-step)

This document shows the complete flow of data through all three layers of Clean Architecture, from user action to UI update.

## Happy Path: Fetching User Data

```
┌─────────────────────────────────────────────────────────────┐
│ 1. UI LAYER - User triggers action                          │
└─────────────────────────────────────────────────────────────┘

User taps "Load User" button
       │
       └─→ onPressed callback fires


┌─────────────────────────────────────────────────────────────┐
│ 2. PRESENTATION LAYER - Cubit receives action              │
└─────────────────────────────────────────────────────────────┘

Widget calls: context.read<UserCubit>().fetchUser('user-123')
       │
       ├─→ Cubit.fetchUser('user-123') called
       │
       ├─→ Emit UserLoading state
       │
       └─→ UI rebuilds: Spinner shown


┌─────────────────────────────────────────────────────────────┐
│ 3. DOMAIN LAYER - Business logic executes                  │
└─────────────────────────────────────────────────────────────┘

Cubit calls: userRepository.getUser('user-123')
       │
       └─→ Repository returns: Result<UserEntity, Exception>


┌─────────────────────────────────────────────────────────────┐
│ 4. DATA LAYER - Fetch from sources                         │
└─────────────────────────────────────────────────────────────┘

Repository.getUser('user-123'):
       │
       ├─→ Try LocalDataSource (cache):
       │   │
       │   └─→ Database hit? YES: Return UserModel
       │       │
       │       └─→ Jump to Mapper
       │
       │   NO: Continue to Remote
       │
       ├─→ Try RemoteDataSource (API):
       │   │
       │   ├─→ HTTPClient.get('/users/user-123')
       │   │
       │   ├─→ Receive JSON response:
       │   │   {
       │   │     "id": "user-123",
       │   │     "name": "John Doe",
       │   │     "email": "john@example.com"
       │   │   }
       │   │
       │   └─→ Parse JSON → UserModel
       │
       ├─→ Cache the result:
       │   │
       │   └─→ LocalDataSource.createUser(userModel)
       │
       └─→ Convert Model to Entity:
           │
           └─→ UserMapper.from(response: userModel)
               │
               └─→ Return: UserEntity(id, name, email)


┌─────────────────────────────────────────────────────────────┐
│ 5. DOMAIN LAYER - Wrap in Result                           │
└─────────────────────────────────────────────────────────────┘

Result.fold succeeded:
       │
       ├─→ (entity) branch:
       │   UserEntity(id: 'user-123', name: 'John Doe', email: '...')
       │
       └─→ Return: Success(userEntity)


┌─────────────────────────────────────────────────────────────┐
│ 6. PRESENTATION LAYER - Handle Result                      │
└─────────────────────────────────────────────────────────────┘

Cubit receives Result<UserEntity, Exception>:
       │
       ├─→ result.fold(
       │   (user) {  // Success path with entity
       │     log.debug('User loaded: ${user.name}');
       │     emit(UserSuccess(user: user));
       │   },
       │   (error) {  // Error path (not taken)
       │     log.error('Error: ${error.message}');
       │     emit(UserError(message: error.message));
       │   }
       │ )


┌─────────────────────────────────────────────────────────────┐
│ 7. UI LAYER - Rebuild with new state                       │
└─────────────────────────────────────────────────────────────┘

BlocBuilder detects state change:
       │
       ├─→ if (state is UserSuccess) {
       │     build: UserInfoCard(user: state.user)
       │   }
       │
       └─→ UI rebuilds and displays user data:
           ┌──────────────────────┐
           │ User Details         │
           │ ─────────────────── │
           │ Name: John Doe      │
           │ Email: john@...     │
           └──────────────────────┘
```

## Error Path: Network Failure

```
┌─────────────────────────────────────────────────────────────┐
│ 4. DATA LAYER - API call fails                             │
└─────────────────────────────────────────────────────────────┘

RemoteDataSource.getUser('user-123'):
       │
       ├─→ HTTPClient.get('/users/user-123')
       │   │
       │   └─→ DioException: Connection timeout
       │
       └─→ Return: Failure(Exception('Failed to fetch user: Timeout'))


┌─────────────────────────────────────────────────────────────┐
│ 3. DATA LAYER - Repository handles error                   │
└─────────────────────────────────────────────────────────────┘

Repository.getUser received Failure from Remote:
       │
       └─→ Return: Failure(Exception('Failed to fetch user: Timeout'))


┌─────────────────────────────────────────────────────────────┐
│ 5. DOMAIN LAYER - Wrap in Result (failure branch)          │
└─────────────────────────────────────────────────────────────┘

Result: Failure(Exception('Failed to fetch user: Timeout'))


┌─────────────────────────────────────────────────────────────┐
│ 6. PRESENTATION LAYER - Handle error                       │
└─────────────────────────────────────────────────────────────┘

Cubit receives Result:
       │
       └─→ result.fold(
           (user) { /* not called */ },
           (error) {  // Error path taken
             log.error('Error: ${error.message}');
             emit(UserError(message: 'Failed to fetch user: Timeout'));
           }
         )


┌─────────────────────────────────────────────────────────────┐
│ 7. UI LAYER - Show error                                   │
└─────────────────────────────────────────────────────────────┘

BlocBuilder detects error state:
       │
       ├─→ if (state is UserError) {
       │     showSnackBar(state.message);
       │     build: ErrorWidget(
       │       message: state.message,
       │       onRetry: () => cubit.fetchUser(userId)
       │     );
       │   }
       │
       └─→ UI shows:
           ┌──────────────────────────────┐
           │ Failed to fetch user: Timeout│
           │ [RETRY Button]               │
           └──────────────────────────────┘
```

## Complete Code Example

### 1. Domain Layer

```dart
// entities/user_entity.dart
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

// repositories/user_repository.dart
abstract class UserRepository {
  Future<Result<UserEntity, Exception>> getUser(String id);
}

// usecases/get_user_usecase.dart
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

### 2. Data Layer

```dart
// models/user_model.dart
class UserModel extends BaseResponseModel {
  const UserModel({
    required this.id,
    required this.name,
    required this.email,
  });

  final String id;
  final String name;
  final String email;

  factory UserModel.fromJson(JSON json) => UserModel(
    id: json['id'] as String? ?? '',
    name: json['name'] as String? ?? '',
    email: json['email'] as String? ?? '',
  );

  @override
  JSON toJson() => {
    'id': id,
    'name': name,
    'email': email,
  };

  @override
  UserModel copyWith({String? id, String? name, String? email}) =>
      UserModel(
        id: id ?? this.id,
        name: name ?? this.name,
        email: email ?? this.email,
      );
}

// datasources/user_data_source.dart
abstract class UserDataSource {
  Future<Result<UserModel, Exception>> getUser(String id);
}

class UserRemoteDataSource implements UserDataSource {
  UserRemoteDataSource({required this.httpModule});
  final HttpModule httpModule;

  @override
  Future<Result<UserModel, Exception>> getUser(String id) async {
    try {
      final response = await httpModule.dio.get('/users/$id');
      return Success(UserModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(Exception('Failed to fetch user: ${e.message}'));
    }
  }
}

// repositories/user_repository_impl.dart
class UserRepositoryImpl implements UserRepository {
  UserRepositoryImpl({
    required this.remote,
    required this.mapper,
  });
  final UserDataSource remote;
  final UserMapper mapper;

  @override
  Future<Result<UserEntity, Exception>> getUser(String id) async {
    final result = await remote.getUser(id);

    return result.fold(
      (model) => Success(mapper.from(response: model)),
      (error) => Failure(error),
    );
  }
}

// mappers/user_mapper.dart
class UserMapper extends BaseResponseMapper<UserModel, UserEntity> {
  @override
  UserEntity from({required UserModel response}) {
    return UserEntity(
      id: response.id,
      name: response.name,
      email: response.email,
    );
  }

  @override
  Iterable<UserEntity> fromList(List<UserModel> params) {
    return params.map((model) => from(response: model));
  }
}
```

### 3. Presentation Layer

```dart
// blocs/user_state.dart
abstract class UserState extends Equatable {
  const UserState();
}

class UserInitial extends UserState {
  const UserInitial();

  @override
  List<Object?> get props => [];
}

class UserLoading extends UserState {
  const UserLoading();

  @override
  List<Object?> get props => [];
}

class UserSuccess extends UserState {
  const UserSuccess({required this.user});
  final UserEntity user;

  @override
  List<Object?> get props => [user];
}

class UserError extends UserState {
  const UserError({required this.message});
  final String message;

  @override
  List<Object?> get props => [message];
}

// blocs/user_cubit.dart
class UserCubit extends Cubit<UserState> {
  UserCubit({
    required this.getUserUseCase,
    required this.log,
  }) : super(const UserInitial());

  final GetUserUseCase getUserUseCase;
  final Log log;

  Future<void> fetchUser(String userId) async {
    emit(const UserLoading());

    final result = await getUserUseCase.call(userId);

    result.fold(
      (user) {
        log.debug('User loaded: ${user.name}');
        emit(UserSuccess(user: user));
      },
      (error) {
        log.error('Error loading user: ${error.message}');
        emit(UserError(message: error.message));
      },
    );
  }
}

// pages/user_detail_page.dart
class UserDetailPage extends StatelessWidget {
  const UserDetailPage({Key? key, required this.userId}) : super(key: key);
  final String userId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('User')),
      body: BlocBuilder<UserCubit, UserState>(
        builder: (context, state) {
          if (state is UserLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is UserSuccess) {
            return UserInfoCard(user: state.user);
          }
          if (state is UserError) {
            return Center(child: Text('Error: ${state.message}'));
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    context.read<UserCubit>().fetchUser(userId);
  }
}
```

## Key Principles Demonstrated

1. **Unidirectional Dependencies:** Data flows through layers, dependencies point inward
2. **Separation of Concerns:** Each layer has specific responsibilities
3. **Testability:** Each layer can be tested independently
4. **Result Pattern:** No exceptions thrown across layers, explicit Success/Failure
5. **Immutability:** States and entities are immutable
6. **Logging:** Important steps are logged for debugging
7. **Caching:** Data from remote sources is cached locally
8. **Error Handling:** Errors are handled at each layer appropriately

---

## Request/Response Sequence (Step-by-Step)

Trace of a single "load product" operation across all layers, including cache miss and network call.

```
User taps "Load Product" button
         │
         ▼
[Page] onPressed → context.read<ProductBloc>().add(ProductEvent.load(id: id))
         │
         ▼
[BLoC] on<LoadProductEvent>
  emit(ProductState.loading())
         │
         ▼ calls
[UseCase] GetProductUseCase.call(GetProductParams(id: id))
         │
         ▼ calls
[Repository interface] ProductRepository.getProduct(id: id)
         │
         ▼ dispatches to
[RepositoryImpl] ProductRepositoryImpl.getProduct
  │
  ├──▶ [LocalDataSource] getCachedProduct(id)
  │         │
  │         ▼
  │    cache MISS (returns null)
  │         │
  │         ▼
  ├──▶ [RemoteDataSource] getProduct(id)
  │         │
  │         ▼
  │    [ApiClient] GET /products/{id}
  │         │
  │         ▼ HTTP 200
  │    response.data → ProductModel.fromJson(json)
  │         │
  │         ▼ returns ProductModel
  │
  ├──▶ [LocalDataSource] cacheProduct(model)   ← save to cache
  │
  ├──▶ [ProductMapper] fromDataModel(model)    ← DataModel → DomainModel
  │         │
  │         ▼ returns Product (DomainModel)
  │
  └──▶ return Success(product)                 ← Result<Product, Exception>
         │
         ▼ Result propagates up
[UseCase] returns Success(product)
         │
         ▼
[BLoC] result.fold(
  (failure) → emit(ProductState.error(failure: failure)),
  (product) → {
    final uiModel = ProductUIMapper.toUIModel(product)  ← DomainModel → UIModel
    emit(ProductState.success(product: uiModel))
  }
)
         │
         ▼
[Page] BlocBuilder rebuilds with ProductState.success
  └──▶ Widget tree reads uiModel.formattedPrice, uiModel.availabilityColor, etc.
```

### Cache Hit Path

When `LocalDataSource.getCachedProduct(id)` returns a non-null value:

```
[RepositoryImpl]
  ├──▶ [LocalDataSource] getCachedProduct(id)
  │         │
  │         ▼
  │    cache HIT → returns ProductModel
  │
  ├──▶ [ProductMapper] fromDataModel(cached)  ← no HTTP call
  │
  └──▶ return Success(product)
```

### Error Path — Network Failure

```
[RemoteDataSource] GET /products/{id}
         │
         ▼ throws DioException (connection timeout)
[RepositoryImpl] catch (DioException e)
  └──▶ return Failure(_mapDioError(e))         ← NetworkFailure
         │
         ▼ Result propagates up
[UseCase] returns Failure(NetworkFailure(...))
         │
         ▼
[BLoC] result.fold(
  (failure) → emit(ProductState.error(failure: failure)),
  ...
)
         │
         ▼
[Page] BlocBuilder rebuilds with ProductState.error
  └──▶ Widget shows error message from failure
```
