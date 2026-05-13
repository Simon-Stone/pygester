from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

import fitz

from common import ensure_dir, read_json, sha256_file, write_json
from parsers.docling_parser import DoclingParser

SKILL_VERSION = "0.4.0"


def _get_parser(name: str):
    if name != "docling":
        raise ValueError(f"Unknown parser: {name}")
    return DoclingParser()


def _rasterize_pages(pdf_path: Path, pages_dir: Path, dpi: int, max_pages: int | None) -> int:
    doc = fitz.open(pdf_path)
    page_count = len(doc) if max_pages is None else min(len(doc), max_pages)
    for i in range(page_count):
        pix = doc[i].get_pixmap(dpi=dpi)
        pix.save(str(pages_dir / f"page_{i+1:04d}.png"))
    return page_count


def _flag_on(value: str) -> bool:
    if value not in {"on", "off"}:
        raise ValueError(f"flag must be 'on' or 'off', got: {value}")
    return value == "on"


def parse_pdf(
    pdf_path: Path,
    out_dir: Path,
    parser_name: str = "docling",
    dpi: int = 200,
    max_pages: int | None = None,
    cache: bool = False,
    formula_enrichment: str = "on",
    table_structure: str = "on",
    ocr: str = "off",
) -> None:
    artifacts = ensure_dir(out_dir / "artifacts")
    parser_dir = ensure_dir(artifacts / "parser")
    pages_dir = ensure_dir(artifacts / "pages")

    input_sha = sha256_file(pdf_path)
    manifest_path = artifacts / "run_manifest.json"
    if cache and manifest_path.exists():
        manifest = read_json(manifest_path)
        cached_cli = manifest.get("cli_args", {})
        if (
            manifest.get("input_pdf_sha256") == input_sha
            and manifest.get("parser", {}).get("name") == parser_name
            and manifest.get("dpi") == dpi
            and manifest.get("max_pages") == max_pages
            and cached_cli.get("formula_enrichment") == formula_enrichment
            and cached_cli.get("table_structure") == table_structure
            and cached_cli.get("ocr") == ocr
        ):
            return

    original_pdf = artifacts / "original.pdf"
    shutil.copy2(pdf_path, original_pdf)

    parser = _get_parser(parser_name)
    do_formula_enrichment = _flag_on(formula_enrichment)
    do_table_structure = _flag_on(table_structure)
    do_ocr = _flag_on(ocr)

    parsed = parser.parse(
        pdf_path,
        max_pages=max_pages,
        do_formula_enrichment=do_formula_enrichment,
        do_table_structure=do_table_structure,
        do_ocr=do_ocr,
    )

    page_count = _rasterize_pages(pdf_path, pages_dir, dpi=dpi, max_pages=max_pages)
    parser_page_count = parsed.page_count if parsed.page_count is not None else page_count

    write_json(parser_dir / "raw_output.json", parsed.raw_output)
    (parser_dir / "raw_output.md").write_text(parsed.markdown or "", encoding="utf-8")

    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "skill_version": SKILL_VERSION,
        "input_pdf": str(pdf_path),
        "input_pdf_sha256": input_sha,
        "artifacts_pdf_sha256": sha256_file(original_pdf),
        "page_count_processed": page_count,
        "dpi": dpi,
        "max_pages": max_pages,
        "cli_args": {
            "max_pages": max_pages,
            "dpi": dpi,
            "cache": cache,
            "formula_enrichment": formula_enrichment,
            "table_structure": table_structure,
            "ocr": ocr,
        },
        "parser": {
            "name": parser.name,
            "version": parser.version,
            "reported_page_count": parser_page_count,
            "config": {
                "do_formula_enrichment": do_formula_enrichment,
                "do_table_structure": do_table_structure,
                "do_ocr": do_ocr,
            },
        },
    }
    write_json(manifest_path, manifest)


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 1: parse PDF + rasterize pages")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--parser", choices=["docling"], default="docling")
    p.add_argument("--dpi", type=int, default=200)
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--cache", action="store_true")
    p.add_argument("--formula-enrichment", choices=["on", "off"], default="on")
    p.add_argument("--table-structure", choices=["on", "off"], default="on")
    p.add_argument("--ocr", choices=["on", "off"], default="off")
    args = p.parse_args()

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


if __name__ == "__main__":
    main()
