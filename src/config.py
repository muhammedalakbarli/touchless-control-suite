# src/config.py

class Config:
    # Camera
    CAM_INDEX = 0
    CAM_W = 640
    CAM_H = 480
    USE_DSHOW = True

    # Cursor area (reduce jitter)
    FRAME_MARGIN = 80

    # Smooth
    SMOOTHING = 8

    # Click
    CLICK_THRESHOLD = 28
    CLICK_COOLDOWN = 0.35

    # Scroll
    SCROLL_SPEED = 60
    SCROLL_COOLDOWN = 0.10

    # Drag
    ENABLE_DRAG = True

    # Safety
    FAILSAFE = False
