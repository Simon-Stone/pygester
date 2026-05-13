from __future__ import annotations

import argparse
from pathlib import Path

from build_context_packet import build_context_packet
from generate_summary import generate_summary
from generate_translation import generate_translation
from normalize import normalize
from parse_pdf import parse_pdf
from section_sanity import section_sanity
from common import read_json


def _enforce_quality_gate(out_dir: Path) -> None:
    quality_path = out_dir / "artifacts" / "quality" / "quality_report.json"
    quality = read_json(quality_path)
    failures = quality.get("failures", [])
    if failures:
        raise SystemExit(f"quality gates failed: {', '.join(failures)}")


def main() -> None:
    p = argparse.ArgumentParser(description="digest-technical-paper v4 pipeline")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--parser", choices=["docling"], default="docling")
    p.add_argument("--dpi", type=int, default=200)
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--extract-only", action="store_true")
    p.add_argument("--llm-only", action="store_true")
    p.add_argument("--fail-on-low-quality", action="store_true")
    p.add_argument("--cache", action="store_true")
    p.add_argument("--formula-enrichment", choices=["on", "off"], default="on")
    p.add_argument("--table-structure", choices=["on", "off"], default="on")
    p.add_argument("--ocr", choices=["on", "off"], default="off")
    p.add_argument("--task", choices=["translation", "summary", "both"], default="both")
    args = p.parse_args()

    if not args.llm_only:
        parse_pdf(
            args.pdf,
            args.out,
            parser_name=args.parser,
            dpi=args.dpi,
            max_pages=args.max_pages,
            cache=args.cache,
            formula_enrichment=args.formula_enrichment,
            table_structure=args.table_structure,
            ocr=args.ocr,
        )
        normalize(args.out)
        section_sanity(args.out)
        build_context_packet(args.out)
        if args.fail_on_low_quality:
            _enforce_quality_gate(args.out)

    if not args.extract_only:
        if args.task in {"summary", "both"}:
            generate_summary(args.out)
        if args.task in {"translation", "both"}:
            generate_translation(args.out)


if __name__ == "__main__":
    main()
