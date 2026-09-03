#!/usr/bin/env python3
from pathlib import Path
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "AGENTS.md",
    "_ai/PROJECT.md",
    "_ai/ARCHITECTURE.md",
    "_ai/DECISIONS.md",
    "_ai/TASKS.md",
    "_ai/STATUS.md",
    "_ai/REVIEW.md",
    "_ai/HANDOFF.md",
]

MARKERS = {
    "_ai/PROJECT.md": ["# Project", "## In scope", "## Out of scope", "## Success criteria"],
    "_ai/ARCHITECTURE.md": ["# Architecture", "## Components", "## Security and privacy boundaries"],
    "_ai/TASKS.md": ["# Tasks", "Acceptance criteria", "Validation"],
    "_ai/STATUS.md": ["# Status", "## Current phase", "## Current blockers"],
    "_ai/REVIEW.md": ["# Review", "## Findings"],
    "_ai/HANDOFF.md": ["# Handoff", "## Validation performed", "## Known limitations"],
}

ALLOWED_TASK_STATUSES = {"DRAFT", "READY", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELLED"}
ALLOWED_WORK_TYPES = {"PLAN", "CODE", "RESEARCH", "ARTIFACT", "OPS", "REVIEW"}


def field(body: str, name: str) -> str | None:
    match = re.search(rf"(?m)^- \*\*{re.escape(name)}:\*\*\s+(.+?)\s*$", body)
    if not match:
        return None
    return match.group(1).strip().strip("`")


def task_id_from_title(title: str) -> str:
    return title.split(" — ", 1)[0].strip()


def project_identity_errors(text: str, template_mode: bool) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    project_id = field(text, "Project ID")
    if not project_id:
        return None, ["_ai/PROJECT.md: missing Project ID"]

    if template_mode:
        if project_id != "PXXX" and not re.fullmatch(r"P\d{3,}", project_id):
            errors.append(f"_ai/PROJECT.md: invalid template Project ID {project_id!r}")
    elif not re.fullmatch(r"P\d{3,}", project_id):
        errors.append(
            f"_ai/PROJECT.md: Project ID {project_id!r} is not a real Pxxx ID; replace template placeholders before normal use"
        )

    return project_id, errors


def task_state_errors(text: str, expected_project: str | None) -> list[str]:
    errors: list[str] = []
    sections = re.findall(r"(?ms)^## (TASK-[^\n]+)\n(.*?)(?=^## TASK-|\Z)", text)
    ready_tasks: list[str] = []
    seen_task_ids: set[str] = set()

    for title, body in sections:
        task_id = task_id_from_title(title)
        if task_id in seen_task_ids:
            errors.append(f"_ai/TASKS.md: duplicate task ID {task_id}")
        seen_task_ids.add(task_id)

        status = field(body, "Status")
        if not status:
            errors.append(f"_ai/TASKS.md: {title} is missing a parseable Status")
        elif status not in ALLOWED_TASK_STATUSES:
            errors.append(f"_ai/TASKS.md: {title} has invalid status {status!r}")
        elif status == "READY":
            ready_tasks.append(title)

        project_id = field(body, "Project")
        if not project_id:
            errors.append(f"_ai/TASKS.md: {title} is missing Project")
        elif expected_project and project_id != expected_project:
            errors.append(
                f"_ai/TASKS.md: {title} belongs to {project_id!r}, expected project {expected_project!r}"
            )

        work_type = field(body, "Work type")
        if work_type not in ALLOWED_WORK_TYPES:
            errors.append(f"_ai/TASKS.md: {title} has invalid/missing Work type {work_type!r}")

    if len(ready_tasks) > 1:
        errors.append("_ai/TASKS.md: more than one READY task: " + ", ".join(ready_tasks))
    return errors


def self_test() -> None:
    valid = """# Tasks

## TASK-001 — A
- **Project:** P001
- **Status:** READY
- **Work type:** CODE

## TASK-002 — B
- **Project:** P001
- **Status:** DONE
- **Work type:** REVIEW
"""
    mismatch = valid.replace("- **Project:** P001", "- **Project:** P002", 1)
    bad_work_type = valid.replace("- **Work type:** CODE", "- **Work type:** CODDE", 1)
    duplicate = valid.replace("## TASK-002 — B", "## TASK-001 — B")

    assert not task_state_errors(valid, "P001")
    assert any("expected project" in item for item in task_state_errors(mismatch, "P001"))
    assert any("invalid/missing Work type" in item for item in task_state_errors(bad_work_type, "P001"))
    assert any("duplicate task ID TASK-001" in item for item in task_state_errors(duplicate, "P001"))

    project_template = "# Project\n\n- **Project ID:** PXXX\n"
    project_real = "# Project\n\n- **Project ID:** P001\n"
    assert not project_identity_errors(project_template, template_mode=True)[1]
    assert project_identity_errors(project_template, template_mode=False)[1]
    assert not project_identity_errors(project_real, template_mode=False)[1]


def main() -> int:
    self_test()
    errors: list[str] = []
    template_mode = os.environ.get("AI_TEMPLATE_MODE") == "1"

    for rel in REQUIRED:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required file: {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required file: {rel}")

    for rel, needed in MARKERS.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in needed:
            if marker not in text:
                errors.append(f"{rel}: missing marker {marker!r}")

    expected_project: str | None = None
    project_path = ROOT / "_ai/PROJECT.md"
    if project_path.exists():
        expected_project, project_errors = project_identity_errors(
            project_path.read_text(encoding="utf-8"), template_mode=template_mode
        )
        errors.extend(project_errors)

    tasks_path = ROOT / "_ai/TASKS.md"
    if tasks_path.exists():
        errors.extend(
            task_state_errors(
                tasks_path.read_text(encoding="utf-8"), expected_project=expected_project
            )
        )

    if errors:
        print("AI state check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AI state check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
