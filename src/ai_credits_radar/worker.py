"""Bounded AI worker that produces artifacts only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .gateway import GatewaySafetyError, invoke_free_only

MAX_CONTEXT_FILES = 8
MAX_CONTEXT_CHARS = 40000
MAX_TASK_TEXT_CHARS = 8000
ALLOWED_CONTEXT_SUFFIXES = {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".txt", ".css", ".js", ".html"}


def load_worker_task(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        task = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"worker task not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid worker task JSON in {source}: {exc}") from exc
    errors = validate_worker_task(task)
    if errors:
        raise ValueError("invalid worker task: " + "; ".join(errors))
    return task


def validate_worker_task(task: Any) -> list[str]:
    if not isinstance(task, dict):
        return ["worker task must be a JSON object"]
    errors: list[str] = []
    for field in ("project", "task_id", "goal", "context_files"):
        if field not in task:
            errors.append(f"missing {field!r}")
    if task.get("project") != "P001":
        errors.append("project must be P001")
    for field in ("task_id", "goal"):
        if not isinstance(task.get(field), str) or not task.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")
    goal = task.get("goal")
    if isinstance(goal, str) and len(goal) > MAX_TASK_TEXT_CHARS:
        errors.append(f"goal exceeds {MAX_TASK_TEXT_CHARS} characters")
    instructions = task.get("instructions", "")
    if not isinstance(instructions, str):
        errors.append("instructions must be a string")
    elif len(instructions) > MAX_TASK_TEXT_CHARS:
        errors.append(f"instructions exceeds {MAX_TASK_TEXT_CHARS} characters")
    context = task.get("context_files")
    if not isinstance(context, list) or not all(isinstance(item, str) and item.strip() for item in context):
        errors.append("context_files must be a list of non-empty strings")
    elif len(context) > MAX_CONTEXT_FILES:
        errors.append(f"context_files may contain at most {MAX_CONTEXT_FILES} files")
    max_output = task.get("max_output_tokens", 800)
    if not isinstance(max_output, int) or isinstance(max_output, bool) or not 1 <= max_output <= 2048:
        errors.append("max_output_tokens must be an integer from 1 to 2048")
    tier = task.get("tier", "A")
    if tier not in {"B", "A", "S"}:
        errors.append("tier must be B, A, or S")
    return errors


def _safe_context_path(repo_root: Path, relative: str) -> Path:
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        raise ValueError(f"unsafe context path: {relative!r}")
    if requested.suffix.casefold() not in ALLOWED_CONTEXT_SUFFIXES:
        raise ValueError(f"unsupported context file type: {relative!r}")
    root = repo_root.resolve()
    target = (root / requested).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"context path escapes repository root: {relative!r}") from exc
    if not target.is_file():
        raise ValueError(f"context file does not exist: {relative!r}")
    return target


def build_worker_prompt(task: dict[str, Any], *, repo_root: str | Path) -> tuple[str, list[str]]:
    root = Path(repo_root)
    chunks: list[str] = []
    used: list[str] = []
    total = 0
    for relative in task.get("context_files", []):
        target = _safe_context_path(root, relative)
        text = target.read_text(encoding="utf-8", errors="replace")
        remaining = MAX_CONTEXT_CHARS - total
        if remaining <= 0:
            break
        text = text[:remaining]
        total += len(text)
        used.append(relative)
        chunks.append(f"\n--- FILE: {relative} ---\n{text}\n--- END FILE ---")
    prompt = (
        "You are a bounded repository worker for project P001. Use only the supplied task and context. "
        "Do not claim you executed commands or changed files. Do not request or expose secrets. "
        "Return Markdown with exactly these sections: Analysis, Proposed changes, Patch or code snippets, Tests, Risks. "
        "If context is insufficient, say what is missing instead of inventing repository facts.\n\n"
        f"TASK ID: {task.get('task_id')}\nGOAL: {task.get('goal')}\n"
        f"INSTRUCTIONS: {task.get('instructions', '')}\n"
        + "".join(chunks)
    )
    return prompt, used


def run_worker(
    task: dict[str, Any],
    inventory: dict[str, Any],
    *,
    repo_root: str | Path,
    output_dir: str | Path,
    dry_run: bool = False,
    usage_log: str | Path | None = None,
) -> dict[str, Any]:
    errors = validate_worker_task(task)
    if errors:
        raise ValueError("invalid worker task: " + "; ".join(errors))
    prompt, context_files = build_worker_prompt(task, repo_root=repo_root)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    result = invoke_free_only(
        inventory,
        prompt=prompt,
        required_tier=str(task.get("tier", "A")),
        resource_type="api",
        max_tokens=int(task.get("max_output_tokens", 800)),
        dry_run=dry_run,
        usage_log=usage_log,
        system="You produce reviewable development artifacts only. Never claim to have modified the repository.",
    )
    metadata = {
        "project": "P001",
        "task_id": task.get("task_id"),
        "dry_run": dry_run,
        "context_files": context_files,
        "gateway_status": result.get("status"),
        "preflight": result.get("preflight"),
    }
    (target / "run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if dry_run:
        (target / "prompt-preview.md").write_text(prompt + "\n", encoding="utf-8")
    else:
        (target / "model-output.md").write_text(str(result.get("content", "")) + "\n", encoding="utf-8")
    return metadata
