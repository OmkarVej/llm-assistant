import argparse, yaml, torch
from tokenizer import ByteTokenizer
from model import MiniGPT

def generate(prompt, config_path, max_new_tokens=100, temperature=0.8, top_k=50):
    cfg = yaml.safe_load(open(config_path))
    model_cfg = cfg['model']
    train_cfg = cfg['train']
    device = torch.device(train_cfg.get('device', 'cpu'))
    tokenizer = ByteTokenizer()
    model = MiniGPT(**model_cfg)
    ckpt = torch.load(train_cfg['ckpt_path'], map_location=device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.to(device).eval()

    prompt_ids = tokenizer.encode(prompt)
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = model.generate(idx, max_new_tokens=max_new_tokens, temperature=temperature, top_k=top_k)
    text = tokenizer.decode(out[0].tolist())
    return text

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='configs/default.yaml')
    parser.add_argument('--prompt', type=str, default='Hello')
    parser.add_argument('--max_new_tokens', type=int, default=100)
    args = parser.parse_args()
    print('\n----- GENERATED TEXT -----\n')
    print(generate(args.prompt, args.config, args.max_new_tokens))
