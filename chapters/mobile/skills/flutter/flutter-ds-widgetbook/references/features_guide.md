# Features — Catalog the Project's Screens

---

## Table of contents

1. [When to catalog a screen](#1-when-to-catalog-a-screen)
2. [Analyze the screen before generating](#2-analyze-the-screen-before-generating)
3. [Isolate the screen from its dependencies](#3-isolate-the-screen-from-its-dependencies)
4. [Screen variants — states to cover](#4-screen-variants--states-to-cover)
5. [Complete pattern of a feature use case](#5-complete-pattern-of-a-feature-use-case)
6. [File location](#6-file-location)
7. [Update existing features](#7-update-existing-features)

---

## 1. When to catalog a screen

| Situation | Action |
|---|---|
| A new screen was created in the project | Create a use case in `widgetbook_[appname]/lib/features/` |
| An existing screen was modified (new fields, states, layout) | Update the existing use case |
| You want to document every screen in the project | Scan `lib/features/` or `lib/screens/` and create the missing use cases |
| The user asks "add this screen to the widgetbook" | Create a use case for that screen |

---

## 2. Analyze the screen before generating

Before writing code, read the entire screen and identify:

### 2.1 — Dependencies to mock

| Dependency type | What to look for | How to mock it |
|---|---|---|
| **State management** | `Provider`, `Bloc`, `Cubit`, `Riverpod`, `GetX` | Wrapper with mock data |
| **Services/Repositories** | Dependency injection, `GetIt`, constructors | Mock instance in the use case |
| **Navigation** | `Navigator.push`, `GoRouter`, `AutoRoute` | Callbacks with `developer.log()` — do not navigate |
| **API/Network** | `http`, `dio`, backend calls | Hardcoded domain data |
| **Local storage** | `SharedPreferences`, `Hive`, `SQLite` | Inline mock data |
| **Auth** | Token, user session, permissions | Mock of an authenticated user |

### 2.2 — Visible screen states

Identify every state the screen can display:

```
Does it have a loading state? → 'loading' variant
Does it have an empty state (no data)? → 'empty' variant
Does it have an error state? → 'error' variant
Does it have a success/confirmation state? → 'success' variant
Does it have a variant for a new user? → 'first_time' variant
Does it have a variant for an unauthenticated user? → 'logged_out' variant
Does it have a variant with complete data? → 'default' variant (always)
```

### 2.3 — Parameters configurable with knobs

Not every screen has explicit parameters like a component does.
Identify what can be controlled from knobs:

- **User data** (name, avatar, role)
- **Number of items** in lists
- **Form state** (empty, with errors, complete)
- **Feature flags** (show/hide sections)
- **Permissions** (admin vs regular user)

---

## 3. Isolate the screen from its dependencies

**Core rule:** the screen must render in isolation in Widgetbook,
without depending on the app's real widget tree, navigation, or remote services.

### 3.1 — Pattern: providers wrapper

```dart
// When the screen needs providers from the tree
@UseCase(name: 'default', type: HomeScreen)
Widget buildHomeScreenUseCase(BuildContext context) {
  final userName = context.knobs.string(
    label: 'userName',
    initialValue: 'Maria Garcia',
  );

  // Mock the providers the screen needs
  return MockAppProviders(
    user: User(name: userName, email: 'maria@example.com'),
    products: _mockProducts,
    child: const HomeScreen(),
  );
}
```

### 3.2 — Pattern: constructor injection

```dart
// If the screen accepts data via constructor (preferred)
@UseCase(name: 'default', type: ProductDetailScreen)
Widget buildProductDetailScreenUseCase(BuildContext context) {
  return ProductDetailScreen(
    product: Product(
      id: 'PRD-001',
      name: context.knobs.string(label: 'productName', initialValue: 'Trail X3 Sneakers'),
      price: context.knobs.double.input(label: 'price', initialValue: 129.90),
      description: 'Trail running shoes with a Vibram sole and premium cushioning.',
      imageUrl: 'https://picsum.photos/400/300?random=1',
      stock: context.knobs.int.slider(label: 'stock', initialValue: 15, min: 0, max: 100),
    ),
    onAddToCart: () => developer.log('Product PRD-001 added to cart'),
    onBack: () => developer.log('Navigate back'),
  );
}
```

### 3.3 — Pattern: replace navigation with callbacks

```dart
// ❌ Don't — depends on real navigation
onTap: () => Navigator.pushNamed(context, '/detail', arguments: item),

// ✅ Do — descriptive developer.log without navigating
onTap: () => developer.log('Navigate to detail: ${item.id} - ${item.name}'),
```

### 3.4 — Pattern: Bloc/Cubit mock

```dart
@UseCase(name: 'default', type: OrderListScreen)
Widget buildOrderListScreenUseCase(BuildContext context) {
  return BlocProvider<OrderListCubit>.value(
    value: MockOrderListCubit(
      state: OrderListState.loaded(
        orders: _mockOrders,
      ),
    ),
    child: const OrderListScreen(),
  );
}

@UseCase(name: 'loading', type: OrderListScreen)
Widget buildOrderListScreenLoadingUseCase(BuildContext context) {
  return BlocProvider<OrderListCubit>.value(
    value: MockOrderListCubit(
      state: const OrderListState.loading(),
    ),
    child: const OrderListScreen(),
  );
}

@UseCase(name: 'empty', type: OrderListScreen)
Widget buildOrderListScreenEmptyUseCase(BuildContext context) {
  return BlocProvider<OrderListCubit>.value(
    value: MockOrderListCubit(
      state: const OrderListState.loaded(orders: []),
    ),
    child: const OrderListScreen(),
  );
}

@UseCase(name: 'error', type: OrderListScreen)
Widget buildOrderListScreenErrorUseCase(BuildContext context) {
  return BlocProvider<OrderListCubit>.value(
    value: MockOrderListCubit(
      state: const OrderListState.error(message: 'Unable to load the orders'),
    ),
    child: const OrderListScreen(),
  );
}
```

---

## 4. Screen variants — states to cover

### General rule for screens

| State | Suggested `name` | When to include it |
|---|---|---|
| Screen with complete data | `'default'` | Always |
| Loading data from the server | `'loading'` | If the screen has an initial fetch |
| No data / empty list | `'empty'` | If the screen may have no content |
| Load / network error | `'error'` | If the screen handles errors |
| Form with validation errors | `'validation_error'` | If it has forms |
| Unauthenticated user | `'logged_out'` | If it has content conditioned by auth |
| First time / onboarding | `'first_time'` | If it has a first-use flow |
| Maximum data / saturation | `'full'` | If the UI can be saturated with lots of data |

### Strategy by screen type

**List screen (home, catalog, history):**
```
default     → list with 10-20 items using Figma copy or domain data
loading     → skeleton / shimmer / spinner
empty       → empty state with a message and illustration
error       → network error with a retry button
```

**Detail screen (product, profile, order):**
```
default     → all data complete
loading     → loading the item's data
error       → item not found or network error
```

**Form screen (login, sign-up, checkout):**
```
default          → empty form ready to fill in
validation_error → fields with visible validation errors
prefilled        → form with preloaded data (editing)
```

**Auth screen (login, sign-up, password recovery):**
```
default     → clean form
error       → invalid credentials / server error
loading     → processing authentication
```

**Dashboard / main screen:**
```
default     → data loaded with metrics/summary
loading     → loading initial data
empty       → new user with no activity
```

---

## 5. Complete pattern of a feature use case

```dart
// widgetbook_[appname]/lib/features/auth/login_screen/login_screen.use_case.dart

import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';
import 'package:widgetbook_annotation/widgetbook_annotation.dart';
import 'package:your_app/features/auth/presentation/login_screen.dart';
import '../../../shared/code_preview_addon.dart';

@UseCase(name: 'default', type: LoginScreen)
Widget buildLoginScreenUseCase(BuildContext context) {
  context.setCodePreview('''
LoginScreen(
  onLogin: (email, password) { /* handle login */ },
  onForgotPassword: () { /* navigate */ },
  onRegister: () { /* navigate */ },
)''');

  return LoginScreen(
    onLogin: (email, password) => developer.log('Login attempt: $email'),
    onForgotPassword: () => developer.log('Navigate to forgot password'),
    onRegister: () => developer.log('Navigate to register'),
  );
}

@UseCase(name: 'error', type: LoginScreen)
Widget buildLoginScreenErrorUseCase(BuildContext context) {
  final errorMessage = context.knobs.string(
    label: 'errorMessage',
    initialValue: 'Invalid credentials. Check your email and password.',
  );

  context.setCodePreview('''
LoginScreen(
  initialError: '$errorMessage',
  onLogin: (email, password) { /* handle retry */ },
  onForgotPassword: () { /* navigate */ },
  onRegister: () { /* navigate */ },
)''');

  return LoginScreen(
    initialError: errorMessage,
    onLogin: (email, password) => developer.log('Login retry: $email'),
    onForgotPassword: () => developer.log('Navigate to forgot password'),
    onRegister: () => developer.log('Navigate to register'),
  );
}

@UseCase(name: 'loading', type: LoginScreen)
Widget buildLoginScreenLoadingUseCase(BuildContext context) {
  context.setCodePreview('''
LoginScreen(
  isLoading: true,
  onLogin: (email, password) { /* handle login */ },
  onForgotPassword: () { /* navigate */ },
  onRegister: () { /* navigate */ },
)''');

  return LoginScreen(
    isLoading: true,
    onLogin: (email, password) => developer.log('Login in progress'),
    onForgotPassword: () => developer.log('Navigate to forgot password'),
    onRegister: () => developer.log('Navigate to register'),
  );
}
```

---

## 6. File location

### Rule: mirror the main project's feature structure

Look up the feature structure in the main project and replicate it
in `widgetbook_[appname]/lib/features/`:

**Main project:**
```
lib/features/
├── auth/
│   ├── login_screen.dart
│   └── register_screen.dart
├── home/
│   └── home_screen.dart
└── profile/
    └── profile_screen.dart
```

**Widgetbook (mirror):**
```
widgetbook_[appname]/lib/
├── ui_system/          ← components (see project_structure.md)
├── features/           ← screens (mirror the project)
│   ├── auth/
│   │   ├── login_screen/
│   │   │   └── login_screen.use_case.dart
│   │   └── register_screen/
│   │       └── register_screen.use_case.dart
│   ├── home/
│   │   └── home_screen/
│   │       └── home_screen.use_case.dart
│   └── profile/
│       └── profile_screen/
│           └── profile_screen.use_case.dart
└── shared/
```

### Detect screens in the project

Look for files ending in `_screen.dart`, `_page.dart`, or `_view.dart`
in the main project:

```
lib/features/**/      → screens by feature
lib/screens/          → flat screens folder
lib/pages/            → flat pages folder
lib/presentation/     → presentation layer (Clean Architecture)
```

---

## 7. Update existing features

When a project screen changes and it already has a use case in Widgetbook:

1. **Read the updated screen** — identify what changed: new fields, states, layout, dependencies.
2. **Compare it with the existing use case** — verify whether the knobs, mocks, and variants are still correct.
3. **Update what's needed:**
   - New parameter → add the corresponding knob or mock
   - New visual state → add a variant
   - Removed dependency → remove the mock
   - Data model change → update the mock data
4. **Regenerate** — run `dart run build_runner build --delete-conflicting-outputs`

### Signals that a use case needs updating

- The screen has parameters that are not in the use case
- The use case uses models with fields that no longer exist
- The screen has new states not covered by variants
- The use case's providers/blocs no longer match the current ones
