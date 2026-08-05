# Mason Command Reference

## Command Syntax

```bash
mason make flutter_clean_feature [OPTIONS]
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `-o, --output` | `string` | Yes | Output directory for feature (e.g., `./features` or `./packages`) |
| `-c, --config` | `string` | No | Path to JSON config file with variables |

## Configuration Variables

When you run the brick, Mason prompts for these variables. Provide them via JSON config file (recommended) or interactively.

### Required Variables

#### `name`
- **Type**: `string`
- **Description**: Feature name
- **Format**: Use lowercase snake_case (no spaces, hyphens, or symbols)
- **Examples**: `profile`, `shopping_cart`, `user_settings`, `order_history`
- **Naming Tips**:
  - Reflect business domain: `checkout` not `payment_flow`
  - Be concise: `profile` not `user_profile_management`
  - Avoid generic names: use specific names for clarity

#### `prefix`
- **Type**: `string`
- **Description**: Naming prefix for classes, files, and configuration
- **Format**: Use camelCase
- **Examples**: `app`, `myApp`, `admin`
- **Impact**: Affects generated class names:
  - `ProfileCubit` (if name=profile, prefix=app)
  - `AppProfileRepository` (uses prefix in some generated names)
  - `app_profile_config.dart` (file naming)

### Optional Variables

#### `packages`
- **Type**: `array` (comma-separated string)
- **Description**: Local monorepo packages to include as workspace dependencies
- **Examples**: `http,uuid` or `networking,image_processing`
- **Format**: Comma-separated list, no spaces
- **Default**: Empty
- **Generated Path**: `../../packages/{package_name}` in pubspec.yaml
- **When to use**: For packages that live in `packages/` directory of your monorepo
- **Important**: These are NOT pub.dev packages. The brick assumes a monorepo structure and generates local path dependencies.

#### `shareds`
- **Type**: `array` (comma-separated string)
- **Description**: Local shared libraries in your monorepo workspace
- **Examples**: `commons,l10n,design_tokens` or just `ui_kit`
- **Format**: Comma-separated list, no spaces
- **Default**: Empty
- **Generated Path**: `../../shared/{shared_name}` in pubspec.yaml
- **When to use**: For shared libraries in your monorepo (localization, design tokens, common utilities)
- **Common values**:
  - `commons`: Utility functions, constants, extensions
  - `l10n`: Localization strings and translations
  - `design_tokens`: Theme, colors, typography tokens
  - `ui_kit`: Reusable UI components
- **Important**: These are local monorepo dependencies, not pub.dev packages

#### `isFromCleanProject`
- **Type**: `boolean`
- **Description**: Whether this is a Clean Architecture project
- **Values**: `true` or `false`
- **Default**: `false`
- **Impact**: When `true`, generates additional DI boilerplate and assumes GetIt + Injectable usage
- **When to use**:
  - `true`: Using domain/data/presentation layers with GetIt + Injectable
  - `false`: Simpler project structure without formal DI

#### `apps`
- **Type**: `array` (comma-separated string)
- **Description**: Target app(s) that will use this feature
- **Examples**: `mobile_app,admin_app` or just `app`
- **Format**: Comma-separated list, no spaces
- **Default**: Empty
- **When to use**: In monorepos with multiple apps, specify which apps need this feature for documentation purposes
- **Note**: Currently informational; actual integration requires manual setup

## Configuration Examples

### Minimal Configuration (Single App, Local Packages)

```json
{
  "name": "profile",
  "prefix": "app",
  "packages": [],
  "shareds": ["commons"],
  "isFromCleanProject": false,
  "apps": []
}
```

### Standard Configuration (Clean Project, Monorepo)

```json
{
  "name": "home",
  "prefix": "app",
  "packages": ["http"],
  "shareds": ["commons", "l10n"],
  "isFromCleanProject": true,
  "apps": ["mobile_app"]
}
```

Generated pubspec.yaml will include:
```yaml
http:
  path: ../../packages/http
commons:
  path: ../../shared/commons
l10n:
  path: ../../shared/l10n
```

### Complex Configuration (Monorepo with Multiple Packages)

```json
{
  "name": "product_detail",
  "prefix": "pragma",
  "packages": ["http", "image_picker", "cached_network_image"],
  "shareds": ["commons", "l10n", "design_tokens", "analytics"],
  "isFromCleanProject": true,
  "apps": ["mobile_app", "tablet_app"]
}
```

## Usage Patterns

### Interactive (No Config File)

```bash
mason make flutter_clean_feature -o ./features
# Mason will prompt for each variable
```

### With Config File (Recommended)

```bash
# 1. Create config file
cat > profile.json << 'EOF'
{
  "name": "profile",
  "prefix": "app",
  "packages": ["http"],
  "shareds": ["commons", "l10n"],
  "isFromCleanProject": true,
  "apps": ["mobile_app"]
}
EOF

# 2. Run with config
mason make flutter_clean_feature -o ./features -c ./profile.json
```

### Programmatic (Scripted)

```bash
# For automation, generate config and run
FEATURE_NAME="settings"
CONFIG_FILE="${FEATURE_NAME}.json"

cat > "${CONFIG_FILE}" << EOF
{
  "name": "${FEATURE_NAME}",
  "prefix": "app",
  "packages": ["http"],
  "shareds": ["commons"],
  "isFromCleanProject": true,
  "apps": ["mobile_app"]
}
EOF

mason make flutter_clean_feature -o ./features -c "${CONFIG_FILE}"
rm "${CONFIG_FILE}"
```

## Post-Generation

After running the brick, the feature is generated but not yet integrated. Follow these steps:

1. **Add to pubspec.yaml**: Register feature in host app's dependencies
2. **Run pub get**: Sync dependencies (`melos bootstrap` for monorepos)
3. **Setup routing**: Add feature routes to app router
4. **Configure DI**: Register feature's GetIt module in app's service locator
5. **Build runner**: Generate code (`dart run build_runner build -d`)
6. **Provide BLoCs**: Add feature BLoCs/Cubits to app's BlocProvider list
7. **Test**: Run feature tests and verify app compiles

See SKILL.md for complete integration workflow.

## Troubleshooting

**Error**: `mason make` not found
**Solution**: Install Mason: `dart pub global activate mason_cli`

**Error**: Brick not found
**Solution**: Add brick: `mason add -g flutter_clean_feature --git-url git@github.com:somospragma/pragma-mason-bricks.git --git-path bricks/flutter_clean_feature --git-ref develop`

**Error**: Invalid config file
**Solution**: Ensure JSON is valid and all required variables are present. Run without `-c` flag to see which variables are missing.

**Error**: Output directory doesn't exist
**Solution**: Mason creates the feature directory but not parent folders. Create parent folder manually: `mkdir -p ./features`

## Best Practices

1. **Use a config file**: More reliable than interactive prompts, easier to automate and version control
2. **Match your monorepo structure**: Ensure `packages/` and `shared/` directories exist in your monorepo root before generating features
3. **Keep feature names simple**: Lowercase snake_case, no hyphens, no symbols
4. **Version your configs**: Commit `{featureName}.json` files with your code for traceability
5. **Validate paths after generation**: After creating a feature, check that pubspec.yaml paths correctly reference your monorepo structure
6. **One feature per brick run**: Run the command once per feature rather than trying to batch multiple features
7. **Test the output**: Verify generated structure matches expectations before proceeding with implementation
8. **Update before running build_runner**: Make sure all path dependencies are correct and packages exist, then run `flutter pub get`, then `build_runner`
