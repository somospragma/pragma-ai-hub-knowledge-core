# Knobs Reference — Widgetbook 3.x

Knob selection guide by parameter type.

---

## Quick selection rule

| Parameter type | Knob to use |
|---|---|
| Required `String` | `context.knobs.string` |
| Optional `String?` | `context.knobs.stringOrNull` |
| Required `bool` | `context.knobs.boolean` |
| Optional `bool?` | `context.knobs.booleanOrNull` |
| Bounded `int` (progress, size) | `context.knobs.int.slider` |
| Free `int` | `context.knobs.int.input` |
| `double` between 0.0 and 1.0 (opacity) | `context.knobs.double.slider` |
| Free `double` | `context.knobs.double.input` |
| `Color` | `context.knobs.color` |
| `Color?` | `context.knobs.colorOrNull` |
| `enum` / option list | `context.knobs.list` |
| `DateTime` | `context.knobs.dateTime` |
| `Duration` | `context.knobs.duration` |
| `IconData` | `context.knobs.list` with `Icons.*` |
| Asset image (`String` PNG/JPEG path) | Hardcode the path + assets declared in pubspec |
| SVG (`String` path) | Hardcode the path + assets declared in pubspec |
| `ImageProvider` | `NetworkImage` (catalog) or `AssetImage` (if assets declared) |
| Complex object | Hardcode + `// TODO` |
| Callback | Descriptive `developer.log()` |

---

## Complete API

### String
```dart
context.knobs.string(label: 'text', initialValue: 'Hello World')
context.knobs.stringOrNull(label: 'subtitle', initialValue: null)
```

### Boolean
```dart
context.knobs.boolean(label: 'enabled', initialValue: true)
context.knobs.booleanOrNull(label: 'showBadge', initialValue: null)
```

### Integer
```dart
// Bounded value with slider
context.knobs.int.slider(
  label: 'progress',
  initialValue: 50,
  min: 0,
  max: 100,
  divisions: 10,
)

// Free value with input
context.knobs.int.input(label: 'itemCount', initialValue: 5)

// Optional
context.knobs.intOrNull.input(label: 'maxLines', initialValue: null)
context.knobs.intOrNull.slider(
  label: 'steps',
  initialValue: null,
  min: 0,
  max: 10,
  divisions: 10,
)
```

### Double
```dart
// Slider for values between 0.0 and 1.0
context.knobs.double.slider(
  label: 'opacity',
  initialValue: 1.0,
  min: 0.0,
  max: 1.0,
  divisions: 20,
)

// Input for free values
context.knobs.double.input(label: 'elevation', initialValue: 4.0)

// Optional
context.knobs.doubleOrNull.input(label: 'borderWidth', initialValue: null)
context.knobs.doubleOrNull.slider(
  label: 'scale',
  initialValue: null,
  min: 0.5,
  max: 2.0,
  divisions: 15,
)
```

### Color
```dart
context.knobs.color(label: 'backgroundColor', initialValue: Colors.blue)
context.knobs.colorOrNull(label: 'borderColor', initialValue: null)
```

### List / Enum
```dart
context.knobs.list<TextAlign>(
  label: 'textAlign',
  initialOption: TextAlign.center,
  options: TextAlign.values,
  labelBuilder: (value) => value.name,
)

// Partial enum (not all values)
context.knobs.list<ButtonSize>(
  label: 'size',
  initialOption: ButtonSize.medium,
  options: [ButtonSize.small, ButtonSize.medium, ButtonSize.large],
  labelBuilder: (value) => value.name,
)
```

### DateTime
```dart
context.knobs.dateTime(
  label: 'selectedDate',
  initialValue: DateTime.now(),
  start: DateTime.now().subtract(const Duration(days: 365)),
  end: DateTime.now().add(const Duration(days: 365)),
)
```

### Duration
```dart
context.knobs.duration(
  label: 'animationDuration',
  initialValue: const Duration(milliseconds: 300),
)
```

---

## Icons and images

> **Prerequisite:** For any asset (PNG, JPEG, SVG) to load correctly
> in Widgetbook, the paths must be declared in `widgetbook_[appname]/pubspec.yaml`.
> See `references/setup.md` § Assets — project images and icons.

### IconData — select an icon with a knob

`IconData` has no native knob: use `context.knobs.list` with a curated set
of icons relevant to the component. Never try to expose every `Icons.*`.

```dart
// Select among icons relevant to the use case
final icon = context.knobs.list<IconData>(
  label: 'icon',
  initialOption: Icons.star,
  options: [
    Icons.star,
    Icons.favorite,
    Icons.bookmark,
    Icons.check_circle,
    Icons.info,
    Icons.warning,
  ],
  labelBuilder: (icon) {
    const names = {
      Icons.star: 'star',
      Icons.favorite: 'favorite',
      Icons.bookmark: 'bookmark',
      Icons.check_circle: 'check_circle',
      Icons.info: 'info',
      Icons.warning: 'warning',
    };
    return names[icon] ?? 'icon';
  },
);
```

