#!/bin/bash
#SBATCH --job-name="digest-test-false"
#SBATCH --error="logs/digest-test-false.log"
#SBATCH --output="logs/digest-test-false.log"
#SBATCH --time=00-01:00:00
#SBATCH --mem=2G
#SBATCH --mail-type=BEGIN,END,FAIL

# Test pipeline without enrichment (fast triage)
cd "$SLURM_SUBMIT_DIR"

echo "Starting Foffano test (enrichment=false)..."
pixi run test-foffano

echo "Starting Cortes test (enrichment=false)..."
pixi run test-cortes

echo "All tests complete"
