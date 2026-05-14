#!/usr/bin/env python3
"""Run all stages: 01-parse → 02-clean → 03-packet."""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="digest-technical-paper: full pipeline")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--formula-enrichment", choices=["true", "false"], default="false")
    p.add_argument("--code-enrichment", choices=["true", "false"], default="false")
    p.add_argument("--ocr", choices=["true", "false"], default="false")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    t0_total = time.monotonic()
    scripts_dir = Path(__file__).parent
    out_dir = args.out

    # Ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Stage 01
    if not (out_dir / "debug" / "parser" / "raw_output.json").exists():
        print(f"[{time.strftime('%H:%M:%S')}] Running Stage 01...")
        stage1_args = [
            sys.executable,
            str(scripts_dir / "01-parse.py"),
            str(args.pdf),
            "--out",
            str(args.out),
            "--formula-enrichment",
            args.formula_enrichment,
            "--code-enrichment",
            args.code_enrichment,
            "--ocr",
            args.ocr,
            "--dpi",
            str(args.dpi),
        ]
        if args.max_pages is not None:
            stage1_args.extend(["--max-pages", str(args.max_pages)])
        subprocess.run(stage1_args, check=True)
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Stage 01 complete, skipping")

    # Stage 02
    if not (out_dir / "paper.md").exists():
        print(f"[{time.strftime('%H:%M:%S')}] Running Stage 02...")
        subprocess.run(
            [sys.executable, str(scripts_dir / "02-clean.py"), "--out", str(args.out)],
            check=True,
        )
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Stage 02 complete, skipping")

    # Stage 03
    if not (out_dir / "context-packet.json").exists():
        print(f"[{time.strftime('%H:%M:%S')}] Running Stage 03...")
        subprocess.run(
            [sys.executable, str(scripts_dir / "03-packet.py"), "--out", str(args.out)],
            check=True,
        )
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Stage 03 complete, skipping")

    elapsed = time.monotonic() - t0_total
    print(f"[{time.strftime('%H:%M:%S')}] Total elapsed: {elapsed:.1f}s")
    print(f"[{time.strftime('%H:%M:%S')}] Pipeline complete")


if __name__ == "__main__":
    main()
