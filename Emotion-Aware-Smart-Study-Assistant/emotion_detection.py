import cv2
from fer import FER
class EmotionDetector:
    def __init__(self):
        self.detector = FER(mtcnn=True)
        self.target_emotions = ["happy", "neutral", "sad", "angry", "fear", "surprise", "disgust"]
        self.negative_emotions = ["sad", "angry", "fear", "disgust"]
    def detect_emotion(self, frame):
        """
        Takes an OpenCV BGR frame, returns:
        - dominant_emotion (str or None)
        - emotion_score (float)
        - bounding_box (list/tuple [x, y, w, h] or None)
        """
        result = self.detector.detect_emotions(frame)
        if not result:
            return None, 0.0, None
        primary_face = result[0]
        box = primary_face["box"]
        emotions = primary_face["emotions"]
        if emotions:
            dominant_emotion = max(emotions, key=emotions.get)
            score = emotions[dominant_emotion]
            return dominant_emotion, score, box
        return None, 0.0, box
    def is_negative(self, emotion):
        return emotion in self.negative_emotions
