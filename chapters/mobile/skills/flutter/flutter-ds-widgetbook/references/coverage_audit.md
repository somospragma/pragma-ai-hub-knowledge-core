# Coverage Audit — Detect Gaps in the Widgetbook

Verify which components and screens from the main project are **not cataloged** in the
widgetbook. Use it when integrating an existing widgetbook into a project with components already
created, or periodically to detect new widgets/screens added after the initial setup.

---

## When to run the audit

| Situation | Action |
|---|---|
| Widgetbook was integrated into a project with existing components | Audit the full UI System |
| New screens were added to the project and were not cataloged | Audit Features |
| The user asks "check what's missing in the widgetbook" / "which components aren't there" | Full audit |
| The Design System was updated and new components may exist | Audit the UI System |
| You want to know the current coverage before a delivery | Full audit |

---

## Audit process — step by step

### Step 1 — Scan the main project

#### For the UI System (components)

Find all Design System widget files in the main app. Typical locations are:

```
lib/core/widgets/
lib/shared/widgets/
lib/design_system/
lib/ui/
lib/components/
lib/common/widgets/
lib/widgets/
lib/atoms/
lib/molecules/
lib/organisms/
```

Look for files that:
- End in `_widget.dart`, `_button.dart`, `_card.dart`, `_field.dart`, `_badge.dart`, `_tile.dart`, `_chip.dart`, `_icon.dart`, `_avatar.dart`, `_text.dart`
- Live inside folders named `atoms/`, `molecules/`, `organisms/`, `components/`, `widgets/`
- Export classes that extend `StatelessWidget` or `StatefulWidget`

**Exploration command:**
```bash
# Find all widget files in the main project
find lib -name "*.dart" -path "*/widgets/*" -o \
         -name "*_widget.dart" -o \
         -name "*_button.dart" -o \
         -name "*_card.dart" -o \
         -name "*_field.dart" -o \
         -name "*_badge.dart" | sort
```

#### For Features (screens)

Look for screens in the typical locations:

```
lib/features/**/presentation/
lib/features/**/*_screen.dart
lib/features/**/*_page.dart
lib/screens/
lib/pages/
lib/presentation/
```

**Exploration command:**
```bash
# Find all screens in the main project
find lib -name "*_screen.dart" -o \
         -name "*_page.dart" -o \
         -name "*_view.dart" | grep -v widgetbook | sort
```

---

### Step 2 — Scan the current widgetbook

#### UI System use cases already cataloged

```bash
# See which components already have a use case
find widgetbook_[appname]/lib/ui_system -name "*.use_case.dart" | sort
```

#### Feature use cases already cataloged

```bash
# See which screens already have a use case
find widgetbook_[appname]/lib/features -name "*.use_case.dart" | sort
```

---

### Step 3 — Cross-reference and detect gaps

Compare the results of steps 1 and 2:

**For each component found in the main project:**
- Derive the widget name (Dart class) from the file name
- Check whether `[name].use_case.dart` exists in `widgetbook_[appname]/lib/ui_system/`
- If it does NOT exist → **gap detected** → add it to the pending list

**For each screen found in the main project:**
- Derive the class name from the file name
- Check whether `[name].use_case.dart` exists in `widgetbook_[appname]/lib/features/`
- If it does NOT exist → **gap detected** → add it to the pending list

---

### Step 4 — Report the result before generating

Before creating any use case, present the coverage report to the user:

