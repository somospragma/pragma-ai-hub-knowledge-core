# Mediator Pattern — Cross-Feature Communication

## Table of Contents

1. [Why Features Must Not Import Each Other](#why-features-must-not-import-each-other)
2. [MediatorEvent — Base Type](#1-mediatorevent--base-type)
3. [AppMediator — Interface](#2-appmediator--interface)
4. [AppMediatorImpl — Implementation](#3-appmediatorimpl--implementation)
5. [Event Catalog — Define Events in Core](#4-event-catalog--define-events-in-core)
6. [BLoC Integration — Publisher](#5-bloc-integration--publisher)
7. [BLoC Integration — Subscriber](#6-bloc-integration--subscriber)
8. [DI Registration](#7-di-registration)
9. [Rules](#8-rules)
10. [When to Use Mediator vs Direct UseCase Call](#9-when-to-use-mediator-vs-direct-usecase-call)
11. [Event Catalog Template](#10-event-catalog-template)

---

## Why Features Must Not Import Each Other

In Clean Architecture, each feature is a vertical slice with its own
`data/domain/presentation` layers. When Feature A imports Feature B directly,
it creates **horizontal coupling** — a dependency that is not governed by the
layer rules and that makes both features impossible to test or reuse in isolation.

```
❌ Direct import — horizontal coupling
feature_a/presentation/bloc/order_bloc.dart
  └── imports feature_b/domain/usecases/get_user_usecase.dart

Problems:
  - OrderBloc now depends on User feature internals
  - Removing or renaming User feature breaks OrderBloc
  - Cannot test OrderBloc without the User feature
  - Cannot reuse OrderBloc in a different app without User

✅ Mediator — decoupled communication
feature_a/presentation/bloc/order_bloc.dart
  └── sends UserLoggedInEvent via AppMediator

feature_b/presentation/bloc/user_bloc.dart
  └── listens to UserLoggedInEvent via AppMediator

Neither feature knows the other exists.
```

---

## 1. MediatorEvent — Base Type

```dart
// lib/core/mediator/mediator_event.dart

/// Base class for all cross-feature events.
abstract interface class MediatorEvent {
  const MediatorEvent();
}
```

---

## 2. AppMediator — Interface

```dart
// lib/core/mediator/app_mediator.dart
import 'mediator_event.dart';

abstract interface class AppMediator {
  /// Publish an event to all subscribers.
  void send(MediatorEvent event);

  /// Subscribe to events of type [T].
  /// Returns a broadcast stream — multiple listeners allowed.
  Stream<T> on<T extends MediatorEvent>();
}
```

---

## 3. AppMediatorImpl — Implementation

```dart
// lib/core/mediator/app_mediator_impl.dart
import 'dart:async';
import 'package:injectable/injectable.dart';
import 'app_mediator.dart';
import 'mediator_event.dart';

@LazySingleton(as: AppMediator)
class AppMediatorImpl implements AppMediator {
  final _controller = StreamController<MediatorEvent>.broadcast();

  @override
  void send(MediatorEvent event) {
    if (!_controller.isClosed) _controller.add(event);
  }

  @override
  Stream<T> on<T extends MediatorEvent>() =>
      _controller.stream.whereType<T>();

  void dispose() => _controller.close();
}
```

---

## 4. Event Catalog — Define Events in Core

Cross-feature events live in `core/mediator/events/` — not inside any feature.
This keeps the contract neutral and prevents either feature from owning it.

```dart
// lib/core/mediator/events/auth_events.dart

/// Published by: AuthBloc (auth feature)
/// Subscribed by: CartBloc (cart feature), ProfileBloc (profile feature)
class UserLoggedInEvent extends MediatorEvent {
  const UserLoggedInEvent({required this.userId, required this.email});
  final String userId;
  final String email;
}

class UserLoggedOutEvent extends MediatorEvent {
  const UserLoggedOutEvent();
}

class SessionExpiredEvent extends MediatorEvent {
  const SessionExpiredEvent();
}
```

```dart
// lib/core/mediator/events/cart_events.dart
class CartUpdatedEvent extends MediatorEvent {
  const CartUpdatedEvent({required this.itemCount, required this.total});
  final int itemCount;
  final double total;
}

class CartClearedEvent extends MediatorEvent {
  const CartClearedEvent();
}
```

---

## 5. BLoC Integration — Publisher

```dart
// lib/auth/presentation/bloc/auth_bloc.dart
@injectable
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final SignInUseCase _signIn;
  final AppMediator _mediator;

  AuthBloc(this._signIn, this._mediator) : super(const AuthState.initial()) {
    on<SignInEvent>(_onSignIn);
    on<SignOutEvent>(_onSignOut);
  }

  Future<void> _onSignIn(SignInEvent event, Emitter<AuthState> emit) async {
    emit(const AuthState.loading());
    final result = await _signIn(SignInParams(
      email: event.email,
      password: event.password,
    ));

    result.fold(
      (failure) => emit(AuthState.error(failure: failure)),
      (user) {
        // ✅ Publish — Auth feature does not know who listens
        _mediator.send(UserLoggedInEvent(
          userId: user.id,
          email: user.email,
        ));
        emit(AuthState.authenticated(user: user));
      },
    );
  }

  Future<void> _onSignOut(SignOutEvent event, Emitter<AuthState> emit) async {
    await _signOut();
    _mediator.send(const UserLoggedOutEvent());
    emit(const AuthState.unauthenticated());
  }
}
```

---

## 6. BLoC Integration — Subscriber

```dart
// lib/cart/presentation/bloc/cart_bloc.dart
@injectable
class CartBloc extends Bloc<CartEvent, CartState> {
  final LoadCartUseCase _loadCart;
  final ClearCartUseCase _clearCart;
  final AppMediator _mediator;

  StreamSubscription<MediatorEvent>? _authSub;

  CartBloc(this._loadCart, this._clearCart, this._mediator)
      : super(const CartState.initial()) {
    on<LoadCartEvent>(_onLoad);
    on<ClearCartEvent>(_onClear);

    // ✅ Subscribe — Cart feature does not know Auth feature exists
    _authSub = _mediator.on<UserLoggedInEvent>().listen((event) {
      add(CartEvent.load(userId: event.userId));
    });

    _mediator.on<UserLoggedOutEvent>().listen((_) {
      add(const CartEvent.clear());
    });
  }

  Future<void> _onLoad(LoadCartEvent event, Emitter<CartState> emit) async {
    emit(const CartState.loading());
    final result = await _loadCart(LoadCartParams(userId: event.userId));
    result.fold(
      (failure) => emit(CartState.error(failure: failure)),
      (cart) => emit(CartState.success(cart: cart)),
    );
  }

  @override
  Future<void> close() async {
    await _authSub?.cancel(); // ✅ always cancel in close()
    return super.close();
  }
}
```

---

## 7. DI Registration

The `AppMediatorImpl` is registered via `@LazySingleton(as: AppMediator)` directly
on the class — Injectable handles the rest. All BLoCs that inject `AppMediator`
share the same singleton instance and therefore the same stream.

---

## 8. Rules

| Rule | Reason |
|---|---|
| Events live in `core/mediator/events/` | Neutral ground — no feature owns the contract |
| Features only import `AppMediator` and event types from `core/` | No horizontal coupling |
| Always cancel subscriptions in BLoC `close()` | Memory leak prevention |
| Events are immutable (`const` constructors) | Safe to share across isolates |
| One event = one thing that happened | Events are facts, not commands |
| Do not send events from the Domain layer | Mediator is a presentation/application concern |

---

## 9. When to Use Mediator vs Direct UseCase Call

| Scenario | Use |
|---|---|
| Feature A needs data from Feature B's domain | Shared UseCase in `core/` or `packages/core/domain/` |
| Feature A needs to notify Feature B that something happened | Mediator event |
| Feature A needs Feature B to perform an action | Mediator event (B decides how to react) |
| Two features share the same domain concept | Extract to a shared package |
| Navigation between features | Router (go_router) — not Mediator |

---

## 10. Event Catalog Template

Document all cross-feature events in a single place for discoverability.

```
core/mediator/events/
├── auth_events.dart        UserLoggedInEvent, UserLoggedOutEvent, SessionExpiredEvent
├── cart_events.dart        CartUpdatedEvent, CartClearedEvent
├── order_events.dart       OrderPlacedEvent, OrderCancelledEvent
└── onboarding_events.dart  OnboardingCompletedEvent
```

Each event file should include a comment with the publisher and expected subscribers (see §4 above).
