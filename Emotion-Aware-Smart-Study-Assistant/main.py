import cv2
import time
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from emotion_detection import EmotionDetector
from audio_alert import AudioAlertSystem
from posture_detection import PostureDetector
from logger import EmotionLogger

class SmartStudyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Emotion-Aware Smart Study Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e2e")
        
        # State & Options
        self.is_monitoring = False
        self.emotion_enabled = tk.BooleanVar(value=True)
        self.posture_enabled = tk.BooleanVar(value=True)
        self.hydration_enabled = tk.BooleanVar(value=True)
        
        # Hardware & Logic
        self.cap = None
        self.detector = None
        self.posture_detector = None
        self.audio_system = None
        self.logger = None
        
        # Timers
        self.PERSISTENCE_THRESHOLD = 3.0  
        self.POSTURE_THRESHOLD = 1 * 10  
        self.COOLDOWN_PERIOD = 10.0       
        self.HYDRATION_INTERVAL = 1 * 60 
        
        self.negative_start_time = None
        self.bad_posture_start_time = None
        self.face_missing_start_time = None
        self.last_alert_time = 0.0
        self.last_hydration_time = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main Layout
        main_frame = tk.Frame(self.root, bg="#1e1e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Video Display
        self.video_label = tk.Label(main_frame, bg="#11111b", text="Camera Feed Offline", fg="#cdd6f4", font=("Segoe UI", 16))
        self.video_label.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Controls Dashboard
        control_frame = tk.Frame(main_frame, bg="#1e1e2e")
        control_frame.pack(fill=tk.X)
        
        # Left side: Settings using native tk.Checkbutton to fix the 'cross sign' UI artifact
        settings_frame = tk.Frame(control_frame, bg="#1e1e2e")
        settings_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(settings_frame, text="Active Modules:", fg="#cdd6f4", bg="#1e1e2e", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Using selectcolor="#1e1e2e" to blend the native tick-box nicely
        tk.Checkbutton(settings_frame, text="Emotion Alerts", variable=self.emotion_enabled, fg="#cdd6f4", bg="#1e1e2e", selectcolor="#2e3440", activebackground="#1e1e2e", activeforeground="#cdd6f4").pack(anchor=tk.W)
        tk.Checkbutton(settings_frame, text="Posture Alerts", variable=self.posture_enabled, fg="#cdd6f4", bg="#1e1e2e", selectcolor="#2e3440", activebackground="#1e1e2e", activeforeground="#cdd6f4").pack(anchor=tk.W)
        tk.Checkbutton(settings_frame, text="Hydration Reminders", variable=self.hydration_enabled, fg="#cdd6f4", bg="#1e1e2e", selectcolor="#2e3440", activebackground="#1e1e2e", activeforeground="#cdd6f4").pack(anchor=tk.W)
        
        # Right side: Power Button & Status
        power_frame = tk.Frame(control_frame, bg="#1e1e2e")
        power_frame.pack(side=tk.RIGHT, padx=10)
        
        self.status_label = tk.Label(power_frame, text="Status: IDLE", fg="#89dceb", bg="#1e1e2e", font=("Segoe UI", 14, "bold"))
        self.status_label.pack(pady=(0, 10))
        
        self.btn_start = tk.Button(power_frame, text="START MONITORING", bg="#a6e3a1", fg="#11111b", 
                                   font=("Segoe UI", 14, "bold"), command=self.toggle_monitoring, relief=tk.FLAT)
        self.btn_start.pack()

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        self.btn_start.config(text="INITIALIZING...", bg="#f9e2af")
        self.root.update()
        
        # Initialize heavy models if not loaded
        if self.detector is None:
            self.detector = EmotionDetector()
            self.posture_detector = PostureDetector()
            self.audio_system = AudioAlertSystem()
            self.logger = EmotionLogger("emotion_log.csv")

        # Open Webcam securely
        self.cap = None
        for target_index in [0, 1, 2]:
            temp_cap = cv2.VideoCapture(target_index, cv2.CAP_DSHOW)
            if temp_cap.isOpened():
                ret, frame = temp_cap.read()
                if ret and frame is not None and frame.max() > 0:
                    self.cap = temp_cap
                    break
            
            temp_cap = cv2.VideoCapture(target_index)
            if temp_cap.isOpened():
                ret, frame = temp_cap.read()
                if ret and frame is not None and frame.max() > 0:
                    self.cap = temp_cap
                    break

        if self.cap is None or not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not access any working webcam.")
            self.btn_start.config(text="START MONITORING", bg="#a6e3a1")
            return
            
        self.is_monitoring = True
        self.last_hydration_time = time.time()
        
        self.btn_start.config(text="STOP MONITORING", bg="#f38ba8")
        self.status_label.config(text="Status: ACTIVE", fg="#a6e3a1")
        
        # Start Video Loop Thread smoothly
        self.thread = threading.Thread(target=self.video_loop, daemon=True)
        self.thread.start()

    def stop_monitoring(self):
        self.is_monitoring = False
        self.btn_start.config(text="START MONITORING", bg="#a6e3a1")
        self.status_label.config(text="Status: IDLE", fg="#89b4fa")
        self.video_label.config(image='', text="Camera Feed Offline")

    def update_frame(self, imgtk):
        """ This method runs securely on the main UI thread to prevent blinking """
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

    def video_loop(self):
        while self.is_monitoring:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            current_time = time.time()
            system_status = "Monitoring"
            alert_triggered = False

            # --- Hardware Detection ---
            dominant_emotion, score, box = self.detector.detect_emotion(frame)
            is_bad_posture, posture_reason = self.posture_detector.check_posture(box)

            in_cooldown = (current_time - self.last_alert_time) < self.COOLDOWN_PERIOD

            # --- Gap Tolerance ---
            if box is None:
                if self.face_missing_start_time is None:
                    self.face_missing_start_time = current_time
                elif (current_time - self.face_missing_start_time) > 2.0:
                    self.bad_posture_start_time = None
                    self.negative_start_time = None
            else:
                self.face_missing_start_time = None

            # --- Posture Logic (Enabled) ---
            if self.posture_enabled.get():
                if is_bad_posture:
                    system_status = f"Bad Posture: {posture_reason}"
                    if self.bad_posture_start_time is None:
                        self.bad_posture_start_time = current_time
                        
                    if (current_time - self.bad_posture_start_time) >= self.POSTURE_THRESHOLD:
                        if not in_cooldown:
                            system_status = "Posture reminder played"
                            self.audio_system.play_posture_alert()
                            alert_triggered = True
                            self.last_alert_time = current_time
                            self.bad_posture_start_time = None
                elif box is not None:
                    self.bad_posture_start_time = None

            # --- Emotion Logic (Enabled) ---
            if self.emotion_enabled.get() and dominant_emotion:
                x, y, w, h = box
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"{dominant_emotion} ({score:.2f})", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                if self.detector.is_negative(dominant_emotion):
                    if not is_bad_posture or not self.posture_enabled.get():
                        system_status = "Negative emotion detected"
                    
                    if self.negative_start_time is None:
                        self.negative_start_time = current_time
                    
                    if (current_time - self.negative_start_time) >= self.PERSISTENCE_THRESHOLD:
                        if not in_cooldown and not alert_triggered:
                            system_status = "Stress reminder played"
                            self.audio_system.play_stress_alert()
                            alert_triggered = True
                            self.last_alert_time = current_time
                            self.negative_start_time = None
                else:
                    self.negative_start_time = None

            # --- Hydration Logic (Enabled) ---
            if self.hydration_enabled.get():
                if (current_time - self.last_hydration_time) >= self.HYDRATION_INTERVAL:
                    self.audio_system.play_hydration_alert()
                    self.last_hydration_time = current_time

            # Log
            if box is not None:
                self.logger.log(str(dominant_emotion), float(score) if score else 0.0, system_status, alert_triggered)

            # Update Feed UI Frame
            cv2.putText(frame, f"Status: {system_status}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Send to main thread sequentially to avoid blinking issue
            self.root.after(0, self.update_frame, imgtk)
            
        # Loop ends when monitoring is stopped
        if self.cap:
            self.cap.release()

def main():
    root = tk.Tk()
    app = SmartStudyApp(root)
    
    def on_closing():
        app.is_monitoring = False
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
