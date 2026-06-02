# Feature Development Workflow - Detailed Steps

This document provides detailed implementation guidance for each step of the feature development process.

## Complete Feature Example: User Profile Feature

We'll build a complete `user_profile` feature that displays, fetches, and manages user information.

### Step 1-2: Setup & Domain Layer

#### Create Feature Package

```bash
# Create directory structure
mkdir -p features/user_profile/lib/src/{domain,data,presentation}/{{entities,repositories,usecases},{datasources,models,mappers,repositories},{blocs,pages,widgets,routes}}
mkdir -p features/user_profile/{test/src,bin}

# Create initial files


touch features/user_profile/{pubspec.yaml,analysis_options.yaml,README.md}
```

#### Domain: Entities

```dart
// lib/src/domain/entities/user_entity.dart
import 'package:commons/commons.dart';
import 'package:equatable/equatable.dart';

class UserEntity extends BaseEntity {
  const UserEntity({
    required this.id,
    required this.name,
    required this.email,
    required this.phone,
    required this.avatar,
  });

  final String id;
  final String name;
  final String email;
  final String phone;
  final String? avatar;

  @override
  List<Object?> get props => [id, name, email, phone, avatar];
}

// lib/src/domain/entities/entities.dart - Barrel export
export 'user_entity.dart';
```

#### Domain: Repositories

```dart
// lib/src/domain/repositories/user_repository.dart
import 'package:commons/commons.dart';
import '../entities/user_entity.dart';

abstract class UserRepository {
  /// Fetch single user by ID
  Future<Result<UserEntity, Exception>> getUser(String id);
  
  /// Fetch all users (paginated)
  Future<Result<List<UserEntity>, Exception>> getUsers({
    int page = 0,
    int limit = 20,
  });
  
  /// Update user profile
  Future<Result<UserEntity, Exception>> updateUser(UserEntity user);
  
  /// Delete user
  Future<Result<bool, Exception>> deleteUser(String id);
}

// lib/src/domain/repositories/repositories.dart - Barrel export
export 'user_repository.dart';
```

#### Domain: UseCases

```dart
// lib/src/domain/usecases/get_user_usecase.dart
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

// lib/src/domain/usecases/get_users_usecase.dart
import 'package:commons/commons.dart';
import 'package:injectable/injectable.dart';

class GetUsersRequest extends Equatable {
  const GetUsersRequest({
    this.page = 0,
    this.limit = 20,
  });

  final int page;
  final int limit;

  @override
  List<Object?> get props => [page, limit];
}

@LazySingleton()
class GetUsersUseCase 
    extends BaseUseCase<GetUsersRequest, Result<List<UserEntity>, Exception>> {
  const GetUsersUseCase({required this.repository});

  final UserRepository repository;

  @override
  Future<Result<List<UserEntity>, Exception>> call(GetUsersRequest request) {
    return repository.getUsers(
      page: request.page,
      limit: request.limit,
    );
  }
}

// lib/src/domain/usecases/update_user_usecase.dart
@LazySingleton()
class UpdateUserUseCase 
    extends BaseUseCase<UserEntity, Result<UserEntity, Exception>> {
  const UpdateUserUseCase({required this.repository});

  final UserRepository repository;

  @override
  Future<Result<UserEntity, Exception>> call(UserEntity user) {
    return repository.updateUser(user);
  }
}

// lib/src/domain/usecases/delete_user_usecase.dart
@LazySingleton()
class DeleteUserUseCase 
    extends BaseUseCase<String, Result<bool, Exception>> {
  const DeleteUserUseCase({required this.repository});

  final UserRepository repository;

  @override
  Future<Result<bool, Exception>> call(String userId) {
    return repository.deleteUser(userId);
  }
}

// lib/src/domain/usecases/usecases.dart - Barrel export
export 'delete_user_usecase.dart';
export 'get_user_usecase.dart';
export 'get_users_usecase.dart';
export 'update_user_usecase.dart';
```

### Step 3: Data Layer

#### Models

```dart
// lib/src/data/models/user_model.dart
import 'package:commons/commons.dart';

class UserModel extends BaseResponseModel {
  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    required this.phone,
    this.avatar,
  });

  final String id;
  final String name;
  final String email;
  final String phone;
  final String? avatar;

  factory UserModel.fromJson(JSON json) => UserModel(
    id: json['id'] as String? ?? '',
    name: json['name'] as String? ?? '',
    email: json['email'] as String? ?? '',
    phone: json['phone'] as String? ?? '',
    avatar: json['avatar'] as String?,
  );

  @override
  JSON toJson() => {
    'id': id,
    'name': name,
    'email': email,
    'phone': phone,
    'avatar': avatar,
  };

  @override
  UserModel copyWith({
    String? id,
    String? name,
    String? email,
    String? phone,
    String? avatar,
  }) => UserModel(
    id: id ?? this.id,
    name: name ?? this.name,
    email: email ?? this.email,
    phone: phone ?? this.phone,
    avatar: avatar ?? this.avatar,
  );
}

// lib/src/data/models/models.dart - Barrel export
export 'user_model.dart';
```

