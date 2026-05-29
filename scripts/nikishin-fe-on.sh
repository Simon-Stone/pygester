#!/bin/bash
#SBATCH --job-name="digest-slurm-nikishin-true"
#SBATCH --error="logs/nikishin-fe-on.log"
#SBATCH --output="logs/nikishin-fe-on.log"
#SBATCH --time=04-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
pixi run ./scripts/run-nikishin-fe-on.sh true
