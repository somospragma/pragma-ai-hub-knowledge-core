---
id: flutter-ds-testing-patterns
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-testing-patterns
description: >
  Widget testing patterns for Flutter Design System components.
  Use when writing widget tests, setting up test helpers, or verifying
  component behavior across states, variants, interactions, and accessibility.
---

# Testing Patterns

> **Scope**: Este skill cubre patrones de testing **específicos para componentes del Design System** (pumpApp, estados, variantes, golden, widgetbook). Para fundamentos generales de testing Flutter (unit, widget, integration, mocking, AAA) → ver skill `flutter-testing`.

## Mount Helper — Always Use `pumpApp`

Every DS widget test mounts the widget through `pumpApp`, never through raw `pumpWidget`. This ensures the DS theme extension is always injected — tests that bypass it will get missing-token errors in real DS code.

```dart
// test/helpers/pump_app.dart
extension PumpApp on WidgetTester {
  Future<void> pumpApp(Widget widget) async {
    await pumpWidget(
      MaterialApp(
        theme: ThemeData(extensions: [/* DS light theme extension */]),
        home: Scaffold(body: widget),
      ),
    );
  }
}
```

> Using bare `pumpWidget(MaterialApp(...))` in tests is not the DS pattern — it duplicates boilerplate and skips theme setup. Always use `pumpApp`.

## Required Test Sections (exactly 6)

Every DS widget test file must include these six groups in this order:

1. **Basic rendering** — minimum params + all params
2. **States** — one test per state enum value
3. **Variants** — one test per variant enum value (use the [loop pattern](#variant-loop))
4. **Interactions** — callback invoked, null-safe, disabled guard
5. **Defaults** — verify default parameter values
6. **Accessibility** — semantics

See [test template](assets/widget_test_template.dart.txt) for complete starter code.

## Conventions

- **AAA pattern**: Arrange-Act-Assert in ALL tests (Pragma mandatory)
- **Names**: `should [verb] when [condition]` — e.g., `'should not crash when onPressed is null'`
- **Independence**: each test stands alone — no shared mutable state
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
  await tester.pumpApp(
    DSWidget(state: DSWidgetState.disabled, onPressed: () => pressed = true),
  );
  await tester.tap(find.byType(DSWidget));
  expect(pressed, isFalse);
});
```

### Null Callback
```dart
testWidgets('should not crash when onPressed is null', (tester) async {
  await tester.pumpApp(const DSWidget(label: 'Test'));
  await tester.tap(find.byType(DSWidget));
  // No exception thrown = test passes
});
```

### Variant Loop
```dart
for (final variant in DSWidgetVariant.values) {
  testWidgets('should render ${variant.name} variant', (tester) async {
    await tester.pumpApp(DSWidget(variant: variant));
    expect(find.byType(DSWidget), findsOneWidget);
  });
}
```

The loop pattern is critical: it ensures every enum value is tested and new variants are automatically covered when the enum grows — no extra tests to write.
