# 🧠 MumAlert: Technical Design Decisions & Architectural Evolution

This document traces the engineering path of **MumAlert**, detailing the transition from a local desktop client to a production-ready, cloud-deployed real-time monitoring suite. It highlights key architectural pivots, the engineering challenges encountered, and how we engineered around each constraint.

---

## 🗺️ Architectural Overview

The core mission of **MumAlert** is to act as a gentle, ambient guardian that monitors your **posture**, **stress levels (emotions)**, and **hydration** in real time, mimicking a parent's caring watch.

```mermaid
flowchart TD
    subgraph Browser (Client Side)
        Camera[User Camera Feed] -->|HTML5 Capture| WebRTC[WebRTC Client]
        BrowserTTS[Web Speech Synthesis] <==|Dynamic JS Injection| BrowserEngine[Audio Alert Output]
    end

    subgraph Streamlit Cloud (Server Side)
        WebRTC -->|Secure WebRTC Stream| Streamer[streamlit-webrtc]
        Streamer -->|RGB Frame Array| Pipeline[Processing Pipeline]
        
        subgraph Pipeline Modules
            FaceDet[Haar Cascade Face Detector] -->|Face Bounding Box| Emotion[FER Neural Net Engine]
            FaceDet -->|Box Geometry| Posture[Relative Position Engine]
        end
        
        Emotion -->|Stress Flag| Decision[Inference & Alert Logic]
        Posture -->|Slouch Flag| Decision
        
        Decision -->|Alert Event| AlertQueue[Async Alert Queue]
        AlertQueue -->|JS Code payload| BrowserEngine
    end
```

---

## 🔄 1. The Great Pivot: Desktop GUI to Deployed Web App

### **The Original Architecture (`main.py`)**
* **Framework:** Local Python `Tkinter` interface.
* **Camera Access:** Directly accessed the laptop's physical webcam hardware index via `cv2.VideoCapture(0)`.
* **Audio Alerts:** Powered by `pyttsx3` communicating with local OS audio drivers (SAPI5 on Windows / NSSpeechSynthesizer on macOS).

### **The Challenges of Desktop Deployment**
* **Friction to Run:** Users had to clone the repo, install Python, set up virtual environments, configure system-level C++ build tools (required by some libraries), and troubleshoot driver conflicts.
* **Portability:** Accessing cameras via hardcoded indices (`0`, `1`, `2`) frequently crashed if virtual camera drivers or OBS virtual cameras were active.

### **The Solution: Migration to Streamlit WebRTC (`app.py`)**
We transitioned to a web application using **Streamlit** and **Streamlit-WebRTC** (`streamlit-webrtc`).
* **Why:** This shifts the entire visual execution, model deployment, and computer vision computation onto a cloud server, leaving the user with a zero-setup, one-click web link.
* **Hardware Bridging:** Frames are captured directly in the browser using standard web APIs (`getUserMedia`) and streamed asynchronously to our server-side processors, rendering the local OS driver issue completely obsolete.

---

## 🚧 2. Engineering Challenges & Technical Triumphs

### 🛡️ Challenge A: Audio Silence on the Cloud (TTS Driver Failure)
* **The Problem:** The original desktop version used `pyttsx3`. When this was executed on a remote Streamlit Cloud container (Linux virtual machine), it failed silently or crashed with `OSError`. Since cloud containers run in a "headless" state with no physical speakers or audio hardware, local OS drivers do not exist.
* **The Pivot:** We could not generate audio files (like `.mp3` or `.wav`) on the server and stream them back, as this introduced seconds of network latency and heavy network overhead.
* **The Engineering Solution:** Built an elegant browser-native speech system in `app.py` using Streamlit's raw HTML/JS component bridge (`components.html`):
  ```python
  def speak_in_browser(text):
      js_code = f"""
      <script>
          var msg = new SpeechSynthesisUtterance({text!r});
          msg.rate = 1.0;
          msg.pitch = 1.05;
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(msg);
      </script>
      """
      components.html(js_code, height=0)
  ```
  * **Result:** Real-time, zero-latency, highly customized text-to-speech utilizing the browser's built-in **Web Speech API**.

---

### 🌐 Challenge B: Missing OS Shared Libraries (`libgthread`)
* **The Problem:** Deployed Python virtual environments are notoriously bare. The moment `cv2` (OpenCV) was imported on the cloud server, it crashed with:
  `ImportError: libgthread-2.0.so.0: cannot open shared object file: No such file or directory`
