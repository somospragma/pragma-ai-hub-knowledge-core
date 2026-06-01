# Presentation Layer — Detailed Patterns

## Table of Contents

1. [States](#states)
2. [Events](#events)
3. [BLoC](#bloc)
4. [Pages and Widgets](#pages-and-widgets)
5. [Testing](#testing)
6. [UIModel and UIMapper](#uimodel-and-uimapper)

The Presentation Layer handles UI, state management, and user interactions. It uses BLoC/Cubit to manage application state.

## States

States represent the different states your UI can be in. They should be immutable and clearly named.

### State Rules

- Extend `Equatable` for equality comparison
- All fields must be `final`
- Use `const` constructors
- Override `props` for equality
- Clear, descriptive names (Initial, Loading, Success, Error)
- One state class per distinct UI state

### State Example

```dart
// presentation/blocs/user_state.dart
import 'package:equatable/equatable.dart';
import '../../domain/entities/user_entity.dart';

abstract class UserState extends Equatable {
  const UserState();

  @override
  List<Object?> get props => [];
}

/// Initial state when Cubit is created
class UserInitial extends UserState {
  const UserInitial();
}

/// Loading state while fetching data
class UserLoading extends UserState {
  const UserLoading();
}

/// Success state with loaded user
class UserSuccess extends UserState {
  const UserSuccess({required this.user});

  final UserEntity user;

  @override
  List<Object?> get props => [user];
}

/// Error state with error message
class UserError extends UserState {
  const UserError({required this.message});

  final String message;

  @override
  List<Object?> get props => [message];
}
```

## Cubits (Simple State Management)

Use Cubit when your state management is straightforward (no complex event handling).

### Cubit Rules

- Extend `Cubit<State>` from flutter_bloc
- Inject dependencies in constructor
- Public methods correspond to user actions
- Always emit states, never return values
- Handle errors and emit error states
- Use `const` for state constructors
- Log important steps

### Cubit Example

```dart
// presentation/blocs/user_cubit.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:commons/commons.dart';
import '../../domain/entities/user_entity.dart';
import '../../domain/usecases/get_user_usecase.dart';
import 'user_state.dart';

class UserCubit extends Cubit<UserState> {
  UserCubit({
    required this.getUserUseCase,
    required this.log,
  }) : super(const UserInitial());

  final GetUserUseCase getUserUseCase;
  final Log log;

  /// Public method: Fetch user by ID
  Future<void> fetchUser(String userId) async {
    // Step 1: Emit loading state
    emit(const UserLoading());

    // Step 2: Call use case
    final result = await getUserUseCase.call(userId);

    // Step 3: Handle result with fold
    result.fold(
      (user) {
        // Success: emit success state
        log.debug('User loaded: ${user.name}');
        emit(UserSuccess(user: user));
      },
      (error) {
        // Error: emit error state
        log.error('Error loading user: ${error.message}');
        emit(UserError(message: error.message));
      },
    );
  }

  /// Public method: Clear user
  void clearUser() {
    log.debug('Clearing user');
    emit(const UserInitial());
  }
}
```

## Pages (Full Screens)

Pages are full-screen widgets that organize the layout and connect BLoC/Cubit to UI.

### Page Rules

- Extend `StatelessWidget` when possible
- Use `BlocBuilder` to rebuild on state changes
- Use `BlocListener` for side effects (navigation, snackbars)
- NO logic, only UI organization
- Delegate state management to Cubit
- Use const constructors with keys

### Page Example

```dart
// presentation/pages/user_detail_page.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/user_cubit.dart';
import '../blocs/user_state.dart';
import '../widgets/user_info_card.dart';

class UserDetailPage extends StatelessWidget {
  const UserDetailPage({
    Key? key,
    required this.userId,
  }) : super(key: key);

  final String userId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('User Details')),
      body: BlocListener<UserCubit, UserState>(
        listener: (context, state) {
          // Handle side effects (showing snackbars, navigation)
          if (state is UserError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message)),
            );
          }
        },
        child: BlocBuilder<UserCubit, UserState>(
          builder: (context, state) {
            // Build UI based on state
            if (state is UserInitial || state is UserLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            if (state is UserSuccess) {
              return SingleChildScrollView(
                child: UserInfoCard(user: state.user),
              );
            }

            if (state is UserError) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Error: ${state.message}'),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () {
                        context.read<UserCubit>().fetchUser(userId);
                      },
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              );
            }

            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Fetch user when page loads
    context.read<UserCubit>().fetchUser(userId);
  }
}
```

## Widgets (Reusable Components)

Widgets are small, focused components that are reused across pages.

### Widget Rules

- Extend `StatelessWidget` by default
- Receive all data through constructor
- Use `const` constructors always
- NO business logic
- NO state management
- `Key` parameter is required
- Single responsibility

### Widget Example

```dart
// presentation/widgets/user_info_card.dart
import 'package:flutter/material.dart';
import '../../domain/entities/user_entity.dart';

class UserInfoCard extends StatelessWidget {
  const UserInfoCard({
    Key? key,
    required this.user,
    this.onTap,
  }) : super(key: key);

  final UserEntity user;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        margin: const EdgeInsets.all(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                user.name,
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              Text(
                'Email: ${user.email}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'ID: ${user.id}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

## BLoC (Complex State Management)

Use BLoC when you have complex event handling with multiple actions and side effects.

```dart
// presentation/blocs/user_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/usecases/get_user_usecase.dart';
import 'user_event.dart';
import 'user_state.dart';

class UserBloc extends Bloc<UserEvent, UserState> {
  UserBloc({required this.getUserUseCase})
      : super(const UserInitial()) {
    // Register event handlers
    on<FetchUserEvent>(_onFetchUser);
    on<RefreshUserEvent>(_onRefreshUser);
  }

  final GetUserUseCase getUserUseCase;

  Future<void> _onFetchUser(
    FetchUserEvent event,
    Emitter<UserState> emit,
  ) async {
    emit(const UserLoading());
    final result = await getUserUseCase.call(event.userId);
    
    result.fold(
      (user) => emit(UserSuccess(user: user)),
      (error) => emit(UserError(message: error.message)),
    );
  }

  Future<void> _onRefreshUser(
    RefreshUserEvent event,
    Emitter<UserState> emit,
  ) async {
    // Similar to fetch but might emit different states
    final result = await getUserUseCase.call(event.userId);
    result.fold(
      (user) => emit(UserSuccess(user: user)),
      (error) => emit(UserError(message: error.message)),
    );
  }
}
```

## Presentation Layer Organization

```
presentation/
├── blocs/
│   ├── user_cubit.dart
│   ├── user_state.dart
│   └── blocs.dart                    # Barrel export
│
├── pages/
│   ├── user_detail_page.dart
│   ├── user_list_page.dart
│   └── pages.dart                    # Barrel export
│
├── widgets/
│   ├── user_info_card.dart
│   ├── user_list_item.dart
│   └── widgets.dart                  # Barrel export
│
└── routes/
    ├── user_routes.dart
    └── routes.dart                   # Barrel export
```

## Testing Presentation Layer

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';

void main() {
  group('UserCubit', () {
    late MockGetUserUseCase mockUseCase;
    late UserCubit userCubit;

    setUp(() {
      mockUseCase = MockGetUserUseCase();
      userCubit = UserCubit(getUserUseCase: mockUseCase);
    });

    blocTest<UserCubit, UserState>(
      'emits [Loading, Success] when fetchUser succeeds',
      build: () {
        when(() => mockUseCase.call('user-1'))
            .thenAnswer((_) async => Success(testUser));
        return userCubit;
      },
      act: (cubit) => cubit.fetchUser('user-1'),
      expect: () => [
        const UserLoading(),
        UserSuccess(user: testUser),
      ],
    );

    blocTest<UserCubit, UserState>(
      'emits [Loading, Error] when fetchUser fails',
      build: () {
        when(() => mockUseCase.call('user-1'))
            .thenAnswer((_) async => Failure(Exception('Not found')));
        return userCubit;
      },
      act: (cubit) => cubit.fetchUser('user-1'),
      expect: () => [
        const UserLoading(),
        UserError(message: 'Exception: Not found'),
      ],
    );
  });
}
```

---

## UIModel and UIMapper

A UIModel is a display-ready version of a DomainModel. It contains strings, colors,
and other Flutter types that are computed once in the mapping step, not on every build.

### Why UIModel?

| Without UIModel | With UIModel |
|---|---|
| Widget formats strings on every rebuild | Formatted once in UIMapper |
| Widget contains `if (product.isAvailable)` logic | Widget reads `product.availabilityColor` directly |
| Widget depends on DomainModel (business type) | Widget depends only on display values |
| Tests must stub domain logic to test display | UIMapper has its own unit tests |

### UIModel Definition

```dart
// lib/{feature}/presentation/ui_models/product_uimodel.dart
class ProductUIModel {
  const ProductUIModel({
    required this.id,
    required this.displayName,
    required this.formattedPrice,
    required this.availabilityLabel,
    required this.availabilityColor,
    required this.imageUrl,
  });

  final String id;
  final String displayName;        // e.g. 'SNEAKERS AIR MAX'
  final String formattedPrice;     // e.g. '$129.99'
  final String availabilityLabel;  // e.g. 'Available' / 'Out of stock'
  final Color availabilityColor;   // Colors.green / Colors.red
  final String imageUrl;
}
```

### UIMapper Definition

```dart
// lib/{feature}/presentation/ui_models/product_uimodel.dart (continued)
abstract final class ProductUIMapper {
  static ProductUIModel toUIModel(Product product) => ProductUIModel(
        id: product.id,
        displayName: product.name.toUpperCase(),
        formattedPrice: '\$${(product.price.amount / 100).toStringAsFixed(2)}',
        availabilityLabel: product.isAvailable ? 'Available' : 'Out of stock',
        availabilityColor: product.isAvailable ? Colors.green : Colors.red,
        imageUrl: product.imageUrl,
      );

  static List<ProductUIModel> toUIModelList(List<Product> products) =>
      products.map(toUIModel).toList();
}
```

### BLoC Uses UIMapper Before Emitting State

```dart
Future<void> _onLoad(LoadProductEvent event, Emitter<ProductState> emit) async {
  emit(const ProductState.loading());
  final result = await _getProduct(GetProductParams(id: event.id));
  result.fold(
    (failure) => emit(ProductState.error(failure: failure)),
    (product) => emit(ProductState.success(
      product: ProductUIMapper.toUIModel(product), // ← mapped here
    )),
  );
}
```

### Testing UIMapper

Since UIMapper is a pure function (`Product` in, `ProductUIModel` out), it is
trivial to unit test without mocking:

```dart
void main() {
  group('ProductUIMapper', () {
    test('formats price correctly', () {
      final product = Product(
        id: '1',
        name: 'Sneakers',
        price: Money(amount: 12999, currency: 'USD'),
        isAvailable: true,
        imageUrl: 'https://example.com/img.jpg',
      );
      final uiModel = ProductUIMapper.toUIModel(product);
      expect(uiModel.formattedPrice, '\$129.99');
      expect(uiModel.displayName, 'SNEAKERS');
      expect(uiModel.availabilityColor, Colors.green);
    });

    test('shows red when out of stock', () {
      final product = Product(
        id: '2', name: 'Hat',
        price: Money(amount: 1999, currency: 'USD'),
        isAvailable: false,
        imageUrl: '',
      );
      expect(ProductUIMapper.toUIModel(product).availabilityColor, Colors.red);
    });
  });
}
```

### UIModel Rules

| Rule | Reason |
|---|---|
| UIModel in `presentation/ui_models/` | Stays in Presentation layer |
| UIMapper is `abstract final class` with `static` methods | No state, no injection needed |
| UIMapper can import `package:flutter/material.dart` | It's a presentation concern |
| UIMapper must NOT import Data layer types | Only DomainModel → UIModel conversion |
| BLoC state holds `UIModel`, not `DomainModel` | Widgets are decoupled from business types |
