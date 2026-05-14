#!/usr/bin/env bash
# verify-enrichment.sh — sanity-check that formula enrichment produced good output
#
# Usage: ./verify-enrichment.sh <run-directory>
# Example: ./verify-enrichment.sh runs/slurm-foffano-fe-on

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <run-directory>" >&2
  echo "Example: $0 runs/slurm-foffano-fe-on" >&2
  exit 1
fi

RUN_DIR="$1"
PAPER_MD="$RUN_DIR/paper.md"
EQUATIONS_JSON="$RUN_DIR/visuals/equations/equations.json"
QUALITY_REPORT="$RUN_DIR/quality-report.json"

# Pretty section headers
section() {
  echo
  echo "═══════════════════════════════════════════════════════════════"
  echo "  $1"
  echo "═══════════════════════════════════════════════════════════════"
}

# Verify the run exists at all
if [ ! -d "$RUN_DIR" ]; then
  echo "ERROR: run directory not found: $RUN_DIR" >&2
  exit 1
fi

section "1. Dollar-sign count in paper.md"
if [ -f "$PAPER_MD" ]; then
  count=$(grep -c '\$' "$PAPER_MD" || true)
  echo "Found $count '\$' characters in paper.md"
  if [ "$count" -eq 0 ]; then
    echo "WARN: zero dollar signs — enrichment didn't fire, or LaTeX didn't reach paper.md"
  elif [ "$count" -lt 10 ]; then
    echo "WARN: very low count — enrichment partially fired? Compare against expected for this paper."
  else
    echo "OK: looks like a real enrichment-on output"
  fi
else
  echo "ERROR: paper.md not found at $PAPER_MD" >&2
fi

section "2. equations.json populated"
if [ -f "$EQUATIONS_JSON" ]; then
  total=$(python3 -c "import json; print(len(json.load(open('$EQUATIONS_JSON'))))")
  echo "Total equation entries: $total"

  python3 <<EOF
import json
eqs = json.load(open("$EQUATIONS_JSON"))
non_empty = sum(1 for e in eqs if e.get("latex", "").strip())
empty = len(eqs) - non_empty
print(f"With LaTeX populated:    {non_empty}")
print(f"With empty LaTeX:        {empty}")

if non_empty == 0:
    print("WARN: every equation has empty LaTeX — enrichment ran but the field isn't being populated")
elif empty > non_empty:
    print("WARN: most equations have empty LaTeX — partial extraction failure")
else:
    print("OK: most equations have populated LaTeX")
EOF
else
  echo "ERROR: equations.json not found at $EQUATIONS_JSON" >&2
fi

section "3. Spot-check equation 1"
if [ -f "$EQUATIONS_JSON" ]; then
  python3 <<EOF
import json
eqs = json.load(open("$EQUATIONS_JSON"))
if not eqs:
    print("WARN: no equations to check")
else:
    e = eqs[0]
    print(f"id:         {e.get('id')}")
    print(f"page:       {e.get('page')}")
    print(f"number:     {e.get('number')}")
    print(f"image_path: {e.get('image_path')}")
    latex = e.get("latex", "")
    if not latex:
        print("latex:      (empty)")
    else:
        preview = latex if len(latex) < 200 else latex[:200] + "..."
        print(f"latex:      {preview}")
EOF
fi

section "4. Worst-case equations (longest LaTeX)"
if [ -f "$EQUATIONS_JSON" ]; then
  python3 <<EOF
import json
eqs = json.load(open("$EQUATIONS_JSON"))
non_empty = [e for e in eqs if e.get("latex", "").strip()]
if not non_empty:
    print("(no equations with LaTeX to rank)")
else:
    ranked = sorted(non_empty, key=lambda e: len(e["latex"]), reverse=True)
    print("Top 3 longest LaTeX strings — check these for prose bleed or \\quad walls:")
    print()
    for e in ranked[:3]:
        latex = e["latex"]
        length = len(latex)
        flag = ""
        if "\\quad" in latex and latex.count("\\quad") > 10:
            flag = "  [BROKEN? many \\quad]"
        if "\\text{" in latex and any(w in latex for w in ("Find", "Conform", "and the", "where")):
            flag = "  [PROSE BLEED?]"
        print(f"  {e['id']} (page {e['page']}, {length} chars){flag}")
        print(f"    {latex[:150]}...")
        print()
EOF
fi

section "5. Quality report summary"
if [ -f "$QUALITY_REPORT" ]; then
  python3 <<EOF
import json
qr = json.load(open("$QUALITY_REPORT"))
print(f"Status: {qr.get('status', 'unknown')}")

# Try to find counts wherever they live in the schema
counts = qr.get("counts") or qr.get("artifacts") or {}
if counts:
    print()
    print("Counts:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

warnings = qr.get("warnings", [])
if warnings:
    print()
    print(f"Warnings ({len(warnings)}):")
    for w in warnings:
        print(f"  - {w}")
else:
    print()
    print("No warnings")

crop_failures = qr.get("crop_failures", 0) or 0
if crop_failures > 0:
    print()
    print(f"WARN: {crop_failures} crop failures recorded")
EOF
else
  echo "WARN: quality-report.json not found at $QUALITY_REPORT"
fi

echo
section "Done"
echo "Check #1-3 are essential. #4-5 are diagnostic."
echo "If #1 says 30+ \$, #2 says most equations populated, and #3 looks right — enrichment works end-to-end."
