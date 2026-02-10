# src/face_gesture_engine.py
import time
import math

class FaceGestureEngine:
    """
    Nose tip = cursor move
    Blink = click
    """

    def __init__(self, blink_threshold=0.20, click_cooldown=0.6):
        self.blink_threshold = blink_threshold
        self.click_cooldown = click_cooldown
        self.last_click_time = 0

    def _dist(self, p1, p2):
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    def eye_aspect_ratio(self, lm, top, bottom, left, right):
        """
        EAR formula:
        (vertical1 + vertical2) / (2 * horizontal)
        """
        v1 = self._dist(lm[top], lm[bottom])
        h1 = self._dist(lm[left], lm[right])

        if h1 == 0:
            return 1.0

        return v1 / h1

    def get_actions(self, face_data):
        actions = []

        lm = face_data["lm"]

        # Nose tip landmark (approx)
        # 1 = nose tip (works well in mediapipe face mesh)
        nx, ny = lm[1]

        actions.append(("MOVE", {"x": nx, "y": ny}))

        # LEFT EYE landmarks (simple)
        # top=159 bottom=145 left=33 right=133
        ear_left = self.eye_aspect_ratio(lm, 159, 145, 33, 133)

        # RIGHT EYE
        # top=386 bottom=374 left=362 right=263
        ear_right = self.eye_aspect_ratio(lm, 386, 374, 362, 263)

        ear = (ear_left + ear_right) / 2.0

        # Blink detection
        if ear < self.blink_threshold:
            now = time.time()
            if now - self.last_click_time > self.click_cooldown:
                actions.append(("CLICK", {}))
                self.last_click_time = now

        actions.append(("DEBUG", {"ear": ear}))

        return actions
