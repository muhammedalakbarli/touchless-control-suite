import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time

# -------------------------
# Settings
# -------------------------
pyautogui.FAILSAFE = False  # mouse küncə gedəndə proqram dayanmasın

SCREEN_W, SCREEN_H = pyautogui.size()

CAM_W, CAM_H = 640, 480

SMOOTHING = 7  # böyük olsa daha smooth olar (amma gecikmə artar)

CLICK_THRESHOLD = 30  # barmaqlar yaxınlaşanda click
CLICK_COOLDOWN = 0.35  # ardıcıl click olmasın

# -------------------------
# Mediapipe Setup
# -------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(3, CAM_W)
cap.set(4, CAM_H)

prev_x, prev_y = 0, 0
curr_x, curr_y = 0, 0

last_click_time = 0

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]

            # Landmark list
            lm = []
            for id, point in enumerate(hand_landmarks.landmark):
                x, y = int(point.x * w), int(point.y * h)
                lm.append((x, y))

            # Index finger tip = 8
            ix, iy = lm[8]

            # Thumb tip = 4
            tx, ty = lm[4]

            # Draw
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.circle(frame, (ix, iy), 10, (255, 255, 255), cv2.FILLED)
            cv2.circle(frame, (tx, ty), 10, (255, 255, 255), cv2.FILLED)

            # Map camera coords -> screen coords
            screen_x = np.interp(ix, (0, CAM_W), (0, SCREEN_W))
            screen_y = np.interp(iy, (0, CAM_H), (0, SCREEN_H))

            # Smoothing
            curr_x = prev_x + (screen_x - prev_x) / SMOOTHING
            curr_y = prev_y + (screen_y - prev_y) / SMOOTHING

            pyautogui.moveTo(curr_x, curr_y)

            prev_x, prev_y = curr_x, curr_y

            # Click gesture (thumb + index close)
            d = distance((ix, iy), (tx, ty))
            cv2.line(frame, (ix, iy), (tx, ty), (255, 255, 255), 2)

            if d < CLICK_THRESHOLD:
                now = time.time()
                if now - last_click_time > CLICK_COOLDOWN:
                    pyautogui.click()
                    last_click_time = now
                    cv2.putText(frame, "CLICK", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

            cv2.putText(frame, f"Dist: {int(d)}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow("Virtual Mouse (ESC to exit)", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
