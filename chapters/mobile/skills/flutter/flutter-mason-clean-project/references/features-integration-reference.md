# Features Integration Reference

Guide for adding features to a generated `flutter_clean_project` after initial project creation.

## Quick Overview

After creating your base Flutter Clean Project, you can add features in two ways:

1. **At generation time** (recommended): Include `features` array in config.json → brick auto-generates stubs
2. **Post-generation** (for new features later): Use `flutter_clean_feature` brick manually

This reference covers both approaches.

---

## Approach 1: Features at Generation Time (Config)

### How It Works

Add features to config.json before running `mason make`:

```json
{
  "organization": "mycompany",
  "name": "myapp",
  "prefix": "app",
  "colors": [...],
  "fontFamily": [...],
  "typography": [...],
  "features": [
    {
      "name": "authentication",
      "packages": ["commons"],
      "shareds": ["l10n"],
      "isFromCleanProject": true
    },
    {
      "name": "home",
      "packages": ["commons"],
      "shareds": ["l10n"],
      "isFromCleanProject": true
    }
  ]
}
```

### Execution

```bash
# Generate with features
mason make flutter_clean_project -o my_app -c config.json

# Wait for post-gen hooks to complete
# The brick auto-runs flutter_clean_feature for each feature
```

### Generated Structure

```
features/
├── authentication/
│   ├── lib/
│   │   ├── src/
│   │   │   ├── domain/          # Business logic
│   │   │   │   ├── entities/
│   │   │   │   ├── repositories/
│   │   │   │   └── usecases/
│   │   │   ├── data/            # Data access
│   │   │   │   ├── datasources/
│   │   │   │   ├── models/
│   │   │   │   ├── repositories/
│   │   │   │   └── mappers/
│   │   │   ├── presentation/    # UI & state mgmt
│   │   │   │   ├── bloc/        # or cubit/
│   │   │   │   ├── pages/
│   │   │   │   └── widgets/
│   │   │   ├── di/              # Dependency injection
│   │   │   └── routes/          # Route definitions
│   │   └── authentication.dart  # Barrel export
│   ├── test/                    # Unit tests (mirrors lib/ structure)
│   └── pubspec.yaml
└── home/
    └── [same structure as authentication/]
```

### Benefits

- ✅ All features created consistently at once
- ✅ Automated dependency injection setup
- ✅ Routes pre-integrated if using router
- ✅ No manual feature creation needed
- ✅ Faster for multi-feature projects

### Limitations

- Features are basic stubs (minimal implementations)
- You still implement business logic post-generation
- Modifying features at generation time requires regenerating

---

## Approach 2: Add Features Post-Generation

### Prerequisites

Ensure `flutter_clean_feature` brick is installed:

```bash
# Check if installed globally
mason list --global | grep flutter_clean_feature

# If not, install
mason add -g flutter_clean_feature --git-url git@github.com:somospragma/pragma-mason-bricks.git --git-path bricks/flutter_clean_feature --git-ref develop
```

### Workflow

Navigate to your generated project and run `flutter_clean_feature` brick for each new feature:

```bash
# Open your generated project
cd my_app

# Add first feature: authentication
mason make flutter_clean_feature \
  -o features \
  -c /path/to/auth_config.json

# Add second feature: settings
mason make flutter_clean_feature \
  -o features \
  -c /path/to/settings_config.json
```

### Feature Configuration

Create a config file for each feature (e.g., `auth_config.json`):

```json
{
  "name": "authentication",
  "stateManagementType": "cubit",      // or "bloc"
  "packages": ["commons"],              // Package dependencies
  "shareds": ["l10n"],                  // Shared resources
  "baseUrl": "http://localhost:8080"   // Optional: API endpoint
}
```

Configuration reference: See [skill-flutter-clean-feature](../skill-flutter-clean-feature/SKILL.md) for detailed schema.

### Verify Feature Generation

After creating a feature, check the structure:

```bash
# Verify feature exists
ls -la features/authentication/

# Check layer structure
tree features/authentication/lib/src/
# Expected: domain/, data/, presentation/, di/, routes/

# Run tests
dart test features/authentication/

# Run analyzer
dart analyze features/authentication/
```

---

## Integration Steps

After generating (or adding) features, integrate them into your main app:

### Step 1: Configure Routes (If Using Router)

**Main App** (`apps/my_app/lib/src/presentation/routes/app_routes.dart`):

```dart
// Import feature routes
import 'package:authentication/src/routes/authentication_routes.dart';
import 'package:home/src/routes/home_routes.dart';

// Add to route definitions
class AppRoutes {
  static const String splash = '/';
  static const String home = '/home';
  static const String login = '/auth/login';
  
  static List<GoRoute> getRoutes() {
    return [
      // Splash/Initial route
      GoRoute(
        path: '/',
        builder: (context, state) => const SplashPage(),
      ),
      
      // Feature routes (imported from feature packages)
      ...authenticationRoutes,
      ...homeRoutes,
    ];
  }
}
```

Each feature provides its own routes (e.g., `authentication_routes` from `authentication` package).

### Step 2: Configure Dependency Injection

**Main App** (`apps/my_app/lib/src/di/app_injector.dart`):

```dart
import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';

// Import feature DI modules
import 'package:authentication/src/di/authentication_module.dart';
import 'package:home/src/di/home_module.dart';

@Singleton()
class AppInjector {
  static final _instance = GetIt.instance;
  
  static Future<void> setup() async {
    // Core + commons DI
    await _setupCommonsDependencies();
    
    // Feature DI modules
    await AuthenticationModule.setup(_instance);
    await HomeModule.setup(_instance);
  }
  
  static Future<void> _setupCommonsDependencies() async {
    // Register core services, API clients, local storage, etc.
  }
}
```

