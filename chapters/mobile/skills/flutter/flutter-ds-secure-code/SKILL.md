---
id: flutter-ds-secure-code
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-secure-code
description: >
  Security rules for Design System code based on OWASP Mobile Application
  Security and Pragma standards. Use when auditing code security, validating
  inputs, reviewing dependencies, or checking for data exposure risks.
---
# Secure Code

> **Scope**: This skill covers Design System-specific security rules (input validation in widgets, data exposure in UI, DS dependencies). For a full OWASP audit (M1-M10), secure storage, and encryption, see `flutter-owasp-mobile-top10`, `flutter-secure-storage`, and `flutter-data-encryption`.

## Pragma Security Principles

1. Validate and sanitize all user input and external data
2. Protect credentials and sensitive data
3. Use secure encryption for data at rest and in transit
4. Secure communication (HTTPS/TLS)
5. Keep dependencies updated
6. Handle errors without exposing internal information

## Authorized Dependencies

DS components are UI-only. They must not import infrastructure, networking, or persistence packages. The allowed dependency list is strict:

| Type | Allowed packages |
|------|-----------------|
| **Production** | `flutter` / `material.dart`, own DS package (e.g., `pragma_ds`) |
| **Dev only** | `alchemist`, `widgetbook`, `flutter_test` |
| **Forbidden** | `http`, `dio`, `shared_preferences`, `flutter_secure_storage`, `firebase_*`, any API/network/storage package |

Adding any forbidden package to a DS widget is a **BLOCKER** — it violates both the Single Responsibility Principle and the DS security boundary. HTTP calls, data persistence, and encryption belong in the feature/data layer, not in DS widgets.

```dart
// ✅ CORRECT — DS widget stays pure UI
import 'package:flutter/material.dart';
import 'package:pragma_ds/pragma_ds.dart';

// ❌ FORBIDDEN in DS production code
import 'package:http/http.dart';              // DS doesn't make requests
import 'package:shared_preferences/...';      // DS doesn't persist data
```

## DS-Specific Rules

### Input Validation

```dart
// ✅ CORRECT — Validate before rendering
class {{DS_PREFIX}}TextField extends StatelessWidget {
  final String? Function(String?)? validator;
  final int? maxLength;

  Widget build(BuildContext context) {
    return TextFormField(
      validator: validator,
      maxLength: maxLength,
      inputFormatters: [
        if (maxLength != null) LengthLimitingTextInputFormatter(maxLength),
      ],
    );
  }
}
```

### No Sensitive Data Exposure

```dart
// ✅ Obfuscate sensitive data
String get _displayText => isMasked ? '•' * text.length : text;

// ❌ NEVER log user data
print('User input: $sensitiveData');
```

### Safe Error Handling

```dart
// ✅ Safe visual fallback
try { return _buildContent(context); }
catch (e) { return _buildError(context); }

// ❌ NEVER expose stack traces
Text(error.toString())
```

### Null Safety

```dart
// ✅ Safe call
onPressed?.call();

// ❌ NEVER force unwrap unnecessarily
onPressed!();
```

## Checklist

- [ ] No `print()` in production code
- [ ] No sensitive data in logs or error messages
- [ ] No unauthorized dependencies (only flutter, own DS package; dev: alchemist, widgetbook, flutter_test)
- [ ] Text inputs with `maxLength` and/or `inputFormatters`
- [ ] Nullable callbacks with safe call (`?.call()`)
- [ ] No unnecessary force unwrap (`!`)
- [ ] Error handling with visual fallback
- [ ] No hardcoded URLs, API keys, or credentials

## OWASP Mobile Top 10 (Applicable)

| ID | Threat | DS Mitigation |
|----|--------|--------------|
| M7 | Code Quality | SOLID, strict linting, no dead code |
| M8 | Code Tampering | Obfuscation in release builds |
| M9 | Reverse Engineering | No sensitive business logic in widgets |
