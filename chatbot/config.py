# chatbot/config.py
# Central configuration file for the chatbot project.
# This module defines global constants, model hyperparameters,
# device selection, and supported intents and sentiments.

import torch

# Select computation device:
# - Uses GPU (CUDA) if available for faster training/inference
# - Falls back to CPU otherwise
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Maximum number of tokens allowed in an input sequence
MAX_LEN = 24

# Dimensionality of word embeddings
EMBED_DIM = 128

# Dimensionality of hidden layers in the neural network
HIDDEN_DIM = 192

# Number of stacked recurrent layers in the model
NUM_LAYERS = 2

# Dropout rate used for regularization to reduce overfitting
DROPOUT = 0.25

# File path for saving and loading the trained chatbot model
MODEL_PATH = "models/chatbot.pt"

# List of supported user intent classes for intent classification
INTENTS = [
    "support_issue",
    "facility_reservation",
    "operation_status",
    "financial_inquiry",
]

# Supported sentiment categories for sentiment analysis
SENTIMENTS = ["negative", "positive", "neutral"]
