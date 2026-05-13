from __future__ import annotations

import argparse
import re
from pathlib import Path
from statistics import median

from common import read_json, write_json

ROMAN_SECTION_RE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)+\.\s+[A-Z]")
ARABIC_SECTION_RE = re.compile(r"^\d+\.\s+\S")
NESTED_ARABIC_RE = re.compile(r"^\d+\.\d+(?:\.\d+)*\s+\S")
LETTER_SUBSECTION_RE = re.compile(r"^[A-Z]\.\s+\S")
NUMBERING_PREFIX_RE = re.compile(r"^([IVXLCDM]+\.|\d+(?:\.\d+)*\.?|[A-Z]\.)\s+")

FALSE_POSITIVE_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("algorithm_promoted_to_section", re.compile(r"^Algorithm\s+\d+", re.IGNORECASE), "Algorithm"),
    ("theorem_promoted_to_section", re.compile(r"^Theorem\s+\d+", re.IGNORECASE), "Theorem"),
    ("lemma_promoted_to_section", re.compile(r"^Lemma\s+\d+", re.IGNORECASE), "Lemma"),
    ("proposition_promoted_to_section", re.compile(r"^Proposition\s+\d+", re.IGNORECASE), "Proposition"),
    ("definition_promoted_to_section", re.compile(r"^Definition\s+\d+", re.IGNORECASE), "Definition"),
    ("corollary_promoted_to_section", re.compile(r"^Corollary\s+\d+", re.IGNORECASE), "Corollary"),
    ("remark_promoted_to_section", re.compile(r"^Remark\s+\d+", re.IGNORECASE), "Remark"),
    ("example_promoted_to_section", re.compile(r"^Example\s+\d+", re.IGNORECASE), "Example"),
]


def _detect_dominant_scheme(headings: list[str]) -> str:
    roman = sum(1 for h in headings if ROMAN_SECTION_RE.match(h.strip()))
    nested = sum(1 for h in headings if NESTED_ARABIC_RE.match(h.strip()))
    arabic = sum(1 for h in headings if ARABIC_SECTION_RE.match(h.strip()))

    if roman >= max(arabic, nested) and roman > 0:
        return "roman"
    if nested >= arabic and nested > 0:
        return "nested_arabic"
    if arabic > 0:
        return "arabic"
    return "unknown"


def _is_references_heading(heading: str) -> bool:
    h = heading.strip().upper()
    return h in {"REFERENCES", "BIBLIOGRAPHY", "ACKNOWLEDGMENTS", "ACKNOWLEDGEMENTS"}


def _apply_level_rules(sections: list[dict], dominant_scheme: str, anomalies: list[str]) -> list[dict]:
    seen_level_1 = False
    for sec in sections:
        heading = str(sec.get("heading", "")).strip()
        prior_level = int(sec.get("level", 1))

        if _is_references_heading(heading):
            level = 1
        elif dominant_scheme == "roman":
            if ROMAN_SECTION_RE.match(heading):
                level = 1
            elif LETTER_SUBSECTION_RE.match(heading) and seen_level_1:
                level = 2
            else:
                level = prior_level
                anomalies.append(f"unmatched_heading_level:{sec.get('id')}")
        elif dominant_scheme in {"arabic", "nested_arabic"}:
            if NESTED_ARABIC_RE.match(heading):
                level = 2
            elif ARABIC_SECTION_RE.match(heading):
                level = 1
            else:
                level = prior_level
                anomalies.append(f"unmatched_heading_level:{sec.get('id')}")
        else:
            level = prior_level
            anomalies.append(f"unmatched_heading_level:{sec.get('id')}")

        sec["level"] = level
        if level == 1:
            seen_level_1 = True

    return sections


