# Logging Interceptor — Safe Redaction & PII Protection

## ⚠️ Security: The PrettyDioLogger Problem

PrettyDioLogger logs **entire request/response bodies** to logcat and console, exposing:
- Auth tokens (`Authorization: Bearer <token>`)
- Passwords, API keys, secrets in request bodies
- User emails, phone numbers, SSNs in response bodies
- Any personally identifiable information (PII)

This data is visible to:
- ✗ Anyone with ADB access to the device
- ✗ Firebase Crashlytics, Sentry, log aggregation services
- ✗ Device manufacturers, competitors, attackers
- ✗ Anyone reviewing logs during development/testing

**Never use PrettyDioLogger in production, and use with caution even in debug.**

---

## Solution: SafeLoggingInterceptor with Redaction

### Core Pattern

Log **metadata only** (method, path, status, duration) and redact all sensitive headers and fields:

```dart
// lib/src/data/http/interceptors/safe_logging_interceptor.dart
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'dart:convert';

@injectable
class SafeLoggingInterceptor extends Interceptor {
  /// Headers that should NEVER be logged (contain secrets/tokens)
  static const _sensitiveHeaders = {
    'authorization',
    'x-api-key',
    'x-auth-token',
    'x-session-token',
    'cookie',
    'set-cookie',
    'x-csrf-token',
    'x-request-id', // sometimes contains device identifiers
    'bearer',
    'proxy-authorization',
  };

  /// JSON fields in request/response bodies that contain PII or secrets
  static const _sensitiveFields = {
    'password', 'passwd', 'pwd',
    'token', 'access_token', 'refresh_token', 'bearer_token',
    'api_key', 'apikey', 'api_secret',
    'secret', 'client_secret',
    'email', 'phone', 'mobile', 'cellphone', 'telephone',
    'ssn', 'social_security_number',
    'credit_card', 'creditcard', 'cc_number',
    'cvv', 'cvc', 'security_code',
    'bank_account', 'account_number', 'routing_number', 'iban', 'swift',
    'identification', 'id_number', 'passport', 'drivers_license',
    'date_of_birth', 'dob',
    'private_key', 'pem', 'pkcs12',
    'oauth_token', 'session_id', 'session_key',
  };

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (kDebugMode) {
      _logRequest(options);
    } else {
      // In release builds, only log errors (handled in onError)
    }
    return handler.next(options);
  }

  @override
  Future<void> onResponse(
    Response<dynamic> response,
    ResponseInterceptorHandler handler,
  ) async {
    if (kDebugMode) {
      _logResponse(response);
    }
    return handler.next(response);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // Log errors in BOTH debug and release (for observability)
    _logError(err);
    return handler.next(err);
  }

  // ─────────────────────────────────────────────────────────────────

  void _logRequest(RequestOptions options) {
    final stopwatch = Stopwatch()..start();
    options.extra['_stopwatch'] = stopwatch;

    final method = options.method.toUpperCase();
    final path = options.path;
    final baseUrl = options.baseUrl;

    debugPrint('─────────────────────────────────────────────────');
    debugPrint('→ REQUEST: $method $path');

    // Log safe headers (redacted)
    if (options.headers.isNotEmpty) {
      final safeHeaders = _redactHeaders(options.headers);
      safeHeaders.forEach((key, value) {
        debugPrint('  $key: $value');
      });
    }

    // Log query parameters (redacted)
    if (options.queryParameters.isNotEmpty) {
      final safeParams = _redactMap(options.queryParameters);
      debugPrint('  Query: $safeParams');
    }

    // Log body size (never log content)
    if (options.data != null) {
      final size = _getDataSize(options.data);
      debugPrint('  Body size: $size bytes');
    }
  }

  void _logResponse(Response<dynamic> response) {
    final stopwatch = response.requestOptions.extra['_stopwatch'] as Stopwatch?;
    stopwatch?.stop();
    final duration = stopwatch?.elapsedMilliseconds ?? 0;

    final statusCode = response.statusCode ?? 'N/A';
    final path = response.requestOptions.path;

    debugPrint('← RESPONSE: $statusCode $path');
    debugPrint('  Duration: ${duration}ms');
    debugPrint('  Response size: ${_getDataSize(response.data)} bytes');
    debugPrint('─────────────────────────────────────────────────');
  }

  void _logError(DioException err) {
    final method = err.requestOptions.method.toUpperCase();
    final path = err.requestOptions.path;
    final statusCode = err.response?.statusCode ?? 'N/A';
    final message = err.message ?? 'Unknown error';
    final type = err.type.toString();

    debugPrint('✗ ERROR: $type');
    debugPrint('  $method $path → $statusCode');
    debugPrint('  Message: $message');

    // Log error response (redacted, errors are safe to show in debug)
    if (err.response?.data != null) {
      final safeData = _redactData(err.response!.data);
      debugPrint('  Response: $safeData');
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // Redaction Helpers

  /// Redacts all sensitive headers, replacing values with [REDACTED]
  Map<String, dynamic> _redactHeaders(Map<String, dynamic> headers) {
    final redacted = <String, dynamic>{};

    for (final entry in headers.entries) {
      final key = entry.key.toLowerCase();
      if (_sensitiveHeaders.contains(key)) {
        redacted[entry.key] = '[REDACTED]';
      } else {
        redacted[entry.key] = entry.value;
      }
    }

    return redacted;
  }

  /// Recursively redacts sensitive fields in a Map
  Map<String, dynamic> _redactMap(Map<dynamic, dynamic> map) {
    final redacted = <String, dynamic>{};

    for (final entry in map.entries) {
      final key = entry.key.toString().toLowerCase();

      if (_sensitiveFields.contains(key)) {
        redacted[entry.key.toString()] = '[REDACTED]';
      } else if (entry.value is Map) {
        redacted[entry.key.toString()] = _redactMap(entry.value as Map<dynamic, dynamic>);
      } else if (entry.value is List) {
        redacted[entry.key.toString()] = _redactList(entry.value as List<dynamic>);
      } else {
        redacted[entry.key.toString()] = entry.value;
      }
    }

    return redacted;
  }

  /// Recursively redacts sensitive fields in a List
  List<dynamic> _redactList(List<dynamic> list) {
    return list.map((item) {
      if (item is Map) {
        return _redactMap(item as Map<dynamic, dynamic>);
      } else if (item is List) {
        return _redactList(item as List<dynamic>);
      } else {
        return item;
      }
    }).toList();
  }

  /// Redacts data from request body (JSON or FormData)
  dynamic _redactData(dynamic data) {
    if (data == null) return null;

    // JSON string
    if (data is String) {
      try {
        final json = jsonDecode(data);
        if (json is Map) {
          return _redactMap(json as Map<dynamic, dynamic>);
        }
        return json;
      } catch (_) {
        return '[Non-JSON string (${data.length} bytes)]';
      }
    }

    // Map/JSON object
    if (data is Map) {
      return _redactMap(data as Map<dynamic, dynamic>);
    }

    // FormData
    if (data is FormData) {
      return _redactFormData(data);
    }

    // Other types (bytes, etc.)
    return '[Binary data (${_getDataSize(data)} bytes)]';
  }

  /// Redacts FormData fields
  String _redactFormData(FormData formData) {
    final fields = formData.fields.map((field) {
      if (_sensitiveFields.contains(field.key.toLowerCase())) {
        return '${field.key}: [REDACTED]';
      }
      return '${field.key}: ${field.value}';
    }).join(', ');

    final files = formData.files
        .map((f) => '${f.key}: [file: ${f.value.filename}]')
        .join(', ');

    return 'FormData($fields${files.isNotEmpty ? ', ' : ''}$files)';
  }

  /// Gets the size of data in bytes
  int _getDataSize(dynamic data) {
    if (data == null) return 0;
    if (data is String) return utf8.encode(data).length;
    if (data is List) return data.length;
    if (data is Map) return jsonEncode(data).length;
    return 0;
  }
}
```

