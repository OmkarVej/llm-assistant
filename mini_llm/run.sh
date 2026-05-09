#!/bin/bash
set -e
echo "Install requirements (recommended in virtualenv):"
echo "  pip install -r requirements.txt"
echo ""
echo "Train (small):"
python src/train.py --config configs/default.yaml
echo ""
echo "Generate:"
python src/generate.py --config configs/default.yaml --prompt "Once upon a time"
