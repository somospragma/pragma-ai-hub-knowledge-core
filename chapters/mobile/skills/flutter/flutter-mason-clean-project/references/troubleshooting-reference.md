# Troubleshooting Reference

Common issues during `flutter_clean_project` generation with diagnosis and resolution steps.

## Table of Contents

1. [Mason Brick Not Found](#mason-brick-not-found)
2. [Flutter Create Failed](#flutter-create-failed)
3. [Melos Bootstrap Timeout](#melos-bootstrap-timeout)
4. [Bundle ID Generation Failed](#bundle-id-generation-failed)
5. [Configuration File Not Found](#configuration-file-not-found)
6. [Git Initialization Failed](#git-initialization-failed)
7. [UI Kit Generation Error](#ui-kit-generation-error)

---

## Mason Brick Not Found

**Symptom**: Error message like "Brick not found" or "brick_name does not exist"

**Likely Cause**: Mason brick not installed globally or installation incomplete.

### Diagnosis

```bash
# Check if flutter_clean_project is installed
mason list --global

# Look for "flutter_clean_project" in the output
# If not present, proceed to Fix
```

### Fix

**Option 1: Install from Git**
```bash
# Install from repository
mason add -g flutter_clean_project --git-url git@github.com:somospragma/pragma-mason-bricks.git --git-path bricks/flutter_clean_project --git-ref develop

# Then verify
mason list --global | grep flutter_clean_project
```

**Option 2: Install from registry (if published)**
```bash
mason add -g flutter_clean_project
```

**Option 3: Direct make without global install (alternative)**
```bash
# Use explicit path to brick
cd /path/to/workspace
mason make flutter_clean_project -o output \
  --brick-path /path/to/pragma-mason-brick/bricks/flutter_clean_project
# Note: This syntax depends on Mason version; verify docs
```

---

## Flutter Create Failed

**Symptom**: Post-gen hook fails with "flutter create failed" or "Flutter SDK not found"

**Error output**: `Command 'flutter create' not found` or exit code non-zero

**Likely Causes**:
- Flutter SDK not in system PATH
- Flutter environment corrupted
- No disk space in output directory

### Diagnosis

```bash
# Check Flutter is installed and in PATH
flutter --version
flutter doctor

# Expected output: Flutter v3.x.x, Dart v3.x.x
# If not found, Flutter is not installed or not in PATH

# Check disk space
df -h /path/to/output/directory
# Ensure at least 2GB free
```

### Fix

**Option 1: Add Flutter to PATH (macOS/Linux)**
```bash
# Find Flutter installation
which flutter
# or
find ~ -name "flutter" -type d 2>/dev/null

# Export PATH in ~/.zprofile or ~/.bash_profile
export PATH="$PATH:/path/to/flutter/bin"
source ~/.zprofile

# Verify
flutter --version
```

**Option 2: Reinstall Flutter (if SDK corrupted)**
```bash
# Follow Flutter docs: https://docs.flutter.dev/get-started/install
# After reinstall, verify with flutter doctor

flutter pub get
flutter pub upgrade
```

**Option 3: Clean and retry**
```bash
# Remove partial generation
rm -rf /path/to/output/my_app

# Try generation again with shorter path (fewer chars)
mason make flutter_clean_project -o ./output
```

---

## Melos Bootstrap Timeout

**Symptom**: Post-gen hook stalls at `melos bootstrap` for >5 minutes, then fails

**Likely Causes**:
- Large dependency tree causing slow download
- Network connectivity issue
- Melos not installed
- Pub cache corruption

### Diagnosis

```bash
# Check Melos is installed
melos --version
# Expected: v4.x.x or later

# Check pub cache
dart pub cache info
# Review "git cache" entries; large cache may slow operations

# Test network connectivity
ping pub.dev
# Should respond
```

### Fix

**Option 1: Install/Update Melos**
```bash
dart pub global activate melos
melos --version
```

**Option 2: Clear pub cache and retry**
```bash
# Clean pub cache (⚠️ will re-download packages)
dart pub cache clean
dart pub pub cache clean

# Retry generation
mason make flutter_clean_project -o output -c config.json
```

**Option 3: Manual bootstrap (skip auto hook)**
```bash
# If generation partially completed, navigate to project
cd output/my_app

# Run melos bootstrap manually with verbose output
melos bootstrap --verbose

# Monitor progress; may take 3-5 minutes
```

**Option 4: Use pub get instead (temporary workaround)**
```bash
# Navigate to each package directory
cd output/apps/my_app && flutter pub get
cd output/packages/commons && dart pub get
cd output/packages/my_app_ui_kit && dart pub get
cd output/shared/l10n && dart pub get

# Then run global melos (if installed)
cd output && melos bootstrap
```

---

## Bundle ID Generation Failed

**Symptom**: Bundle ID manually configured or skipped message; iOS/Android identifiers not updated

**Error message**: "Bundle id and App name not updated!" or rename command not found

**Likely Cause**: `rename` package not globally installed (this is optional)

### Diagnosis

```bash
# Check if rename is installed
rename --version
# If not found, proceed to Fix
```

### Fix

**Option 1: Install rename tool (recommended)**
```bash
dart pub global activate rename

# Verify
rename --version
```

**Option 2: Manual bundle ID configuration (if rename unavailable)**

After generation completes, manually update bundle IDs:

**iOS** (`ios/Runner.xcodeproj/project.pbxproj`):
```bash
cd apps/my_app/ios

# Use Xcode or sed/awk to replace bundle ID
# Example (macOS/Linux):
sed -i '' 's/com\.example\.myApp/com\.mycompany\.myapp/g' Runner.xcodeproj/project.pbxproj
```

**Android** (`android/app/build.gradle`):
```bash
cd apps/my_app/android/app

# Edit build.gradle and update applicationId
# Old: applicationId "com.example.my_app"
# New: applicationId "com.mycompany.my_app"

# For iOS:
cd ../../../ios
# Edit ios/Runner/Info.plist or use Xcode GUI
```

**Option 3: Ignore (for development only)**
- Generated apps will run on emulator/simulator with default IDs
- For production release, update IDs via Xcode and Android Studio before building

---

## Configuration File Not Found

**Symptom**: Error "config.json not found" or "File does not exist"

**Likely Cause**: Incorrect path to configuration file in mason command

### Diagnosis

```bash
# Verify config file exists
ls -la /path/to/config.json

# Check file is valid JSON
cat /path/to/config.json | jq . > /dev/null
# If error, JSON is malformed
```

### Fix

**Option 1: Correct file path**
```bash
# Use absolute path
mason make flutter_clean_project -o output -c /Users/me/projects/config.json

# Or relative to current directory
mason make flutter_clean_project -o output -c ./config.json
```

**Option 2: Create config from example**
```bash
# Copy example from brick
cp /path/to/pragma-mason-brick/bricks/flutter_clean_project/config-example.json my_config.json

# Edit my_config.json with your values
# Then use it
mason make flutter_clean_project -o output -c my_config.json
```

**Option 3: Validate JSON syntax**
```bash
# Use jq to validate and pretty-print
cat my_config.json | jq . | less

# If error, fix JSON (missing commas, quotes, etc.)
```

---

## Git Initialization Failed

**Symptom**: Post-gen hook fails at "git init" step; Git not found or repository creation fails

**Error message**: "Command not found: git" or "Failed to initialize git repository"

**Likely Cause**: Git not installed or not in PATH

### Diagnosis

```bash
# Check Git is installed
git --version
# Expected: git version 2.x.x or later

# Check if directory is already a git repo
cd /path/to/output && git status
# If success, repo already exists (no error)
```

### Fix

**Option 1: Install Git (if not present)**
```bash
# macOS (Homebrew)
brew install git

# Linux (Ubuntu/Debian)
sudo apt-get install git

# Windows
# Download from https://git-scm.com/download/win

# Verify
git --version
```

**Option 2: Manual git init (if auto hook failed)**
```bash
# Navigate to generated project
cd /path/to/output

# Initialize manually
git init
git branch -m master
# (renames initial branch to 'master' if on 'main')

# Add and commit initial structure
git add .
git commit -m "chore: initial commit"
```

**Option 3: Skip git for now**
- Git initialization is optional; generation succeeds without it
- Initialize manually later: `git init` in project root

---

## UI Kit Generation Error

**Symptom**: Post-gen hook fails at "Generate UI Kit brick" stage; wrong colors/fonts/typography in generated UI Kit

**Error output**: "Failed to generate UI Kit" or similar

**Likely Cause**: Configuration errors in colors/typography (invalid hex, missing font family, etc.)

### Diagnosis

```bash
# Validate JSON schema
jq . my_config.json > /dev/null

# Check color hex values (must be 6 chars, no #)
jq '.colors[].defaultColor' my_config.json
# Example output: "0b92d5" (correct)

# Check fontFamily exist in Google Fonts
jq '.fontFamily' my_config.json
# Verify names match: "Roboto", "Inter", "Poppins", etc.

# Check typography references existing fonts
jq '.typography[].fontFamily' my_config.json
# Ensure each exists in fontFamily array
```

### Fix

**Option 1: Fix configuration JSON**
```javascript
// Error: invalid hex (too short)
{ "defaultColor": "0b92" }  // ❌ 4 chars
{ "defaultColor": "0b92d5" } // ✅ 6 chars

// Error: font not in array
{
  "fontFamily": ["Roboto"],
  "typography": [
    { "fontFamily": "Inter" } // ❌ Not in fontFamily array
  ]
}

// Fix: add font to array
{
  "fontFamily": ["Roboto", "Inter"],
  "typography": [
    { "fontFamily": "Inter" } // ✅ Now in array
  ]
}
```

**Option 2: Use config-example.json defaults**
```bash
# Copy unmodified example
cp /path/to/brick/config-example.json my_config.json

# Run generation (colors/fonts/typography are valid)
mason make flutter_clean_project -o output -c my_config.json

# Then edit generated files post-gen to customize
```

---

## Other Issues

### Issue: "FileSystemException: File already exists"
- Output directory already contains a project
- **Fix**: Use different output path or remove existing directory:
```bash
rm -rf /path/to/output/my_app
mason make flutter_clean_project -o /path/to/output
```

### Issue: "Cannot find module: commons"
- Dependencies not installed yet
- **Fix**: Wait for melos bootstrap to complete; if stuck, run manually:
```bash
cd output && melos bootstrap --verbose
```

### Issue: "Dart fix failed" or formatting errors
- Post-gen lint/format failed; code has analyzer errors
- **Fix**: Navigate to project and run manually:
```bash
cd output && dart format . --fix && dart fix --apply
```

---

## Getting Help

If issue persist after these steps:

1. **Check logs**: Mason often outputs detailed error messages to terminal; capture full output
2. **Verify environment**: Ensure Flutter, Dart, Melos, and Mason versions match requirements
3. **Inspect generated files**: Navigate to output directory and check:
   - `pubspec.yaml` in each app/package for dependency issues
   - `lib/` structure for file generation issues
4. **Test manual commands**: Try running `flutter pub get` and `melos bootstrap` manually to isolate the issue
