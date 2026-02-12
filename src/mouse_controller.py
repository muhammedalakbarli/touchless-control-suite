# src/mouse_controller.py
import pyautogui
import numpy as np
import math

class MouseController:
    def __init__(
        self,
        smoothing=8,
        frame_margin=80,
        deadzone_px=6,
        max_step_px=120
    ):
        pyautogui.FAILSAFE = False

        self.screen_w, self.screen_h = pyautogui.size()

        self.smoothing = smoothing
        self.frame_margin = frame_margin

        # PRO: ignore micro jitter
        self.deadzone_px = deadzone_px

        # PRO: prevent crazy jumps
        self.max_step_px = max_step_px

        self.prev_x = None
        self.prev_y = None

        self.dragging = False

    def _clamp(self, v, vmin, vmax):
        return max(vmin, min(vmax, v))

    def move(self, x_cam, y_cam, cam_w, cam_h):
        # Clamp camera coords inside usable area
        x_cam = self._clamp(x_cam, self.frame_margin, cam_w - self.frame_margin)
        y_cam = self._clamp(y_cam, self.frame_margin, cam_h - self.frame_margin)

        # Map camera -> screen
        x = np.interp(x_cam, (self.frame_margin, cam_w - self.frame_margin), (0, self.screen_w))
        y = np.interp(y_cam, (self.frame_margin, cam_h - self.frame_margin), (0, self.screen_h))

        # First move initialization
        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = x, y
            pyautogui.moveTo(x, y)
            return

        # Calculate delta
        dx = x - self.prev_x
        dy = y - self.prev_y
        dist = math.hypot(dx, dy)

        # Deadzone: ignore micro movement
        if dist < self.deadzone_px:
            return

        # Prevent huge jumps (tracking glitch)
        if dist > self.max_step_px:
            x = self.prev_x + (dx / dist) * self.max_step_px
            y = self.prev_y + (dy / dist) * self.max_step_px

        # Smooth
        curr_x = self.prev_x + (x - self.prev_x) / self.smoothing
        curr_y = self.prev_y + (y - self.prev_y) / self.smoothing

        pyautogui.moveTo(curr_x, curr_y)
        self.prev_x, self.prev_y = curr_x, curr_y

    def click(self):
        pyautogui.click()

    def scroll(self, amount):
        pyautogui.scroll(amount)

    def drag_start(self):
        if not self.dragging:
            pyautogui.mouseDown()
            self.dragging = True

    def drag_stop(self):
        if self.dragging:
            pyautogui.mouseUp()
            self.dragging = False
