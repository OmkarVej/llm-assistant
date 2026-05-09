import argparse, yaml, os, torch
from tqdm import tqdm
from tokenizer import ByteTokenizer
from dataset import TextDataset, collate_batch
from model import MiniGPT

def train(config_path):
    cfg = yaml.safe_load(open(config_path))
    model_cfg = cfg['model']
    train_cfg = cfg['train']

    device = torch.device(train_cfg.get('device', 'cpu'))
    tokenizer = ByteTokenizer()
    dataset = TextDataset(train_cfg['data_dir'], tokenizer, block_size=model_cfg['block_size'])
    from torch.utils.data import DataLoader
    dl = DataLoader(dataset, batch_size=train_cfg['batch_size'], shuffle=True, collate_fn=collate_batch)

    model = MiniGPT(**model_cfg).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=train_cfg['lr'])

    os.makedirs(os.path.dirname(train_cfg['ckpt_path']) or '.', exist_ok=True)
    global_step = 0
    model.train()
    for epoch in range(train_cfg['epochs']):
        pbar = tqdm(dl, desc=f'Epoch {epoch+1}/{train_cfg["epochs"]}')
        for xb, yb in pbar:
            xb, yb = xb.to(device), yb.to(device)
            _, loss = model(xb, yb)
            optim.zero_grad()
            loss.backward()
            optim.step()
            global_step += 1
            if global_step % train_cfg.get('log_interval', 50) == 0:
                pbar.set_postfix({'loss': loss.item()})
        torch.save({'model_state_dict': model.state_dict(), 'config': {'model': model_cfg, 'train': train_cfg}}, train_cfg['ckpt_path'])
        print(f'Saved checkpoint to {train_cfg["ckpt_path"]}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='configs/default.yaml')
    args = parser.parse_args()
    train(args.config)
