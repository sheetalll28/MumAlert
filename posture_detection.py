class PostureDetector:
    def __init__(self):
        self.baseline_y = None
        self.baseline_w = None
        self.calibration_frames = 0
        self.calibration_max = 30 
    def check_posture(self, box):
        """
        Takes the face bounding box [x, y, w, h] from the emotion detector 
        and calculates if the posture is bad based on relative changes.
        """
        if not box:
            return False, "No face detected"
        x, y, w, h = box
        if self.calibration_frames < self.calibration_max:
            if self.baseline_y is None:
                self.baseline_y = y
                self.baseline_w = w
            else:
                self.baseline_y = int((self.baseline_y * self.calibration_frames + y) / (self.calibration_frames + 1))
                self.baseline_w = int((self.baseline_w * self.calibration_frames + w) / (self.calibration_frames + 1))
            self.calibration_frames += 1
            return False, "Calibrating..."
        slouch_threshold = self.baseline_h_scaled_threshold(self.baseline_w)
        if y - self.baseline_y > slouch_threshold:
            return True, "Slouching / Hunched over"
        if w > self.baseline_w * 1.4:
            return True, "Leaning too close to screen"
        return False, "Good Posture"
    def baseline_h_scaled_threshold(self, width):
        return width * 0.5
    def reset_calibration(self):
        """
        Call this if the user manually resets their position.
        """
        self.baseline_y = None
        self.baseline_w = None
        self.calibration_frames = 0
