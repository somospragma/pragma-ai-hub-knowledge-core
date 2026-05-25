---
id: flutter-concurrency
version: 1.1.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
description: Handles concurrent operations safely in Flutter: mutex locks with synchronized, Completer for manual Future control, Can
---

# Concurrency

See the reference files for complete patterns and code examples.

**This skill covers concurrency within a single isolate (the main thread).**
For CPU-bound parallelism across isolates, see the `flutter-isolates` skill.

## Scope — What This Skill Covers

```
flutter-concurrency (this skill)          flutter-isolates skill
─────────────────────────────────         ──────────────────────
Mutex / Lock (synchronized)               compute() / Isolate.run()
Completer (manual Future control)         Isolate.spawn()
CancelToken (cancellable operations)      worker_manager pool
Debounce / Throttle (UI actions)          isolate_manager (web+WASM)
Future.wait / Future.any (parallel I/O)
Race condition prevention
Semaphore (limit concurrency)
```

---

## Package Status (April 2026)

| Package | Version | Purpose |
|---|---|---|
| **synchronized** | 3.3.x | Mutex / Lock for async critical sections |
| **dio** | 5.x | `CancelToken` for cancellable HTTP requests |

Everything else uses native `dart:async`.

---

## Core Patterns — Quick Reference

### Mutex — prevent concurrent access
```dart
final _lock = Lock();

Future<void> criticalSection() async {
  await _lock.synchronized(() async {
    // Only one caller runs this at a time
    await _database.write(data);
  });
}
```

### Completer — manual Future control
```dart
final completer = Completer<String>();
// Complete from anywhere:
completer.complete('result');
// Or fail:
completer.completeError(Exception('failed'));
// Await:
final result = await completer.future;
```

### Debounce — wait for silence (UI actions)
```dart
Timer? _debounce;

void onSearchChanged(String query) {
  _debounce?.cancel();
  _debounce = Timer(const Duration(milliseconds: 300), () {
    context.read<SearchBloc>().add(SearchEvent.queryChanged(query));
  });
}
```

### Cancellable HTTP request
```dart
final cancelToken = CancelToken();

// Cancel from anywhere:
cancelToken.cancel('User navigated away');

// Use in Dio:
await _dio.get('/products', cancelToken: cancelToken);
```

### Parallel I/O — Future.wait
```dart
// Run independent async operations concurrently
final (user, cart, config) = await (
  _userRepo.getUser(),
  _cartRepo.getCart(),
  _configRepo.getConfig(),
).wait; // Dart 3 record syntax
```

---

## Common Concurrency Problems

| Problem | Symptom | Solution |
|---|---|---|
| Double-submit | Form submitted twice | `droppable()` BLoC / `_isSubmitting` flag |
| Race condition on write | Corrupted data | `Lock` from `synchronized` |
| Stale response | Old response overwrites new | `CancelToken` + `restartable()` BLoC |
| Concurrent token refresh | Multiple 401 → multiple refresh calls | `Lock` + `Completer` |
| UI jank from parallel awaits | Sequential when could be parallel | `Future.wait` |
| Semaphore overflow | Too many concurrent requests | `Semaphore` with max count |

---

## Architecture Integration

```
Presentation (BLoC — droppable/restartable EventTransformer)
  ↓
Domain (UseCase — CancelToken, Future.wait)
  ↓
Data (RepositoryImpl — Lock for critical sections, CancelToken for HTTP)
  └── DataSource (Dio with CancelToken)
```

---

## Quick Wins Checklist

- [ ] Form submit uses `droppable()` or `_isSubmitting` guard — no double-submit
- [ ] Token refresh uses `Lock` — only one refresh at a time
- [ ] Independent async calls use `Future.wait` — not sequential `await`
- [ ] Navigation-triggered requests use `CancelToken` — cancelled on dispose
- [ ] `Lock` instance is shared (field/singleton) — not created per call
- [ ] `Completer` completed exactly once — guarded with `isCompleted` check
- [ ] `Timer` cancelled in `dispose()` — no callbacks after widget is gone

## Reference Files

- `references/mutex_lock.md` — synchronized Lock, reentrant lock, token refresh pattern, semaphore
- `references/completer_cancel.md` — Completer, CancelToken, cancellable operations, timeout
- `references/parallel_debounce.md` — Future.wait, Future.any, debounce, throttle, double-submit prevention