```
## Coverage report — Widgetbook

### UI System
| Component          | Source file                                 | In widgetbook |
|--------------------|---------------------------------------------|---------------|
| PrimaryButton      | lib/core/widgets/primary_button.dart        | ✅ Cataloged   |
| AppTextField       | lib/core/widgets/app_text_field.dart        | ✅ Cataloged   |
| StatusBadge        | lib/shared/widgets/status_badge.dart        | ❌ Missing     |
| ProductCard        | lib/features/catalog/widgets/product_card.dart | ❌ Missing  |

UI System coverage: 2/4 (50%)

### Features
| Screen             | Source file                                 | In widgetbook |
|--------------------|---------------------------------------------|---------------|
| LoginScreen        | lib/features/auth/login_screen.dart         | ✅ Cataloged   |
| HomeScreen         | lib/features/home/home_screen.dart          | ✅ Cataloged   |
| ProfileScreen      | lib/features/profile/profile_screen.dart    | ❌ Missing     |
| CheckoutScreen     | lib/features/checkout/checkout_screen.dart  | ❌ Missing     |
| OrderDetailScreen  | lib/features/orders/order_detail_screen.dart| ❌ Missing     |

Features coverage: 2/5 (40%)

### Summary
- UI System: 2 missing → StatusBadge, ProductCard
- Features: 3 missing → ProfileScreen, CheckoutScreen, OrderDetailScreen
- Total gaps: 5 use cases to create
```

> **Rule:** Always show the full report before starting to generate. Never create
> use cases silently without first reporting the coverage status.

---

### Step 5 — Prioritize and generate the gaps

After the report, ask the user (if unclear) in what order to prioritize,
or proceed with all of them if the user says so.

For each gap, follow the standard process according to its type:

- **Missing components** → follow `references/project_structure.md` + `references/variants_guide.md`
- **Missing screens** → follow `references/features_guide.md`

After creating all the missing use cases:

```bash
cd widgetbook_[appname] && dart run build_runner build --delete-conflicting-outputs
```

---

### Step 6 — Verify coverage after generation

After running `build_runner`, repeat the scan and confirm that the gaps no longer exist:

```bash
# Confirm the directory tree includes all the new use cases
grep -E "name:|type:" widgetbook_[appname]/lib/main.directories.g.dart | sort
```

Present the updated report and compare it against the previous one.

---

## Signals that an element should be excluded from the audit

Not every `.dart` file in widget folders should be cataloged. Exclude:

| File | Reason |
|---|---|
| `*_mixin.dart` | Mixin, not a renderable widget |
| `*_extension.dart` | Extension, not a widget |
| `*_theme.dart` | Design theme/tokens, not a widget |
| `*_model.dart` / `*_entity.dart` | Data model |
| `*_provider.dart` / `*_bloc.dart` / `*_cubit.dart` | State management |
| `*_service.dart` / `*_repository.dart` | Services |
| `index.dart` / `barrel.dart` | Barrel files (re-exports) |
| Private widgets (`_MyWidget`) | Internal, non-exported classes |
| Generic layout widgets with no visual variants of their own | Wrappers without public props |

---

## Incremental audit — detect new changes

For projects that already have an established widgetbook, detect only what was recently added:

```bash
# See widget files modified or created in the last 30 days
find lib -name "*.dart" -newer widgetbook_[appname]/lib/main.dart \
  \( -path "*/widgets/*" -o -name "*_screen.dart" -o -name "*_page.dart" \) | sort
```

This command compares each file's modification date against the widgetbook's `main.dart`,
finding everything added after the last time the catalog was updated.

---

## Quick report template

Use this template when reporting before creating use cases:

```markdown
## Widgetbook audit — [project name]

**UI System** — X/Y cataloged (Z%)
- ✅ [ComponentA] → already has a use case
- ✅ [ComponentB] → already has a use case
- ❌ [ComponentC] → missing use case → `lib/path/component_c.dart`
- ❌ [ComponentD] → missing use case → `lib/path/component_d.dart`

**Features** — X/Y cataloged (Z%)
- ✅ [ScreenA] → already has a use case
- ❌ [ScreenB] → missing use case → `lib/features/feature/screen_b.dart`
- ❌ [ScreenC] → missing use case → `lib/features/feature/screen_c.dart`

**Proposed action:** Create the N missing use cases. Should I proceed with all of them, or would you prefer to prioritize any?
```
