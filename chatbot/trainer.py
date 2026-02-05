# Training pipeline for the chatbot model.
# This module handles dataset generation, tokenization,
# model training, validation, early stopping, and model persistence.

import os
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from .config import DEVICE, MAX_LEN, MODEL_PATH, INTENTS, SENTIMENTS
from .tokenizer import Tokenizer
from .model import ChatbotModel
from .data_generator import generate_dataset

def train_and_save(total_per_intent=500, epochs=40, lr=0.003, val_ratio=0.2, seed=42):
    # Entry point for training the chatbot model
    print("===================================")
    print("✅ Training STARTED")
    print("===================================")
    
    # Ensure model output directory exists
    os.makedirs("models", exist_ok=True)
    random.seed(seed)

    # Generate synthetic training dataset
    rows = generate_dataset(total_per_intent=total_per_intent, seed=seed)
    print(f"Train samples: {int(len(rows)*(1-val_ratio))} | Val samples: {int(len(rows)*val_ratio)}")

    # Shuffle dataset before splitting
    random.shuffle(rows)

    # Split dataset into training and validation subsets
    val_size = int(len(rows) * val_ratio)
    val_rows = rows[:val_size]
    train_rows = rows[val_size:]

    train_texts = [r[0] for r in train_rows]
    val_texts = [r[0] for r in val_rows]

    # Initialize and fit tokenizer on all available texts
    tokenizer = Tokenizer()
    tokenizer.fit(train_texts + val_texts)
    print(f"Vocab size: {len(tokenizer.word2idx)}")
    print(f"Epochs: {epochs} | lr: {lr}")
    print("-----------------------------------")

    def build_xy(rws):
        # Convert raw samples into tensors suitable for training
        X = torch.tensor([tokenizer.encode(t, MAX_LEN) for t, _, _, _ in rws], dtype=torch.long)
        y_int = torch.tensor([INTENTS.index(intent) for _, intent, _, _ in rws], dtype=torch.long)
        y_sent = torch.tensor([SENTIMENTS.index(sent) for *_, sent, _ in rws], dtype=torch.long)
        return X, y_int, y_sent

    # Build training and validation tensors
    Xtr, ytr_i, ytr_s = build_xy(train_rows)
    Xva, yva_i, yva_s = build_xy(val_rows)

    # Create PyTorch data loaders
    train_loader = DataLoader(TensorDataset(Xtr, ytr_i, ytr_s), batch_size=16, shuffle=True)
    val_loader = DataLoader(TensorDataset(Xva, yva_i, yva_s), batch_size=16, shuffle=False)

    # Initialize model and optimizer
    model = ChatbotModel(vocab_size=len(tokenizer.word2idx)).to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    # Cross-entropy losses with label smoothing for better generalization
    loss_fn_int = nn.CrossEntropyLoss(label_smoothing=0.05)
    loss_fn_sent = nn.CrossEntropyLoss(label_smoothing=0.05)

    # Early stopping configuration
    best_val = float('inf')
    patience = 6
    bad_epochs = 0

    for ep in range(epochs):
        # Training phase
        model.train()
        total = 0.0
        for xb, yi, ys in train_loader:
            xb, yi, ys = xb.to(DEVICE), yi.to(DEVICE), ys.to(DEVICE)
            opt.zero_grad()
            li, ls, _ = model(xb)
            loss = loss_fn_int(li, yi) + loss_fn_sent(ls, ys)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total += loss.item()
        train_loss = total / max(1, len(train_loader))

        # Validation phase
        model.eval()
        vtotal = 0.0
        with torch.no_grad():
            for xb, yi, ys in val_loader:
                xb, yi, ys = xb.to(DEVICE), yi.to(DEVICE), ys.to(DEVICE)
                li, ls, _ = model(xb)
                vloss = loss_fn_int(li, yi) + loss_fn_sent(ls, ys)
                vtotal += vloss.item()
        val_loss = vtotal / max(1, len(val_loader))

        # Periodic logging
        if ep % 5 == 0 or ep == epochs-1:
            print(f"Epoch {ep:03d} | TrainLoss={train_loss:.4f} | ValLoss={val_loss:.4f}")
          
        # Early stopping and model checkpointing
        if val_loss < best_val - 1e-4:
            best_val = val_loss
            bad_epochs = 0
            torch.save(
                {"model_state": model.state_dict(),
                 "vocab": tokenizer.word2idx,
                 "max_len": MAX_LEN},
                MODEL_PATH
            )
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                print("✅ Early stopping activated.")
                break

    print("-----------------------------------")
    print(f"✅ Best model saved to: {MODEL_PATH}")
    print("✅ Training FINISHED")
    print("===================================")
