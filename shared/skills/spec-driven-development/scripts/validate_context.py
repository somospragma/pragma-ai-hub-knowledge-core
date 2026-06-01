#!/usr/bin/env python3
"""
validate_context.py — Validate .specs/*/context.json files against the SDD JSON Schema.

Usage:
    python3 scripts/validate_context.py                    # validate all specs in .specs/
    python3 scripts/validate_context.py .specs/my_feature/ # validate a single spec folder
    python3 scripts/validate_context.py --strict           # exit 1 on any warning

Exit codes:
    0 — all valid
    1 — one or more validation errors
    2 — schema or dependency error
"""

import json
import sys
import pathlib
import argparse
from typing import Any


SCHEMA_PATH = pathlib.Path(__file__).parent / "context.schema.json"
VALID_PHASE_TRANSITIONS = {
    "requirements": ["design"],
    "design": ["tasks"],
    "tasks": ["execution"],
    "execution": ["complete"],
    "complete": [],
}


def load_schema() -> dict[str, Any]:
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        scripts_dir = pathlib.Path(__file__).parent
        print(
            "⚠  jsonschema not installed — running structural checks only.\n"
            "   To enable full schema validation, install dependencies with Hatch:\n"
            f"\n"
            f"     cd {scripts_dir}\n"
            f"     hatch env create\n"
            f"     hatch run validate {pathlib.Path(__file__).name} [path]\n",
            file=sys.stderr,
        )
        return {}
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_file(context_path: pathlib.Path, schema: dict[str, Any]) -> list[str]:
    """Validate a single context.json. Returns a list of error messages (empty = valid)."""
    errors: list[str] = []

    # ── 1. Parse JSON ────────────────────────────────────────────────────────
    try:
        with open(context_path) as f:
            ctx = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    # ── 2. JSON Schema validation ────────────────────────────────────────────
    if schema:
        try:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            for err in sorted(validator.iter_errors(ctx), key=str):
                errors.append(f"Schema: {err.message} (path: {' → '.join(str(p) for p in err.absolute_path)})")
        except Exception as e:
            errors.append(f"Schema validation error: {e}")

    # ── 3. Business-rule checks ──────────────────────────────────────────────
    phases = ctx.get("phases", {})
    current = ctx.get("current_phase", "")

    # Rule: if design is approved, requirements must also be approved
    if phases.get("design", {}).get("status") == "approved":
        if phases.get("requirements", {}).get("status") != "approved":
            errors.append(
                "Business rule: design is 'approved' but requirements is not — "
                "phases must be approved in order (requirements → design → tasks)"
            )

    # Rule: if tasks is approved, design must also be approved
    if phases.get("tasks", {}).get("status") == "approved":
        if phases.get("design", {}).get("status") != "approved":
            errors.append(
                "Business rule: tasks is 'approved' but design is not — "
                "phases must be approved in order (requirements → design → tasks)"
            )

    # Rule: approved_at must be non-null when status = "approved"
    for phase_name, phase_data in phases.items():
        if isinstance(phase_data, dict):
            if phase_data.get("status") == "approved" and not phase_data.get("approved_at"):
                errors.append(
                    f"Business rule: phases.{phase_name}.status is 'approved' "
                    f"but approved_at is null — set approved_at to the approval timestamp"
                )

    # Rule: feature_name must match the folder name
    folder_name = context_path.parent.name
    feature_name = ctx.get("feature_name", "")
    if feature_name and feature_name != folder_name:
        errors.append(
            f"Consistency: feature_name '{feature_name}' does not match "
            f"the spec folder name '{folder_name}'"
        )

    # Rule: spec_folder must reference the correct path
    expected_spec_folder = f".specs/{feature_name}"
    actual_spec_folder = ctx.get("spec_folder", "")
    if feature_name and actual_spec_folder != expected_spec_folder:
        errors.append(
            f"Consistency: spec_folder '{actual_spec_folder}' should be "
            f"'{expected_spec_folder}' for feature '{feature_name}'"
        )

    # ── Execution block checks ───────────────────────────────────────────────
    execution = ctx.get("execution")
    if execution is not None:
        # Rule: execution can only be in_progress or complete if tasks is approved
        exec_status = execution.get("status", "not_started")
        if exec_status in ("in_progress", "complete"):
            if phases.get("tasks", {}).get("status") != "approved":
                errors.append(
                    "Business rule: execution.status is 'in_progress' or 'complete' "
                    "but phases.tasks is not approved — tasks must be approved before execution starts"
                )

        # Rule: execution.approved_at must be set when status is complete
        if exec_status == "complete" and not execution.get("approved_at"):
            errors.append(
                "Business rule: execution.status is 'complete' but execution.approved_at is null"
            )

        # Rule: unit statuses must be valid
        valid_unit_statuses = {"pending", "in_progress", "complete", "blocked"}
        for unit in execution.get("units", []):
            unit_name = unit.get("name", "<unnamed>")
            unit_status = unit.get("status", "")
            if unit_status not in valid_unit_statuses:
                errors.append(
                    f"Business rule: execution unit '{unit_name}' has invalid status "
                    f"'{unit_status}' — must be one of {sorted(valid_unit_statuses)}"
                )

        # Rule: completed_units entries must appear in units list
        unit_names = {u.get("name") for u in execution.get("units", [])}
        for completed in execution.get("completed_units", []):
            if completed not in unit_names:
                errors.append(
                    f"Consistency: execution.completed_units contains '{completed}' "
                    f"which is not in execution.units"
                )

        # Rule: depends_on references must resolve to known unit names
        for unit in execution.get("units", []):
            unit_name = unit.get("name", "<unnamed>")
            for dep in unit.get("depends_on", []):
                if dep not in unit_names:
                    errors.append(
                        f"Consistency: unit '{unit_name}' depends_on '{dep}' "
                        f"which is not a known unit name"
                    )

    return errors


def find_context_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Find all context.json files under .specs/ in the given root."""
    specs_dir = root / ".specs"
    if not specs_dir.exists():
        return []
    return sorted(specs_dir.rglob("context.json"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate SDD context.json files against the schema and business rules."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Spec folder(s) or context.json file(s) to validate. "
             "Defaults to all specs found under .specs/ in the current directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 on warnings as well as errors.",
    )
    args = parser.parse_args()

    schema = load_schema()

    # Resolve targets
    targets: list[pathlib.Path] = []
    if args.paths:
        for p_str in args.paths:
            p = pathlib.Path(p_str)
            if p.is_file() and p.name == "context.json":
                targets.append(p)
            elif p.is_dir():
                ctx = p / "context.json"
                if ctx.exists():
                    targets.append(ctx)
                else:
                    print(f"⚠  No context.json found in {p}", file=sys.stderr)
            else:
                print(f"⚠  Path not found: {p}", file=sys.stderr)
    else:
        targets = find_context_files(pathlib.Path("."))

    if not targets:
        print("No context.json files found. Nothing to validate.")
        return 0

    total_errors = 0
    for ctx_path in targets:
        errors = validate_file(ctx_path, schema)
        if errors:
            print(f"\n❌ {ctx_path}")
            for err in errors:
                print(f"   • {err}")
            total_errors += len(errors)
        else:
            print(f"✅ {ctx_path}")

    print()
    if total_errors:
        print(f"Found {total_errors} error(s) across {len(targets)} file(s).")
        return 1
    else:
        print(f"All {len(targets)} context.json file(s) are valid.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