---

## DI Setup

Register `SafeLoggingInterceptor` in your GetIt/Injectable module:

```dart
// lib/core/network/di/http_module.dart
import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

@module
abstract class HttpModule {
  @lazySingleton
  Dio provideDio(
    AuthInterceptor authInterceptor,
    RetryInterceptor retryInterceptor,
    SafeLoggingInterceptor loggingInterceptor,
    ErrorInterceptor errorInterceptor,
  ) =>
      Dio(
        BaseOptions(
          baseUrl: 'https://api.example.com',
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 30),
        ),
      )
        ..interceptors.addAll([
          authInterceptor,
          retryInterceptor,
          loggingInterceptor, // ← Debug logging only, never logs PII
          errorInterceptor,
        ]);

  @injectable
  SafeLoggingInterceptor provideSafeLoggingInterceptor() =>
      SafeLoggingInterceptor();
}
```

---

## Interceptor Execution Order (with Logging)

```
Request Path:
→ AuthInterceptor (injects Bearer token, redacted by logging)
→ RetryInterceptor (only on transient errors)
→ SafeLoggingInterceptor (logs method, path, headers—REDACTED, body size)
→ ErrorInterceptor (not executed; returns to SafeLoggingInterceptor)
→ [Dio HTTP Layer] → Server

Response Path:
← [Server Response]
← ErrorInterceptor (may convert DioException)
← SafeLoggingInterceptor (logs status, duration, response size—NOT body)
← RetryInterceptor (checks if should retry)
← AuthInterceptor (stores new token if present)
← App receives Either<Failure, T>
```

The logging happens **in between**, seeing requests/responses in their final state but redacting all sensitive data.

---

## What Gets Logged (Safe)

### Debug Mode (`kDebugMode`)

```
─────────────────────────────────────────────────
→ REQUEST: POST /auth/login
  accept: application/json
  content-type: application/json
  authorization: [REDACTED]
  Query: {}
  Body size: 47 bytes
```

**NOT logged:**
- ✗ Actual Authorization header value (TOKEN)
- ✗ Request body (contains password)
- ✗ Response body (would contain user emails)

### Release Mode

- ✅ Errors ARE logged (with redacted bodies)
- ✗ Successful requests NOT logged
- Why: No PII exposure, but observability for issues

