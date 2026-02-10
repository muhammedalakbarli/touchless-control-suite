import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time

pyautogui.FAILSAFE = False

SCREEN_W, SCREEN_H = pyautogui.size()
CAM_W, CAM_H = 640, 480

SMOOTHING = 8
FRAME_MARGIN = 80

CLICK_THRESHOLD = 28
CLICK_COOLDOWN = 0.35

SCROLL_SPEED = 60
SCROLL_COOLDOWN = 0.10

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, CAM_W)
cap.set(4, CAM_H)

prev_x, prev_y = 0, 0
last_click_time = 0
last_scroll_time = 0
dragging = False
paused = False

def dist(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def fingers_up(lm, hand_label):
    """
    hand_label: 'Left' or 'Right'
    Returns [thumb, index, middle, ring, pinky]
    """
    fingers = [0, 0, 0, 0, 0]

    # Thumb: depends on left/right hand
    # Right hand: thumb tip x > thumb ip x
    # Left hand:  thumb tip x < thumb ip x
    if hand_label == "Right":
        fingers[0] = 1 if lm[4][0] > lm[3][0] else 0
    else:
        fingers[0] = 1 if lm[4][0] < lm[3][0] else 0

    tips = [8, 12, 16, 20]
    pip = [6, 10, 14, 18]

    for i in range(4):
        fingers[i+1] = 1 if lm[tips[i]][1] < lm[pip[i]][1] else 0

    return fingers

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
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

        cv2.rectangle(frame, (FRAME_MARGIN, FRAME_MARGIN), (w-FRAME_MARGIN, h-FRAME_MARGIN), (255, 255, 255), 2)

        # Store hands by label
        hands_data = {}

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                label = handedness.classification[0].label  # "Left" or "Right"

                lm = []
                for point in hand_landmarks.landmark:
                    x, y = int(point.x * w), int(point.y * h)
                    lm.append((x, y))

                hands_data[label] = {
                    "lm": lm,
                    "landmarks": hand_landmarks
                }

                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # label draw
                cx, cy = lm[0]
                cv2.putText(frame, label, (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        # -------------------------
        # LEFT HAND: Scroll + Pause
        # -------------------------
        if "Left" in hands_data:
            lmL = hands_data["Left"]["lm"]
            fL = fingers_up(lmL, "Left")

            totalL = sum(fL)

            # Open palm = pause/unpause (5 fingers)
            if totalL == 5:
                paused = True
                cv2.putText(frame, "PAUSED (Left Palm)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            else:
                paused = False

            # 2 fingers (index+middle) = scroll
            if fL[1] == 1 and fL[2] == 1 and fL[3] == 0 and fL[4] == 0:
                ix, iy = lmL[8]
                mx, my = lmL[12]

                now = time.time()
                if now - last_scroll_time > SCROLL_COOLDOWN:
                    if my < iy - 10:
                        pyautogui.scroll(SCROLL_SPEED)
                        cv2.putText(frame, "SCROLL UP (Left)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
                    elif my > iy + 10:
                        pyautogui.scroll(-SCROLL_SPEED)
                        cv2.putText(frame, "SCROLL DOWN (Left)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

                    last_scroll_time = now

        # -------------------------
        # RIGHT HAND: Mouse Control
        # -------------------------
        if "Right" in hands_data:
            lmR = hands_data["Right"]["lm"]
            fR = fingers_up(lmR, "Right")
            totalR = sum(fR)

            ix, iy = lmR[8]
            tx, ty = lmR[4]

            # Move cursor only if not paused
            if not paused:
                # Index up only = move
                if fR[1] == 1 and fR[2] == 0 and fR[3] == 0 and fR[4] == 0:
                    screen_x = np.interp(ix, (FRAME_MARGIN, w - FRAME_MARGIN), (0, SCREEN_W))
                    screen_y = np.interp(iy, (FRAME_MARGIN, h - FRAME_MARGIN), (0, SCREEN_H))

                    curr_x = prev_x + (screen_x - prev_x) / SMOOTHING
                    curr_y = prev_y + (screen_y - prev_y) / SMOOTHING

                    pyautogui.moveTo(curr_x, curr_y)
                    prev_x, prev_y = curr_x, curr_y

                    cv2.putText(frame, "MOVE (Right)", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Click pinch
            d_click = dist((ix, iy), (tx, ty))
            cv2.line(frame, (ix, iy), (tx, ty), (255, 255, 255), 2)

            if d_click < CLICK_THRESHOLD and not paused:
                now = time.time()
                if now - last_click_time > CLICK_COOLDOWN:
                    pyautogui.click()
                    last_click_time = now
                    cv2.putText(frame, "CLICK (Right)", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

            # Drag with fist (0 fingers)
            if totalR == 0 and not paused:
                if not dragging:
                    pyautogui.mouseDown()
                    dragging = True
                    cv2.putText(frame, "DRAG START (Right)", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            else:
                if dragging:
                    pyautogui.mouseUp()
                    dragging = False
                    cv2.putText(frame, "DRAG STOP (Right)", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            cv2.putText(frame, f"Right Fingers: {fR}", (20, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if "Left" in hands_data:
            fL_dbg = fingers_up(hands_data["Left"]["lm"], "Left")
            cv2.putText(frame, f"Left Fingers: {fL_dbg}", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("IRONMAN MODE (ESC to exit)", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
