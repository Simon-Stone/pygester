#!/bin/bash
#SBATCH --job-name="digest-slurm-cortes-fe-off"
#SBATCH --error="logs/cortes-fe-off.log"
#SBATCH --output="logs/cortes-fe-off.log"
#SBATCH --time=02-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
./scripts/run-cortes-fe-off.sh false
