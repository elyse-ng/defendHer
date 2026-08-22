"""
Train an LSTM pose classifier (kick or punch) with proper handling of
variable-length sequences via pack_padded_sequence, so padding zeros
never get fed into the LSTM as if they were real motion.

Usage:
    python train_lstm.py kick
    python train_lstm.py punch
"""

import sys
import pickle

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ----------------------------
# Config
# ----------------------------
if len(sys.argv) < 2:
    print("Usage: python train_lstm.py <kick|punch>")
    sys.exit(1)

ACTION = sys.argv[1]
CSV_PATH = f"{ACTION}_csvs/all_{ACTION}.csv"

# Must match main.py's EXCLUDED_LANDMARK_INDICES exactly
EXCLUDED_LANDMARK_INDICES = set(range(0, 10))

NUM_EPOCHS = 30
BATCH_SIZE = 8
HIDDEN_SIZE = 64
LEARNING_RATE = 0.001


# ----------------------------
# Load data
# ----------------------------
drop_columns = []
for i in sorted(EXCLUDED_LANDMARK_INDICES):
    drop_columns += [f"x{i+1}", f"y{i+1}", f"z{i+1}", f"visibility{i+1}"]

df = pd.read_csv(CSV_PATH)
df = df.drop(columns=drop_columns)

print("Columns:", df.columns.tolist())
print("Rows:", df.shape[0])

feature_columns = [c for c in df.columns if c not in ["video_no", "frame", "timestamp_ms", "good"]]

# ----------------------------
# Group frames into per-video sequences, keep REAL (unpadded) length
# ----------------------------
sequences = []
lengths = []
labels = []

for video_id, group in df.groupby("video_no"):
    group = group.sort_values("frame")
    seq = group[feature_columns].to_numpy(dtype=np.float32)
    sequences.append(seq)
    lengths.append(seq.shape[0])
    labels.append(group["good"].iloc[0])

max_len = max(lengths)
num_features = sequences[0].shape[1]

print(f"\nSequence length stats — min: {min(lengths)}, max: {max_len}, "
      f"mean: {np.mean(lengths):.1f}")
print("If mean is far below max, a few outlier videos are inflating max_len — "
      "consider capping max_len at a percentile instead of the true max.\n")

X_padded = np.zeros((len(sequences), max_len, num_features), dtype=np.float32)
for i, seq in enumerate(sequences):
    X_padded[i, :seq.shape[0], :] = seq

lengths = np.array(lengths, dtype=np.int64)

# ----------------------------
# Encode labels, split (keep lengths aligned with X/y)
# ----------------------------
le = LabelEncoder()
y_encoded = le.fit_transform(labels)

indices = np.arange(len(sequences))
idx_train, idx_temp = train_test_split(
    indices, train_size=0.7, stratify=y_encoded, random_state=42)
idx_val, idx_test = train_test_split(
    idx_temp, train_size=0.5, stratify=y_encoded[idx_temp], random_state=42)


def subset(idx):
    return X_padded[idx], lengths[idx], y_encoded[idx]


X_train, len_train, y_train = subset(idx_train)
X_val, len_val, y_val = subset(idx_val)
X_test, len_test, y_test = subset(idx_test)


# ----------------------------
# Dataset / DataLoader — now also yields the real sequence length
# ----------------------------
class PoseSequenceDataset(Dataset):
    def __init__(self, X, lengths, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.lengths = torch.tensor(lengths, dtype=torch.int64)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.lengths[idx], self.y[idx]


train_loader = DataLoader(PoseSequenceDataset(X_train, len_train, y_train),
                           batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(PoseSequenceDataset(X_val, len_val, y_val),
                         batch_size=BATCH_SIZE)
test_loader = DataLoader(PoseSequenceDataset(X_test, len_test, y_test),
                          batch_size=BATCH_SIZE)


# ----------------------------
# Model — uses pack_padded_sequence so padding is skipped, not learned from
# ----------------------------
class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=1, num_classes=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x, lengths):
        # lengths must be on CPU for pack_padded_sequence
        packed = pack_padded_sequence(
            x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, (h_n, _) = self.lstm(packed)
        last_hidden = h_n[-1]
        out = self.fc(last_hidden)
        return out


model = LSTMClassifier(input_size=num_features, hidden_size=HIDDEN_SIZE,
                        num_classes=len(le.classes_))

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)


# ----------------------------
# Train — now actually logs loss / accuracy every epoch
# ----------------------------
def run_eval(loader):
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for X_batch, len_batch, y_batch in loader:
            outputs = model(X_batch, len_batch)
            preds = torch.argmax(outputs, dim=1)
            correct += (preds == y_batch).sum().item()
            total += y_batch.size(0)
    return correct / total if total else 0.0


print(f"\nTraining LSTM for action='{ACTION}'...\n")

for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0.0
    for X_batch, len_batch, y_batch in train_loader:
        optimizer.zero_grad()
        outputs = model(X_batch, len_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    val_acc = run_eval(val_loader)
    avg_loss = total_loss / len(train_loader)
    print(f"Epoch {epoch+1:2d}/{NUM_EPOCHS} | Train Loss: {avg_loss:.4f} | Val Acc: {val_acc:.4f}")


# ----------------------------
# Test set evaluation
# ----------------------------
model.eval()
all_preds, all_labels, all_confidences = [], [], []

with torch.no_grad():
    for X_batch, len_batch, y_batch in test_loader:
        outputs = model(X_batch, len_batch)
        probs = torch.softmax(outputs, dim=1)
        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.tolist())
        all_labels.extend(y_batch.tolist())
        all_confidences.extend(probs.max(dim=1).values.tolist())

print("\nTest Accuracy:", accuracy_score(all_labels, all_preds))
print("\nClassification Report:\n",
      classification_report(all_labels, all_preds, target_names=le.classes_))
print("\nConfusion Matrix:\n", confusion_matrix(all_labels, all_preds))
print("\nConfidence spread on test set — min: {:.3f}, max: {:.3f}, mean: {:.3f}".format(
    min(all_confidences), max(all_confidences), np.mean(all_confidences)))
print("(If confidence barely varies across the test set, the model may still be "
      "under-differentiating — but the packing fix above removes the padding-dominance cause.)")


# ----------------------------
# Save model + label encoder + config
# ----------------------------
torch.save(model.state_dict(), f"{ACTION}_lstm_model.pth")

with open(f"{ACTION}_label_encoder.pkl", "wb") as f:
    pickle.dump(le, f)

with open(f"{ACTION}_model_config.pkl", "wb") as f:
    pickle.dump({"max_len": max_len, "num_features": num_features}, f)

print(f"\nSaved {ACTION}_lstm_model.pth, {ACTION}_label_encoder.pkl, {ACTION}_model_config.pkl")