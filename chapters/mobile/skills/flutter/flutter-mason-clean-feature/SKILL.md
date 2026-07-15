---
id: flutter-mason-clean-feature
version: 2.0.1
scope: stack
type: skill
chapter: mobile
stack: [flutter]
tags: [archetype, flutter, mobile, mason, clean architecture, feature, feature generation]
name: flutter-mason-clean-feature
description: Complete workflow for creating Flutter features using the flutter_clean_feature Mason brick. Use when creating a new feature in a Flutter project with Clean Architecture, setting up feature-specific dependency injection, integrating features into host apps, configuring routing and navigation, or understanding feature scope and boundaries. Works with any Flutter project structure—from monorepos with multiple apps to single-app projects. Covers Mason brick configuration, layer implementation, DI setup, app integration, testing structure, and best practices.
license: Complete terms in LICENSE.txt
metadata:
  category: productivity
---

# Flutter Clean Feature with Mason

Create modular, production-ready features for Flutter applications using the `flutter_clean_feature` Mason brick. This skill guides you through the complete workflow: from configuration and brick execution to feature integration and testing.

## Quick Start

Generate a new feature with two commands:

```bash
# 1. Create config file (optional but recommended)
echo -e '{ "name": "profile", "prefix": "app", "packages": ["commons"], "shareds": ["l10n"], "isFromCleanProject": true, "apps": ["mobile_app"] }' > profile.json

# 2. Run Mason brick
mason make flutter_clean_feature -o ./features -c ./profile.json
```

That's it. You now have a feature directory with Clean Architecture layers (Domain, Data, Presentation) ready for implementation.

## Understanding the Brick

The `flutter_clean_feature` brick generates a feature structure following **Clean Architecture principles**:

- **Domain Layer**: Business logic, entities, use cases, abstract repositories
- **Data Layer**: Concrete repository implementations, data sources (local/remote)
- **Presentation Layer**: UI pages, BLoCs/Cubits, widgets

The brick is **configuration-driven**—you provide metadata about your feature, and it scaffolds the entire structure.

**Important**: This brick is designed for **Flutter monorepo projects**. Package and shared library dependencies use local paths (`../../packages/{name}`, `../../shared/{name}`), not pub.dev package names.

### Key Concepts

1. **Feature**: An isolated, modular unit of functionality (e.g., profile, shopping cart, authentication)
2. **Scope**: A feature should be cohesive and independent; avoid mixing unrelated concerns
3. **Clean Architecture**: Three-layer dependency flow (Domain ← Data ← Presentation)
4. **Dependency Injection**: Features use GetIt + Injectable for scoped dependency management
5. **Monorepo Structure**: Packages and shareds are local workspace dependencies, not external pub.dev packages

## Complete Workflow

### Phase 1: Prepare Configuration

Define your feature metadata in a JSON config file:

```json
{
  "name": "profile",           // Feature name (snake_case)
  "prefix": "app",             // Naming prefix for classes/files
  "packages": ["commons"],     // External package dependencies
  "shareds": ["l10n"],         // Shared libraries (l10n, design_tokens, etc)
  "isFromCleanProject": true,  // Set true for Clean Architecture projects
  "apps": ["mobile_app"]       // Target app(s) using this feature
}
```

See [references/mason-command.md](references/mason-command.md) for details on each variable and configuration options.

### Phase 2: Generate Feature Structure

Execute the Mason brick to scaffold the complete feature:

```bash
mason make flutter_clean_feature -o ./features -c ./config.json
```

This creates a feature directory with Clean Architecture structure:
```
features/profile/
├── lib/
│   ├── profile.dart                          # Public API export
│   └── src/
│       ├── data/
│       │   ├── datasources/                  # Local & remote data sources
│       │   ├── models/                       # Data models
│       │   ├── mappers/                      # Data entity mappers
│       │   └── repositories/                 # Repository implementations
│       ├── domain/
│       │   ├── entities/                     # Domain entities
│       │   ├── repositories/                 # Abstract repository interfaces
│       │   └── usecases/                     # Business logic (use cases)
│       ├── presentation/
│       │   ├── blocs/                        # Cubits/BLoCs (state management)
│       │   ├── pages/                        # Full screens
│       │   └── widgets/                      # Reusable components
│       ├── routes/                           # Feature routing definitions
│       └── di/                               # Dependency injection (GetIt + Injectable)
├── test/                                      # Test structure mirrors lib/src
├── pubspec.yaml                              # Feature-specific dependencies
├── analysis_options.yaml                     # Linting configuration
└── README.md
```

See [references/generated-structure.md](references/generated-structure.md) for a complete breakdown of each directory and file.

### Phase 3: Add to Host Project

Register your feature in the host app's `pubspec.yaml`:

```yaml
dependencies:
  profile:
    path: ../features/profile
```

Then sync dependencies:

```bash
# For monorepos with melos
melos bootstrap

# For single project
flutter pub get
```

### Phase 4: Integrate Routing

Add feature routes to your app's router (e.g., `apps/mobile_app/lib/router/app_router.dart`):

```dart
import 'package:profile/profile.dart' as profile;
import 'package:go_router/go_router.dart';

class AppRouter {
  static final router = GoRouter(
    routes: [
      ...profile.ProfileRoutes.routes,  // ← Export routes from feature
    ],
  );
}
```

The feature generates a `ProfileRoutes` class that defines all its routes as a static list.

### Phase 5: Configure Dependency Injection

1. **Register the feature module** in the app's service locator:

