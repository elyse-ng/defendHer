
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle

# Load and drop 1-10 coords
drop_columns = []
for i in range(10):
    drop_columns += [f"x{i+1}", f"y{i+1}", f"z{i+1}", f"visibility{i+1}"]

csv_path = "punch_csvs/all_punch.csv"
punch_data = pd.read_csv(csv_path)
punch_data = punch_data.drop(columns=drop_columns)

print("Columns:", punch_data.columns.tolist())
print("Rows:", punch_data.shape[0])

# group frames by video
feature_columns = [c for c in punch_data.columns if c not in ["video_no", "frame", "timestamp_ms", "good"]]

sequences = []
labels = []

for video_id, group in punch_data.groupby("video_no"):
    group = group.sort_values("frame")
    seq = group[feature_columns].to_numpy(dtype=np.float32)
    label = group["good"].iloc[0]
    sequences.append(seq)
    labels.append(label)

# pad to same length
max_len = max(seq.shape[0] for seq in sequences)
num_features = sequences[0].shape[1]

X_padded = np.zeros((len(sequences), max_len, num_features), dtype=np.float32)

for i, seq in enumerate(sequences):
    length = seq.shape[0]
    X_padded[i, :length, :] = seq

# encode label and split data
le = LabelEncoder()
y_encoded = le.fit_transform(labels)

X_train, X_temp, y_train, y_temp = train_test_split(
    X_padded, y_encoded, train_size=0.7, stratify=y_encoded, random_state=42)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, train_size=0.5, stratify=y_temp, random_state=42)

# Data loader
class PoseSequenceDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_dataset = PoseSequenceDataset(X_train, y_train)
val_dataset = PoseSequenceDataset(X_val, y_val)
test_dataset = PoseSequenceDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=8)
test_loader = DataLoader(test_dataset, batch_size=8)

# Define LSTM
class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=1, num_classes=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        last_hidden = h_n[-1]
        out = self.fc(last_hidden)
        return out

model = LSTMClassifier(input_size=num_features, hidden_size=64, num_classes=len(le.classes_))

# Train
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

num_epochs = 30

for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            outputs = model(X_batch)
            preds = torch.argmax(outputs, dim=1)
            correct += (preds == y_batch).sum().item()
            total += y_batch.size(0)

# Test set
model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for X_batch, y_batch in test_loader:
        outputs = model(X_batch)
        #how to get "confidence score"
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        print(probabilities[0][0]) #probability that the first one is "bad"
        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.tolist())
        all_labels.extend(y_batch.tolist())

print("\nTest Accuracy:", accuracy_score(all_labels, all_preds))
print("\nClassification Report:\n", classification_report(all_labels, all_preds, target_names=le.classes_))
print("\nConfusion Matrix:\n", confusion_matrix(all_labels, all_preds))

# save video
torch.save(model.state_dict(), "punch_lstm_model.pth")

with open("punch_label_encoder.pkl", "wb") as f:
    pickle.dump(le, f)

with open("punch_model_config.pkl", "wb") as f:
    pickle.dump({"max_len": max_len, "num_features": num_features}, f)

print("\nSaved punch_lstm_model.pth and punch_label_encoder.pkl")