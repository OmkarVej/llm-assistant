# mini-llm
Minimal GPT-style LLM project scaffold (toy-scale) — ready to run locally.

## Quickstart
1. Install dependencies:
   pip install -r requirements.txt
2. Put one or more .txt files in `data/` (a sample is included).
3. Train (small demo):
   python src/train.py --config configs/default.yaml
4. Generate:
   python src/generate.py --config configs/default.yaml --prompt "Hello world"

Notes:
- This is an educational, toy-scale example. For real LLM work you need more data & GPUs.
- Uses a simple byte-level tokenizer so it works with any text.
