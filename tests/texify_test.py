#!/usr/bin/env python3
"""Verify Docling formula extraction against Texify ground truth."""

from pathlib import Path
from texify.inference import batch_inference
from texify.model.model import load_model
from texify.model.processor import load_processor
from PIL import Image

# Load once (first call downloads model ~500MB)
print("Loading Texify model...")
model = load_model()
processor = load_processor()
print("Loaded.")
print()

# Default: use slurm-foffano-true output
crops_dir = Path("runs/slurm-foffano-true/visuals/equations")

if not crops_dir.exists():
    print(f"ERROR: crops directory not found: {crops_dir}")
    print("Run the SLURM job first: sbatch scripts/foffano-fe-on.sh")
    exit(1)

# Clean baseline + the two known-broken equations from the QC run
test_cases = [
    ("eq-001", "equation_001.png", "Clean — Docling got this right"),
    ("eq-005", "equation_005.png", "Docling failure (quad wall)"),
    ("eq-018", "equation_018.png", "Docling partial (prose bleed)"),
    ("eq-025", "equation_025.png", "Docling failure (hallucinated text)"),
]

for eq_id, filename, label in test_cases:
    print("=" * 70)
    print(f"{eq_id} — {label}")
    print("=" * 70)
    img_path = crops_dir / filename
    if not img_path.exists():
        print(f"MISSING: {img_path}")
        continue
    img = Image.open(img_path)
    result = batch_inference([img], model, processor)
    print(result[0])
    print()
