from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_dir


def generate_summary(out_dir: Path) -> None:
    outputs = ensure_dir(out_dir / "outputs")
    text_path = out_dir / "artifacts" / "text" / "plaintext.txt"
    text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""

    preview = text[:3000].strip()
    summary = f"""# Summary (Scaffold)

## Status
LLM generation not wired yet. This file is placeholder scaffold output.

## Preview of canonical plaintext

```
{preview}
```

## Next
- integrate provider SDK
- feed llm/context_packet.json + plaintext
- enforce page-grounded citations
"""
    (outputs / "paper.md").write_text(summary, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    generate_summary(args.out)


if __name__ == "__main__":
    main()
