#!/usr/bin/env python3
"""Point the official Qwen-Image 2.1 templates at the installed W4A8 encoder."""

from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_ROOTS = (
    PROJECT_ROOT / "qwen21WorkFlows",
    PROJECT_ROOT / "ComfyUI" / "user" / "default" / "workflows",
)
LOCAL_ENCODER = "qwen3vl_8b_w4a8.safetensors"
MISSING_ENCODERS = (
    "qwen3vl_8b_int8_convrot.safetensors",
    "qwen3.5_9b_qwen_image_2.1_pe_t2i.int8_convrot.safetensors",
    "qwen3.5_9b_qwen_image_2.1_pe_i2i.int8_convrot.safetensors",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report changes without writing")
    args = parser.parse_args()

    changed = False
    paths = []
    for root in WORKFLOW_ROOTS:
        if root.exists():
            paths.extend(root.glob("qwen_image_2_1_turbo_*.json"))

    for path in sorted(set(paths)):
        text = path.read_text(encoding="utf-8-sig")
        updated = text
        counts = {}
        for missing in MISSING_ENCODERS:
            count = updated.count(missing)
            if count:
                updated = updated.replace(missing, LOCAL_ENCODER)
                counts[missing] = count
        if not counts:
            continue

        changed = True
        print(f"{path.relative_to(PROJECT_ROOT).as_posix()}: {counts}")
        if not args.check:
            path.write_text(updated, encoding="utf-8", newline="\n")

    if not changed:
        print("No missing Qwen encoder references found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
