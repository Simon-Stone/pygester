from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_dir, write_json


def enrich_structures(out_dir: Path) -> None:
    artifacts = out_dir / "artifacts"
    figures_dir = ensure_dir(artifacts / "figures")
    tables_dir = ensure_dir(artifacts / "tables")
    refs_dir = ensure_dir(artifacts / "references")

    # Scaffold placeholders. Replace with actual detectors/extractors.
    write_json(figures_dir / "figures.json", {
        "status": "scaffold",
        "items": [],
        "notes": ["Implement figure bbox + caption extraction."],
    })

    write_json(tables_dir / "tables.json", {
        "status": "scaffold",
        "items": [],
        "notes": ["Implement table detection and CSV export."],
    })

    write_json(refs_dir / "references.json", {
        "status": "scaffold",
        "items": [],
        "notes": ["Implement bibliography/reference parsing."],
    })


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    enrich_structures(args.out)


if __name__ == "__main__":
    main()
