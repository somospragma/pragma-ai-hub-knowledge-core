---
id: flutter-ds-asset-management
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-asset-management
description: >
  Graphic asset management (SVGs, icons, images) for the Design System.
  Use when downloading assets from Figma, optimizing SVGs, registering
  resources in centralized classes, or referencing assets in widget code.
---
# Asset Management

## Asset Types

> The `assets/...` paths in this document are paths inside the Flutter target
> (package/app), not internal skill paths.

| Type | Format | Location | Registry |
|------|--------|----------|----------|
| DS Icons | SVG | `assets/icons/` | `{{DS_PREFIX}}Icons` class |
| Illustrations | SVG/PNG | `assets/illustrations/` | `{{DS_PREFIX}}Illustrations` class |
| Logos | SVG | `assets/logos/` | `{{DS_PREFIX}}Logos` class |

## Process

### 1. Download
- Export every visible source asset from Figma MCP before implementation
- Archive the original under `{SPEC_PACKET_PATH}/source-assets/figma/` with its
  node id, format and SHA-256 before copying it to the runtime target
- Export as SVG when the source is vector; use a Figma-provided raster format
  only when required
- Name: `snake_case` descriptive (e.g., `icon_close.svg`)

### 2. Optimize (SVG)
```bash
svgo input.svg -o output.svg --multipass
```
- Clean XML (no unnecessary Figma metadata)
- No heavy inline styles
- Correct viewbox
- Optimized paths

Do not optimize or rewrite an archived Figma source that participates in a
deterministic workflow. Runtime files must remain byte-identical to the archive
unless a human-approved, separately audited transformation is explicitly added
to the spec.

### 3. Register
```dart
abstract class {{DS_PREFIX}}AppResources {
  /// Close icon.
  static const String iconClose = 'assets/icons/icon_close.svg';
}
```

### 4. Declare in pubspec
```yaml
flutter:
  assets:
    - assets/icons/
    - assets/illustrations/
    - assets/logos/
```

## Usage in Widgets

```dart
// ✅ CORRECT — Centralized reference
SvgPicture.asset(
  {{DS_PREFIX}}AppResources.iconClose,
  width: {{DS_PREFIX}}Sizes.iconMd,
  height: {{DS_PREFIX}}Sizes.iconMd,
  colorFilter: ColorFilter.mode(/* color token */, BlendMode.srcIn),
)

// ❌ Hardcoded path
SvgPicture.asset('assets/icons/icon_close.svg')

// ❌ Hardcoded size
SvgPicture.asset(icon, width: 24, height: 24)
```

## Checklist

- [ ] Asset downloaded and placed in correct folder
- [ ] SVG optimized (no unnecessary metadata)
- [ ] Variable registered in resource class
- [ ] Declared in `pubspec.yaml` under `flutter.assets`
- [ ] Render size uses size token
- [ ] Color uses semantic token (not hardcoded)
