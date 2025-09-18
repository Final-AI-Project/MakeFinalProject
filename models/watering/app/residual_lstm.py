# app/residual_lstm.py
import torch
import torch.nn as nn

class ResidualLSTM(nn.Module):
    """
    입력: [soil_pct, vpd, temp, rh] 시퀀스
    출력: 다음 h-step soil 잔차 예측(단일 step 또는 다단계)
    """
    def __init__(self, input_dim=4, hidden=32, layers=1):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden, num_layers=layers, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):
        # x: [B, T, D]
        out, _ = self.lstm(x)
        y = self.head(out[:, -1, :])
        return y  # [B, 1]
