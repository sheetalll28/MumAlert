import threading
import pyttsx3
class AudioAlertSystem:
    def __init__(self):
        self.is_playing = False
    def _speak_thread(self, text):
        self.is_playing = True
        try:
            local_engine = pyttsx3.init()
            local_engine.setProperty('rate', 150)
            local_engine.say(text)
            local_engine.runAndWait()
        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            self.is_playing = False
    def play_stress_alert(self):
        """
        Plays the specific alert for stress/negative emotions.
        """
        if self.is_playing:
            return
        message = "Please take a rest."
        print(f"[AUDIO SYSTEM]: Playing message -> '{message}'")
        threading.Thread(target=self._speak_thread, args=(message,)).start()
    def play_hydration_alert(self):
        """
        Plays the specific alert for hydration reminders.
        """
        if self.is_playing:
            return
        message = "It has been 45 minutes. Please drink some water."
        print(f"[AUDIO SYSTEM]: Playing message -> '{message}'")
        threading.Thread(target=self._speak_thread, args=(message,)).start()
    def play_posture_alert(self):
        """
        Plays the specific alert for bad posture.
        """
        if self.is_playing:
            return
        message = "Please sit up straight and correct your posture."
        print(f"[AUDIO SYSTEM]: Playing message -> '{message}'")
        threading.Thread(target=self._speak_thread, args=(message,)).start()
