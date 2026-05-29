#!/bin/bash
#SBATCH --job-name="digest-slurm-foffano-fe-off"
#SBATCH --error="logs/foffano-fe-off.log"
#SBATCH --output="logs/foffano-fe-off.log"
#SBATCH --time=02-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
./scripts/run-foffano-fe-off.sh false
