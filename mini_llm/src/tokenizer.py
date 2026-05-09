class ByteTokenizer:
    """Simple reversible byte-level tokenizer."""
    def __init__(self):
        self.vocab_size = 256
    def encode(self, text: str):
        return list(text.encode('utf-8'))
    def decode(self, tokens):
        return bytes(tokens).decode('utf-8', errors='replace')
