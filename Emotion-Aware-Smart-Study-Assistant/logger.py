import csv
import os
from datetime import datetime
class EmotionLogger:
    def __init__(self, filename="emotion_log.csv"):
        self.filename = filename
        self._initialize_file()
    def _initialize_file(self):
        file_exists = os.path.isfile(self.filename)
        if not file_exists:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Detected_Emotion", "Confidence", "Status", "Alert_Triggered"])
    def log(self, emotion, confidence, status, alert_triggered=False):
        """
        Logs an emotion event.
        - emotion: Current detected dominant emotion
        - confidence: Confidence score of the detection (0-1)
        - status: e.g. 'Monitoring', 'Negative emotion detected', 'Break reminder played'
        - alert_triggered: Boolean, True if an audio alert was played
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, emotion, f"{confidence:.2f}", status, "Yes" if alert_triggered else "No"])
