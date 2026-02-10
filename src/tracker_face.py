# src/tracker_face.py
import cv2
import mediapipe as mp

class FaceTracker:
    def __init__(self, det_conf=0.7, track_conf=0.7):
        self.mp_face = mp.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=det_conf,
            min_tracking_confidence=track_conf
        )

    def process(self, frame_bgr):
        """
        Returns:
          face = {
            "lm": [(x,y)...]  # 468+ landmarks
          }
          or None
        """
        h, w, _ = frame_bgr.shape
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        if not result.multi_face_landmarks:
            return None

        face_landmarks = result.multi_face_landmarks[0]
        lm = []
        for p in face_landmarks.landmark:
            x, y = int(p.x * w), int(p.y * h)
            lm.append((x, y))

        return {"lm": lm}