* **The Pivot:** Added a `packages.txt` file (Streamlit's interface to `apt-get`) to install `libgl1` and `libglib2.0-0`.
* **The Secondary Hurdle (Debian Trixie Upgrade):** Suddenly, the build system failed with:
  `libglib2.0-0 has unmet dependencies / is not installable`. 
  Streamlit Cloud had upgraded its base containers to **Debian Trixie** (where libraries were transitioned to support the 64-bit time format).
* **The Engineering Solution:** Tracked down the new Debian package architecture naming convention and replaced `libglib2.0-0` with `libglib2.0-0t64`.

---

### 📦 Challenge C: The `pkg_resources` & `setuptools` Deprecation War
* **The Problem:** Deploying the application suddenly failed with a hard crash:
  `ModuleNotFoundError: No module named 'pkg_resources'`
* **The Diagnosis:** The emotion-recognition library (`fer`) utilizes legacy import calls via `pkg_resources`. In modern Python environments, installing dependencies defaults to downloading the latest packages. Recently, **`setuptools` version 70.0.0+** completely removed `pkg_resources` from its API. 
* **The Engineering Solution:** 
  1. We pinned the setup requirements strictly to `setuptools<70.0.0` inside `requirements.txt`.
  2. To guarantee safety even if the server environment pre-installed a newer setuptools in its base image, we engineered an active dynamic importing interceptor directly in the Python source code:
     ```python
     import subprocess, sys, importlib
     try:
         import pkg_resources
     except ImportError:
         subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools<70.0.0"])
         importlib.invalidate_caches()
     ```

---

### ⚡ Challenge D: The WebRTC Stream Freeze (MTCNN Weight Block)
* **The Problem:** When the user clicked "Start", the camera stream appeared but **no bounding boxes, emotion overlays, or real-time logging activated**.
* **The Diagnosis:** The facial emotion tracker was configured with `mtcnn=True` (Multi-task Cascaded Convolutional Networks). 
  1. MTCNN is a deep-learning face-detection model that tries to download pre-trained weights from external repositories at runtime. In Streamlit's sandbox, this network request either timed out or was blocked.
  2. Even when cached, MTCNN requires massive CPU execution times (often taking 600ms+ per frame), causing severe frame dropping and crashing the async WebRTC pipeline.
* **The Engineering Solution:** We reconfigured the detector to use `mtcnn=False`.
  * **Result:** This falls back to OpenCV's built-in **Haar Cascade Face Detector**. Because Haar Cascades are baked directly into the library binaries, they require **zero external weight downloads** and execute in under **10 milliseconds** on ordinary cloud CPUs, instantly restoring smooth 30fps overlays.

---

### 🎨 Challenge E: Invisible UI Toggles (Contrast Issues)
* **The Problem:** We injected a custom, modern dark UI styling with deep blue/purple gradients:
  `background: linear-gradient(135deg, #0f0c29, #302b63, #24243e)`
  However, this caused Streamlit's default light-mode toggle elements ("Active Modules") to render their text labels in a dark, muddy grey. They were virtually invisible against our background.
* **The Engineering Solution:** We injected specialized overriding CSS styles directly into the document DOM, targeting the underlying Streamlit Markdown containers:
  ```css
  div[data-testid="stWidgetLabel"],
  div[data-testid="stWidgetLabel"] p,
  label,
  span[data-testid="stWidgetLabel"] {
      color: #f8f9fa !important;
      font-weight: 500 !important;
  }
  ```
  * **Result:** Crisp, highly readable labels that pop out with premium contrast.

---

## 📈 Summary of Technical Pivots

| Component | Legacy Desktop Approach (`main.py`) | Cloud-Production Approach (`app.py`) | Reason for Change |
| :--- | :--- | :--- | :--- |
| **GUI Framework** | Tkinter | Streamlit Cloud | Portability, zero-setup link sharing, instant cloud deployment |
| **Video Capture** | Local index `cv2.VideoCapture` | `streamlit-webrtc` | Cloud servers don't have access to your local physical webcam |
| **Audio Synthesizer**| `pyttsx3` (OS Driver-dependent) | Web Speech API (`speechSynthesis`) | Cloud containers are headless and lack local speakers / audio devices |
| **Face Detection** | MTCNN (Deep Learning) | Haar Cascades (`mtcnn=False`) | MTCNN is extremely slow and blocks container builds with model downloads |
| **System Libraries** | Presumed pre-installed | `packages.txt` with `libglib2.0-0t64` | Native C++ libraries needed for OpenCV missing in slim Linux containers |
| **Dependency Engine**| standard `pip` | pinned `setuptools<70.0.0` | Restores the deprecated `pkg_resources` needed internally by `fer` |

---

### 💡 The Takeaway
By shifting from OS-reliant scripts to lightweight, web-compatible components (like Haar Cascades and the browser-native Web Speech API), we transformed **MumAlert** into a robust, high-performance web app that loads instantly in any modern browser without sacrificing real-time precision. 💛
