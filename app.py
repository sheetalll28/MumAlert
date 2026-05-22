import cv2
import time
import queue
import streamlit as st
import streamlit.components.v1 as components
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode

from emotion_detection import EmotionDetector
from posture_detection import PostureDetector

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="MummyAlert", layout="wide", page_icon="💛")

# ==========================================
# CUSTOM CSS — Beautiful Dark UI
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #f0f0f0;
}

/* Ensure widget labels, toggle texts, and other control texts are bright and visible */
div[data-testid="stWidgetLabel"],
div[data-testid="stWidgetLabel"] p,
label,
span[data-testid="stWidgetLabel"] {
    color: #f8f9fa !important;
    font-weight: 500 !important;
}

/* Hero header */
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(90deg, #f7971e, #ffd200);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}

.hero-subtitle {
    font-size: 1.0rem;
    color: #a0a0c0;
    font-weight: 300;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

/* Sentimental description card */
.desc-card {
    background: rgba(255,255,255,0.05);
    border-left: 4px solid #ffd200;
    border-radius: 10px;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 24px;
    line-height: 1.8;
    font-size: 1.05rem;
    color: #d0d0e8;
}

/* Section headings */
.section-heading {
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffd200;
    margin-top: 1.2rem;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Metric cards row */
.metric-row {
    display: flex;
    gap: 12px;
    margin-bottom: 18px;
    flex-wrap: wrap;
}

.metric-card {
    flex: 1;
    min-width: 100px;
    background: rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 14px 16px;
    text-align: center;
    border: 1px solid rgba(255,210,0,0.15);
}

.metric-card .icon { font-size: 1.6rem; }
.metric-card .label {
    font-size: 0.72rem;
    color: #a0a0c0;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Alert log box */
.alert-log {
    background: rgba(255, 80, 80, 0.12);
    border: 1px solid rgba(255, 80, 80, 0.4);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 0.95rem;
    color: #ffaaaa;
    margin-top: 8px;
}

/* Style Streamlit buttons */
div.stButton > button {
    background: linear-gradient(90deg, #f7971e, #ffd200);
    color: #1a1a2e;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    width: 100%;
    cursor: pointer;
    transition: opacity 0.2s;
}
div.stButton > button:hover { opacity: 0.85; }

/* Slider accent */
.stSlider > div > div > div { background: #ffd200 !important; }

/* Input box */
.stTextInput > div > input {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,210,0,0.3);
    border-radius: 8px;
    color: #f0f0f0;
}

/* Info/success/error overrides */
div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Hide Streamlit default header & footer */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
/* Make Streamlit toggle label text bright for visibility */
[data-testid="stToggle"] label, .stToggle label {
    color: #fff !important;
    font-weight: 600;
    letter-spacing: 0.01em;
}
/* Make Streamlit toggle label text bright yellow for visibility */
[data-testid="stToggle"] label, .stToggle label {
    color: #ffd700 !important;
    font-weight: 700;
    letter-spacing: 0.01em;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HERO HEADER
# ==========================================
st.markdown('<div class="hero-title">💛 MumAlert</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Real-Time Posture · Stress · Hydration Monitoring System</div>', unsafe_allow_html=True)

st.markdown("""
<div class="desc-card">
  You know how your mum always knew when you were stressed, sitting wrong, or hadn't had water in hours - even before you did?
  <br><br>
  <strong>MumAlert</strong> is that feeling, built into your screen. It watches over you while you study, gently nudging you to sit up straight, take a breath, and stay hydrated - just like she would. 💛
  <br><br>
  Because sometimes, all you need is a quiet reminder that someone cares.
</div>
""", unsafe_allow_html=True)

# ==========================================
# AUDIO via Web Speech API (browser-native)
# ==========================================
def speak_in_browser(text):
    """Uses the browser's built-in Web Speech API - zero files, zero encoding."""
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

# ==========================================
# SESSION STATE — hydration settings
# ==========================================
if "hydration_interval" not in st.session_state:
    st.session_state.hydration_interval = 1          # seconds (1s for testing)
if "hydration_message" not in st.session_state:
    st.session_state.hydration_message = "Hey! Don't forget to drink some water. Stay hydrated!"
if "last_hydration_time" not in st.session_state:
    st.session_state.last_hydration_time = time.time()
if "emotion_enabled" not in st.session_state:
    st.session_state.emotion_enabled = True
if "posture_enabled" not in st.session_state:
    st.session_state.posture_enabled = True

# ==========================================
# WEBRTC VIDEO PROCESSOR
# ==========================================
class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        # Lazy-loaded to avoid blocking WebRTC offer processing (10s timeout)
        self.detector        = None
        self.posture_detector = None
        self._models_loaded  = False

        self.PERSISTENCE_THRESHOLD = 3.0
        self.POSTURE_THRESHOLD     = 3.0
        self.COOLDOWN_PERIOD       = 10.0

        self.negative_start_time   = None
        self.bad_posture_start_time = None
        self.last_bad_posture_time = None
        self.last_negative_time    = None
        self.last_alert_time       = 0.0

        # Public flags — updated from UI via ctx.video_processor
        self.emotion_enabled = True
        self.posture_enabled = True

        self.alert_queue = queue.Queue()

    def _load_models(self):
        """Load heavy models on first frame to avoid WebRTC timeout."""
        if not self._models_loaded:
            self.detector         = EmotionDetector()
            self.posture_detector = PostureDetector()
            self._models_loaded   = True

    def transform(self, frame):
        self._load_models()
        img = frame.to_ndarray(format="bgr24")
        img = cv2.resize(img, (1280, 720))
        img = cv2.flip(img, 1)

        current_time = time.time()
        in_cooldown  = (current_time - self.last_alert_time) < self.COOLDOWN_PERIOD
        system_status = "Monitoring..."
        alert_visual  = ""

        dominant_emotion, score, box = self.detector.detect_emotion(img)
        is_bad_posture, posture_reason = self.posture_detector.check_posture(box)

        if box is not None:
            x, y, w, h = box

            if dominant_emotion:
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 210, 0), 2)
                cv2.putText(img, f"{dominant_emotion} ({score:.2f})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 210, 0), 2)

            # --- POSTURE (only if enabled) ---
            if self.posture_enabled:
                if is_bad_posture:
                    system_status = f"Bad Posture: {posture_reason}"
                    self.last_bad_posture_time = current_time
                    if self.bad_posture_start_time is None:
                        self.bad_posture_start_time = current_time
                    elif (current_time - self.bad_posture_start_time) >= self.POSTURE_THRESHOLD:
                        if not in_cooldown:
                            self.alert_queue.put("posture")
                            self.last_alert_time = current_time
                            self.bad_posture_start_time = None
                else:
                    if self.last_bad_posture_time and (current_time - self.last_bad_posture_time) > 1.5:
                        self.bad_posture_start_time = None
            else:
                self.bad_posture_start_time = None

            # --- EMOTION (only if enabled) ---
            if self.emotion_enabled:
                if dominant_emotion and self.detector.is_negative(dominant_emotion):
                    if not is_bad_posture:
                        system_status = f"Negative Emotion: {dominant_emotion}"
                    self.last_negative_time = current_time
                    if self.negative_start_time is None:
                        self.negative_start_time = current_time
                    elif (current_time - self.negative_start_time) >= self.PERSISTENCE_THRESHOLD:
                        if not in_cooldown:
                            self.alert_queue.put("stress")
                            self.last_alert_time = current_time
                            self.negative_start_time = None
                else:
                    if self.last_negative_time and (current_time - self.last_negative_time) > 1.0:
                        self.negative_start_time = None
            else:
                self.negative_start_time = None

        if in_cooldown:
            alert_visual = "COOLDOWN ACTIVE"

        cv2.putText(img, f"Status: {system_status}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
        if alert_visual:
            cv2.putText(img, alert_visual, (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 80, 255), 2)
        return img


# ==========================================
# MAIN LAYOUT
# ==========================================
cam_col, ctrl_col = st.columns([3, 2])

with cam_col:
    st.markdown('<div class="section-heading">📹 Live Camera Feed</div>', unsafe_allow_html=True)
    ctx = webrtc_streamer(
        key="mummy-alert",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoProcessor,
        media_stream_constraints={
            "video": {
                "width":     {"ideal": 1280},
                "height":    {"ideal": 720},
                "frameRate": {"ideal": 30}
            },
            "audio": False
        },
        async_processing=True
    )

with ctrl_col:

    # --- Active Modules Toggles ---
    st.markdown('<div class="section-heading">⚙️ Active Modules</div>', unsafe_allow_html=True)
    emotion_enabled = st.toggle("😤 Emotion Alerts", value=st.session_state.emotion_enabled, key="toggle_emotion")
    posture_enabled = st.toggle("🪑 Posture Alerts", value=st.session_state.posture_enabled, key="toggle_posture")
    hydration_enabled = st.toggle("💧 Hydration Reminders", value=True, key="toggle_hydration")

    # Sync toggle state to session and live video processor
    st.session_state.emotion_enabled = emotion_enabled
    st.session_state.posture_enabled = posture_enabled
    st.session_state.hydration_enabled = hydration_enabled
    if ctx.state.playing and ctx.video_processor:
        ctx.video_processor.emotion_enabled = emotion_enabled
        ctx.video_processor.posture_enabled = posture_enabled

    # --- Status Metrics ---
    st.markdown('<div class="section-heading">📊 Monitor Status</div>', unsafe_allow_html=True)
    def _badge(on): return "🟢" if on else "🔴"
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="icon">{_badge(emotion_enabled)}😤</div><div class="label">Stress Watch</div></div>
        <div class="metric-card"><div class="icon">{_badge(posture_enabled)}🪑</div><div class="label">Posture Watch</div></div>
        <div class="metric-card"><div class="icon">{_badge(hydration_enabled)}💧</div><div class="label">Hydration Watch</div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- Posture Calibration ---
    st.markdown('<div class="section-heading">🎯 Posture Calibration</div>', unsafe_allow_html=True)
    if st.button("Reset Posture Baseline"):
        if ctx.state.playing and ctx.video_processor:
            ctx.video_processor.posture_detector.reset_calibration()
            st.success("✅ Baseline reset! Sit up straight — recalibrating for 1 second.")

    # --- Hydration Customization ---
    st.markdown('<div class="section-heading">💧 Hydration Alert Settings</div>', unsafe_allow_html=True)

    hydration_message = st.text_input(
        "Custom hydration message",
        value=st.session_state.hydration_message,
        placeholder="e.g. Drink water, beta! 💛",
        key="hydration_msg_input"
    )
    st.session_state.hydration_message = hydration_message

    # Slider: 1s for testing, up to 45 minutes. Default = 1s for now.
    # For real use, a good value is 1200–1800 seconds (20–30 minutes).
    hydration_interval = st.slider(
        "Remind me every (seconds)",
        min_value=1,
        max_value=2700,            # 45 minutes max
        value=st.session_state.hydration_interval,
        step=1,
        help="Set to 1s for testing. For real study sessions, 1200–1800s (20–30 min) is ideal."
    )
    st.session_state.hydration_interval = hydration_interval
    st.caption(f"⏱ Currently set to every **{hydration_interval}s** — "
               f"{'🧪 Testing mode' if hydration_interval < 30 else '✅ Real-time mode'}")

    # --- Logs ---
    st.markdown('<div class="section-heading">🔔 Alert Log</div>', unsafe_allow_html=True)
    log_placeholder = st.empty()


# ==========================================
# POLLING LOOP: alerts + hydration timer
# ==========================================
ALERT_MESSAGES = {
    "stress":  "Hey, you look stressed. Please take a short rest.",
    "posture": "Please sit up straight and correct your posture.",
}

if ctx.state.playing:
    while True:
        now = time.time()

        # --- Hydration timer (runs independently from WebRTC) ---
        if (now - st.session_state.last_hydration_time) >= st.session_state.hydration_interval:
            speak_in_browser(st.session_state.hydration_message)
            log_placeholder.markdown(
                f'<div class="alert-log">💧 <strong>Hydration Reminder:</strong> {st.session_state.hydration_message}</div>',
                unsafe_allow_html=True
            )
            st.session_state.last_hydration_time = now
            time.sleep(4)
            st.rerun()

        # --- Stress / Posture alerts from video processor ---
        if ctx.video_processor:
            try:
                alert_key = ctx.video_processor.alert_queue.get_nowait()
                message   = ALERT_MESSAGES.get(alert_key, "Please take a break.")
                speak_in_browser(message)
                icon = "😤" if alert_key == "stress" else "🪑"
                log_placeholder.markdown(
                    f'<div class="alert-log">{icon} <strong>Alert:</strong> {message}</div>',
                    unsafe_allow_html=True
                )
                time.sleep(4)
                st.rerun()
            except queue.Empty:
                pass

        time.sleep(1)
        st.rerun()
