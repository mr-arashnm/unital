# Neural network architecture for the chatbot.
# This module defines the attention mechanism and the main model
# used for joint intent classification and sentiment analysis.

import torch
import torch.nn as nn
from .config import INTENTS, SENTIMENTS, EMBED_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT

class Attention(nn.Module):
    """
    Simple additive attention mechanism.
    Computes attention weights over time steps and
    produces a context vector as a weighted sum.
    """
    def init(self, dim):
        super().__init__()
        self.proj = nn.Linear(dim, 1)

    def forward(self, x):
        # x shape: [batch_size, sequence_length, hidden_dim]
        scores = self.proj(x).squeeze(-1)       # [B, T] attention scores
        weights = torch.softmax(scores, dim=1) # [B, T] normalized weights
        context = (x * weights.unsqueeze(-1)).sum(dim=1)  # [B, D] context vector
        return context, weights

class ChatbotModel(nn.Module):
    """
    Main chatbot model based on a bidirectional GRU with attention.
    Produces intent and sentiment predictions from a shared encoder.
    """
    def init(self, vocab_size):
        super().__init__()

        # Embedding layer for token indices
        self.embedding = nn.Embedding(vocab_size, EMBED_DIM, padding_idx=0)

        # Bidirectional GRU encoder
        self.gru = nn.GRU(
            input_size=EMBED_DIM,
            hidden_size=HIDDEN_DIM,
            num_layers=NUM_LAYERS,
            batch_first=True,
            bidirectional=True,
            dropout=DROPOUT if NUM_LAYERS > 1 else 0.0
        )

        # Attention layer applied on top of GRU outputs
        self.attn = Attention(HIDDEN_DIM * 2)

        # Classification head for intent prediction
        self.intent_head = nn.Sequential(
            nn.Linear(HIDDEN_DIM * 2, 256),
            nn.ReLU(),
            nn.Dropout(DROPOUT),
            nn.Linear(256, len(INTENTS))
        )

        # Classification head for sentiment prediction
        self.sentiment_head = nn.Sequential(
            nn.Linear(HIDDEN_DIM * 2, 128),
            nn.ReLU(),
            nn.Dropout(DROPOUT),
            nn.Linear(128, len(SENTIMENTS))
        )

    def forward(self, x):
        # x: tokenized input sequence [B, T]
        emb = self.embedding(x)          # [B, T, E]
        out, _ = self.gru(emb)           # [B, T, 2H]
        ctx, weights = self.attn(out)    # ctx: [B, 2H], weights: [B, T]

        # Compute logits for each task
        intent_logits = self.intent_head(ctx)
        sentiment_logits = self.sentiment_head(ctx)

        return intent_logits, sentiment_logits, weights
