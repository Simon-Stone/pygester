#!/bin/bash
#SBATCH --job-name="digest-slurm-mishmast-fe-off"
#SBATCH --error="logs/mishmast-fe-off.log"
#SBATCH --output="logs/mishmast-fe-off.log"
#SBATCH --time=02-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
pixi run ./scripts/run-mishmast-fe-off.sh false
