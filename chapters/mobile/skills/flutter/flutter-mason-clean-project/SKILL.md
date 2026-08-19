---
id: flutter-mason-clean-project
version: 2.1.1
scope: stack
type: skill
chapter: mobile
stack: [flutter]
tags: [archetype, flutter, mobile, mason, clean architecture, monorepo, design system, project generation]
name: flutter-mason-clean-project
description: >
  Create Flutter applications using Mason's flutter_clean_project brick. Use this skill when bootstrapping a new Flutter monorepo with Clean Architecture, multiple apps, design system integration, and automated project structure generation. Guides you through configuration (colors, typography, fonts), project generation, and initial feature setup—applicable to any organization.
license: Complete terms in LICENSE.txt
metadata:
  category: productivity
---
# Flutter Clean Project Skill

## Quick Overview

**⚠️ Scope**: This skill is **exclusively** for Flutter project generation using Mason's `flutter_clean_project` brick. It does not cover application development, feature implementation, or infrastructure setup beyond project scaffolding.

`flutter_clean_project` is a Mason brick that generates a complete Flutter monorepo scaffold with:

- **Multiple apps**: Main app + WidgetBook companion app (for design system presentation)
- **Design system integration**: Auto-generated UI Kit from colors, typography, and fonts config
- **Clean Architecture**: Pre-structured domain/data/presentation layers
- **Monorepo setup**: Melos-managed workspace with shared packages (commons, l10n)
- **Automated hooks**: Post-generation setup (flutter create, melos bootstrap, git init, feature generation)

**Use this skill when**: Starting a new Flutter project, setting up monorepo structure, defining design tokens, creating features within the new app.

## Security & Prerequisites

**⚠️ Important Security Notes**:
- This skill guides you through **generation steps only**. Your system must have Flutter, Dart, and Mason already installed.
- System package installation (e.g., `brew install`, `apt-get`) is **your responsibility**. This skill provides informational commands only.
- Destructive operations (removing directories, modifying system files) require **your explicit confirmation**. Never run commands blindly.
- Environment PATH modifications are **optional**; document any changes for your team.

Before generating a Flutter Clean Project, ensure:

- **Mason CLI**: `mason --version` returns v0.1.2 or later
- **Flutter & Dart**: `flutter --version` available in PATH
- **Melos**: Optional but recommended for monorepo management (`melos --version`)
- **Git**: Initialized locally for post-gen hooks

Optional: **Rename package** (`dart pub global activate rename`) for automated bundle ID configuration on iOS/Android.

## Core Workflow

### Step 1: Prepare Configuration (Minimal vs. Custom)

**Minimal approach** (use defaults):
```bash
mason make flutter_clean_project -o /path/to/output
# Prompts for: organization, name, prefix
# Uses default colors/fonts/typography
```

**Custom approach** (use config file):
```bash
mason make flutter_clean_project -o /path/to/output -c config.json
# All variables read from JSON, no prompts
# Note: the flag is -c (long form: --config-path)
```

Create `config.json` starting from the brick's `config-example.json` or See [config-schema-reference.md](references/config-schema-reference.md) for complete schema with examples.

> **Critical config rules (full schema in config-schema-reference.md):**
> - `organization`: plain company name, all lowercase, no spaces — e.g., `"mycompany"` (NOT `"com.mycompany"`)
> - Hex color values: **no `#` prefix** — e.g., `"1565c0"` not `"#1565c0"`
> - Color structure: use `isMaterialColor: true` + `value` array of `{level, value}` objects (levels 50–900)
> - `fontFamily`: exact Google Fonts names in an array — e.g., `["Roboto", "Poppins"]`

### Step 2: Generate Project Structure

Execute mason make with your chosen approach:

```bash
# Basic (prompts)
cd /path/to/workspace
mason make flutter_clean_project -o my_project

# Custom (silent with config)
mason make flutter_clean_project -o my_project -c my_config.json
```

Expected prompts (if no config file):
- **organization**: Company/org name → used for bundle ID (e.g., `com.mycompany.myapp`)
- **name**: Application name (becomes directory, workspace name)
- **prefix**: File/class name prefix (e.g., `app` → `app_radius.dart`, `AppRadius`)

### Step 3: Generation Completes (Hooks Run Automatically)

The brick's post-generation hooks execute automatically:

1. **Creates apps**: Main app + WidgetBook via `flutter create`
2. **Configures bundles**: Sets iOS/Android identifiers (requires `rename` package)
3. **Generates UI Kit**: Converts config colors/typography into Flutter theme
4. **Installs dependencies**: Runs `melos bootstrap` across all packages
5. **Formats code**: `dart format` + `dart fix --apply`
6. **Initializes git**: Sets up repository with master branch
7. **Generates initial features**: Creates features from config (if specified)

Monitor the terminal for progress messages and errors. See [troubleshooting-reference.md](references/troubleshooting-reference.md) if hooks fail.

### Step 4: Verify Generated Structure

After generation completes, check your project:

```
my_project/
├── apps/
│   ├── my_app/                    # Main Flutter app
│   │   ├── lib/
│   │   │   └── src/
│   │   │       ├── domain/        # Business logic
│   │   │       ├── data/          # Data access
│   │   │       ├── presentation/  # UI & state mgmt
│   │   │       └── di/            # Dependency injection
│   │   └── test/
│   └── my_app_widgetbook/         # UI component catalog
├── packages/
│   ├── commons/                   # Shared utilities
│   └── my_app_ui_kit/             # Design system (auto-generated)
├── shared/
│   └── l10n/                      # Localization
├── features/                      # (empty, for flutter_clean_feature)
├── docs/                          # Project documentation
└── pubspec.yaml                   # Workspace root and Melos 7+ configuration
```