Each feature's DI module registers its own repositories, usecases, and blocs/cubits.

### Step 3: Add Features as Dependencies

**Main App** (`pubspec.yaml`):

```yaml
dependencies:
  flutter:
    sdk: flutter
  commons:
    path: ../../../packages/commons
  my_app_ui_kit:
    path: ../../../packages/my_app_ui_kit
  
  # Feature dependencies
  authentication:
    path: ../../../features/authentication
  home:
    path: ../../../features/home
```

### Step 4: Run Dependency Resolution

```bash
# From project root
cd my_app
flutter pub get

# Or use Melos (from workspace root)
cd ../../../
melos get
```

### Step 5: Test Integration

```bash
# From main app directory
flutter run

# Features should be accessible via defined routes
```

---

## Feature Structure Explanation

Each feature follows Clean Architecture with 3 layers:

### Domain Layer (`domain/`)

Business logic independent of frameworks. Contains:

```
domain/
├── entities/              # Business objects
│   └── user_entity.dart
├── repositories/          # Abstract interfaces
│   └── user_repository.dart
└── usecases/             # Business processes
    ├── login_usecase.dart
    ├── logout_usecase.dart
    └── get_user_usecase.dart
```

**Key rules**:
- No Flutter imports
- No external dependencies
- Pure Dart + Result<Success, Failure> pattern

### Data Layer (`data/`)

Data access and transformation. Contains:

```
data/
├── datasources/          # Local/Remote sources
│   ├── local_datasource.dart
│   └── remote_datasource.dart
├── models/               # Data transfer objects
│   └── user_model.dart
├── repositories/         # Concrete implementations
│   └── user_repository_impl.dart
└── mappers/             # Entity ↔ Model transforms
    └── user_mapper.dart
```

**Key rules**:
- Implements domain repository interfaces
- Handles API/local storage interactions
- Maps models ↔ entities

### Presentation Layer (`presentation/`)

UI and state management. Contains:

```
presentation/
├── bloc/ (or cubit/)       # State management
│   ├── user_bloc.dart      # or user_cubit.dart
│   └── user_event.dart
├── pages/                  # Full-screen widgets
│   └── login_page.dart
├── widgets/                # Reusable components
│   └── user_card.dart
└── routes/                 # Feature routing
    └── authentication_routes.dart
```

**Key rules**:
- Depends on domain layer (repositories, usecases)
- No business logic (delegated to bloc/cubit)
- Bloc/Cubit emits states that pages/widgets consume

### DI Layer (`di/`)

Dependency injection configuration. Contains:

```
di/
└── authentication_module.dart   # Registers domain/data/presentation dependencies
```

**Key rules**:
- Registers all feature dependencies with GetIt
- Called during app initialization
- Makes non-public classes available to main app

---

## Best Practices

### 1. One Feature = One Use Case Domain
- `authentication` → Login, logout, password reset
- `home` → Feed, recommendations, trending
- `profile` → User profile, settings, preferences
- DO NOT mix domains in one feature

### 2. Dependency Direction
```
presentation → domain ← data
        ↓
       commons (shared utilities)
```
- Presentation depends on domain
- Data depends on domain
- Domain NEVER depends on data or presentation

### 3. Feature Independence
- Features should not import from each other
- Communicate via main app's router and DI
- Share only through `commons` package

### 4. Testing Structure
```
test/
├── src/
│   ├── domain/usecases/
│   │   └── login_usecase_test.dart
│   ├── data/repositories/
│   │   └── user_repository_impl_test.dart
│   └── presentation/bloc/
│       └── user_bloc_test.dart
```

Create tests mirroring `lib/` structure.

### 5. Implementation Progress

**Phase 1 (immediate)**: Stubs generate automatically
- Feature structure: ✅
- Route definitions: ✅
- DI configuration: ✅
- Implementation: ❌ (empty usecases, bloc stubs)

**Phase 2 (development)**: Implement business logic
- Domain: Write entities, repositories, usecases
- Data: Implement datasources, models, mappers
- Tests: Write unit tests (AAA pattern)

**Phase 3 (ui)**: Implement UI
- Presentation: Pages, widgets, bloc/cubit handlers
- Routes: Connect pages to route definitions
- Integration: Add to main app routes + DI

---

## Common Integration Errors

### Error: "Package not found: authentication"

**Cause**: Feature not declared in pubspec.yaml

**Fix**:
```yaml
# Add to apps/my_app/pubspec.yaml
dependencies:
  authentication:
    path: ../../../features/authentication
```

### Error: "GetIt instance not found"

**Cause**: Feature DI module not registered during app init

**Fix**:
```dart
// In main app's main.dart
void main() async {
  await AppInjector.setup();  // Must call this first
  runApp(const MyApp());
}
```

### Error: "Route /auth/login not found"

**Cause**: Feature routes not added to app's route configuration

**Fix**:
```dart
// In app_routes.dart
GoRouter(
  routes: [
    ...AppRoutes.getRoutes(),  // Core routes
    ...authenticationRoutes,    // Feature routes
    ...homeRoutes,              // Feature routes
  ],
);
```

---

## For Detailed Feature Development

Refer to the **skill-flutter-clean-feature** skill for:
- Complete feature creation workflow
- Testing strategies (AAA/GWT patterns)
- Advanced DI configurations
- State management (BLoC vs Cubit)
- Route integration patterns
