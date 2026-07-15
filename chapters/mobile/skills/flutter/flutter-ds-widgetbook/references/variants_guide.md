# Variants — How Many and Which to Generate

---

## General rule

### UI System (components)

| Widget complexity | Minimum variants |
|---|---|
| Simple atom (button, badge, icon) | 2-4 |
| Molecule (card, list tile) | 2-3 |
| Organism (form, list) | 2-3 |
| Widget with many states | One per relevant state |

### Features (screens)

| Screen type | Minimum variants |
|---|---|
| List (home, catalog, history) | 3-4: default, loading, empty, error |
| Detail (product, profile, order) | 2-3: default, loading, error |
| Form (login, signup, checkout) | 2-3: default, validation_error, prefilled |
| Dashboard / summary | 2-3: default, loading, empty |

For the complete guide to screen variants, see `references/features_guide.md`.

More variants is not always better — each one must demonstrate something
that the others do not show.

---

## States you must always cover (if the widget has them)

> **Implementation rule:** if the state is controlled by a constructor parameter (`isLoading`, `isEnabled`, `isEmpty`...) → **knob**. Only create a separate `@UseCase` if the widget renders a different visual structure that cannot be controlled with a parameter.

| State | `name` if it is a `@UseCase` | Equivalent knob | Preferred implementation |
|---|---|---|---|
| Functional base state | `'default'` | — | Always a `@UseCase` |
| Loading data | `'loading'` | `context.knobs.boolean(label: 'Loading')` | **Knob** if there is an `isLoading` prop |
| Disabled | `'disabled'` | `context.knobs.boolean(label: 'Enabled')` | **Knob** if there is an `isEnabled` / `enabled` prop |
| No data / empty | `'empty'` | `context.knobs.boolean(label: 'Empty')` | **Knob** if the widget accepts an empty or nullable list |
| Error | `'error'` | `context.knobs.boolean(label: 'Error')` | **Knob** if there is a `hasError` / `errorMessage` prop |
| With maximum content | `'full'` | `context.knobs.int.slider(label: 'itemCount')` | **Knob** with a high value in the slider |
| Read only | `'read_only'` | `context.knobs.boolean(label: 'ReadOnly')` | **Knob** if there is a `readOnly` prop |

---

## Strategy by component type

### Buttons

> **Rule:** A single `@UseCase(name: 'default')` with knobs for all states and visual variants. Only create additional `@UseCase`s if the widget renders radically different structures (see the Golden rule below).

```dart
// default — one use case, with knobs:
//   - label/text (string)
//   - variant (list<ButtonVariant>)  ← primary, secondary, ghost, destructive…
//   - size (list<ButtonSize>)        ← small, normal, large…
//   - icon (list<IconData>)
//   - iconPosition (list<IconPosition>) ← start, end
//   - showIcon (boolean)
//   - isLoading (boolean)            ← do NOT create a separate 'loading' @UseCase
//   - isEnabled (boolean)            ← do NOT create a separate 'disabled' @UseCase
```

### Text fields / inputs
```dart
// default   — empty interactive field
// with_value — field with content
// error      — showing an error message
// disabled   — not editable
```

### Cards / List tiles
```dart
// default    — with complete data
// minimal    — with only the required fields
// loading    — skeleton or shimmer (if applicable)
```

### Lists
```dart
// with_data   — list with N items (use List.generate for realistic volume)
// empty       — no items, empty state
// loading     — loading state
```

### Forms
```dart
// default     — empty fields
// with_errors — validation triggered with visible errors
// prefilled   — fields with example data
```

---

## Golden rule: knobs first, separate variants only when there is a structural difference

> **A separate `@UseCase` is only justified when the widget renders a fundamentally different visual structure that cannot be controlled with a knob.**

| Situation | Decision |
|---|---|
| `loading`, `disabled`, `showIcon` state, icon position... | **Knob** — same widget, only one parameter changes |
| Visual variant of the component (`primary`, `secondary`, `ghost`...) | **`list<Enum>` knob** — same widget with a different prop |
| The widget renders a completely different structure (e.g. active progress bar vs. icon) | **Separate `@UseCase`** |

### ✅ Correct pattern for buttons — one variant, all states as knobs

All states (loading, disabled) **and** the visual types (primary, secondary...) are exposed as knobs within a single `@UseCase`:

