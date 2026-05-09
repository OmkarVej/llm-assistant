import torch
import torch.nn as nn
import torch.nn.functional as F

def causal_mask(sz, device):
    return torch.triu(torch.ones(sz, sz, device=device), diagonal=1).bool()

class CausalSelfAttention(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout):
        super().__init__()
        self.mha = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout, batch_first=True)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)
    def forward(self, x, attn_mask=None):
        out, _ = self.mha(x, x, x, attn_mask=attn_mask)
        out = self.dropout(self.proj(out))
        return out

class FeedForward(nn.Module):
    def __init__(self, embed_dim, ff_multiplier=4, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embed_dim, ff_multiplier*embed_dim),
            nn.GELU(),
            nn.Linear(ff_multiplier*embed_dim, embed_dim),
            nn.Dropout(dropout),
        )
    def forward(self, x):
        return self.net(x)

class Block(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout):
        super().__init__()
        self.ln1 = nn.LayerNorm(embed_dim)
        self.attn = CausalSelfAttention(embed_dim, num_heads, dropout)
        self.ln2 = nn.LayerNorm(embed_dim)
        self.ff = FeedForward(embed_dim, dropout=dropout)
    def forward(self, x, attn_mask=None):
        x = x + self.attn(self.ln1(x), attn_mask=attn_mask)
        x = x + self.ff(self.ln2(x))
        return x

class MiniGPT(nn.Module):
    def __init__(self, vocab_size=256, block_size=128, n_layer=2, n_head=4, n_embd=128, dropout=0.1):
        super().__init__()
        self.vocab_size = vocab_size
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, n_embd)
        self.pos_emb = nn.Embedding(block_size, n_embd)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList([Block(n_embd, n_head, dropout) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size, bias=False)
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        b, t = idx.size()
        tok = self.tok_emb(idx)
        pos = self.pos_emb(torch.arange(t, device=idx.device))[None, :, :]
        x = self.drop(tok + pos)
        mask = causal_mask(t, device=idx.device)
        for blk in self.blocks:
            x = blk(x, attn_mask=mask)
        x = self.ln_f(x)
        logits = self.head(x)
        if targets is None:
            return logits
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens=100, temperature=1.0, top_k=None):
        device = idx.device
        for _ in range(max_new_tokens):
            t = idx.size(1)
            if t > self.block_size:
                idx_cond = idx[:, -self.block_size:]
            else:
                idx_cond = idx
            logits = self.forward(idx_cond)
            logits = logits[:, -1, :] / (temperature if temperature>0 else 1.0)
            if top_k is not None:
                v, _ = torch.topk(logits, top_k)
                minv = v[:, -1].unsqueeze(1)
                logits = torch.where(logits < minv, torch.full_like(logits, -1e10), logits)
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, next_token], dim=1)
        return idx
