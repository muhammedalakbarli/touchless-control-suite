# src/gesture_engine.py
import time
from src.utils import dist

class GestureEngine:
    """
    Turns landmarks into high-level actions:
    - MOVE
    - CLICK
    - SCROLL_UP / SCROLL_DOWN
    - DRAG_START / DRAG_STOP
    - PAUSE
    """

    def __init__(self, click_threshold=28, click_cooldown=0.35, scroll_cooldown=0.10):
        self.click_threshold = click_threshold
        self.click_cooldown = click_cooldown
        self.scroll_cooldown = scroll_cooldown

        self.last_click_time = 0
        self.last_scroll_time = 0
        self.paused = False

    def fingers_up(self, lm, hand_label):
        """
        Returns [thumb, index, middle, ring, pinky]
        """
        fingers = [0, 0, 0, 0, 0]

        # Thumb depends on left/right
        if hand_label == "Right":
            fingers[0] = 1 if lm[4][0] > lm[3][0] else 0
        else:
            fingers[0] = 1 if lm[4][0] < lm[3][0] else 0

        tips = [8, 12, 16, 20]
        pip = [6, 10, 14, 18]

        for i in range(4):
            fingers[i+1] = 1 if lm[tips[i]][1] < lm[pip[i]][1] else 0

        return fingers

    def get_actions(self, hands_data):
        """
        Returns list of actions like:
        [
          ("MOVE", {"x":..., "y":..., "hand":"Right"}),
          ("CLICK", {"hand":"Right"}),
          ("SCROLL", {"amount":+60, "hand":"Left"}),
          ("DRAG_START", {"hand":"Right"}),
        ]
        """
        actions = []

        # LEFT HAND: scroll + pause
        if "Left" in hands_data:
            lmL = hands_data["Left"]["lm"]
            fL = self.fingers_up(lmL, "Left")
            totalL = sum(fL)

            # Open palm = pause
            self.paused = True if totalL == 5 else False

            # Scroll: index + middle
            if fL[1] == 1 and fL[2] == 1 and fL[3] == 0 and fL[4] == 0:
                ix, iy = lmL[8]
                mx, my = lmL[12]

                now = time.time()
                if now - self.last_scroll_time > self.scroll_cooldown:
                    if my < iy - 10:
                        actions.append(("SCROLL", {"amount": +60, "hand": "Left"}))
                    elif my > iy + 10:
                        actions.append(("SCROLL", {"amount": -60, "hand": "Left"}))

                    self.last_scroll_time = now

        # RIGHT HAND: move + click + drag
        if "Right" in hands_data:
            lmR = hands_data["Right"]["lm"]
            fR = self.fingers_up(lmR, "Right")
            totalR = sum(fR)

            ix, iy = lmR[8]
            tx, ty = lmR[4]

            # Move only when not paused and index only
            if not self.paused:
                if fR[1] == 1 and fR[2] == 0 and fR[3] == 0 and fR[4] == 0:
                    actions.append(("MOVE", {"x": ix, "y": iy, "hand": "Right"}))

            # Click pinch
            d_click = dist((ix, iy), (tx, ty))
            if d_click < self.click_threshold and not self.paused:
                now = time.time()
                if now - self.last_click_time > self.click_cooldown:
                    actions.append(("CLICK", {"hand": "Right"}))
                    self.last_click_time = now

            # Drag: fist
            if not self.paused:
                if totalR == 0:
                    actions.append(("DRAG_START", {"hand": "Right"}))
                else:
                    actions.append(("DRAG_STOP", {"hand": "Right"}))

        return actions
