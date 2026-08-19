---
id: flutter-firebase-performance
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-firebase-performance
description: >
  Monitors Flutter app performance in real time: custom traces, HTTP monitoring, startup time, and screen rendering. Firebase Performance is the primary provider, with a Strategy + Adapter pattern to swap to Sentry, Datadog, or custom providers. Use this skill when instrumenting critical user flows, tracking API latency, measuring cold start time, or setting up performance regression alerts.
---
# Performance Monitoring

See the reference files for complete patterns and code examples.

**Performance monitoring = measure what users actually experience, not what you think they experience.**

## Provider Options (April 2026)

| Provider | Package | Best for |
|---|---|---|
| **Firebase Performance** | `firebase_performance ^0.11.3` | Firebase ecosystem, free tier, automatic HTTP |
| **Sentry** | `sentry_flutter ^9.x` | Error + performance in one SDK, distributed tracing |
| **Datadog RUM** | `datadog_flutter_plugin ^3.2.x` | Enterprise, session replay, full observability |
| **Custom / OpenTelemetry** | — | Full control, vendor-neutral |

> Firebase Performance is the primary implementation. Use the `PerformanceMonitor`
> Strategy + Adapter pattern to swap providers without touching business logic.

---

## What to Measure

| Metric | How | Target |
|---|---|---|
| Cold start time | Automatic (Firebase) / startup trace | < 2s |
| Screen render time | Custom trace per screen | < 300ms |
| API response time | HTTP metric / Dio interceptor | < 500ms p95 |
| Critical user flow | Custom trace (login, checkout, etc.) | Define per flow |
| Frame rate / jank | Firebase automatic | 0 frozen frames |

---

## Provider Strategy Pattern

The abstraction rule: **only `FirebasePerformanceAdapter` imports `firebase_performance`. Everything else — BLoC, UseCase, Repository, Cubit — depends only on the `PerformanceMonitor` interface.** This is what enables swapping Firebase → Sentry with a single DI change.

```
Domain (PerformanceMonitor interface)
  ↓ abstract interface class — no firebase_performance import
Data (PerformanceMonitorAdapter)
  ├── FirebasePerformanceAdapter   ← primary (only file that imports firebase_performance)
  ├── SentryPerformanceAdapter     ← alternative
  ├── DatadogPerformanceAdapter    ← enterprise
  └── NoOpPerformanceAdapter       ← debug / tests
DI
  └── bind PerformanceMonitor → FirebasePerformanceAdapter
```

---

## Core Patterns — Quick Reference

**Critical rule: never import `firebase_performance` in BLoC, Cubit, UseCase, or Repository. Always call `_monitor.startTrace()` through the interface — this is what makes provider-swapping possible.**

### Attribute privacy rule

Trace attributes are sent to third-party observability platforms (Firebase, Sentry, Datadog) and may be retained for extended periods with broader access than your primary database. **Never attach PII or sensitive financial data to trace attributes or metrics.**

```dart
// ❌ PII / sensitive financial data — violates GDPR, PCI-DSS
trace.putAttribute('card_number', user.cardNumber);
trace.putAttribute('email', user.email);
trace.putAttribute('user_id', user.internalId);   // directly identifies a person

// ✅ Non-identifying categorical attributes — safe for telemetry
trace.putAttribute('payment_type', 'card');        // generic category, not card details
trace.putAttribute('user_tier', 'premium');        // business segment, not identity
trace.putAttribute('checkout_variant', 'express'); // feature flag / A-B test label
trace.putAttribute('item_count', '3');             // aggregate, non-identifying
```

Use categorical labels that describe *behavior* or *configuration*, not identity.

### Custom trace
```dart
// ✅ Correct — calls the interface, never Firebase SDK directly
final trace = await _monitor.startTrace('checkout_flow');
trace.putAttribute('payment_type', 'card');        // ← generic category, not card details
trace.putAttribute('user_tier', 'premium');
// ... do work ...
trace.putMetric('items_count', cart.items.length);
await trace.stop();  // ← always in a finally block to guarantee execution
```

```dart
// ❌ Wrong — bypasses the abstraction, couples business logic to Firebase
final trace = FirebasePerformance.instance.newTrace('checkout_flow');
await trace.start();
// ... this prevents you from swapping providers later
await trace.stop();
```

### HTTP metric (Dio interceptor)
```dart
// Automatically tracks: response time, payload size, status code
dio.interceptors.add(PerformanceHttpInterceptor(_monitor));
```

### Screen trace
```dart
// Wrap in initState / dispose
final _trace = await _monitor.startTrace('screen_product_detail');
// dispose:
await _trace.stop();
```

---

## Quick Wins Checklist

- [ ] `PerformanceMonitor` interface used — not Firebase SDK directly in BLoC/domain
- [ ] `NoOpPerformanceAdapter` used in debug builds — no overhead during development
- [ ] Dio interceptor added — automatic HTTP latency tracking
- [ ] Startup trace wraps `main()` initialization
- [ ] Critical user flows (login, checkout, onboarding) have custom traces
- [ ] Attributes added to traces for filtering — non-identifying categorical values only (user tier, feature flag, payment type category); never PII, emails, card numbers, or user IDs
- [ ] Performance disabled in tests — `NoOpPerformanceAdapter` injected
- [ ] Alerts configured in Firebase console for p95 latency regressions

## Reference Files

- `references/firebase_implementation.md` — Firebase Performance setup, custom traces, HTTP metrics, Dio interceptor, startup trace
- `references/performance_provider_pattern.md` — PerformanceMonitor interface, adapters (Firebase, Sentry, Datadog, NoOp), DI binding
