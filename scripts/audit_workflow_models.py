#!/usr/bin/env python3
"""Report model references in workflows that have no matching local model file."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_ROOT = PROJECT_ROOT / "ComfyUI" / "models"
WORKFLOW_ROOTS = (
    PROJECT_ROOT / "workflows",
    PROJECT_ROOT / "animaWorkFlows",
    PROJECT_ROOT / "sefiWorkFlows",
    PROJECT_ROOT / "h3WorkFlows",
    PROJECT_ROOT / "qwen21WorkFlows",
    PROJECT_ROOT / "ComfyUI" / "user" / "default" / "workflows",
)
MODEL_SUFFIXES = {".safetensors", ".gguf", ".pth", ".pt", ".bin", ".ckpt", ".onnx"}
NOTE_TYPES = {"MarkdownNote", "Note"}
UI_ONLY_NODES = {
    "PrimitiveNode",
    "Fast Groups Bypasser (rgthree)",
    "Fast Groups Muter (rgthree)",
}
BACKUP_PARTS = {"backup", "_backup_fix"}
OPTIONAL_PARTS = {"optional"}
UUID_RE = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$", re.IGNORECASE)
LORA_TAG_RE = re.compile(r"<lora:([^:>]+)(?::[^>]*)?>")


def node_type(value: dict) -> str | None:
    kind = value.get("type") or value.get("class_type")
    return kind if isinstance(kind, str) else None


def collect_refs(value: object, current_node: str | None = None) -> list[tuple[str | None, str]]:
    refs: list[tuple[str | None, str]] = []

    if isinstance(value, dict):
        kind = node_type(value)
        if kind in NOTE_TYPES:
            return refs
        node = kind or current_node
        for child in value.values():
            refs.extend(collect_refs(child, node))
    elif isinstance(value, list):
        for child in value:
            refs.extend(collect_refs(child, current_node))
    elif isinstance(value, str):
        candidate = value.strip()
        if (
            not candidate.startswith(("http://", "https://"))
            and Path(candidate.replace("\\", "/")).suffix.lower() in MODEL_SUFFIXES
        ):
            refs.append((current_node, candidate))
        for match in LORA_TAG_RE.finditer(candidate):
            refs.append((current_node, f"{match.group(1)}.safetensors"))

    return refs


def collect_node_types(value: object, node_types: set[str]) -> None:
    if isinstance(value, dict):
        class_type = value.get("class_type")
        plain_type = value.get("type")
        if isinstance(class_type, str):
            node_types.add(class_type)
        elif (
            isinstance(plain_type, str)
            and "id" in value
            and ("widgets_values" in value or "inputs" in value)
        ):
            node_types.add(plain_type)

        for child in value.values():
            collect_node_types(child, node_types)
    elif isinstance(value, list):
        for child in value:
            collect_node_types(child, node_types)


def load_model_index() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)
    if not MODEL_ROOT.exists():
        return index
    for path in MODEL_ROOT.rglob("*"):
        if path.is_file():
            index[path.name.casefold()].append(path)
    return index


def relative_display(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--include-backups",
        action="store_true",
        help="also audit historical backup workflows",
    )
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="also audit workflows that require extra third-party models",
    )
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    args = parser.parse_args()

    model_index = load_model_index()
    missing: list[dict[str, str]] = []
    missing_nodes: list[dict[str, str]] = []
    references: list[dict[str, str]] = []
    workflow_node_types: list[tuple[Path, str]] = []
    workflow_count = 0

    for workflow_root in WORKFLOW_ROOTS:
        if not workflow_root.exists():
            continue
        for workflow_path in sorted(workflow_root.rglob("*.json")):
            if not args.include_backups and BACKUP_PARTS.intersection(workflow_path.parts):
                continue
            if not args.include_optional and OPTIONAL_PARTS.intersection(workflow_path.parts):
                continue
            try:
                data = json.loads(workflow_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as exc:
                missing.append(
                    {
                        "workflow": relative_display(workflow_path),
                        "node": "<workflow>",
                        "reference": f"INVALID_JSON: {exc}",
                    }
                )
                continue

            workflow_count += 1
            node_types: set[str] = set()
            collect_node_types(data, node_types)
            workflow_node_types.extend((workflow_path, value) for value in node_types)

            seen: set[tuple[str | None, str]] = set()
            for node, reference in collect_refs(data):
                key = (node, reference)
                if key in seen:
                    continue
                seen.add(key)

                basename = Path(reference.replace("\\", "/")).name
                matches = model_index.get(basename.casefold(), [])
                item = {
                    "workflow": relative_display(workflow_path),
                    "node": node or "<unknown>",
                    "reference": reference,
                }
                references.append(item)
                if not matches:
                    missing.append(item)

    available_nodes: set[str] = set()
    try:
        with urllib.request.urlopen(f"{args.server}/object_info", timeout=10) as response:
            available_nodes = set(json.load(response))
    except OSError:
        pass

    if available_nodes:
        for workflow_path, value in workflow_node_types:
            if (
                value not in available_nodes
                and value not in NOTE_TYPES
                and value not in UI_ONLY_NODES
                and not UUID_RE.match(value)
            ):
                missing_nodes.append(
                    {
                        "workflow": relative_display(workflow_path),
                        "node": value,
                    }
                )

    unique_missing_nodes = {
        (item["workflow"], item["node"]): item for item in missing_nodes
    }.values()

    if args.json:
        print(
            json.dumps(
                {
                    "workflow_count": workflow_count,
                    "reference_count": len(references),
                    "missing_count": len(missing),
                    "missing": missing,
                    "missing_node_count": len(unique_missing_nodes),
                    "missing_nodes": list(unique_missing_nodes),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if not missing else 1

    print(f"Scanned workflows: {workflow_count}")
    print(f"Model references: {len(references)}")
    print(f"Missing model references: {len(missing)}")
    for item in missing:
        print(f"{item['workflow']} | {item['node']} | {item['reference']}")
    print(f"Missing workflow node types: {len(unique_missing_nodes)}")
    for item in unique_missing_nodes:
        print(f"{item['workflow']} | NODE | {item['node']}")
    return 0 if not missing and not unique_missing_nodes else 1


if __name__ == "__main__":
    raise SystemExit(main())
