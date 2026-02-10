# src/tracker_hand.py
import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self, max_hands=2, det_conf=0.7, track_conf=0.7):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=det_conf,
            min_tracking_confidence=track_conf
        )

    def process(self, frame_bgr):
        """
        Returns:
          hands_data = {
            "Left": {"lm": [(x,y)...], "landmarks": ..., "label": "Left"},
            "Right": {...}
          }
        """
        h, w, _ = frame_bgr.shape
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        hands_data = {}

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                label = handedness.classification[0].label  # Left / Right

                lm = []
                for point in hand_landmarks.landmark:
                    x, y = int(point.x * w), int(point.y * h)
                    lm.append((x, y))

                hands_data[label] = {
                    "lm": lm,
                    "landmarks": hand_landmarks,
                    "label": label
                }

        return hands_data

    def draw(self, frame_bgr, hands_data):
        for _, data in hands_data.items():
            self.mp_draw.draw_landmarks(
                frame_bgr,
                data["landmarks"],
                self.mp_hands.HAND_CONNECTIONS
            )
