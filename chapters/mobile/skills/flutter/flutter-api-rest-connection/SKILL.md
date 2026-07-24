---
id: flutter-api-rest-connection
version: 2.0.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
description: >
  Configures and implements REST API connections in Flutter using Dio: complete Dio client setup with environment-based URLs, interceptor stack (auth with 401 token refresh + mutex lock, safe logging without PII exposure, exponential backoff retry, error mapping), multipart file upload, request cancellation, and Clean Architecture integration. USE THIS SKILL when: setting up HTTP communication with a backend, implementing 401 token refresh with race condition prevention, adding secure logging without exposing tokens/passwords/PII, implementing resilient retry logic for transient network failures, mapping HTTP errors to domain Failures, handling multipart file uploads, or integrating HTTP client with DataSource/Repository layers.
---
# REST API Connection in Flutter

**The HTTP layer lives entirely in the Data layer.** Domain never knows about Dio, HTTP status codes, or JSON responses.

---

## Quick Start: 3-Step Setup

### Step 1: Register Dio as a singleton
```dart
@module
abstract class HttpModule {
  @lazySingleton
  Dio provideDio(
    AuthInterceptor authInterceptor,
    RetryInterceptor retryInterceptor,
    SafeLoggingInterceptor loggingInterceptor,
    ErrorInterceptor errorInterceptor,
  ) =>
      Dio(BaseOptions(
        baseUrl: Env.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 30),
      ))
        ..interceptors.addAll([
          authInterceptor,
          retryInterceptor,
          loggingInterceptor,
          errorInterceptor,
        ]);

  @injectable
  ApiClient provideApiClient(Dio dio) => ApiClientImpl(dio);
}
```

### Step 2: Implement RemoteDataSource
```dart
@Injectable()
class ProductRemoteDataSource {
  final ApiClient _client;
  ProductRemoteDataSource(this._client);

  Future<List<ProductModel>> getProducts() async {
    try {
      final response = await _client.get<List>('/products');
      return (response.data as List).map(ProductModel.fromJson).toList();
    } catch (e) {
      rethrow; // ErrorInterceptor handles conversion to AppException
    }
  }
}
```

### Step 3: Map to Repository
```dart
@Singleton()
class ProductRepositoryImpl implements ProductRepository {
  final ProductRemoteDataSource _remoteDataSource;
  ProductRepositoryImpl(this._remoteDataSource);

  @override
  Future<Either<Failure, List<Product>>> getProducts() async {
    try {
      final models = await _remoteDataSource.getProducts();
      return Right(models.map((m) => m.toDomain()).toList());
    } on AppException catch (e) {
      return Left(e.toFailure()); // Convert to domain Failure
    }
  }
}
```

---

## Architecture — Layer Responsibilities

```
┌─────────────────────────────────────────────────────────┐
│ Presentation (BLoC/Widget)                              │
│ calls useCase, receives Either<Failure, Model>          │
└────────────────┬────────────────────────────────────────┘
                 │ calls
┌────────────────▼────────────────────────────────────────┐
│ Domain (UseCase, Repository Interface)                  │
│ NO Dio, NO HTTP knowledge, NO JSON                      │
└────────────────┬────────────────────────────────────────┘
                 │ implements
┌────────────────▼────────────────────────────────────────┐
│ Data Layer (RepositoryImpl)                              │
│ • RemoteDataSource (calls ApiClient)                    │
│ • ApiClient (Dio wrapper)                               │
│ • Interceptors (auth, retry, logging, errors)           │
│ • Models (with JSON serialization)                      │
│ • Exception → Failure mapping                           │
└─────────────────────────────────────────────────────────┘
```

**Critical rules:**
- `ApiClient` and `Dio` are **Data layer only**
- `RemoteDataSource` returns `DataModel`, never `DomainModel`
- `RepositoryImpl` maps `AppException` → `Failure` — never throws
- Domain only sees `Either<Failure, T>` — never HTTP details

---

## Interceptor Stack (Complete Flow)

### Execution Order