def section_sanity(out_dir: Path) -> None:
    sections_path = out_dir / "artifacts" / "text" / "sections.json"
    quality_path = out_dir / "artifacts" / "quality" / "quality_report.json"
    plaintext_path = out_dir / "artifacts" / "text" / "plaintext.txt"

    sections = read_json(sections_path) if sections_path.exists() else []
    quality = read_json(quality_path) if quality_path.exists() else {}
    plain_text = plaintext_path.read_text(encoding="utf-8") if plaintext_path.exists() else ""

    anomalies: list[str] = []

    heading_lengths = [len(str(s.get("heading", "")).strip()) for s in sections if str(s.get("heading", "")).strip()]
    median_heading_len = median(heading_lengths) if heading_lengths else 0

    first_numbered_idx = None
    for idx, sec in enumerate(sections):
        heading = str(sec.get("heading", "")).strip()
        if ROMAN_SECTION_RE.match(heading) or ARABIC_SECTION_RE.match(heading) or NESTED_ARABIC_RE.match(heading):
            first_numbered_idx = idx
            break

    title_idx = None
    title_section = None  # Initialize
    search_end = first_numbered_idx if first_numbered_idx is not None else len(sections)
    for idx in range(search_end):
        heading = str(sections[idx].get("heading", "")).strip()
        if NUMBERING_PREFIX_RE.match(heading):
            continue
        if len(heading) >= median_heading_len and heading:
            title_idx = idx
            break

    # Title detection: if no section header title found, assume text before first numbered section is title
    if title_idx is None and first_numbered_idx is not None:
        # No section header title - check if first section is I. INTRODUCTION or similar
        if first_numbered_idx == 0 and ROMAN_SECTION_RE.match(sections[0].get("heading", "")):
            # Title is likely first non-empty line of plaintext
            first_line = plain_text.split("\n", 1)[0].strip()
            if first_line and len(first_line) > 10 and not NUMBERING_PREFIX_RE.match(first_line):
                title_section = {"heading": first_line, "end_char": 0}
            else:
                anomalies.append("title_not_detected")
            title_end = 0
        else:
            anomalies.append("title_not_detected")
            title_end = 0
    elif title_idx is not None:
        title_section = sections.pop(title_idx)
        # title_end is the start of where abstract begins (after title heading itself)
        # Use start_char of title section + length of heading, or just 0 if title at start
        title_start = int(title_section.get("start_char", 0) or 0)
        title_heading_len = len(str(title_section.get("heading", "")))
        title_end = title_start + title_heading_len
    else:
        anomalies.append("title_not_detected")
        title_end = 0

    filtered_sections: list[dict] = []
    for sec in sections:
        heading = str(sec.get("heading", "")).strip()
        matched_false_positive = False
        for code, pattern, label in FALSE_POSITIVE_PATTERNS:
            if pattern.match(heading):
                anomalies.append(code)
                anomalies.append(f"demoted_heading:{label}:{sec.get('id')}")
                matched_false_positive = True
                break
        if not matched_false_positive:
            filtered_sections.append(sec)

    dominant_scheme = _detect_dominant_scheme([str(s.get("heading", "")) for s in filtered_sections])
    filtered_sections = _apply_level_rules(filtered_sections, dominant_scheme, anomalies)

    filtered_sections.sort(key=lambda s: (int(s.get("start_char", 0)), int(s.get("end_char", 0))))

    title = None
    if title_section is not None:
        title = str(title_section.get("heading", "")).strip()

    first_level1_start = None
    references_at_level1 = False
    has_level1 = False
    for sec in filtered_sections:
        level = int(sec.get("level", 1))
        if level == 1 and first_level1_start is None:
            first_level1_start = int(sec.get("start_char", 0))
        if level == 1:
            has_level1 = True
        if level == 1 and _is_references_heading(str(sec.get("heading", ""))):
            references_at_level1 = True

    # Abstract synthesis: text between title_end and first level-1 section
    abstract_inserted = False
    first_level1_start = None
    for sec in filtered_sections:
        if int(sec.get("level", 1)) == 1:
            first_level1_start = int(sec.get("start_char", 0))
            break
    
    if first_level1_start is not None and first_level1_start > title_end + 50:
        abstract_text = plain_text[title_end:first_level1_start].strip()
        if len(abstract_text) >= 50:  # Minimum abstract length
            abstract_section = {
                "id": "sec-abstract",
                "heading": "Abstract",
                "level": 1,
                "start_char": title_end,
                "end_char": first_level1_start,
            }
            filtered_sections.insert(0, abstract_section)
            abstract_inserted = True

    if not abstract_inserted and not any(str(s.get("heading", "")).strip().lower() == "abstract" for s in filtered_sections):
        anomalies.append("abstract_not_detected")

    has_abstract = abstract_inserted or any(str(s.get("heading", "")).strip().lower() == "abstract" for s in filtered_sections)

    # Check: no level-2 before ANY level-1 (strict) OR level-2 immediately follows a level-1 (lenient)
    level2_before_level1 = False
    seen_level1 = False
    prev_was_level1 = False
    for sec in filtered_sections:
        level = int(sec.get("level", 1))
        if level == 1:
            seen_level1 = True
            prev_was_level1 = True
        elif level == 2:
            if not seen_level1 and not prev_was_level1:
                # Level-2 appears before any level-1 AND not immediately after level-1
                level2_before_level1 = True
                anomalies.append("level2_before_level1")
            prev_was_level1 = False
        else:
            prev_was_level1 = False

    false_positive_remaining = any(
        pattern.match(str(sec.get("heading", "")).strip())
        for sec in filtered_sections
        for _, pattern, _ in FALSE_POSITIVE_PATTERNS
    )
    if false_positive_remaining:
        anomalies.append("false_positive_heading_remaining")

    title_unique_and_level0 = title is not None
    if not title_unique_and_level0:
        anomalies.append("title_not_level0_or_missing")

    if not has_level1:
        anomalies.append("no_level1_sections")

    if not references_at_level1:
        anomalies.append("references_at_wrong_level")

    section_hierarchy_consistent = all(
        [
            title_unique_and_level0,
            has_level1,
            not level2_before_level1,
            references_at_level1,
            has_abstract,
            not false_positive_remaining,
        ]
    )

    write_json(sections_path, filtered_sections)

    gates = quality.get("gates", {})
    gates["has_abstract"] = has_abstract
    gates["has_references"] = references_at_level1
    gates["section_hierarchy_consistent"] = section_hierarchy_consistent

    failures = set(quality.get("failures", []))
    for gate_name in ["canonical_non_empty", "raster_page_count_ok", "has_abstract", "has_references", "section_hierarchy_consistent"]:
        if gates.get(gate_name) is False:
            failures.add(gate_name)
        elif gate_name in failures and gates.get(gate_name) is True:
            failures.remove(gate_name)

    quality["paper_profile"] = {
        "title": title,
        "authors": quality.get("paper_profile", {}).get("authors"),
    }
    quality["gates"] = gates
    quality["failures"] = sorted(failures)
    quality["section_sanity_anomalies"] = sorted(set(anomalies))
    quality["status"] = "ok" if not quality["failures"] else "warn"

    write_json(quality_path, quality)


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 2.5: section hierarchy sanity pass")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    section_sanity(args.out)


if __name__ == "__main__":
    main()
