#!/bin/bash
#SBATCH --job-name="digest-slurm-nikishin-fe-off"
#SBATCH --error="logs/nikishin-fe-off.log"
#SBATCH --output="logs/nikishin-fe-off.log"
#SBATCH --time=02-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
./scripts/run-nikishin-fe-off.sh false