```
┌─────────────────── REQUEST PATH ───────────────────┐
│ BLoC calls RemoteDataSource.getProducts()          │
│ ▼                                                  │
│ AuthInterceptor                                    │
│   • Retrieves access token from TokenRepository    │
│   • Injects Authorization: Bearer <token>          │
│ ▼                                                  │
│ RetryInterceptor                                   │
│   • On timeout/connection error: retry up to 3x    │
│   • On 4xx/5xx: pass through (no retry)            │
│ ▼                                                  │
│ SafeLoggingInterceptor                             │
│   • Logs method, path, headers (redacted)          │
│   • Logs body size (never logs content)            │
│   • In release: only errors logged                 │
│ ▼                                                  │
│ ErrorInterceptor (error handling only)             │
│ ▼                                                  │
│ [Dio HTTP Layer] → [Server]                        │
└──────────────────────────────────────────────────┘

┌─────────────────── RESPONSE PATH ─────────────────┐
│ [Server Response]                                  │
│ ▼                                                  │
│ ErrorInterceptor                                   │
│   • Catches DioException                           │
│   • Converts to AppException                       │
│   • Passes successful responses through            │
│ ▼                                                  │
│ SafeLoggingInterceptor                             │
│   • Logs status, duration                          │
│   • Never logs response body                       │
│ ▼                                                  │
│ RetryInterceptor                                   │
│   • Already completed (responses don't retry)      │
│ ▼                                                  │
│ AuthInterceptor                                    │
│   • On 401: triggers token refresh (with lock)     │
│   • On other: passes through                       │
│ ▼                                                  │
│ AppException → RemoteDataSource                    │
│ ▼                                                  │
│ AppException → RepositoryImpl                       │
│ ▼                                                  │
│ Failure → UseCase → BLoC                           │
└──────────────────────────────────────────────────┘
```

| Interceptor | On Request | On Response/Error |
|---|---|---|
| **AuthInterceptor** | Inject Bearer token | Handle 401 → refresh token + retry |
| **RetryInterceptor** | No-op | Retry on transient errors only (NOT 4xx/5xx) |
| **SafeLoggingInterceptor** | Log metadata (redacted) | Log status + duration (no body) |
| **ErrorInterceptor** | No-op | Map `DioException` → `AppException` |

---

## Security: Safe Logging Without PII Exposure

### ⚠️ Never Use PrettyDioLogger in Production

PrettyDioLogger logs entire request/response bodies, exposing:
- Auth tokens → Authorization header leaks
- Passwords → visible in logcat + Crashlytics
- User emails/phone/SSN → GDPR/PCI-DSS violations
- API keys → compromised

```dart
// ❌ NEVER DO THIS IN PRODUCTION
dio.interceptors.add(PrettyDioLogger(
  requestBody: true,  // ← Logs passwords, tokens!
  responseBody: true, // ← Logs user emails, SSNs!
));
```

### ✅ Use SafeLoggingInterceptor Instead

Logs metadata only, redacts sensitive headers and fields:

```dart
// ✅ SAFE: Logs method, status, duration—never logs PII
dio.interceptors.add(SafeLoggingInterceptor());

// Console output (debug mode):
// → REQUEST: POST /auth/login
//   authorization: [REDACTED]
//   content-type: application/json
//   Body size: 47 bytes
// ← RESPONSE: 200 /auth/login
//   Duration: 342ms
//   Response size: 156 bytes
```

**Redacts:**
- Headers: `Authorization`, `X-API-Key`, `Cookie`, `X-CSRF-Token`, etc.
- JSON fields: `password`, `email`, `phone`, `ssn`, `credit_card`, `token`, etc.
- **Never logs request/response bodies** (only size)

See `references/logging_interceptor.md` for complete implementation.

---

## Common Patterns

### Pattern 1: Authenticated Request (Auto-Injected Token)

```dart
// AuthInterceptor handles this automatically
// No manual header needed
final response = await apiClient.get<Product>('/me/profile');
```

### Pattern 2: Token Refresh on 401 (Race Condition Safe)

```dart
// AuthInterceptor uses Lock (synchronized) to prevent race conditions
// If 10 requests get 401 simultaneously:
// • Only ONE refresh happens
// • Other 9 requests WAIT for that refresh
// • All retry with new token
```

### Pattern 3: Retry Transient Failures (Exponential Backoff)

```dart
// RetryInterceptor retries on:
// ✅ Connection timeout (after 10s of no response)
// ✅ Socket exception (network error)
// ✗ NOT on 4xx/5xx (server errors won't auto-recover)

// Backoff: 500ms → 1s → 2s
// Jitter: ±25% (prevents thundering herd)
```

### Pattern 4: Multipart File Upload

```dart
final file = File('/path/to/image.jpg');
final formData = FormData.fromMap({
  'file': await MultipartFile.fromFile(
    file.path,
    filename: 'image.jpg',
    contentType: MediaType('image', 'jpeg'),
  ),
  'description': 'My photo',
});
await apiClient.post('/upload', data: formData);
```

### Pattern 5: Cancel Long-Running Request

```dart
final cancelToken = CancelToken();

// Start request
unawaited(apiClient.get('/search?q=query', cancelToken: cancelToken));

// In BLoC.close() or dispose():
cancelToken.cancel();
```

---

## Troubleshooting

### ❌ 401 errors keep repeating infinitely

**Cause:** Token refresh is also getting 401 (refresh endpoint unavailable).