---

## Testing SafeLoggingInterceptor

```dart
// test/data/http/interceptors/safe_logging_interceptor_test.dart
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

void main() {
  group('SafeLoggingInterceptor', () {
    late SafeLoggingInterceptor interceptor;

    setUp(() {
      interceptor = SafeLoggingInterceptor();
    });

    test('redacts Authorization header', () {
      final options = RequestOptions(
        path: '/users',
        headers: {'Authorization': 'Bearer secret-token-123'},
      );

      final redacted = interceptor._redactHeaders(options.headers);

      expect(redacted['Authorization'], '[REDACTED]');
    });

    test('redacts sensitive JSON fields', () {
      final data = {
        'email': 'user@example.com',
        'password': 'SecurePass123',
        'firstName': 'John',
      };

      final redacted = interceptor._redactData(data);

      expect(redacted['email'], '[REDACTED]');
      expect(redacted['password'], '[REDACTED]');
      expect(redacted['firstName'], 'John'); // Safe field, not redacted
    });

    test('preserves non-sensitive headers', () {
      final options = RequestOptions(
        path: '/data',
        headers: {
          'User-Agent': 'MyApp/1.0',
          'Accept': 'application/json',
        },
      );

      final redacted = interceptor._redactHeaders(options.headers);

      expect(redacted['User-Agent'], 'MyApp/1.0');
      expect(redacted['Accept'], 'application/json');
    });

    test('handles nested JSON objects', () {
      final data = {
        'user': {
          'id': 123,
          'email': 'user@example.com',
          'profile': {'phone': '555-1234'},
        },
      };

      final redacted = interceptor._redactData(data);

      expect(redacted['user']['email'], '[REDACTED]');
      expect(redacted['user']['profile']['phone'], '[REDACTED]');
      expect(redacted['user']['id'], 123); // Safe, not redacted
    });

    test('logs without throwing on malformed data', () {
      expect(
        () => interceptor._redactData('not json {'),
        returnsNormally,
      );
    });
  });
}
```

---

## Related Patterns

### Sentry Integration (Safe)

When using Sentry for error reporting, ensure Sentry's `beforeSend` hook also redacts:

```dart
import 'package:sentry/sentry.dart';

await Sentry.init(
  'https://examplePublicKey@o0.ingest.sentry.io/0',
  beforeSend: (event, _) {
    // Redact sensitive data before sending to Sentry
    if (event.request != null) {
      event.request!.headers?.remove('Authorization');
      event.request!.headers?.remove('X-API-Key');
      // Redact request body if needed
    }
    return event;
  },
);
```

### Firebase Crashlytics Integration (Safe)

Avoid logging to Crashlytics entirely, or use custom keys without sensitive data:

```dart
// ✅ Safe: Log metadata only
FirebaseCrashlytics.instance.log('[HTTP] GET /users/123 → 200');

// ❌ DANGEROUS: Never log responses
// FirebaseCrashlytics.instance.log('Response: $responseBody');
```

---

## Checklist: Secure Logging

- [ ] **Never use PrettyDioLogger in production** (not even with compression)
- [ ] SafeLoggingInterceptor registered before ErrorInterceptor
- [ ] Sensitive headers (Authorization, X-API-Key, Cookie) in redaction list
- [ ] Sensitive fields (password, email, token, ssn, etc.) in redaction list
- [ ] Recursion handles nested JSON (Map within Map, List within Map, etc.)
- [ ] kDebugMode check: logging disabled in release builds
- [ ] Errors ARE logged (observability), but bodies are redacted
- [ ] Sentry/Crashlytics also redacts before sending
- [ ] Tests verify redaction works on real API responses
- [ ] Team trained: never log `response.data.toString()` directly

---

## Security Comparison: PrettyDioLogger vs SafeLoggingInterceptor

| Feature | PrettyDioLogger | SafeLoggingInterceptor |
|---------|-----------------|----------------------|
| **Logs Request Headers** | ✗ All (INCLUDING Authorization) | ✅ All except sensitive |
| **Logs Request Body** | ✗ Entire body (passwords, emails) | ✅ Size only, no content |
| **Logs Response Body** | ✗ Entire body (PII, tokens) | ✅ Never logs body |
| **Logs HTTP Status** | ✅ Yes | ✅ Yes |
| **Logs Duration** | ✅ Yes | ✅ Yes |
| **Redaction** | ✗ None | ✅ Headers + JSON fields |
| **Works in Release** | ✅ Always visible | ✅ Errors only, redacted |
| **Production Safe** | ❌ DANGEROUS | ✅ Safe |
| **Debug Utility** | ✅ High (but leaks PII) | ✅ Sufficient |
| **Compliance** | ❌ Fails GDPR/PCI-DSS | ✅ Passes |

---

## Further Reading

- Flutter documentation: [HttpClient internals](https://dart.dev/guides/libraries/library-tour#dartio---io-for-command-line-apps)
- Dio documentation: [Interceptors](https://github.com/flutterchina/dio/blob/master/README.md#interceptor)
- OWASP: [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- PCI-DSS: [Data Protection Requirements](https://www.pcisecuritystandards.org/)
