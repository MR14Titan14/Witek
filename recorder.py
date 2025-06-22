import sys
import sounddevice as sd
import soundfile as sf
import numpy as np
import torch
import torchaudio
from model import AttentionRNN
from transforms import get_transform
import threading
import os
import time
import queue
import msvcrt


class Recorder(threading.Thread):
    class_to_idx = {
        "Полужирный": 0,
        "Курсив": 1,
        "Подчёркнутый": 2,
        "Зачёркнутый": 3,
        "Удалить форматирование": 4,
        "Верхний индекс": 5,
        "Нижний индекс": 6,
        "Изменить регистр": 7,
        "По левому краю": 8,
        "По центру": 9,
        "По правому краю": 10,
        "По ширине": 11,
        "Ненумерованный список": 12,
        "Нумерованный список": 13,
        "Увеличить отступ": 14,
        "Уменьшить отступ": 15,
    }
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    model_path = "best.pth"
    sample_rate = 16000
    max_length = 48000
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AttentionRNN(num_classes=len(class_to_idx)).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    transform = get_transform(sample_rate, max_length)
    running = True
    sr = 16000

    def __init__(self):
        super().__init__()
        self.audio_buffer = []
        self.is_recording = False
        self.silence_counter = 0
        self.silence_threshold = 1
        self.silence_level = 7
        self.command_queue = queue.Queue()
        self.word_control = None
        self.stream = None
        self.stream_active = False
        self.running = True
        self.terminate = False
        self.confidence_threshold = 0.9

    def stop(self):
        self.terminate = True
        self.running = False

    def prediction(self):
        with torch.no_grad():
            try:
                audio, _ = torchaudio.load("audio/incoming.wav")
                if self.transform:
                    audio = self.transform(audio)
                if audio.ndim == 1:
                    audio = audio.unsqueeze(0)
                audio = audio.to(self.device)
                output = self.model(audio)
                print(self.idx_to_class)
                print(output)
                if torch.max(output) > self.confidence_threshold:
                    predicted_idx = torch.argmax(output, dim=1).item()
                    command = self.idx_to_class[predicted_idx]
                    self.command_queue.put(command)
                    print(f"Распознано: {command}")
                    return command
            except Exception as e:
                print(f"Ошибка распознавания: {e}")
            self.command_queue.put("мимо")
            return "мимо"

    def check_volume(self, indata, outdata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        if volume_norm > self.silence_level:
            if not self.is_recording:
                self.is_recording = True
                self.audio_buffer = []
                self.silence_counter = 0
                print("Начало записи команды...")
            self.audio_buffer.append(indata.copy())
            self.silence_counter = 0
        else:
            if self.is_recording:
                self.silence_counter += 1
                self.audio_buffer.append(indata.copy())
                if self.silence_counter >= self.silence_threshold:
                    combined_audio = np.concatenate(self.audio_buffer, axis=0)
                    sf.write("audio/incoming.wav", combined_audio, self.sr)
                    print("Команда сохранена")
                    self.is_recording = False
                    self.audio_buffer = []
        # outdata[:] = indata

    def toggle_rec(self):
        self.running = not self.running

    def run(self):
        while not self.terminate:
            if self.running and not self.stream_active:
                self.stream = sd.Stream(
                    callback=self.check_volume,
                    blocksize=int(0.5 * self.sr),
                    samplerate=self.sr,
                    channels=1,
                    dtype="float32",
                )
                self.stream.__enter__()
                self.stream_active = True
            elif not self.running and self.stream_active:
                self.stream.__exit__(None, None, None)
                self.stream = None
                self.stream_active = False
            if self.running:
                if os.path.exists("audio/incoming.wav"):
                    try:
                        command = self.prediction()
                        os.remove("audio/incoming.wav")
                    except Exception as e:
                        print(f"Ошибка обработки: {e}")
            else:
                time.sleep(0.1)
