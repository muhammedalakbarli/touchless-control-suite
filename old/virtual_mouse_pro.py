import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time

pyautogui.FAILSAFE = False

SCREEN_W, SCREEN_H = pyautogui.size()
CAM_W, CAM_H = 640, 480

# Smoothness
SMOOTHING = 8

# Click
CLICK_THRESHOLD = 28
CLICK_COOLDOWN = 0.35

# Scroll
SCROLL_SPEED = 35
SCROLL_COOLDOWN = 0.12

# Drag
DRAG_THRESHOLD = 35

# Frame reduction (cursor area)
FRAME_MARGIN = 80

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, CAM_W)
cap.set(4, CAM_H)

prev_x, prev_y = 0, 0
last_click_time = 0
last_scroll_time = 0
dragging = False

def dist(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def fingers_up(lm):
    """
    Returns list [thumb, index, middle, ring, pinky]
    1 = up, 0 = down
    """
    fingers = [0, 0, 0, 0, 0]

    # Thumb (x comparison)
    if lm[4][0] > lm[3][0]:
        fingers[0] = 1

    # Index, Middle, Ring, Pinky (y comparison)
    tips = [8, 12, 16, 20]
    pip = [6, 10, 14, 18]

    for i in range(4):
        if lm[tips[i]][1] < lm[pip[i]][1]:
            fingers[i+1] = 1

    return fingers

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

        # UI box for cursor area
        cv2.rectangle(frame, (FRAME_MARGIN, FRAME_MARGIN), (w-FRAME_MARGIN, h-FRAME_MARGIN), (255, 255, 255), 2)

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            lm = []
            for point in hand_landmarks.landmark:
                x, y = int(point.x * w), int(point.y * h)
                lm.append((x, y))

            fingers = fingers_up(lm)
            total_fingers = sum(fingers)

            # Key points
            ix, iy = lm[8]   # index tip
            mx, my = lm[12]  # middle tip
            tx, ty = lm[4]   # thumb tip

            # -----------------------------
            # MODE 1: Move Cursor
            # Index up only (or index+thumb)
            # -----------------------------
            if total_fingers in [1, 2] and fingers[1] == 1 and fingers[2] == 0:
                # Map coords
                screen_x = np.interp(ix, (FRAME_MARGIN, w - FRAME_MARGIN), (0, SCREEN_W))
                screen_y = np.interp(iy, (FRAME_MARGIN, h - FRAME_MARGIN), (0, SCREEN_H))

                # Smooth
                curr_x = prev_x + (screen_x - prev_x) / SMOOTHING
                curr_y = prev_y + (screen_y - prev_y) / SMOOTHING

                pyautogui.moveTo(curr_x, curr_y)
                prev_x, prev_y = curr_x, curr_y

                cv2.putText(frame, "MODE: MOVE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # -----------------------------
            # MODE 2: Click (Pinch)
            # Thumb + Index close
            # -----------------------------
            d_click = dist((ix, iy), (tx, ty))
            cv2.line(frame, (ix, iy), (tx, ty), (255, 255, 255), 2)

            if d_click < CLICK_THRESHOLD:
                now = time.time()
                if now - last_click_time > CLICK_COOLDOWN:
                    pyautogui.click()
                    last_click_time = now
                    cv2.putText(frame, "CLICK", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

            # -----------------------------
            # MODE 3: Scroll
            # Index + Middle up
            # -----------------------------
            if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                now = time.time()
                if now - last_scroll_time > SCROLL_COOLDOWN:
                    # Scroll based on middle finger y
                    if my < iy - 10:
                        pyautogui.scroll(SCROLL_SPEED)
                        cv2.putText(frame, "SCROLL UP", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
                    elif my > iy + 10:
                        pyautogui.scroll(-SCROLL_SPEED)
                        cv2.putText(frame, "SCROLL DOWN", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

                    last_scroll_time = now

            # -----------------------------
            # MODE 4: Drag
            # Fist = drag
            # -----------------------------
            if total_fingers == 0:
                if not dragging:
                    pyautogui.mouseDown()
                    dragging = True
                    cv2.putText(frame, "DRAG START", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            else:
                if dragging:
                    pyautogui.mouseUp()
                    dragging = False
                    cv2.putText(frame, "DRAG STOP", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            # Debug
            cv2.putText(frame, f"Fingers: {fingers}  Total: {total_fingers}", (20, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Virtual Mouse PRO (ESC to exit)", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