```dart
// apps/mobile_app/lib/di/service_locator.dart
import 'package:profile/profile.dart';

@InjectableInit(
  initializerName: r'$initGetIt',
  externalPackageModulesBefore: [
    ExternalModule(ProfilePackageModule, scope: 'profile'),
  ],
)
Future<void> configureDependencies() async {
  await $initGetIt(getIt);
  await initProfileScope(getIt);
}
```

2. **Provide BLoCs/Cubits** in the app:

```dart
// apps/mobile_app/lib/di/repository_cubit.dart
import 'package:profile/profile.dart' as profile;
import 'package:flutter_bloc/flutter_bloc.dart';

class RepositoryCubit {
  static List<BlocProvider> get() {
    return [
      BlocProvider<profile.ProfileCubit>(
        create: (_) => profile.ProfileCubit(
          useCase: getIt<profile.GetDataUseCase>(),
        ),
      ),
    ];
  }
}
```

### Phase 6: Generate Code

Compile generated files (GetIt + Injectable):

```bash
# From project root (for monorepo)
melos exec -- "dart run build_runner build -d"

# Or for single project
dart run build_runner build -d
```

### Phase 7: Implement Layers

Now implement business logic:

- **Domain**: Entity definitions, abstract repositories, use cases
- **Data**: Repository implementations, concrete data sources, serialization
- **Presentation**: Pages, BLoCs/Cubits, widgets

Refer to `skill-clean-architecture` for detailed patterns on each layer.

## Key Decisions

### When to Create a New Feature

Create a new feature when:
- The functionality is **distinct and cohesive** (profile management, order history, settings)
- It has **no high-risk dependency** on other features
- You plan to **test it independently**

Do NOT create a feature for:
- Minor UI components (buttons, badges, dialogs)
- Shared utilities (validation, formatting) → use `commons` package instead
- Business domain rules that belong in another feature

### Choosing the Feature Name

- Use **lowercase snake_case**: `product_detail`, `checkout`, `auth`
- Be **descriptive but concise**: `profile` not `user_profile_management_page`
- Reflect the **business domain**, not implementation: `checkout` not `payment_flow`

### Package vs Shared Dependencies

**Both are local paths** in a monorepo (not pub.dev packages):

- **packages**: Local package paths at `../../packages/{name}` (e.g., http, networking, image_processing)
- **shareds**: Internal shared libraries at `../../shared/{name}` (e.g., l10n, design_tokens, commons)

```json
{
  "packages": ["http", "uuid"],
  "shareds": ["commons", "l10n", "design_tokens"]
}
```

The brick generates pubspec.yaml with these as local path dependencies:
```yaml
http:
  path: ../../packages/http
l10n:
  path: ../../shared/l10n
```

**If your monorepo structure differs** (e.g., using pub.dev packages or different paths), manually adjust the paths in pubspec.yaml after generation.

### isFromCleanProject Flag

Set `true` if:
- Using Clean Architecture with Domain/Data/Presentation layers
- Using GetIt + Injectable for DI
- Following this skill's patterns

Set `false` for simpler projects that don't follow Clean Architecture.

## Integration Checklist

After generating the feature, ensure:

- [ ] Feature folder is in `features/` or equivalent
- [ ] Added to host app's `pubspec.yaml`
- [ ] Routes are exported in `lib/{name}.dart`
- [ ] Feature module registered in app's DI container
- [ ] Build runner compiled successfully
- [ ] BLoCs/Cubits provided to affected pages
- [ ] Feature tests pass: `flutter test features/profile/test`
- [ ] App compiles without import errors
- [ ] Feature routes are accessible from the app

## Related Skills

- **skill-clean-architecture**: Deep dive into Domain/Data/Presentation layers and design patterns
- **skill-feature-development**: Generic feature development workflow (complements this skill)
- **skill-coding-standards**: Dart/Flutter naming conventions and code quality standards
- **skill-testing-strategy**: TDD patterns and test organization for features

## Troubleshooting

**Issue**: `mason make` command not found  
**Solution**: Install Mason globally: `dart pub global activate mason_cli`

**Issue**: Generated feature fails to compile due to missing dependencies (pubspec.yaml errors)  
**Solution**: The brick assumes monorepo paths (`../../packages/...`, `../../shared/...`). Verify your actual monorepo structure matches these paths. Adjust paths in pubspec.yaml manually if your structure is different (e.g., using pub.dev packages instead).

**Issue**: Post-generation warnings about workspace root, analysis_options.yaml, or melos setup  
**Solution**: These occur when running outside a complete Flutter monorepo. The feature structure is generated correctly. Ensure you're running the command in a proper monorepo root directory with a workspace pubspec.yaml.

**Issue**: Build runner fails after feature generation  
**Solution**: Run `flutter pub get` in feature directory, then: `dart run build_runner clean && dart run build_runner build -d`. Ensure GetIt + Injectable are configured in your project.

**Issue**: GetIt scope not found when running app  
**Solution**: Ensure the feature module is registered in your app's service_locator.dart with the correct ExternalModule declaration. See Phase 5 in the workflow.

**Issue**: Feature routes not accessible from app  
**Solution**: Verify routes are correctly exported in `lib/{featureName}.dart` and properly added to your app's GoRouter configuration. Import the feature's route list: `...ProfileRoutes.routes`

**Issue**: DI injection fails with "module not found" or similar errors  
**Solution**: After structural generation, ensure you run build_runner to generate code from @module and @lazySingleton annotations. This is a critical step that must not be skipped.
