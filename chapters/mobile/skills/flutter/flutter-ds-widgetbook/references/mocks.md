# Mocking dependencies

Cataloging a widget that has external dependencies (providers, services, repositories) requires an explicit strategy. There are two approaches; choose based on the type of widget.

## When to use each approach

| Situation | Approach |
|---|---|
| The widget receives data as parameters but internally reads a provider | **Extraction** — extract the dependency into a parameter |
| The widget is a *full screen* that consumes providers and cannot be refactored | **Library mocking** — inject the mocked provider into the tree |
| The widget is a simple reusable component | **Hardcode values** directly in the use case (no provider) |

---

## Approach I: Extraction

The simplest way: extract the dependency into the widget's constructor and pass it directly in the use case. It changes the widget tree but makes the component more testable and portable.

**Original widget (with an internal dependency):**
```dart
class UserTile extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<UserProvider>(
      builder: (context, provider, child) => Text(provider.user),
    );
  }
}
```

**Refactored widget (dependency extracted):**
```dart
class UserTile extends StatelessWidget {
  const UserTile({super.key, required this.user});
  final String user;

  @override
  Widget build(BuildContext context) => Text(user);
}
```

**Use case with extraction:**
```dart
@UseCase(name: 'default', type: UserTile)
Widget buildUserTileUseCase(BuildContext context) {
  final user = context.knobs.string(label: 'user', initialValue: 'Ana Garcia');

  context.setCodePreview('''
UserTile(
  user: '\$user',
)''');

  return UserTile(user: user);
}
```

**Resulting tree in Widgetbook:**
```
WidgetbookApp
└── UserTile
    └── Text
```

---

## Approach II: Library mocking (mocktail)

When the widget is a full screen that depends on providers and refactoring it is not feasible, inject the mocked provider directly into the use case tree.

### Step 1 — Add `mocktail` to the widgetbook's `pubspec.yaml`

```yaml
dependencies:
  # ...
  mocktail: ^1.0.0
```

> `mocktail` goes under `dependencies` (not `dev_dependencies`) because the entire widgetbook is a development tool; it is not included in the app's production build.

### Step 2 — Create the mock and use it in the use case

```dart
import 'package:flutter/material.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';
import 'package:widgetbook/widgetbook.dart';
import 'package:widgetbook_annotation/widgetbook_annotation.dart';
import 'package:my_app/features/home/home_screen.dart';
import 'package:my_app/providers/user_provider.dart';
import '../../../shared/code_preview_addon.dart';

// Mock defined at file level (outside the use case)
class MockUserProvider extends Mock implements UserProvider {}

@UseCase(name: 'default', type: HomeScreen)
Widget buildHomeScreenUseCase(BuildContext context) {
  final userName = context.knobs.string(label: 'userName', initialValue: 'Ana Garcia');
  final isAuthenticated = context.knobs.boolean(label: 'isAuthenticated', initialValue: true);

  context.setCodePreview('''
HomeScreen()''');

  return ChangeNotifierProvider<UserProvider>(
    create: (_) {
      final provider = MockUserProvider();
      when(() => provider.user).thenReturn(userName);
      when(() => provider.isAuthenticated).thenReturn(isAuthenticated);
      return provider;
    },
    child: const HomeScreen(),
  );
}
```

**Resulting tree in Widgetbook:**
```
WidgetbookApp
└── MockUserProvider     ← mocked provider injected by the use case
    └── HomeScreen
        └── Consumer<UserProvider>
            └── Text
```

---

## Mocking multiple dependencies

When a screen depends on several providers, stack them with `MultiProvider`:

```dart
class MockAuthProvider extends Mock implements AuthProvider {}
class MockCartProvider extends Mock implements CartProvider {}

@UseCase(name: 'default', type: CheckoutScreen)
Widget buildCheckoutScreenUseCase(BuildContext context) {
  final userName = context.knobs.string(label: 'userName', initialValue: 'Carlos Lopez');
  final itemCount = context.knobs.int.input(label: 'itemCount', initialValue: 3);
  final total = context.knobs.double.input(label: 'total', initialValue: 129.99);

  context.setCodePreview('''
CheckoutScreen()''');

  return MultiProvider(
    providers: [
      ChangeNotifierProvider<AuthProvider>(
        create: (_) {
          final auth = MockAuthProvider();
          when(() => auth.userName).thenReturn(userName);
          return auth;
        },
      ),
      ChangeNotifierProvider<CartProvider>(
        create: (_) {
          final cart = MockCartProvider();
          when(() => cart.itemCount).thenReturn(itemCount);
          when(() => cart.total).thenReturn(total);
          return cart;
        },
      ),
    ],
    child: const CheckoutScreen(),
  );
}
```

---

## Mocking repositories and services (no provider)

For widgets that inject repositories or services directly through the constructor:

```dart
class MockProductRepository extends Mock implements ProductRepository {}

@UseCase(name: 'default', type: ProductDetailScreen)
Widget buildProductDetailScreenUseCase(BuildContext context) {
  final title = context.knobs.string(label: 'title', initialValue: 'Runner Pro Sneakers');
  final price = context.knobs.double.input(label: 'price', initialValue: 89.99);

  final repo = MockProductRepository();
  when(() => repo.getProduct(any())).thenAnswer(
    (_) async => Product(title: title, price: price),
  );

  context.setCodePreview('''
ProductDetailScreen(
  repository: repository,
  productId: '123',
)''');

  return ProductDetailScreen(
    repository: repo,
    productId: '123',
  );
}
```

---

## Rules

- Mocks are declared **at file level**, outside the use case method, so they can be reused across variants of the same widget.
- Use `when(() => mock.property).thenReturn(value)` to stub synchronous properties.
- Use `when(() => mock.method(any())).thenAnswer((_) async => value)` for async methods.
- Stubbed values **should be wired to knobs** whenever they are useful for interactive exploration.
- Never depend on the app's real tree or on globally registered providers — the use case must be fully self-contained.
- `mocktail` goes under `dependencies` (not `dev_dependencies`) in `widgetbook_[appname]/pubspec.yaml`.