#### DataSources

```dart
// lib/src/data/datasources/user_data_source.dart
import 'package:commons/commons.dart';
import '../models/user_model.dart';

abstract class UserDataSource {
  Future<Result<UserModel, Exception>> getUser(String id);
  Future<Result<List<UserModel>, Exception>> getUsers({
    int page = 0,
    int limit = 20,
  });
  Future<Result<UserModel, Exception>> updateUser(UserModel user);
  Future<Result<bool, Exception>> deleteUser(String id);
}

// lib/src/data/datasources/user_remote_data_source.dart
import 'package:dio/dio.dart';

class UserRemoteDataSource implements UserDataSource {
  UserRemoteDataSource({required this.httpModule});

  final HttpModule httpModule;

  @override
  Future<Result<UserModel, Exception>> getUser(String id) async {
    try {
      final response = await httpModule.dio.get('/users/$id');
      final model = UserModel.fromJson(response.data as JSON);
      return Success(model);
    } on DioException catch (e) {
      return Failure(Exception('Failed to fetch user: ${e.message}'));
    } catch (e) {
      return Failure(Exception('Unexpected error: $e'));
    }
  }

  @override
  Future<Result<List<UserModel>, Exception>> getUsers({
    int page = 0,
    int limit = 20,
  }) async {
    try {
      final response = await httpModule.dio.get(
        '/users',
        queryParameters: {'page': page, 'limit': limit},
      );
      final models = (response.data as List)
          .map((item) => UserModel.fromJson(item as JSON))
          .toList();
      return Success(models);
    } on DioException catch (e) {
      return Failure(Exception('Failed to fetch users: ${e.message}'));
    } catch (e) {
      return Failure(Exception('Unexpected error: $e'));
    }
  }

  @override
  Future<Result<UserModel, Exception>> updateUser(UserModel user) async {
    try {
      final response = await httpModule.dio.put(
        '/users/${user.id}',
        data: user.toJson(),
      );
      final model = UserModel.fromJson(response.data as JSON);
      return Success(model);
    } on DioException catch (e) {
      return Failure(Exception('Failed to update user: ${e.message}'));
    } catch (e) {
      return Failure(Exception('Unexpected error: $e'));
    }
  }

  @override
  Future<Result<bool, Exception>> deleteUser(String id) async {
    try {
      await httpModule.dio.delete('/users/$id');
      return const Success(true);
    } on DioException catch (e) {
      return Failure(Exception('Failed to delete user: ${e.message}'));
    } catch (e) {
      return Failure(Exception('Unexpected error: $e'));
    }
  }
}

// lib/src/data/datasources/user_local_data_source.dart
// (Similar implementation for local cache using Hive or SharedPreferences)

// lib/src/data/datasources/data_sources.dart - Barrel export
export 'user_data_source.dart';
```

#### Mappers

```dart
// lib/src/data/mappers/user_mapper.dart
import 'package:commons/commons.dart';
import '../../domain/entities/user_entity.dart';
import '../models/user_model.dart';

class UserMapper extends BaseResponseMapper<UserModel, UserEntity> {
  @override
  UserEntity from({required UserModel response}) {
    return UserEntity(
      id: response.id,
      name: response.name,
      email: response.email,
      phone: response.phone,
      avatar: response.avatar,
    );
  }

  @override
  Iterable<UserEntity> fromList(List<UserModel> params) {
    return params.map((model) => from(response: model));
  }

  UserModel toModel(UserEntity entity) {
    return UserModel(
      id: entity.id,
      name: entity.name,
      email: entity.email,
      phone: entity.phone,
      avatar: entity.avatar,
    );
  }
}

// lib/src/data/mappers/mappers.dart - Barrel export
export 'user_mapper.dart';
```

#### Repositories (Implementation)

