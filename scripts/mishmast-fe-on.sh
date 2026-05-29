#!/bin/bash
#SBATCH --job-name="digest-slurm-mishmast-true"
#SBATCH --error="logs/mishmast-fe-on.log"
#SBATCH --output="logs/mishmast-fe-on.log"
#SBATCH --time=04-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
pixi run ./scripts/run-mishmast-fe-on.sh true
