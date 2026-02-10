# src/mouse_controller.py
import pyautogui
import numpy as np

class MouseController:
    def __init__(self, smoothing=8, frame_margin=80):
        pyautogui.FAILSAFE = False

        self.screen_w, self.screen_h = pyautogui.size()
        self.smoothing = smoothing
        self.frame_margin = frame_margin

        self.prev_x = 0
        self.prev_y = 0
        self.dragging = False

    def move(self, x_cam, y_cam, cam_w, cam_h):
        x = np.interp(x_cam, (self.frame_margin, cam_w - self.frame_margin), (0, self.screen_w))
        y = np.interp(y_cam, (self.frame_margin, cam_h - self.frame_margin), (0, self.screen_h))

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
