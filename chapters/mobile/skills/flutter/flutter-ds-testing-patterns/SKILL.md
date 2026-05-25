---
id: flutter-ds-testing-patterns
version: 1.1.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
description: Widget testing patterns for Flutter Design System components.   Use when writing widget tests, setting up test helpers,
---

# Testing Patterns

> **Scope**: Este skill cubre patrones de testing **específicos para componentes del Design System** (pumpApp, estados, variantes, golden, widgetbook). Para fundamentos generales de testing Flutter (unit, widget, integration, mocking, AAA) → ver skill `flutter-testing`.

## Mount Helper

The project must have a `pumpApp` helper (per `project.config.yaml`):

```dart
// test/helpers/pump_app.dart
extension PumpApp on WidgetTester {
  Future<void> pumpApp(Widget widget) async {
    await pumpWidget(
      MaterialApp(
        theme: ThemeData(extensions: [/* light theme extension */]),
        home: Scaffold(body: widget),
      ),
    );
  }
}
```

## Required Test Sections

Every widget test must include these groups:

1. **Basic rendering** — minimum params + all params
2. **States** — one test per state enum value
3. **Variants** — one test per variant enum value
4. **Interactions** — callback invoked, null-safe, disabled guard
5. **Defaults** — verify default values
6. **Accessibility** — semantics

See [test template](assets/widget_test_template.dart.txt) for complete starter code.

## Conventions

- **AAA pattern**: Arrange-Act-Assert in ALL tests (Pragma mandatory)
- **Names**: `should [verb] when [condition]`
- **Independence**: each test stands alone
- **Helper**: always use `pumpApp` to mount widgets
- **Find**: `find.byType()` for render verification
- **Disabled**: verify `Opacity(0.5)` + `IgnorePointer` + callback not invoked
- **Loading**: verify absence of real content
- **Null-safe**: test callbacks with `null` (must not crash)
- **Coverage**: all states × variants × interactions

## Key Patterns

### Disabled State
```dart
testWidgets('should not invoke callback when disabled', (tester) async {
  var pressed = false;
  await tester.pumpApp(Widget(state: .disabled, onPressed: () => pressed = true));
  await tester.tap(find.byType(Widget));
  expect(pressed, isFalse);
});
```

### Null Callback
```dart
testWidgets('should not crash when callback is null', (tester) async {
  await tester.pumpApp(const Widget(label: 'Test'));
  await tester.tap(find.byType(Widget));
  // No exception = pass
});
```

### Variant Loop
```dart
for (final variant in WidgetVariant.values) {
  testWidgets('should render ${variant.name}', (tester) async {
    await tester.pumpApp(Widget(variant: variant));
    expect(find.byType(Widget), findsOneWidget);
  });
}
```