```dart
// lib/src/data/repositories/user_repository_impl.dart
import 'package:commons/commons.dart';
import '../../domain/entities/user_entity.dart';
import '../../domain/repositories/user_repository.dart';
import '../datasources/user_data_source.dart';
import '../mappers/user_mapper.dart';

class UserRepositoryImpl extends BaseRepository implements UserRepository {
  UserRepositoryImpl({
    required this.localDataSource,
    required this.remoteDataSource,
    required this.mapper,
  });

  final UserDataSource localDataSource;
  final UserDataSource remoteDataSource;
  final UserMapper mapper;

  @override
  Future<Result<UserEntity, Exception>> getUser(String id) async {
    // Try local first
    final localResult = await localDataSource.getUser(id);
    
    if (localResult is Success) {
      return Success(mapper.from(response: localResult.value));
    }

    // Fall back to remote
    final remoteResult = await remoteDataSource.getUser(id);
    
    return remoteResult.fold(
      (model) async {
        // Cache locally
        await localDataSource.updateUser(model);
        return Success(mapper.from(response: model));
      },
      (error) => Failure(error),
    );
  }

  @override
  Future<Result<List<UserEntity>, Exception>> getUsers({
    int page = 0,
    int limit = 20,
  }) async {
    final remoteResult = await remoteDataSource.getUsers(
      page: page,
      limit: limit,
    );
    
    return remoteResult.fold(
      (models) async {
        return Success(mapper.fromList(models).toList());
      },
      (error) => Failure(error),
    );
  }

  @override
  Future<Result<UserEntity, Exception>> updateUser(UserEntity user) async {
    final model = mapper.toModel(user);
    final remoteResult = await remoteDataSource.updateUser(model);
    
    return remoteResult.fold(
      (model) async {
        await localDataSource.updateUser(model);
        return Success(mapper.from(response: model));
      },
      (error) => Failure(error),
    );
  }

  @override
  Future<Result<bool, Exception>> deleteUser(String id) async {
    return await remoteDataSource.deleteUser(id);
  }
}

// lib/src/data/repositories/repositories.dart - Barrel export
export 'user_repository_impl.dart';
```

### Step 4: Presentation Layer

#### States

```dart
// lib/src/presentation/blocs/user_state.dart
import 'package:equatable/equatable.dart';
import '../../domain/entities/user_entity.dart';

abstract class UserState extends Equatable {
  const UserState();

  @override
  List<Object?> get props => [];
}

class UserInitial extends UserState {
  const UserInitial();
}

class UserLoading extends UserState {
  const UserLoading();
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

// lib/src/presentation/blocs/blocs.dart - Barrel export
export 'user_cubit.dart';
export 'user_state.dart';
```

#### Cubits

```dart
// lib/src/presentation/blocs/user_cubit.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:commons/commons.dart';
import 'package:injectable/injectable.dart';
import '../../domain/entities/user_entity.dart';
import '../../domain/usecases/usecases.dart';
import 'user_state.dart';

@injectable
class UserCubit extends Cubit<UserState> {
  UserCubit({
    required this.getUserUseCase,
    required this.updateUserUseCase,
    required this.log,
  }) : super(const UserInitial());

  final GetUserUseCase getUserUseCase;
  final UpdateUserUseCase updateUserUseCase;
  final Log log;

  Future<void> fetchUser(String userId) async {
    emit(const UserLoading());

    final result = await getUserUseCase.call(userId);

    result.fold(
      (user) {
        log.debug('User ${user.name} fetched successfully');
        emit(UserSuccess(user: user));
      },
      (error) {
        log.error('Failed to fetch user: ${error.message}');
        emit(UserError(message: error.message));
      },
    );
  }

  Future<void> updateUser(UserEntity user) async {
    // Keep current state while updating
    if (state is UserSuccess) {
      emit(const UserLoading());
    }

    final result = await updateUserUseCase.call(user);

    result.fold(
      (updatedUser) {
        log.debug('User ${updatedUser.name} updated successfully');
        emit(UserSuccess(user: updatedUser));
      },
      (error) {
        log.error('Failed to update user: ${error.message}');
        emit(UserError(message: error.message));
      },
    );
  }

  void clearUser() {
    emit(const UserInitial());
  }
}
```

#### Pages

```dart
// lib/src/presentation/pages/user_detail_page.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/blocs.dart';
import '../widgets/widgets.dart';

class UserDetailPage extends StatelessWidget {
  const UserDetailPage({
    Key? key,
    required this.userId,
  }) : super(key: key);

  final String userId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('User Profile')),
      body: BlocListener<UserCubit, UserState>(
        listener: (context, state) {
          if (state is UserError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message)),
            );
          }
        },
        child: BlocBuilder<UserCubit, UserState>(
          builder: (context, state) {
            if (state is UserLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            if (state is UserSuccess) {
              return UserProfileWidget(user: state.user);
            }

            if (state is UserError) {
              return ErrorWidget(
                message: state.message,
                onRetry: () => context.read<UserCubit>().fetchUser(userId),
              );
            }

            return Center(
              child: ElevatedButton(
                onPressed: () => context.read<UserCubit>().fetchUser(userId),
                child: const Text('Load User'),
              ),
            );
          },
        ),
      ),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    context.read<UserCubit>().fetchUser(userId);
  }
}

// lib/src/presentation/pages/pages.dart - Barrel export
export 'user_detail_page.dart';
```

#### Widgets

