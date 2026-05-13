from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

from common import ensure_dir, sha256_file, write_json


def extract_artifacts(pdf_path: Path, out_dir: Path, dpi: int = 300, max_pages: int | None = None) -> None:
    artifacts = ensure_dir(out_dir / "artifacts")
    pages_dir = ensure_dir(artifacts / "pages")
    layout_dir = ensure_dir(artifacts / "layout")
    text_dir = ensure_dir(artifacts / "text")

    original_pdf = artifacts / "original.pdf"
    shutil.copy2(pdf_path, original_pdf)

    doc = fitz.open(pdf_path)
    page_count = len(doc) if max_pages is None else min(len(doc), max_pages)

    raw_text_parts: list[str] = []
    raw_blocks: list[dict] = []
    raw_dict_pages: list[dict] = []
    raw_words: list[dict] = []

    for i in range(page_count):
        page = doc[i]
        page_id = i + 1

        pix = page.get_pixmap(dpi=dpi)
        pix.save(str(pages_dir / f"page_{page_id:04d}.png"))

        text = page.get_text("text")
        raw_text_parts.append(f"\n\n===== PAGE {page_id} =====\n{text}")

        blocks = page.get_text("blocks")
        raw_blocks.append({"page": page_id, "blocks": blocks})

        page_dict = page.get_text("dict")
        page_dict["page"] = page_id
        raw_dict_pages.append(page_dict)

        words = page.get_text("words")
        raw_words.append({"page": page_id, "words": words})

    (text_dir / "raw_text.txt").write_text("".join(raw_text_parts), encoding="utf-8")
    write_json(text_dir / "raw_blocks.json", raw_blocks)
    write_json(text_dir / "raw_dict.json", raw_dict_pages)
    write_json(text_dir / "raw_words.json", raw_words)
    write_json(layout_dir / "layout.json", raw_dict_pages)

    run_manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_pdf": str(pdf_path),
        "input_pdf_sha256": sha256_file(pdf_path),
        "artifacts_pdf_sha256": sha256_file(original_pdf),
        "page_count_processed": page_count,
        "dpi": dpi,
        "engine": "PyMuPDF",
    }
    write_json(artifacts / "run_manifest.json", run_manifest)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--max-pages", type=int, default=None)
    args = p.parse_args()

    extract_artifacts(args.pdf, args.out, dpi=args.dpi, max_pages=args.max_pages)


if __name__ == "__main__":
    main()
