import torch
import torchaudio
from torchaudio.transforms import MelSpectrogram, AmplitudeToDB, Resample, Vad, MFCC
from torchvision.transforms import Compose

def pad_tensor(x, max_len):
    if x.size(1) > max_len:
        return x[:, :max_len]
    elif x.size(1) < max_len:
        return torch.nn.functional.pad(x, (0, max_len - x.size(1)))
    return x

def get_transform(sample_rate=16000, max_length=48000):
    return Compose([
        # Resample(orig_freq=44100, new_freq=sample_rate),
        lambda x: x.mean(dim=0, keepdim=True) if x.ndim == 2 and x.shape[0] > 1 else x,
        lambda x: pad_tensor(x, max_length)
    ])