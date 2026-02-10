# main_face.py
import cv2
from src.config import Config
from src.tracker_face import FaceTracker
from src.face_gesture_engine import FaceGestureEngine
from src.mouse_controller import MouseController

def main():
    tracker = FaceTracker()
    engine = FaceGestureEngine(blink_threshold=0.20, click_cooldown=0.6)

    mouse = MouseController(
        smoothing=Config.SMOOTHING,
        frame_margin=Config.FRAME_MARGIN
    )

    if Config.USE_DSHOW:
        cap = cv2.VideoCapture(Config.CAM_INDEX, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(Config.CAM_INDEX)

    cap.set(3, Config.CAM_W)
    cap.set(4, Config.CAM_H)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        face = tracker.process(frame)

        if face:
            actions = engine.get_actions(face)

            for action, payload in actions:
                if action == "MOVE":
                    mouse.move(payload["x"], payload["y"], w, h)

                elif action == "CLICK":
                    mouse.click()

                elif action == "DEBUG":
                    ear = payload["ear"]
                    cv2.putText(frame, f"EAR: {ear:.3f}", (20, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

            # Draw nose point
            nx, ny = face["lm"][1]
            cv2.circle(frame, (nx, ny), 6, (0, 255, 0), -1)

        cv2.putText(frame, "FACE MODE (ESC to exit)", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow("Face Mouse v1", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
# main_face.py
import cv2
from src.config import Config
from src.tracker_face import FaceTracker
from src.face_gesture_engine import FaceGestureEngine
from src.mouse_controller import MouseController

def main():
    tracker = FaceTracker()
    engine = FaceGestureEngine(blink_threshold=0.20, click_cooldown=0.6)

    mouse = MouseController(
        smoothing=Config.SMOOTHING,
        frame_margin=Config.FRAME_MARGIN
    )

    if Config.USE_DSHOW:
        cap = cv2.VideoCapture(Config.CAM_INDEX, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(Config.CAM_INDEX)

    cap.set(3, Config.CAM_W)
    cap.set(4, Config.CAM_H)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        face = tracker.process(frame)

        if face:
            actions = engine.get_actions(face)

            for action, payload in actions:
                if action == "MOVE":
                    mouse.move(payload["x"], payload["y"], w, h)

                elif action == "CLICK":
                    mouse.click()

                elif action == "DEBUG":
                    ear = payload["ear"]
                    cv2.putText(frame, f"EAR: {ear:.3f}", (20, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

            # Draw nose point
            nx, ny = face["lm"][1]
            cv2.circle(frame, (nx, ny), 6, (0, 255, 0), -1)

        cv2.putText(frame, "FACE MODE (ESC to exit)", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow("Face Mouse v1", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
