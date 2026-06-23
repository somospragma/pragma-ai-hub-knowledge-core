# Configuration Schema Reference

## Overview

The `flutter_clean_project` brick is configured via a JSON file containing:
- Project metadata (organization, name, prefix)
- Design tokens (colors, typography, fonts)
- Optional features list

This reference documents the complete schema with examples and validation rules.

## JSON Schema

### Root Level

```javascript
{
  "organization": "string",        // Required: org name
  "name": "string",                // Required: app name
  "prefix": "string",              // Required: file prefix
  "colors": [...],                 // Required: color definitions
  "fontFamily": [...],             // Required: Google Fonts list
  "typography": [...],             // Required: typography definitions
  "features": [...]                // Optional: initial features to generate
}
```

---

## Properties

### organization

**Type**: `string`  
**Required**: Yes  
**Description**: Organization or company name used for bundle ID generation.

**Rules**:
- Lowercase, no spaces
- Used in: `com.{organization}.{name}`
- Examples: `mycompany`, `pragmatech`, `startupai`

**Example**:
```json
{
  "organization": "mycompany"
  // Result: com.mycompany.myapp
}
```

---

### name

**Type**: `string`  
**Required**: Yes  
**Description**: Application name. Becomes project directory and workspace name.

**Rules**:
- Lowercase or camelCase
- No special characters (alphanumeric only)
- **Security**: Avoid using path traversal sequences like `../` or absolute paths to prevent writing files outside the intended directory.
- Becomes directory: `apps/{name}/`
- Template transforms: `.snakeCase()`, `.titleCase()`, `.pascalCase()`

**Example**:
```json
{
  "name": "mobileApp"
  // Result directory: apps/mobile_app/
  // Used in bundle: com.mycompany.mobile_app
}
```

---

### prefix

**Type**: `string`  
**Required**: Yes  
**Description**: Prefix for generated file and class names.

**Rules**:
- Lowercase, short (2–5 chars recommended)
- **Security**: Ensure the prefix contains only alphanumeric characters to prevent directory traversal or malicious file naming.
- Becomes file prefix: `app_colors.dart`
- Becomes class prefix: `AppColors`
- Transforms: `.pascalCase()` for class names

**Example**:
```json
{
  "prefix": "app"
  // Files: app_radius.dart, app_colors.dart
  // Classes: AppRadius, AppColors, AppSpacing
}
```

---

## colors

**Type**: `array<ColorObject>`  
**Required**: Yes  
**Min items**: 1  
**Description**: Design system color palette. Each color becomes a Material color with shade levels.

### ColorObject Schema

```javascript
{
  "name": "string",                // Color identifier
  "isMaterialColor": boolean,      // Always true for Material Design
  "defaultColor": "string",        // Hex without # (base color)
  "value": [                       // Shade levels array
    {
      "level": number,             // 50, 100, 200, ..., 900
      "value": "string"            // Hex without #
    }
  ]
}
```

### ColorObject Rules

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | Yes | Lowercase, no spaces (e.g., `primary`, `secondary`, `brand`) |
| `isMaterialColor` | boolean | Yes | Always `true` |
| `defaultColor` | string | Yes | Hex 6 chars (e.g., `0b92d5`), no `#` prefix |
| `value` | array | Yes | Min 1 shade, typically 50–900 in 50/100 increments |
| `value[].level` | number | Yes | 50, 100, 200, 300, 400, 500, 600, 700, 800, 900 |
| `value[].value` | string | Yes | Hex 6 chars (e.g., `f1f9fe`), no `#` prefix |

### Complete Color Example

```json
{
  "colors": [
    {
      "name": "primary",
      "isMaterialColor": true,
      "defaultColor": "0b92d5",
      "value": [
        { "level": 50, "value": "f1f9fe" },
        { "level": 100, "value": "e3f2fd" },
        { "level": 200, "value": "bbdefb" },
        { "level": 300, "value": "90caf9" },
        { "level": 400, "value": "64b5f6" },
        { "level": 500, "value": "2196f3" },
        { "level": 600, "value": "1e88e5" },
        { "level": 700, "value": "1976d2" },
        { "level": 800, "value": "1565c0" },
        { "level": 900, "value": "0d47a1" }
      ]
    }
  ]
  // Result: AppColors.primary50, AppColors.primary500, AppColors.primary900, etc.
}
```

---

## fontFamily

**Type**: `array<string>`  
**Required**: Yes  
**Min items**: 1  
**Description**: Google Fonts names to be supported by the project.

