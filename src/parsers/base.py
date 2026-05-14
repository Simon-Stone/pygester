
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ParserOutput:
    markdown: str
    raw_output: dict[str, Any]
    page_count: int | None = None


class Parser(Protocol):
    name: str
    version: str

    def parse(
        self,
        pdf_path: Path,
        max_pages: int | None = None,
        do_formula_enrichment: bool = True,
        do_table_structure: bool = True,
        do_ocr: bool = False,
    ) -> ParserOutput: ...
