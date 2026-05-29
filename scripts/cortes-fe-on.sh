#!/bin/bash
#SBATCH --job-name="digest-slurm-cortes-true"
#SBATCH --error="logs/cortes-fe-on.log"
#SBATCH --output="logs/cortes-fe-on.log"
#SBATCH --time=04-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

cd "$SLURM_SUBMIT_DIR"
./scripts/run-cortes-fe-on.sh true
