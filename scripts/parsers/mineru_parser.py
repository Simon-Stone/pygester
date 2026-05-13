
from pathlib import Path

from .base import ParserOutput


class MineruParser:
    name = "mineru"
    version = "optional"

    def parse(self, pdf_path: Path, max_pages: int | None = None) -> ParserOutput:
        raise RuntimeError(
            "MinerU backend not wired in this build. Use --parser docling."
        )
