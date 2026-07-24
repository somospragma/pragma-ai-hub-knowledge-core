# Widgetbook Setup

Add Widgetbook as a development-only catalog. It must not affect the production app bundle.

## Install

```bash
flutter pub add widgetbook widgetbook_annotation --dev
flutter pub add build_runner widgetbook_generator --dev
```

## Folder Structure

```text
widgetbook_[appname]/lib/
├── main.dart
├── ui_system/
├── features/
└── shared/
```

Always create `ui_system/`, `features/`, and `shared/` before generating use cases.

## Assets

Widgetbook is an independent Flutter project. Assets used by cataloged widgets must be declared in `widgetbook_[appname]/pubspec.yaml`, even when the app package is included through `path:`.

After editing assets or dependencies:

```bash
cd widgetbook_[appname]
flutter pub get
dart run build_runner build --delete-conflicting-outputs
```

## Code Preview

The code preview must be shown outside the device frame. It should display the constructor call a developer would copy into the app, not the implementation of the use case itself.

Do not embed code preview panels inside the returned widget.

## Canvas Background

UI System components must render over the same background color they would use in the app. Wrap them in catalog scaffolding such as `ColoredBox` when needed, but do not include that wrapper in the code preview.

Full-screen feature use cases usually provide their own `Scaffold`.

## Run

```bash
cd widgetbook_[appname]
flutter run -d chrome
```
