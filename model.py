import torch
import torch.nn as nn
import torchaudio.transforms as T
import torch.nn.functional as F


class AttentionRNN(nn.Module):
    def __init__(
        self,
        num_classes,
        sample_rate=16000,
        input_length=16000,
        n_mfcc=40,
        rnn_func=nn.LSTM,
    ):
        super(AttentionRNN, self).__init__()
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.input_length = input_length
        self.num_classes = num_classes

        self.mfcc_transform = T.MFCC(
            sample_rate=sample_rate,
            n_mfcc=n_mfcc,
            melkwargs={"n_fft": 400, "hop_length": 160, "n_mels": 80, "center": True},
        )

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 10, kernel_size=(5, 1), padding="same"),
            nn.BatchNorm2d(10),
            nn.ReLU(),
            nn.Conv2d(10, 1, kernel_size=(5, 1), padding="same"),
            nn.BatchNorm2d(1),
            nn.ReLU(),
        )

        self.rnn1 = rnn_func(
            input_size=n_mfcc, hidden_size=64, bidirectional=True, batch_first=False
        )
        self.rnn2 = rnn_func(
            input_size=128, hidden_size=64, bidirectional=True, batch_first=False
        )

        self.query_proj = nn.Linear(128, 128)

        self.classifier = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, num_classes),
            nn.Softmax(dim=1),
        )

    def forward(self, x):
        """
        x: Tensor [batch_size, input_length]
        """
        batch_size = x.size(0)

        x = self.mfcc_transform(x)

        x = x.unsqueeze(1)
        x = self.cnn(x)

        x = x.squeeze(1)

        x = x.permute(2, 0, 1)

        x, _ = self.rnn1(x)
        x, _ = self.rnn2(x)

        x = x.permute(1, 0, 2)

        x_last = x[:, -1, :]
        query = self.query_proj(x_last)

        att_scores = torch.bmm(query.unsqueeze(1), x.transpose(1, 2))
        att_weights = F.softmax(att_scores, dim=-1)

        att_output = torch.bmm(att_weights, x).squeeze(1)

        x = self.classifier(att_output)
        return x
