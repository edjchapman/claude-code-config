#!/usr/bin/env python3
"""
Validate YAML frontmatter in markdown files.

Usage: validate-frontmatter.py <directory> <required_field1> [required_field2] ...

Example:
    validate-frontmatter.py agents name description model
    validate-frontmatter.py skills name description globs
"""

import glob
import sys

import yaml


def validate_directory(directory: str, required_fields: list[str]) -> list[str]:
    """Validate all markdown files in a directory have valid frontmatter."""
    errors = []
    files = glob.glob(f"{directory}/*.md")

    if not files:
        errors.append(f"No .md files found in {directory}/")
        return errors

    for filepath in sorted(files):
        with open(filepath) as f:
            content = f.read()

        if not content.startswith("---"):
            errors.append(f"{filepath}: missing YAML frontmatter")
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            errors.append(f"{filepath}: malformed frontmatter (missing closing ---)")
            continue

        try:
            meta = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            errors.append(f"{filepath}: invalid YAML: {e}")
            continue

        if not isinstance(meta, dict):
            errors.append(f"{filepath}: frontmatter must be a YAML mapping")
            continue

        for field in required_fields:
            if field not in meta:
                errors.append(f'{filepath}: missing required field "{field}"')

        # Type-specific validation
        if "globs" in meta and not isinstance(meta.get("globs"), list):
            errors.append(f"{filepath}: globs must be a list")

        if "model" in meta and meta.get("model") not in ("opus", "sonnet", "haiku"):
            errors.append(f'{filepath}: model must be "opus", "sonnet", or "haiku"')

    return errors


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    directory = sys.argv[1]
    required_fields = sys.argv[2:]

    errors = validate_directory(directory, required_fields)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
    else:
        files = glob.glob(f"{directory}/*.md")
        print(f"All {len(files)} files in {directory}/ valid")


if __name__ == "__main__":
    main()
