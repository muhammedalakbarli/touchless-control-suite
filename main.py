# main.py
import cv2
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

        hands_data = tracker.process(frame)
        tracker.draw(frame, hands_data)

        # UI Box
        cv2.rectangle(frame, (Config.FRAME_MARGIN, Config.FRAME_MARGIN),
                      (w - Config.FRAME_MARGIN, h - Config.FRAME_MARGIN),
                      (255, 255, 255), 2)

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

        # Debug UI
        status = "PAUSED" if engine.paused else "ACTIVE"
        cv2.putText(frame, f"STATUS: {status}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Touchless Control Suite v1 (ESC to exit)", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
