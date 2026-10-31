#!/usr/bin/env python3
"""Download a large model with parallel HTTP range requests."""

from __future__ import annotations

import argparse
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


def download_segment(
    url: str,
    destination: Path,
    start: int,
    end: int,
    retries: int,
) -> None:
    expected = end - start + 1
    for attempt in range(1, retries + 1):
        try:
            existing = destination.stat().st_size if destination.exists() else 0
            if existing >= expected:
                return
            request_start = start + existing
            headers = {
                "Range": f"bytes={request_start}-{end}",
                "User-Agent": "Mozilla/5.0",
            }
            with requests.get(url, headers=headers, stream=True, timeout=120) as response:
                if response.status_code != 206:
                    raise RuntimeError(f"HTTP {response.status_code}, expected 206")
                received = existing
                with destination.open("ab" if existing else "wb") as output:
                    for chunk in response.iter_content(1024 * 1024):
                        if not chunk:
                            continue
                        output.write(chunk)
                        received += len(chunk)
                if received != expected:
                    raise RuntimeError(f"received {received}, expected {expected}")
                return
        except Exception:
            if attempt == retries:
                raise
            time.sleep(3 * attempt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("destination", type=Path)
    parser.add_argument("total_bytes", type=int)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--retries", type=int, default=8)
    parser.add_argument("--keep-parts", action="store_true")
    args = parser.parse_args()

    destination = args.destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    parts_dir = destination.parent / f".{destination.name}.parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    if destination.exists() and destination.stat().st_size == args.total_bytes:
        print(f"Already complete: {destination}")
        return 0

    segment_size = args.total_bytes // args.workers
    ranges = []
    for index in range(args.workers):
        start = index * segment_size
        end = args.total_bytes - 1 if index == args.workers - 1 else (index + 1) * segment_size - 1
        ranges.append((index, start, end))

    stop_progress = threading.Event()

    def report_progress() -> None:
        while not stop_progress.wait(5):
            downloaded = sum(path.stat().st_size for path in parts_dir.glob("part*"))
            percent = downloaded * 100 / args.total_bytes
            print(
                f"\r{downloaded / (1024 ** 3):.2f} / "
                f"{args.total_bytes / (1024 ** 3):.2f} GiB ({percent:.1f}%)",
                end="",
                flush=True,
            )

    reporter = threading.Thread(target=report_progress, daemon=True)
    reporter.start()
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(
                    download_segment,
                    args.url,
                    parts_dir / f"part{index}",
                    start,
                    end,
                    args.retries,
                ): index
                for index, start, end in ranges
            }
            for future in as_completed(futures):
                future.result()
    finally:
        stop_progress.set()
        reporter.join()
        print()

    assembled = destination.with_suffix(destination.suffix + ".assembled")
    with assembled.open("wb") as output:
        for index, _, _ in ranges:
            part = parts_dir / f"part{index}"
            with part.open("rb") as source:
                shutil.copyfileobj(source, output, length=8 * 1024 * 1024)
    if assembled.stat().st_size != args.total_bytes:
        raise RuntimeError(
            f"Assembled size {assembled.stat().st_size} != expected {args.total_bytes}"
        )
    os.replace(assembled, destination)
    if not args.keep_parts:
        shutil.rmtree(parts_dir)
    print(f"Complete: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
