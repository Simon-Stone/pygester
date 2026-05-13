from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_dir


def generate_translation(out_dir: Path) -> None:
    outputs = ensure_dir(out_dir / "outputs")
    text_path = out_dir / "artifacts" / "text" / "plaintext.txt"
    text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""

    preview = text[:3000].strip()
    translation = f"""# Translation (Scaffold)

## Status
Direct markdown translation pipeline not wired to LLM yet.

## Canonical plaintext excerpt

```
{preview}
```

## Next
- integrate translation prompt template
- section-by-section transform
- preserve equations/tables/citations with provenance
"""
    (outputs / "translation.md").write_text(translation, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    generate_translation(args.out)


if __name__ == "__main__":
    main()
