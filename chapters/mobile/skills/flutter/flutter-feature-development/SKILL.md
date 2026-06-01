---
id: flutter-feature-development
version: 1.0.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-feature-development
description: >
  Complete workflow for developing new Flutter features using Clean Architecture. ALWAYS use this skill when creating new features, implementing user stories, structuring domain/data/presentation layers, configuring dependency injection for features, or organizing feature packages. Activate for ANY Flutter project layout — monorepo with top-level `features/` directory, single-app with `lib/src/features/`, or standalone Dart packages. ALWAYS trigger when users ask "where do I put this code?", "how do I structure a new screen?", "how does DI work in a feature?", "where does this business logic go?", or describe wanting to add a new user story, module, or feature. Use this skill even when the user doesn't explicitly say "Clean Architecture", "feature package", or "BLoC" — you should recognize feature-creation intent from context.
license: Complete terms in LICENSE.txt
metadata:
  category: productivity
---

# Feature Development

This skill provides the complete process for developing a new feature from setup to completion. Features are self-contained, modular packages following Clean Architecture.

## Feature Template Structure

Every feature follows this directory structure. The root depends on your project layout:

| Project Type | Feature Root |
|-------------|-------------|
| Monorepo | `features/{feature_name}/` (sibling to `apps/`, `packages/`) |
| Single-app | `lib/src/features/{feature_name}/` |
| Standalone package | Package root itself |

```
{feature_root}/
├── lib/
│   ├── {feature_name}.dart                    # Public barrel export
│   └── src/
│       ├── domain/                            # Business logic layer
│       │   ├── entities/
│       │   │   ├── entities.dart
│       │   │   └── {entity}_entity.dart
│       │   ├── repositories/
│       │   │   ├── repositories.dart
│       │   │   └── {entity}_repository.dart
│       │   └── usecases/
│       │       ├── {action}_usecase.dart
│       │       └── get_{entity}_usecase.dart
│       │
│       ├── data/                              # Data access layer
│       │   ├── datasources/
│       │   │   ├── data_sources.dart
│       │   │   ├── {entity}_local_data_source.dart
│       │   │   └── {entity}_remote_data_source.dart
│       │   ├── models/
│       │   │   ├── models.dart
│       │   │   └── {entity}_model.dart
│       │   ├── mappers/
│       │   │   ├── mappers.dart
│       │   │   └── {entity}_mapper.dart
│       │   └── repositories/
│       │       ├── repositories.dart
│       │       └── {entity}_repository_impl.dart
│       │
│       ├── presentation/                      # UI and state layer
│       │   ├── blocs/
│       │   │   ├── blocs.dart
│       │   │   ├── {entity}_cubit.dart
│       │   │   └── {entity}_state.dart
│       │   ├── pages/
│       │   │   ├── pages.dart
│       │   │   └── {entity}_detail_page.dart
│       │   ├── widgets/
│       │   │   ├── widgets.dart
│       │   │   └── {entity}_card.dart
│       │   └── routes/
│       │       ├── enum/
│       │       │   └── {prefix}_routes.dart
│       │       └── routes.dart
│       │
│       └── di/                                # Dependency injection
│           ├── feature_register_module.dart
│           └── injector.module.dart
│
├── test/
│   └── src/
│       ├── domain/
│       │   ├── usecases/
│       │   └── repositories/
│       ├── data/
│       │   ├── datasources/
│       │   ├── models/
│       │   ├── mappers/
│       │   └── repositories/
│       └── presentation/
│           ├── blocs/
│           └── pages/
│
├── pubspec.yaml
└── analysis_options.yaml
```

## Step-by-Step Feature Development Process

### Step 1: Create Feature Package

Create the feature directory and basic files. Adjust the path `features/user_profile/` to match your project layout (e.g., `lib/src/features/user_profile/` for a single-app):

```bash
# From project root (monorepo style)
mkdir -p features/user_profile/lib/src/{domain/{entities,repositories,usecases},data/{datasources,models,mappers,repositories},presentation/{blocs,pages,widgets,routes},di}
mkdir -p features/user_profile/test/src/{domain,data,presentation}
touch features/user_profile/pubspec.yaml
touch features/user_profile/analysis_options.yaml
```

Update `pubspec.yaml` (adjust package names and paths to fit your project):

