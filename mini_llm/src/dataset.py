import os
from glob import glob
import torch
from torch.utils.data import Dataset

class TextDataset(Dataset):
    def __init__(self, data_dir: str, tokenizer, block_size: int = 128):
        files = glob(os.path.join(data_dir, '*.txt'))
        if len(files) == 0:
            raise RuntimeError(f'No .txt files found in {data_dir}')
        data_bytes = []
        for f in files:
            with open(f, 'rb') as fh:
                data_bytes.append(fh.read().strip())
        self.data = b'\n'.join(data_bytes)
        self.tokens = list(self.data)
        self.block_size = block_size
        self.tokenizer = tokenizer
    def __len__(self):
        return max(0, len(self.tokens) - self.block_size)
    def __getitem__(self, idx):
        s = idx
        e = s + self.block_size
        x = torch.tensor(self.tokens[s:e], dtype=torch.long)
        y = torch.tensor(self.tokens[s+1:e+1], dtype=torch.long)
        return x, y

def collate_batch(batch):
    xs = torch.stack([b[0] for b in batch])
    ys = torch.stack([b[1] for b in batch])
    return xs, ys
