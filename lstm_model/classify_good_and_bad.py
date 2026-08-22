from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

action = "kick"
csv = f"../{action}_coordinates.csv" # CSV for coordinates
# Process the data
data = pd.read_csv(csv)
# Drop irrelevant columns (1-10)
# Transform data to relevant formats

# Split into 70/30 training testing
train, test = train_test_split(data,test_size=0.3)

# Decide model hyperparameters
# Build model
# Train model

# Get accuracy metrics

# save the model to ./models/[type]/[hyperparameter]_timestamp
