# reference: https://www.datacamp.com/tutorial/lstm-models
import torch
import torch.nn as nn
import numpy as np
 
torch.manual_seed(42)
np.random.seed(42)
 
 
class LSTMClassifier(nn.Module):
    def __init__(
        self,
        input_size,
        hidden_size,
        output_size,
        num_layers=1,
        dropout=0.0,
        bidirectional=False,
        padding_idx=0,
    ):
    
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional,
        )

        fc_input_size = hidden_size * (2 if bidirectional else 1)
        self.fc = nn.Linear(fc_input_size, output_size)

    def forward(self, x, lengths=None):
        if lengths is None:
            _, (h_n, _) = self.lstm(x.float())
        else:
            packed = nn.utils.rnn.pack_padded_sequence(
                x.float(), lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            _, (h_n, _) = self.lstm(packed)

        if self.bidirectional:
            h_final = torch.cat([h_n[-2], h_n[-1]], dim=1)
        else:
            h_final = h_n[-1]

        return self.fc(h_final)