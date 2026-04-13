# Emotion-Aware Smart Study Assistant

## Abstract
Continuous studying often leads to fatigue, stress, and burnout, which negatively affect a student's learning efficiency. The "Emotion-Aware Smart Study Assistant" is an intelligent software-based prototype that addresses this problem by monitoring the student's facial expressions in real time using a standard webcam. By applying deep learning-based Facial Emotion Recognition (FER), the system categorizes the user's emotional state (e.g., happy, neutral, sad, angry). If negative emotions persist beyond a predefined threshold, the assistant proactively intervenes with a soft, text-to-speech audio alert encouraging the student to take a break or hydrate. The system includes cooldown mechanisms to prevent annoyance and meticulously logs all emotional states for future analysis.

## Novelty Statement
Unlike traditional wellness apps that rely on manual user inputs or fixed timers (like the Pomodoro technique), this system introduces an adaptive, non-intrusive approach to mental wellbeing. It dynamically responds to the *actual* cognitive and emotional state of the user in real-time. The core novelty lies in the localized, threshold-based persistence logic that ensures interventions only happen when genuinely needed, significantly reducing false positives from transient facial expressions.

## Text-Based Architecture Diagram
```mermaid
graph TD
    A[Webcam Input] --> B[OpenCV Frame Capture]
    B --> C{Facial Emotion Recognition Model (FER)}
    C -->|Detects Happy/Neutral| D[Update Display & Log]
    C -->|Detects Sad/Angry/Fear| E[Persistence Timer Started]
    
    E --> F{Negative Emotion > 3 seconds?}
    F -->|No| D
    F -->|Yes| G{In Cooldown Period?}
    
    G -->|Yes| D
    G -->|No| H[Trigger Audio Alert - pyttsx3 Thread]
    H --> I[Reset Timer & Enter Cooldown]
    I --> D
```

## Setup and Run Instructions

### 1. Prerequisites
- A PC/Laptop with a functioning webcam.
- Python 3.8+ installed.

### 2. Installation
Open a terminal and navigate to the project directory, then run:
```bash
pip install -r requirements.txt
```

### 3. Usage
Run the main script:
```bash
python main.py
```
- A window will pop up showing your webcam feed.
- Look at the camera. If you mimic a "sad" or "angry" face for 3-5 seconds, an audio voice will remind you to take a break.
- Press `q` to quit the application.

### 4. Logging
All detected emotions, along with confidence scores and whether a break was triggered, are logged in `emotion_log.csv` located in the same directory. This data can later be used for performance tracking.

---

## Future Scope (IoT Expansion)
While this software-only prototype demonstrates the core intelligence, it is designed with extreme modularity to transition easily into a full IoT project. Future phases can integrate hardware components by passing serial commands (e.g., via `pyserial`) to an ESP32 or Arduino:
1. **LED Feedback:** A tricolor LED could glow green for 'happy/neutral' and switch to red for 'negative' emotions.
2. **Buzzer/Haptic Alerts:** Instead of, or in addition to PC audio, a physical buzzer could provide gentle notifications.
3. **Environment Control:** The ESP32 could trigger smart room integrations, such as dimming the study lamp or playing a physical study playlist via Bluetooth based on the user's stress levels.
4. **Cloud Analytics:** Real-time data could stream to a cloud dashboard (like ThingSpeak or Blynk) for parents or counselors to monitor prolonged stress patterns.

---
