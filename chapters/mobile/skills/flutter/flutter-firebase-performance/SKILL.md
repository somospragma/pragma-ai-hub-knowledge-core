---
id: flutter-firebase-performance
version: 1.1.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
description: Monitors Flutter app performance in real time: custom traces, HTTP monitoring, startup time, and screen rendering. Fireb
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

```
Domain (PerformanceMonitor interface)
  ↓ abstract interface class
Data (PerformanceMonitorAdapter)
  ├── FirebasePerformanceAdapter   ← primary
  ├── SentryPerformanceAdapter     ← alternative
  ├── DatadogPerformanceAdapter    ← enterprise
  └── NoOpPerformanceAdapter       ← debug / tests
DI
  └── bind PerformanceMonitor → FirebasePerformanceAdapter
```

---

## Core Patterns — Quick Reference

### Custom trace
```dart
final trace = await _monitor.startTrace('checkout_flow');
trace.putAttribute('payment_method', 'card');
// ... do work ...
trace.putMetric('items_count', cart.items.length);
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
- [ ] Attributes added to traces for filtering (user tier, feature flag, etc.)
- [ ] Performance disabled in tests — `NoOpPerformanceAdapter` injected
- [ ] Alerts configured in Firebase console for p95 latency regressions

## Reference Files

- `references/firebase_implementation.md` — Firebase Performance setup, custom traces, HTTP metrics, Dio interceptor, startup trace
- `references/performance_provider_pattern.md` — PerformanceMonitor interface, adapters (Firebase, Sentry, Datadog, NoOp), DI binding
