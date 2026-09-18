#!/usr/bin/env python3
"""
Spec-Driven Development CLI Tool
Manages master specs, feature scaffolding, ADRs, tasks, and status tracking.
"""

import os
import sys
import argparse
import datetime
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

def read_template(filename: str) -> str:
    template_path = TEMPLATES_DIR / filename
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def cmd_init(project_name: str, root_dir: Path):
    """Initializes specs/ and features/ in the project root."""
    specs_dir = root_dir / "specs"
    features_dir = root_dir / "features"

    specs_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()

    # 1. Create specs/main-spec.md if not exists
    main_spec = specs_dir / "main-spec.md"
    if not main_spec.exists():
        content = read_template("main-spec.template.md")
        content = content.replace("{{PROJECT_NAME}}", project_name)
        content = content.replace("{{DATE}}", today)
        content = content.replace("{{REPO_ROOT}}", str(root_dir))
        with open(main_spec, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {main_spec}")
    else:
        print(f"Main spec already exists: {main_spec}")

    # 2. Create features/README.md if not exists
    feat_readme = features_dir / "README.md"
    if not feat_readme.exists():
        content = (
            f"# Feature Registry Dashboard: {project_name}\n\n"
            f"> **Last Updated:** {today}\n\n"
            "This directory contains all individual feature modules. Each feature folder follows the standard lifecycle:\n"
            "- `spec.md`: Functional scope, user stories, contracts\n"
            "- `design.md`: HLD diagrams and Architecture Decision Records (ADRs)\n"
            "- `tasks.md`: Phased execution checklist and current status\n"
            "- `testing.md`: Test cases, automated tests, and acceptance criteria\n\n"
            "## Active & Registered Features\n\n"
            "| Feature ID | Feature Title | Status | Primary Action Needed | Directory Link |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
        )
        with open(feat_readme, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {feat_readme}")
    else:
        print(f"Features README already exists: {feat_readme}")

def cmd_new_feature(feature_id: str, feature_title: str, root_dir: Path):
    """Scaffolds a new feature folder with spec, design, tasks, and testing files."""
    features_dir = root_dir / "features"
    feat_dir = features_dir / feature_id

    if feat_dir.exists():
        print(f"Error: Feature directory already exists: {feat_dir}")
        sys.exit(1)

    feat_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    replacements = {
        "{{FEATURE_ID}}": feature_id,
        "{{FEATURE_NAME}}": feature_title,
        "{{DATE}}": today
    }

    files = [
        ("spec.template.md", feat_dir / "spec.md"),
        ("design.template.md", feat_dir / "design.md"),
        ("tasks.template.md", feat_dir / "tasks.md"),
        ("testing.template.md", feat_dir / "testing.md")
    ]

    for tpl_name, target_path in files:
        content = read_template(tpl_name)
        for k, v in replacements.items():
            content = content.replace(k, v)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {target_path}")

    # Register in features/README.md
    feat_readme = features_dir / "README.md"
    if feat_readme.exists():
        row = f"| `{feature_id}` | {feature_title} | `PROPOSED` | Review ADRs & Design | [{feature_id}](./{feature_id}/spec.md) |\n"
        with open(feat_readme, "a", encoding="utf-8") as f:
            f.write(row)
        print(f"Registered in {feat_readme}")

    # Register in specs/main-spec.md if table present
    main_spec = root_dir / "specs" / "main-spec.md"
    if main_spec.exists():
        with open(main_spec, "r", encoding="utf-8") as f:
            main_content = f.read()
        row = f"| `{feature_id}` | {feature_title} | Team | `PROPOSED` | TBD | [{feature_id}](../features/{feature_id}/spec.md) |\n"
        if "## 4. Master Feature Registry" in main_content:
            parts = main_content.split("## 4. Master Feature Registry")
            after_header = parts[1]
            if "| Feature ID |" in after_header:
                table_split = after_header.split("\n\n", 1)
                new_table = table_split[0] + "\n" + row
                main_content = parts[0] + "## 4. Master Feature Registry" + new_table + "\n\n" + (table_split[1] if len(table_split) > 1 else "")
                with open(main_spec, "w", encoding="utf-8") as f:
                    f.write(main_content)
                print(f"Registered in {main_spec}")

    print(f"\nFeature '{feature_id} - {feature_title}' created successfully!")
    print(f"Next step: Define ADRs in {feat_dir / 'design.md'} and review with user.")

def cmd_status(root_dir: Path):
    """Scans all features and outputs summary table."""
    features_dir = root_dir / "features"
    if not features_dir.exists():
        print("No 'features/' directory found in project.")
        return

    print("\n=== Feature Lifecycle Status Dashboard ===")
    print(f"{'Feature ID':<20} | {'Status':<15} | {'Next Action / Focus'}")
    print("-" * 75)

    subdirs = sorted([d for d in features_dir.iterdir() if d.is_dir()])
    if not subdirs:
        print("No features registered yet.")
        return

    for d in subdirs:
        tasks_file = d / "tasks.md"
        status = "UNKNOWN"
        action = "None specified"
        if tasks_file.exists():
            with open(tasks_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "**Status:**" in line:
                        status = line.split("**Status:**")[1].strip().split()[0]
                    if "**Current Focus / Next Action:**" in line:
                        action = line.split("**Current Focus / Next Action:**")[1].strip()
        print(f"{d.name:<20} | {status:<15} | {action}")

def main():
    parser = argparse.ArgumentParser(description="Spec-Driven Development CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_p = subparsers.add_parser("init", help="Initialize specs and features structure")
    init_p.add_argument("--name", default="My Project", help="Project name")
    init_p.add_argument("--path", default=".", help="Project root directory")

    new_p = subparsers.add_parser("new-feature", help="Scaffold a new feature")
    new_p.add_argument("feature_id", help="Feature ID (e.g., FEAT-001)")
    new_p.add_argument("feature_title", help="Feature Title (e.g., 'User Authentication')")
    new_p.add_argument("--path", default=".", help="Project root directory")

    status_p = subparsers.add_parser("status", help="Show all feature statuses")
    status_p.add_argument("--path", default=".", help="Project root directory")

    args = parser.parse_args()
    root_dir = Path(getattr(args, "path", ".")).resolve()

    if args.command == "init":
        cmd_init(args.name, root_dir)
    elif args.command == "new-feature":
        cmd_new_feature(args.feature_id, args.feature_title, root_dir)
    elif args.command == "status":
        cmd_status(root_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