> **Select domain icons:** Choose the icons the widget will actually use
> in production — not a generic list. If the widget always shows the same icon,
> hardcode it directly (`icon: Icons.arrow_forward`) without a knob.

### Icon widget — hardcode without a knob

If the parameter is a `Widget` and the widget always receives a specific icon:

```dart
// Parameter: Widget? leadingIcon
leadingIcon: const Icon(Icons.notifications, size: 24),

// Parameter: Widget? trailingIcon  
trailingIcon: const Icon(Icons.chevron_right, size: 20),
```

### PNG / JPEG asset — use a path with declared assets

When the parameter is a `String` with the asset path:

```dart
// Hardcode a real project path
// The asset MUST be declared in widgetbook_[appname]/pubspec.yaml
imagePath: 'assets/images/product_placeholder.png',

// If the component accepts the Widget directly:
image: Image.asset(
  'assets/images/product_placeholder.png',
  fit: BoxFit.cover,
),
```

### SVG asset — use a path with declared assets

If the project uses `flutter_svg`:

```dart
// Hardcode the path of a real project SVG
// The asset MUST be declared in widgetbook_[appname]/pubspec.yaml
iconPath: 'assets/icons/ic_home.svg',

// If the component receives the Widget directly:
icon: SvgPicture.asset(
  'assets/icons/ic_home.svg',
  width: 24,
  height: 24,
),

// With a knob to switch between several project SVGs
final iconPath = context.knobs.list<String>(
  label: 'icon',
  initialOption: 'assets/icons/ic_home.svg',
  options: [
    'assets/icons/ic_home.svg',
    'assets/icons/ic_profile.svg',
    'assets/icons/ic_settings.svg',
  ],
  labelBuilder: (path) => path.split('/').last.replaceAll('.svg', ''),
);
// Uso:
SvgPicture.asset(iconPath, width: 24, height: 24)
```

### ImageProvider — prefer NetworkImage in the catalog

When the parameter is an `ImageProvider` or a `String` network URL, use `NetworkImage`
for the catalog: it does not require declaring assets and always shows a real image.

```dart
// NetworkImage — does not require configuring assets
avatarImage: const NetworkImage('https://picsum.photos/200'),

// With a knob to switch between network image variants
final imageUrl = context.knobs.list<String>(
  label: 'image',
  initialOption: 'https://picsum.photos/400/300?random=1',
  options: [
    'https://picsum.photos/400/300?random=1',
    'https://picsum.photos/400/300?random=2',
    'https://picsum.photos/400/300?random=3',
  ],
  labelBuilder: (url) => 'Image ${url.split('random=').last}',
);
// Usage:
Image.network(imageUrl, fit: BoxFit.cover)
```

### Decision rule — asset or network?

| Situation | Strategy |
|---|---|
| The component loads images from a URL (avatar, product) | `NetworkImage` or `Image.network` |
| The component uses project assets (icons, illustrations) | Asset path + declare in pubspec |
| The SVG is a design system icon | Asset path + declare in pubspec |
| You want to switch between multiple images with a knob | `context.knobs.list<String>` with paths or URLs |
| The parameter is optional (`ImageProvider?`) | `null` if it is not relevant to the variant |

### Complex object — hardcode with a TODO
```dart
// When the type is not mappable to a simple knob
final config = CardConfiguration(
  borderRadius: 12.0,
  elevation: 4.0,
  padding: const EdgeInsets.all(16),
); // TODO: configure CardConfiguration manually as needed
```

### Callbacks — always with a descriptive developer.log
```dart
// Simple
onPressed: () => developer.log('Button pressed'),

// With data
onChanged: (value) => developer.log('Value changed: $value'),

// With an object
onItemSelected: (item) => developer.log('Item selected: ${item.id} - ${item.name}'),

// Async
onSave: () async {
  developer.log('Save started');
  await Future.delayed(const Duration(seconds: 1));
  developer.log('Save completed');
},
```

### State management — mock provider with domain data

The mock's visible text must come literally from Figma when it exists.
If Figma does not define a value, use data from the project's real domain and
mark it as an example; never make up interface copy or use
generic values such as "test", "lorem ipsum", or placeholder data.

```dart
// ✅ Mock contextualized to the domain (e-commerce)
@UseCase(name: 'with_data', type: OrderSummaryWidget)
Widget buildOrderSummaryWidgetWithDataUseCase(BuildContext context) {
  return MockOrderProvider(
    order: Order(
      id: 'ORD-2024-1587',
      customerName: 'Maria Garcia Lopez',
      items: [
        OrderItem(name: 'Running Pro T-Shirt', quantity: 2, price: 49.99),
        OrderItem(name: 'Trail X3 Sneakers', quantity: 1, price: 129.90),
      ],
      total: 229.88,
      status: OrderStatus.pending,
    ), // TODO: adjust the fields to the project's real model
    child: OrderSummaryWidget(
      onConfirm: () => developer.log('Order ORD-2024-1587 confirmed'),
    ),
  );
}

// ❌ Generic mock — do not do this
return MockOrderProvider(
  order: Order.mock(), // empty or placeholder data
  child: OrderSummaryWidget(onConfirm: () => developer.log('confirmed')),
);
```