**Rules**:
- Exact names from [Google Fonts](https://fonts.google.com/)
- Comma-separated list or JSON array
- Examples: `Roboto`, `Source Sans 3`, `Inter`, `Poppins`

**Example**:
```json
{
  "fontFamily": [
    "Roboto",
    "Source Sans 3",
    "Inter"
  ]
}
```

---

## typography

**Type**: `array<TypographyObject>`  
**Required**: Yes  
**Min items**: 1  
**Description**: Text styles (label, body, heading, etc.) with font families and parameters.

### TypographyObject Schema

```javascript
{
  "name": "string",                // Style identifier
  "fontFamily": "string",          // Must exist in fontFamily array
  "fontSize": number,              // Font size in pixels (optional)
  "parameters": [                  // Function parameters for this style
    {
      "type": "string",            // Dart type (Color?, FontWeight, etc.)
      "name": "string",            // Parameter name
      "default": "string"          // Default value (optional)
    }
  ]
}
```

### TypographyObject Rules

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | Yes | Lowercase, no spaces (e.g., `label`, `body`, `heading`) |
| `fontFamily` | string | Yes | Must match entry in `fontFamily` array |
| `fontSize` | number | No | Pixels (e.g., 12, 16, 24) |
| `parameters` | array | Yes | Array of parameter definitions |
| `parameters[].type` | string | Yes | Dart type (e.g., `Color?`, `FontWeight`, `TextDecoration?`) |
| `parameters[].name` | string | Yes | camelCase (e.g., `color`, `fontWeight`, `decoration`) |
| `parameters[].default` | string | No | Default value expression (e.g., `FontWeight.w400`) |

### Complete Typography Example

```json
{
  "typography": [
    {
      "name": "label",
      "fontFamily": "Roboto",
      "fontSize": 12,
      "parameters": [
        {
          "type": "Color?",
          "name": "color"
        },
        {
          "type": "FontWeight",
          "name": "fontWeight",
          "default": "FontWeight.w100"
        },
        {
          "type": "TextDecoration?",
          "name": "decoration"
        }
      ]
    },
    {
      "name": "body",
      "fontFamily": "Source Sans 3",
      "fontSize": 16,
      "parameters": [
        {
          "type": "Color?",
          "name": "color"
        },
        {
          "type": "FontWeight",
          "name": "fontWeight",
          "default": "FontWeight.w400"
        }
      ]
    },
    {
      "name": "heading",
      "fontFamily": "Inter",
      "fontSize": 24,
      "parameters": [
        {
          "type": "Color?",
          "name": "color"
        },
        {
          "type": "FontWeight",
          "name": "fontWeight",
          "default": "FontWeight.w700"
        }
      ]
    }
  ]
  // Result: AppTypography.label(), AppTypography.body(), AppTypography.heading()
}
```

---

## features (Optional)

**Type**: `array<FeatureObject>`  
**Required**: No  
**Default**: `[]`  
**Description**: Initial features to generate during post-gen hook via `flutter_clean_feature` brick.

### FeatureObject Schema

```javascript
{
  "name": "string",                // Feature identifier
  "packages": ["string"],          // Package dependencies
  "shareds": ["string"],           // Shared resources (l10n, etc.)
  "isFromCleanProject": boolean    // Internal flag (always true)
}
```

### FeatureObject Rules

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | Yes | Lowercase, no spaces (e.g., `home`, `authentication`, `settings`) |
| `packages` | array | Yes | Usually `["commons"]`; auto-injected as dependency |
| `shareds` | array | Yes | Usually `["l10n"]` for localization |
| `isFromCleanProject` | boolean | Yes | Always `true` |

### Features Example

```json
{
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
    },
    {
      "name": "profile",
      "packages": ["commons"],
      "shareds": ["l10n"],
      "isFromCleanProject": true
    }
  ]
  // Result: features/authentication/, features/home/, features/profile/
  // Each with domain/, data/, presentation/ layers
}
```

---

## Complete Example Configuration

```json
{
  "organization": "techstartup",
  "name": "mobileApp",
  "prefix": "app",
  "colors": [
    {
      "name": "primary",
      "isMaterialColor": true,
      "defaultColor": "0b92d5",
      "value": [
        { "level": 50, "value": "f1f9fe" },
        { "level": 100, "value": "e3f2fd" },
        { "level": 500, "value": "2196f3" },
        { "level": 900, "value": "0d47a1" }
      ]
    },
    {
      "name": "secondary",
      "isMaterialColor": true,
      "defaultColor": "8f7de8",
      "value": [
        { "level": 50, "value": "f5f4fe" },
        { "level": 100, "value": "ecebfc" },
        { "level": 500, "value": "7c3aed" },
        { "level": 900, "value": "4c1d95" }
      ]
    }
  ],
  "fontFamily": ["Inter", "Roboto"],
  "typography": [
    {
      "name": "label",
      "fontFamily": "Roboto",
      "fontSize": 12,
      "parameters": [
        { "type": "Color?", "name": "color" },
        { "type": "FontWeight", "name": "fontWeight", "default": "FontWeight.w500" }
      ]
    },
    {
      "name": "body",
      "fontFamily": "Inter",
      "fontSize": 16,
      "parameters": [
        { "type": "Color?", "name": "color" },
        { "type": "FontWeight", "name": "fontWeight", "default": "FontWeight.w400" }
      ]
    }
  ],
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

---

## Validation Rules

### Required Fields
- `organization`, `name`, `prefix` must be non-empty strings
- `colors`, `fontFamily`, `typography` cannot be empty arrays
- Color hex values must be 6 characters (e.g., `f1f9fe`)

### Constraints
- Font families must match Google Fonts (case-sensitive)
- Color levels should use standard Material Design increments (50, 100, ..., 900)
- Feature names must be unique within the array

### Casing
- Use lowercase + underscores for all names (organization, name, color name, feature name)
- Exception: `fontFamily` values match Google Fonts exactly (may include spaces: "Source Sans 3")