Open `apps/my_app/` to start developing.

## Configuration Levels

### Level 1: Basic (Default)

Use config-example.json from the brick as-is:

```bash
mason make flutter_clean_project -o output -c config-example.json
```

**Result**: Project with predefined colors/fonts/typography. Perfect for proof-of-concept or learning.

### Level 2: Intermediate (Customize Design Tokens)

Modify colors, typography, and fonts for your brand:

1. Copy `config-example.json` → `my_config.json`
2. Edit color swatches (MaterialColor definitions with levels 50–900)
3. Add Google Fonts (e.g., "Inter", "Poppins")
4. Define typography styles (label, body, heading, etc.)
5. Run: `mason make flutter_clean_project -o output -c my_config.json`

**Details**: See [config-schema-reference.md](references/config-schema-reference.md) for color/typography structure and validation rules.

### Level 3: Advanced (Add Features at Generation Time)

Include initial features (authentication, home, settings) in config:

```json
{
  "organization": "MyOrganization",
  "name": "myApp",
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
    }
  ]
}
```

The brick auto-generates feature stubs during post-gen hooks. For feature-specific details, see [features-integration-reference.md](references/features-integration-reference.md).

## Naming Conventions

When setting `organization`, `name`, and `prefix` values, follow these casing rules (automatically applied by Mason templates):

| Field | Format | Example | Usage |
|-------|--------|---------|-------|
| **organization** | lowercase, no spaces | `mycompany` | Plain company name only — bundle ID `com.mycompany.myapp` is built by the brick automatically |
| **name** | camelCase or lowercase | `mobileApp` or `mobile_app` | Directory: `mobile_app/`, workspace name |
| **prefix** | lowercase, short | `app` or `ui` | Files: `app_radius.dart`, Classes: `AppRadius` |

Mason automatically applies `.snakeCase()`, `.titleCase()`, `.pascalCase()` transformations via template syntax (`{{name.snakeCase()}}`).

✅ **Correct**:
```json
{
  "organization": "pragmatech",
  "name": "mobileApp",
  "prefix": "app"
}
```
Result: `lib/app_colors.dart`, `class AppColors`, bundle `com.pragmatech.mobile_app`

❌ **Incorrect**:
```json
{
  "organization": "Pragma Tech Inc",
  "name": "My Mobile App!",
  "prefix": "MyApp"
}
```
Result: Invalid characters, spaces, inconsistent casing in generated files.

## Common Issues

**⚠️ Before reporting issues**: Verify your system has Flutter, Dart, Melos, and Mason installed. This skill cannot install system dependencies for you.

**Issue: "Mason brick not found"**
- Ensure brick is installed globally: `mason add -g flutter_clean_project --git-url git@github.com:somospragma/pragma-mason-bricks.git --git-path bricks/flutter_clean_project --git-ref develop`
- Verify brick name exactly matches (case-sensitive)

**Issue: "flutter create failed"**
- Confirm Flutter SDK is in PATH: `flutter --version`
- Check disk space in output directory
- **Note**: If Flutter is not installed, see your system's Flutter installation guide—this skill does not cover installation.

## Out of Scope

This skill **does not cover**:
- System package manager usage (`brew`, `apt-get`, `pacman`, `choco`, etc.)
- Modifying user system environment variables permanently
- Installing dependencies on your system
- Infrastructure or CI/CD configuration
- Application feature development post-generation
- Mobile app distribution or publishing
- Dependency version management beyond initial bootstrap

**Issue: "Bundle ID generation failed" or rename skipped**
- Optional: `rename` package not installed
- Manual workaround: Edit iOS/Android config files post-generation

For more troubleshooting steps, see [troubleshooting-reference.md](references/troubleshooting-reference.md).

## Example: Complete Minimal Project

```bash
# 1. Create configuration (use defaults)
mason make flutter_clean_project -o my_app

# Prompts:
# What is your organization name? [Pragma] > mycompany
# Please enter the name for the project: [mobileApp] > myapp
# Please enter the prefix you want to use for files names: [app] > app

# 2. Wait for hooks to complete (~2-5 minutes)
# ✓ Flutter app created
# ✓ WidgetBook app created
# ✓ UI Kit generated
# ✓ Melos bootstrap completed
# ✓ Git initialized

# 3. Open project
cd my_app/apps/myapp
flutter run

# 4. Explore design system
cd ../myapp_widgetbook
flutter run
```

Result:
- Fully bootstrapped Flutter monorepo
- Two runnable apps (main + WidgetBook)
- Design system integrated
- Ready for feature development

## Integration with Features

After creating the base project, add features using the **`flutter_clean_feature`** Mason brick:

```bash
# Navigate to your generated project root
cd my_app

# Create a feature config (profile_config.json):
# {
#   "name": "profile",
#   "stateManagementType": "bloc",   // or "cubit"
#   "packages": ["commons"],
#   "shareds": ["l10n"],
#   "isFromCleanProject": true
# }

mason make flutter_clean_feature -o features -c profile_config.json
```

Then integrate: add the feature to the main app's `pubspec.yaml`, register its DI module in `AppInjector`, and add its routes to your GoRouter config.

See [features-integration-reference.md](references/features-integration-reference.md) for the full workflow including DI, routes, and pubspec wiring.

## For Extended Guidance

- **Design system configuration**: [config-schema-reference.md](references/config-schema-reference.md)
- **Troubleshooting generation issues**: [troubleshooting-reference.md](references/troubleshooting-reference.md)
- **Adding features post-generation**: [features-integration-reference.md](references/features-integration-reference.md)
- **Brick documentation**: See brick's README.md and brick.yaml for variable definitions
