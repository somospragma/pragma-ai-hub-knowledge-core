# Knob Reference

Use knobs only for values that the target user naturally changes while inspecting a component or screen.

## Quick Selection

| Parameter type | Preferred knob |
|---|---|
| `bool` | `context.knobs.boolean` |
| enum/list option | `context.knobs.list<T>` with `labelBuilder` |
| short `String` | `context.knobs.string` |
| bounded `int`/`double` | slider knob |
| color token | token list knob, not a raw color picker |
| `ImageProvider` | `NetworkImage` for catalog data, `AssetImage` only when assets are declared |

## Icons And Images

Use a small curated list of domain-relevant icons. Do not expose all `Icons.*`.

If the widget always receives the same icon widget, hardcode that icon in the use case instead of adding a knob.

For asset paths, use project constants or declared paths. Widgetbook is a separate Flutter project, so assets must also be declared in the Widgetbook `pubspec.yaml`.

## Domain Data

If Figma does not define a value, use realistic domain data from the project. Avoid generic placeholders such as `test`, `value`, `lorem ipsum`, or empty mock objects.

Good examples:

```dart
context.knobs.string(label: 'customerName', initialValue: 'Maria Garcia Lopez');
context.knobs.string(label: 'productName', initialValue: 'Premium Trail Shoes');
```

Bad examples:

```dart
context.knobs.string(label: 'title', initialValue: 'Test');
order: Order.mock();
```
