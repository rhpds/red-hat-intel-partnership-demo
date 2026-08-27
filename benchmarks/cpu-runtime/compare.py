#!/usr/bin/env python3
"""Create a concise Markdown comparison from two benchmark JSON files."""

import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def keyed(data: dict) -> dict:
    return {(cell["profile"], cell["concurrency"]): cell for cell in data["cells"]}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare.py OVMS.json VLLM_OPENVINO.json", file=sys.stderr)
        return 2
    left, right = load(sys.argv[1]), load(sys.argv[2])
    left_cells, right_cells = keyed(left), keyed(right)
    print("# OVMS vs vLLM-OpenVINO Benchmark\n")
    print(f"Model: `{left['model']}`\n")
    print("| Profile | Concurrency | OVMS TTFT p95 (s) | vLLM+OV TTFT p95 (s) | OVMS tok/s | vLLM+OV tok/s |")
    print("|---|---:|---:|---:|---:|---:|")
    for key in sorted(set(left_cells) & set(right_cells)):
        a, b = left_cells[key], right_cells[key]
        print(
            f"| {key[0]} | {key[1]} | {a['ttft_seconds']['p95']:.3f} | "
            f"{b['ttft_seconds']['p95']:.3f} | "
            f"{a['aggregate_output_tokens_per_second']:.2f} | "
            f"{b['aggregate_output_tokens_per_second']:.2f} |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

