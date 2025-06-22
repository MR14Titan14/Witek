from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import sys
import os

import queue
from recorder import Recorder
from word_controller import WordController


class RecorderThread(QThread):
    command_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recorder = Recorder()
        self.recorder.command_queue = queue.Queue()

    def run(self):
        self.recorder.start()
        while not self.isInterruptionRequested():
            if not self.recorder.command_queue.empty():
                command = self.recorder.command_queue.get()
                self.command_received.emit(command)
            self.msleep(100)

    def stop(self):
        self.requestInterruption()
        self.recorder.stop()
        self.quit()
        self.wait()

    def toggle_rec(self):
        self.recorder.toggle_rec()

    def set_silence_level(self, value):
        self.recorder.silence_level = value

    def set_confidence_threshold(self, value):
        self.recorder.confidence_threshold = value


class MainWindow(QWidget):
    COMMANDS_SHORTCUTS = {
        "Полужирный": "Ctrl + B",
        "Курсив": "Ctrl + I",
        "Подчёркнутый": "Ctrl + U",
        "Зачёркнутый": "Ctrl + T",
        "Удалить форматирование": "Ctrl + Space",
        "Верхний индекс": "Ctrl + Shift + =",
        "Нижний индекс": "Ctrl + =",
        "Изменить регистр": "Shift + F3",
        "По левому краю": "Ctrl + L",
        "По центру": "Ctrl + E",
        "По правому краю": "Ctrl + R",
        "По ширине": "Ctrl + J",
        "Ненумерованный список": "Ctrl + Shift + L",
        "Нумерованный список": "Ctrl + Alt + L",
        "Увеличить отступ": "Ctrl + M",
        "Уменьшить отступ": "Ctrl + Shift + M",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Witek")
        self.setGeometry(100, 100, 400, 500)
        self.setStyleSheet("font-size: 14px;")

        self.recorder_thread = RecorderThread()
        self.recorder_thread.command_received.connect(self.update_output)
        self.word_controller = WordController()

        self.record_button = QPushButton("")
        self.record_button.setFixedSize(80, 80)
        self.record_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FF6F61;
                border-radius: 40px;
                font-size: 30px;
                color: white;
            }
            QPushButton:checked {
                background-color: #6B5B95;
            }
        """
        )
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self.toggle_recording)

        self.commands_button = QPushButton("Список команд")
        self.commands_button.clicked.connect(self.show_commands)

        self.silence_label = QLabel("Порог тишины: 7")
        self.silence_slider = QSlider(Qt.Horizontal)
        self.silence_slider.setMinimum(1)
        self.silence_slider.setMaximum(10)
        self.silence_slider.setValue(7)
        self.silence_slider.valueChanged.connect(self.update_silence_threshold)

        self.confidence_label = QLabel("Порог уверенности: 0.9")
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(1)
        self.confidence_slider.setMaximum(100)
        self.confidence_slider.setValue(90)
        self.confidence_slider.valueChanged.connect(self.update_confidence_threshold)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #f0f0f0;
                font-size: 16px;
                font-weight: bold;
            }
        """
        )
        self.output_text.setFixedHeight(60)
        self.output_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.output_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.output_text.setAlignment(Qt.AlignCenter)

        # --- Расположение элементов ---
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.record_button)
        top_layout.addStretch()
        top_layout.addWidget(self.commands_button)

        layout.addLayout(top_layout)
        layout.addWidget(self.silence_label)
        layout.addWidget(self.silence_slider)
        layout.addWidget(self.confidence_label)
        layout.addWidget(self.confidence_slider)
        layout.addWidget(QLabel("Последняя команда:"))
        layout.addWidget(self.output_text)

        self.setLayout(layout)

        self.recorder_thread.start()

    def closeEvent(self, event):
        self.recorder_thread.stop()
        event.accept()

    def toggle_recording(self, checked):
        self.recorder_thread.toggle_rec()
        self.record_button.setChecked(checked)

    def update_silence_threshold(self, value):
        self.silence_label.setText(f"Порог тишины: {value}")
        self.recorder_thread.set_silence_level(value)

    def update_confidence_threshold(self, value):
        threshold = value / 100.0
        self.confidence_label.setText(f"Порог уверенности: {threshold:.2f}")
        self.recorder_thread.set_confidence_threshold(threshold)

    def show_commands(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Доступные команды")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Создаем таблицу
        table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(len(self.COMMANDS_SHORTCUTS))
        table.setHorizontalHeaderLabels(["Команда", "Сочетание клавиш"])

        for row, (command, shortcut) in enumerate(self.COMMANDS_SHORTCUTS.items()):
            name_item = QTableWidgetItem(command)
            shortcut_item = QTableWidgetItem(shortcut)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            shortcut_item.setFlags(shortcut_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, shortcut_item)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setFixedHeight(400)
        table.setFixedWidth(400)

        layout = QVBoxLayout()
        layout.addWidget(table)

        dialog.setLayout(layout)

        # Показываем диалог
        dialog.setStyleSheet(
            """
            QDialog {
                min-width: 800px;
            }
            QTableWidget {
                selection-background-color: #f0f0f0;
                selection-color: black;
            }
        """
        )

        dialog.exec_()

    def update_output(self, command):
        self.output_text.clear()
        if command == "мимо":
            self.output_text.setPlainText("Команда не распознана")
        else:
            self.output_text.setPlainText(command)
            if self.word_controller:
                self.word_controller.apply_formatting(command)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
