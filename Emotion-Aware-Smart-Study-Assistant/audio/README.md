# Audio Placeholder Directory

This application defaults to using `pyttsx3` for real-time Text-To-Speech (TTS) offline generation. Thus, it does not strictly need pre-recorded audio files.

If you wish to use pre-recorded MP3 or WAV files instead (for a more human-sounding voice):
1. Place your `alert_1.mp3`, `alert_2.mp3` files here.
2. Install the `pygame` or `playsound` library.
3. Modify the `audio_alert.py` file to load and play random files from this directory instead of initializing the TTS engine.
