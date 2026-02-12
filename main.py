# main.py
import cv2
import time

from src.config import Config
from src.tracker_hand import HandTracker
from src.gesture_engine import GestureEngine
from src.mouse_controller import MouseController


def main():
    tracker = HandTracker(max_hands=2)

    engine = GestureEngine(
        click_threshold=Config.CLICK_THRESHOLD,
        click_cooldown=Config.CLICK_COOLDOWN,
        scroll_cooldown=Config.SCROLL_COOLDOWN
    )

    mouse = MouseController(
        smoothing=Config.SMOOTHING,
        frame_margin=Config.FRAME_MARGIN
    )

    # Camera
    if Config.USE_DSHOW:
        cap = cv2.VideoCapture(Config.CAM_INDEX, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(Config.CAM_INDEX)

    cap.set(3, Config.CAM_W)
    cap.set(4, Config.CAM_H)

    # FPS
    prev_time = time.time()
    fps = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # FPS calc
        curr_time = time.time()
        dt = curr_time - prev_time
        prev_time = curr_time
        if dt > 0:
            fps = 1 / dt

        # Tracking
        hands_data = tracker.process(frame)
        tracker.draw(frame, hands_data)

        # UI Box (active tracking zone)
        cv2.rectangle(
            frame,
            (Config.FRAME_MARGIN, Config.FRAME_MARGIN),
            (w - Config.FRAME_MARGIN, h - Config.FRAME_MARGIN),
            (255, 255, 255),
            2
        )

        # Get actions
        actions = engine.get_actions(hands_data)

        # Execute actions
        for action, payload in actions:
            if action == "MOVE":
                mouse.move(payload["x"], payload["y"], w, h)

            elif action == "CLICK":
                mouse.click()

            elif action == "SCROLL":
                mouse.scroll(payload["amount"])

            elif action == "DRAG_START" and Config.ENABLE_DRAG:
                mouse.drag_start()

            elif action == "DRAG_STOP" and Config.ENABLE_DRAG:
                mouse.drag_stop()

        # -------------------------
        # PRO OVERLAY UI
        # -------------------------
        status = "PAUSED" if engine.paused else "ACTIVE"
        has_left = "Left" in hands_data
        has_right = "Right" in hands_data

        # Header
        cv2.putText(frame, "Touchless Control Suite v2", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        # Status
        cv2.putText(frame, f"STATUS: {status}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Hands
        cv2.putText(frame, f"Left Hand: {'ON' if has_left else 'OFF'}", (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        cv2.putText(frame, f"Right Hand: {'ON' if has_right else 'OFF'}", (20, 135),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        # FPS
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 165),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        # Gesture legend
        cv2.putText(frame, "GESTURES:", (20, 210),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.putText(frame, "Right: Index=Move | Pinch=Click | Fist=Drag", (20, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        cv2.putText(frame, "Left: 2 fingers=Scroll | Palm=Pause", (20, 265),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        # Show
        cv2.imshow("Touchless Control Suite (ESC to exit)", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
