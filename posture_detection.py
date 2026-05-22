class PostureDetector:
    def __init__(self):
        self.baseline_y = None
        self.baseline_w = None
        self.calibration_frames = 0
        self.calibration_max = 15   # reduced from 30 — calibrates faster

    def check_posture(self, box):
        """
        Takes the face bounding box [x, y, w, h] from the emotion detector
        and calculates if the posture is bad based on relative changes.
        Returns (is_bad_posture: bool, reason: str).
        """
        if box is None:
            return False, "No face detected"

        x, y, w, h = box

        # ---- Calibration phase ----
        if self.calibration_frames < self.calibration_max:
            if self.baseline_y is None:
                self.baseline_y = y
                self.baseline_w = w
            else:
                # Rolling average
                self.baseline_y = int(
                    (self.baseline_y * self.calibration_frames + y)
                    / (self.calibration_frames + 1)
                )
                self.baseline_w = int(
                    (self.baseline_w * self.calibration_frames + w)
                    / (self.calibration_frames + 1)
                )
            self.calibration_frames += 1
            remaining = self.calibration_max - self.calibration_frames
            return False, f"Calibrating... ({remaining} frames left)"

        # ---- Detection phase ----
        slouch_threshold = self.baseline_w * 0.15   # tighter than original 0.25

        # Head dropped below baseline → slouching
        if y - self.baseline_y > slouch_threshold:
            return True, "Slouching / Hunched over"

        # Face noticeably larger → leaning in too close
        if w > self.baseline_w * 1.15:
            return True, "Leaning too close to screen"

        # Face noticeably smaller → leaning too far back
        if w < self.baseline_w * 0.80:
            return True, "Sitting too far from screen"

        return False, "Good Posture"

    def reset_calibration(self):
        """Call this if the user manually resets their position."""
        self.baseline_y = None
        self.baseline_w = None
        self.calibration_frames = 0