```dart
// lib/src/presentation/widgets/user_profile_widget.dart
import 'package:flutter/material.dart';
import '../../domain/entities/user_entity.dart';

class UserProfileWidget extends StatelessWidget {
  const UserProfileWidget({Key? key, required this.user}) : super(key: key);

  final UserEntity user;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildAvatarSection(context),
          const SizedBox(height: 32),
          _buildInfoSection(context),
        ],
      ),
    );
  }

  Widget _buildAvatarSection(BuildContext context) {
    return Center(
      child: Column(
        children: [
          if (user.avatar != null)
            Image.network(
              user.avatar!,
              width: 120,
              height: 120,
              fit: BoxFit.cover,
            )
          else
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Theme.of(context).primaryColor.withOpacity(0.3),
              ),
              child: Icon(
                Icons.person,
                size: 60,
                color: Theme.of(context).primaryColor,
              ),
            ),
          const SizedBox(height: 16),
          Text(
            user.name,
            style: Theme.of(context).textTheme.headlineSmall,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoField('Email', user.email),
        _buildInfoField('Phone', user.phone),
      ],
    );
  }

  Widget _buildInfoField(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(value),
        const SizedBox(height: 16),
      ],
    );
  }
}

// lib/src/presentation/widgets/error_widget.dart
class ErrorWidget extends StatelessWidget {
  const ErrorWidget({
    Key? key,
    required this.message,
    this.onRetry,
  }) : super(key: key);

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline,
            color: Colors.red.shade400,
            size: 64,
          ),
          const SizedBox(height: 16),
          Text(
            'Error',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: Colors.red.shade400,
            ),
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(height: 24),
          if (onRetry != null)
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
        ],
      ),
    );
  }
}

// lib/src/presentation/widgets/widgets.dart - Barrel export
export 'user_profile_widget.dart';
export 'error_widget.dart';
```

### Step 5: Dependency Injection

```dart
// lib/src/di/feature_register_module.dart
import 'package:commons/commons.dart';
import 'package:injectable/injectable.dart';
import '../data/datasources/data_sources.dart';
import '../data/mappers/mappers.dart';
import '../data/repositories/repositories.dart';
import '../domain/repositories/repositories.dart';

@module
abstract class FeatureRegisterModule {
  @lazySingleton
  @Named('userRemoteDataSource')
  UserDataSource provideUserRemoteDataSource(HttpModule httpModule) =>
      UserRemoteDataSource(httpModule: httpModule);

  @lazySingleton
  @Named('userLocalDataSource')
  UserDataSource provideUserLocalDataSource() =>
      const UserLocalDataSource();

  @lazySingleton
  UserMapper provideUserMapper() => UserMapper();

  @lazySingleton
  UserRepository provideUserRepository(
    @Named('userRemoteDataSource') UserDataSource remote,
    @Named('userLocalDataSource') UserDataSource local,
    UserMapper mapper,
  ) => UserRepositoryImpl(
    remoteDataSource: remote,
    localDataSource: local,
    mapper: mapper,
  );
}

// lib/src/di/injector.module.dart
import 'feature_register_module.dart';

part 'injector.module.g.dart';

@injectableInit
void configureDependencies() => _i1.init(_serviceLocator);
```

### Step 6: Public API & Routing

```dart
// lib/user_profile.dart - Public barrel export
export 'src/domain/entities/entities.dart';
export 'src/domain/repositories/repositories.dart';
export 'src/domain/usecases/usecases.dart';
export 'src/presentation/blocs/blocs.dart';
export 'src/presentation/pages/pages.dart';
export 'src/di/injector.module.dart';

// lib/src/routes/enum/user_profile_routes.dart
enum UserProfileRoutes {
  detail('/user/:id'),
  ;

  const UserProfileRoutes(this.path);
  final String path;
}

// lib/src/routes/routes.dart
export 'enum/user_profile_routes.dart';
```

## Common Patterns

### Error Handling Pattern

```dart
// Always use Result pattern
result.fold(
  (success) => handleSuccess(success),
  (failure) => handleFailure(failure),
);
```

### Testing Pattern

Create test files mirroring lib structure:

```
test/src/
├── domain/usecases/get_user_usecase_test.dart
├── data/repositories/user_repository_impl_test.dart
├── data/mappers/user_mapper_test.dart
└── presentation/blocs/user_cubit_test.dart
```

### Naming Convention

- Entities: `{name}_entity.dart`
- Repositories: `{name}_repository.dart`, `{name}_repository_impl.dart`
- UseCases: `{action}_{entity}_usecase.dart` or `{action}_usecase.dart`
- Models: `{name}_model.dart`
- DataSources: `{name}_{remote/local}_data_source.dart`
- Mappers: `{name}_mapper.dart`
- Cubits: `{name}_cubit.dart` + `{name}_state.dart`
- Pages: `{name}_page.dart`
- Widgets: `{name}_widget.dart`
