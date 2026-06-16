#!/bin/bash
# lint_fix.sh
# Usage: bash scripts/lint_fix.sh [project_path] [--dry-run]
#
# Applies dart fix, formats code, and runs the analyzer.
#
# Flags:
#   --dry-run   Preview changes without modifying any files.
#               Uses `dart fix --dry-run` and `dart format --output show`.
#
# Safety:
#   The script aborts if the git working directory has uncommitted changes,
#   protecting against unintended overwrites of in-progress work.
#   Pass --dry-run to bypass the git check and just preview changes.

set -euo pipefail

DRY_RUN=false
PROJECT="."

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    -*) echo "Unknown flag: $arg" >&2; exit 1 ;;
    *) PROJECT="$arg" ;;
  esac
done

echo "╔══════════════════════════════════════╗"
echo "║     Automatic Lint Fix              ║"
echo "╚══════════════════════════════════════╝"

if [ "$DRY_RUN" = true ]; then
  echo "  ℹ️  DRY-RUN mode — no files will be modified"
fi

cd "$PROJECT" || exit 1

# ── Safety check: abort on uncommitted changes ────────────────────────────────
# Applying dart fix / dart format on a dirty tree can silently overwrite
# intentional, in-progress changes. We skip this check in dry-run mode
# because dry-run never touches files.
if [ "$DRY_RUN" = false ] && git rev-parse --is-inside-work-tree &>/dev/null; then
  if ! git diff --exit-code --quiet || ! git diff --cached --exit-code --quiet; then
    echo ""
    echo "  ❌ Uncommitted changes detected in the working directory."
    echo "     Commit or stash your changes before running lint_fix.sh,"
    echo "     or use --dry-run to preview changes without applying them."
    exit 1
  fi
fi

echo ""
echo "── Step 1: dart fix ─────────────────────────────────"
if [ "$DRY_RUN" = true ]; then
  dart fix --dry-run
  echo "  ℹ️  Dry-run: changes above would be applied by dart fix"
else
  dart fix --apply
  echo "  ✅ dart fix applied"
fi

echo ""
echo "── Step 2: dart format ──────────────────────────────"
if [ "$DRY_RUN" = true ]; then
  # --output show prints the reformatted files to stdout without writing them
  dart format --output show lib/ test/ > /dev/null
  echo "  ℹ️  Dry-run: dart format would reformat the files above"
else
  dart format lib/ test/
  echo "  ✅ dart format applied"
fi

echo ""
echo "── Step 3: flutter analyze ──────────────────────────"
flutter analyze --fatal-infos
ANALYZE_EXIT=$?
if [ $ANALYZE_EXIT -eq 0 ]; then
  echo "  ✅ flutter analyze: no issues"
else
  echo "  ❌ flutter analyze found issues — fix manually"
  exit $ANALYZE_EXIT
fi

echo ""
echo "── Step 4: Check import order ───────────────────────"
IMPORT_ISSUES=$(grep -rn "^import 'dart:" lib/ --include="*.dart" -l | \
  while read -r file; do
    dart_line=$(grep -n "^import 'dart:" "$file" | head -1 | cut -d: -f1)
    pkg_line=$(grep -n "^import 'package:" "$file" | head -1 | cut -d: -f1)
    if [ -n "$dart_line" ] && [ -n "$pkg_line" ] && [ "$pkg_line" -lt "$dart_line" ]; then
      echo "  $file (dart: import after package:)"
    fi
  done)

if [ -n "$IMPORT_ISSUES" ]; then
  echo "  ⚠️  Import order issues (fix manually):"
  echo "$IMPORT_ISSUES"
else
  echo "  ✅ Import order correct"
fi

echo ""
echo "══════════════════════════════════════════"
if [ "$DRY_RUN" = true ]; then
  echo "  ℹ️  Dry-run complete — no files were modified"
else
  echo "  ✅ All automatic fixes applied"
fi
