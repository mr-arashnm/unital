# Simple word-level tokenizer.
# This module is responsible for text normalization,
# vocabulary construction, and encoding text into fixed-length sequences.

import re

class Tokenizer:
    def init(self):
        # Mapping from tokens to indices
        # <pad>: padding token, <unk>: unknown token
        self.word2idx = {"<pad>": 0, "<unk>": 1}
        self.idx2word = {0: "<pad>", 1: "<unk>"}

    def _normalize(self, text: str) -> str:
        # Normalize input text by trimming whitespace
        # and collapsing multiple spaces into one
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def fit(self, texts):
        # Build vocabulary from a list of input texts
        for t in texts:
            t = self._normalize(t)
            for w in t.split():
                if w not in self.word2idx:
                    idx = len(self.word2idx)
                    self.word2idx[w] = idx
                    self.idx2word[idx] = w

    def encode(self, text, max_len: int):
        # Convert text into a list of token indices
        # Applies padding or truncation to match max_len
        text = self._normalize(text)
        ids = [self.word2idx.get(w, 1) for w in text.split()]
        if len(ids) < max_len:
            ids += [0] * (max_len - len(ids))
        return ids[:max_len]