```yaml
name: user_profile
version: 0.0.1
publish_to: 'none'

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  # Shared utilities package — use your own or inline equivalents
  # commons:
  #   path: ../../packages/commons
  flutter_bloc: ^8.1.0
  # DI framework — injectable/get_it is recommended, but optional
  injectable: ^2.2.0
  equatable: ^2.0.0
  dio: ^5.0.0
  # Result type — choose one: dartz, fpdart, or a custom Result class
  # dartz: ^0.10.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0   # or very_good_analysis for stricter rules
  mocktail: ^1.0.0
  bloc_test: ^9.1.0
```

### Step 2: Define Domain Layer

Start with domain layer entities, repositories, and usecases:

**Entity:**
```dart
// lib/src/domain/entities/user_entity.dart
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

**Repository Interface:**
```dart
// lib/src/domain/repositories/user_repository.dart
import 'package:commons/commons.dart';
import '../entities/user_entity.dart';

abstract class UserRepository {
  Future<Result<UserEntity, Exception>> getUser(String id);
  Future<Result<List<UserEntity>, Exception>> getAllUsers();
  Future<Result<UserEntity, Exception>> updateUser(UserEntity user);
}
```

**UseCase:**
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
```

**Barrel Exports:**
```dart
// lib/src/domain/entities/entities.dart
export 'user_entity.dart';

// lib/src/domain/repositories/repositories.dart
export 'user_repository.dart';

// lib/src/domain/usecases/usecases.dart
export 'get_user_usecase.dart';
```

### Step 3: Implement Data Layer

Create models, datasources, mappers, and repository implementations.

**Model:**
```dart
// lib/src/data/models/user_model.dart
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
```

See [Feature Workflow](./references/feature-workflow.md) for complete DataSource, Mapper, and Repository implementation examples.

### Step 4: Create Presentation Layer

Define states, cubits, pages, and widgets.

**State:**
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
```

**Cubit:**
```dart
// lib/src/presentation/blocs/user_cubit.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:commons/commons.dart';
import '../../domain/usecases/get_user_usecase.dart';
import 'user_state.dart';

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
        log.debug('User loaded successfully');
        emit(UserSuccess(user: user));
      },
      (error) {
        log.error('Error loading user: ${error.message}');
        emit(UserError(message: error.message));
      },
    );
  }
}
```

### Step 5: Configure Dependency Injection

Create DI module for feature registration:

```dart
// lib/src/di/feature_register_module.dart
import 'package:commons/commons.dart';
import 'package:injectable/injectable.dart';
import '../data/datasources/user_data_source.dart';
import '../data/mappers/user_mapper.dart';
import '../data/repositories/user_repository_impl.dart';
import '../domain/repositories/user_repository.dart';

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
```

### Step 6: Export Public API

Create barrel exports for feature:

```dart
// lib/user_profile.dart - Public API
export 'src/domain/entities/entities.dart';
export 'src/domain/repositories/repositories.dart';
export 'src/domain/usecases/usecases.dart';
export 'src/presentation/blocs/blocs.dart';
export 'src/presentation/pages/pages.dart';
export 'src/di/injector.module.dart';
export 'src/routes/routes.dart';
```

## Development Checklist

Before submitting a feature for code review:

- [ ] All files created and organized per template
- [ ] Domain layer implemented (entities, repositories, usecases)
- [ ] Data layer implemented (models, datasources, mappers, repositories)
- [ ] Presentation layer implemented (states, cubits, pages, widgets)
- [ ] DI configuration complete and tested
- [ ] All unit tests written and passing (target: >80% coverage)
- [ ] All files formatted with `dart format`
- [ ] No linting errors (`dart analyze`)
- [ ] Code follows naming conventions
- [ ] Documentation added where needed
- [ ] Public API exports correct in barrel files
- [ ] Feature can be imported and used

## Testing Strategy

Write tests following these guidelines:

```bash
# Run all feature tests
flutter test

# By layer
flutter test test/src/domain/
flutter test test/src/data/
flutter test test/src/presentation/

# With coverage report
flutter test --coverage
```

> In a Melos monorepo, use `melos test` to run tests across all packages.

## For Detailed Guidance

- [Feature Workflow Details](./references/feature-workflow.md) — Step-by-step implementation with full examples
- [Clean Architecture Reference](../flutter-clean-architecture/SKILL.md) — Layer patterns and principles
