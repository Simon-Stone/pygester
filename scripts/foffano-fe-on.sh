#!/bin/bash
#SBATCH --job-name="digest-slurm-foffano-true"
#SBATCH --error="logs/foffano-fe-on.log"
#SBATCH --output="logs/foffano-fe-on.log"
#SBATCH --time=04-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
pixi run ./scripts/run-foffano-fe-on.sh true