**Solution:**
- Validate that refresh endpoint is working: `POST /auth/refresh` with refresh_token
- In AuthInterceptor, on refresh failure, clear tokens and force logout
- Add exponential backoff to prevent hammering the refresh endpoint

```dart
// In AuthInterceptor.onError():
if (newToken == null) {
  await _tokenRepository.clearTokens();
  // Trigger app-level logout event
  return handler.next(err); // Pass the 401 to app
}
```

### ❌ Requests timeout but aren't retried

**Cause:** RetryInterceptor only retries on `DioExceptionType.connectionTimeout`, not others.

**Solution:** Verify the error type in SafeLoggingInterceptor output:
```
✗ ERROR: connectionTimeout  ← Will retry
✗ ERROR: sendTimeout       ← Won't retry (consider adding)
✗ ERROR: unknown           ← Won't retry (check actual cause)
```

Adjust RetryInterceptor thresholds or add more error types.

### ❌ Sensitive data (passwords, tokens) showing in Crashlytics logs

**Cause:** Using PrettyDioLogger or logging response bodies directly.

**Solution:**
- Replace with SafeLoggingInterceptor
- Never log `response.data.toString()` in try/catch
- Configure Sentry/Crashlytics `beforeSend` hook to redact

```dart
Sentry.init(dsn, beforeSend: (event, _) {
  if (event.request?.headers != null) {
    event.request!.headers!.remove('Authorization');
  }
  return event;
});
```

### ❌ File upload fails with "FormData not serializable"

**Cause:** Dio v5 requires `MultipartFile` for file fields, not raw `File`.

**Solution:**
```dart
// ✅ Correct
final formData = FormData.fromMap({
  'file': await MultipartFile.fromFile(file.path),
});

// ❌ Wrong
final formData = FormData.fromMap({
  'file': file, // Won't serialize
});
```

### ❌ Requests work in debug, fail in release

**Cause:** Often TLS/certificate pinning not configured, or certificate validation disabled in debug.

**Solution:**
- Use `flutter-certificate-pinning` skill for production
- Or ensure `HttpClient` respects device's system certificates
- In release, enable strict certificate validation

---

## Package Dependencies

```yaml
dependencies:
  dio: ^5.9.2              # HTTP client
  get_it: ^9.2.1           # Service locator (DI)
  injectable: ^3.0.0       # DI code generation
  fpdart: ^1.2.0           # Either<Failure, T> for Result pattern
  synchronized: ^3.1.0     # Lock for mutex-like sync (used by AuthInterceptor)

dev_dependencies:
  injectable_generator: ^3.0.2  # Generates DI module code
  build_runner: ^2.14.1         # Runs code generators
  mocktail: ^1.0.5              # Mocking for tests
```

---

## Quick Wins Checklist

- [ ] Dio registered as `@lazySingleton` (one instance per app)
- [ ] AuthInterceptor injects Bearer token on EVERY request
- [ ] 401 token refresh uses `Lock` or `Completer` (prevents race conditions)
- [ ] RetryInterceptor retries only on connection/timeout errors (NOT 4xx/5xx)
- [ ] **SafeLoggingInterceptor** used instead of PrettyDioLogger
- [ ] ErrorInterceptor maps `DioException` → `AppException` (try/catch not allowed)
- [ ] RepositoryImpl maps `AppException` → `Failure` (never throws)
- [ ] `CancelToken` used in BLoC and cancelled in `close()`
- [ ] Base URL from environment config or `--dart-define` (never hardcoded)
- [ ] Timeouts configured: `connectTimeout: 10s`, `receiveTimeout: 30s`
- [ ] Interceptor order verified: Auth → Retry → Logging → Error
- [ ] Tests mock Dio with Mocktail (not real network calls)
- [ ] No `print()` or `debugPrint()` of responses (use SafeLoggingInterceptor)

---

## Reference Files

**Start here based on your need:**

| If you're... | Read this |
|---|---|
| Setting up Dio for the first time | `dio_setup.md` |
| Implementing 401 token refresh | `interceptors.md` → AuthInterceptor section |
| Adding retry logic | `interceptors.md` → RetryInterceptor section |
| Securing logging without PII | `logging_interceptor.md` |
| Building a RemoteDataSource | `data_source.md` |
| Testing HTTP layer | `testing.md` |

---

## Related Skills

- **`flutter-environments`** — Environment-based URLs, flavors, `--dart-define`
- **`flutter-clean-architecture`** — Domain/Data/Presentation layer structure
- **`flutter-certificate-pinning`** — HTTPS security for production APIs
- **`flutter-caching-strategy`** — HTTP cache layer on top of Dio
- **`flutter-offline-first-pattern`** — Local-first sync with remote backend