```dart
@UseCase(name: 'default', type: AppButton)
Widget buildAppButtonUseCase(BuildContext context) {
  // Content knobs
  final label = context.knobs.string(label: 'Text', initialValue: 'Continue');

  // Visual variant knob — dropdown with all the enum types
  final variant = context.knobs.list<ButtonVariant>(
    label: 'Variant',
    initialOption: ButtonVariant.primary,
    options: ButtonVariant.values,
    labelBuilder: (v) => v.name,
  );

  // Size and behavior knobs
  final size = context.knobs.list<ButtonSize>(
    label: 'Size',
    initialOption: ButtonSize.normal,
    options: ButtonSize.values,
    labelBuilder: (v) => v.name,
  );

  // Icon knobs
  final icon = context.knobs.list<IconData>(
    label: 'Icon',
    initialOption: Icons.balance,
    options: [Icons.balance, Icons.star, Icons.favorite, Icons.check_circle],
    labelBuilder: (i) => {
      Icons.balance: 'balance',
      Icons.star: 'star',
      Icons.favorite: 'favorite',
      Icons.check_circle: 'check_circle',
    }[i] ?? 'icon',
  );

  final iconPosition = context.knobs.list<IconPosition>(
    label: 'Icon position',
    initialOption: IconPosition.start,
    options: IconPosition.values,
    labelBuilder: (p) => p.name,
  );

  // State knobs — do NOT create separate @UseCases for these
  final showIcon = context.knobs.boolean(label: 'Show icon', initialValue: true);
  final isLoading = context.knobs.boolean(label: 'Loading', initialValue: false);
  final isEnabled = context.knobs.boolean(label: 'Enabled', initialValue: true);

  // The code preview shows the widget instantiation WITHOUT the ColoredBox —
  // that wrapper is catalog scaffolding, not production code.
  context.setCodePreview('''
AppButton(
  label: '$label',
  variant: ButtonVariant.${variant.name},
  size: ButtonSize.${size.name},
  icon: Icons.${icon.toString().split('.').last},
  iconPosition: IconPosition.${iconPosition.name},
  showIcon: $showIcon,
  isLoading: $isLoading,
  isEnabled: $isEnabled,
  onPressed: () {},
)''');

  // Wrap in a ColoredBox with the correct background based on the active theme.
  // The already-registered code preview only shows AppButton(...) — without this wrapper.
  final isDark = Theme.of(context).brightness == Brightness.dark;
  return ColoredBox(
    color: isDark ? AppColors.primary900 : AppColors.primary0,
    child: Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: AppButton(
          label: label,
          variant: variant,
          size: size,
          icon: icon,
          iconPosition: iconPosition,
          showIcon: showIcon,
          isLoading: isLoading,
          isEnabled: isEnabled,
          onPressed: () => developer.log('AppButton pressed'),
        ),
      ),
    ),
  );
}
```

### ✅ Justified separate variants — radically different visual structure

Only when the widget **cannot render** all of its states with a single widget tree controlled by parameters:

```dart
@UseCase(name: 'default', type: UploadButton)
Widget buildUploadButtonUseCase(BuildContext context) { /* normal state */ }

@UseCase(name: 'uploading', type: UploadButton)
Widget buildUploadButtonUploadingUseCase(BuildContext context) { /* active progress bar, different structure */ }

@UseCase(name: 'success', type: UploadButton)
Widget buildUploadButtonSuccessUseCase(BuildContext context) { /* animated checkmark */ }

@UseCase(name: 'error', type: UploadButton)
Widget buildUploadButtonErrorUseCase(BuildContext context) { /* error icon + retry */ }
```

### ❌ Antipattern — do NOT create one @UseCase per state when a knob is enough

```dart
// ❌ Wrong: three use cases for what are only parameter changes
@UseCase(name: 'primary_disabled', type: AppButton)
Widget buildAppButtonPrimaryDisabledUseCase(BuildContext context) {
  return AppButton(variant: ButtonVariant.primary, isEnabled: false, ...);
}

@UseCase(name: 'primary_loading', type: AppButton)
Widget buildAppButtonPrimaryLoadingUseCase(BuildContext context) {
  return AppButton(variant: ButtonVariant.primary, isLoading: true, ...);
}

@UseCase(name: 'primary_with_icon', type: AppButton)
Widget buildAppButtonPrimaryWithIconUseCase(BuildContext context) {
  return AppButton(variant: ButtonVariant.primary, showIcon: true, ...);
}
// ✅ Correct: a single 'default' use case with isEnabled, isLoading, and showIcon knobs
```

---

## Test data and text — contextualized to the project

**Key rule:** for visible text, use the literal value from Figma when it
exists. If Figma does not define the value, identify the app's domain (fintech,
e-commerce, health, education, logistics, etc.) and use example data consistent
with that context. Never use "lorem ipsum", "text", "value", "test", or generic
data, and never make up interface copy.

### How to identify the domain

1. Check the package name in `pubspec.yaml`
2. Read the data models in `lib/models/` or `lib/domain/`
3. Look at the existing screens in `lib/features/` or `lib/screens/`
4. Infer the domain from the terminology used in the code

### Examples by domain

**Fintech / Banking:**
```dart
context.knobs.string(label: 'accountHolder', initialValue: 'Maria Garcia Lopez')
context.knobs.double.input(label: 'balance', initialValue: 2450.75)
context.knobs.string(label: 'transactionDescription', initialValue: 'Transfer to Carlos Perez')
context.knobs.list<String>(label: 'accountType', initialOption: 'Savings', options: ['Savings', 'Checking', 'Payroll'])

final transactions = List.generate(15, (i) => Transaction(
  id: '$i',
  description: '${['Electricity', 'Water', 'Internet', 'Gas'][i % 4]} bill payment',
  amount: (i + 1) * 23.50,
  date: DateTime.now().subtract(Duration(days: i)),
));
```

**E-commerce:**
```dart
context.knobs.string(label: 'productName', initialValue: 'Premium Basic T-Shirt')
context.knobs.double.input(label: 'price', initialValue: 49.99)
context.knobs.int.slider(label: 'stock', initialValue: 24, min: 0, max: 100)
context.knobs.string(label: 'category', initialValue: 'Sportswear')

final products = List.generate(20, (i) => Product(
  id: '$i',
  name: '${['Running', 'Training', 'Casual', 'Outdoor'][i % 4]} Product ${i + 1}',
  price: 29.99 + (i * 10),
  imageUrl: 'https://picsum.photos/200/200?random=$i',
));
```

**Health / Telemedicine:**
```dart
context.knobs.string(label: 'patientName', initialValue: 'Ana Martinez')
context.knobs.string(label: 'specialty', initialValue: 'Cardiology')
context.knobs.string(label: 'doctorName', initialValue: 'Dr. Roberto Sanchez')
context.knobs.dateTime(label: 'appointmentDate', initialValue: DateTime.now().add(const Duration(days: 3)))

final appointments = List.generate(8, (i) => Appointment(
  id: '$i',
  doctorName: 'Dr. ${['Lopez', 'Garcia', 'Martin', 'Torres'][i % 4]}',
  specialty: ['Cardiology', 'Dermatology', 'Pediatrics', 'Neurology'][i % 4],
  dateTime: DateTime.now().add(Duration(days: i + 1)),
));
```

**Education:**
```dart
context.knobs.string(label: 'courseName', initialValue: 'Introduction to Flutter')
context.knobs.string(label: 'instructorName', initialValue: 'Prof. Laura Vega')
context.knobs.int.slider(label: 'progressPercent', initialValue: 65, min: 0, max: 100)
context.knobs.int.input(label: 'enrolledStudents', initialValue: 142)
```

### ❌ Antipatterns — never use these values

```dart
// ❌ Generic / no context
context.knobs.string(label: 'text', initialValue: 'text')
context.knobs.string(label: 'name', initialValue: 'Lorem ipsum')
context.knobs.string(label: 'title', initialValue: 'Title')
context.knobs.double.input(label: 'value', initialValue: 0.0)
context.knobs.string(label: 'description', initialValue: 'Description here')

// ❌ Test/placeholder data
final items = List.generate(5, (i) => Item(name: 'Item $i'));
```

### For lists — volume and domain data

```dart
// ✅ Enough to test scroll, performance, and visual variation
final items = List.generate(20, (i) => ProductItem(
  id: '$i',
  name: 'Product ${i + 1}',
  price: 19.99 + (i * 5.50),
));
```

---

## Code preview per variant

The code preview is shown **outside the device frame**, in the Widgetbook page panel.
Each use case calls `context.setCodePreview(...)` with the **widget's constructor call**,
interpolating the current knob values — the panel updates in real time.

> The displayed code is the widget instantiation (what the developer would copy into their app),
> not the use case function. Never embed code panels inside the returned widget.

```dart
import '../../../shared/code_preview_addon.dart';

// ✅ A single use case — all states are knobs, NOT separate @UseCases
@UseCase(name: 'default', type: AppButton)
Widget buildAppButtonUseCase(BuildContext context) {
  final label    = context.knobs.string(label: 'Text', initialValue: 'Confirm');
  final variant  = context.knobs.list<ButtonVariant>(
    label: 'Variant',
    initialOption: ButtonVariant.primary,
    options: ButtonVariant.values,
    labelBuilder: (v) => v.name,
  );
  final isLoading = context.knobs.boolean(label: 'Loading', initialValue: false);
  final isEnabled = context.knobs.boolean(label: 'Enabled', initialValue: true);

  context.setCodePreview('''
AppButton(
  label: '$label',
  variant: ButtonVariant.${variant.name},
  isLoading: $isLoading,
  isEnabled: $isEnabled,
  onPressed: () {},
)''');

  return AppButton(
    label: label,
    variant: variant,
    isLoading: isLoading,
    isEnabled: isEnabled,
    onPressed: () => developer.log('AppButton pressed'),
  );
}

// ❌ Do NOT do this — 'loading' is not a structural variant, it is a knob
// @UseCase(name: 'loading', type: AppButton)
// Widget buildAppButtonLoadingUseCase(BuildContext context) { ... }
```

### ✗ Antipattern — never do this

```dart
// ❌ Do NOT embed the code preview inside the use case
@UseCase(name: 'loading', type: AppButton)
Widget buildAppButtonLoadingUseCase(BuildContext context) {
  return Column(
    children: [
      AppButton(label: 'Saving...', isLoading: true, onPressed: () {}),
      SizedBox(height: 24),
      _CodePreviewPanel(tabs: [...]),  // ❌ Renders INSIDE the phone
    ],
  );
}
```
