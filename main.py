"""
main.py — Entry point for Password Manager (PyWebView)
Run this file to launch the app.
"""

import os
import webview
from api import Api

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_PATH  = os.path.join(BASE_DIR, "ui", "login.html")

MAX_W, MAX_H = 520, 720   # soft max — clamped via resized event

def _clamp(window):
    """Clamp window to max size if user drags it too large."""
    w = min(window.width,  MAX_W)
    h = min(window.height, MAX_H)
    if w != window.width or h != window.height:
        window.resize(w, h)

if __name__ == "__main__":
    api    = Api()
    window = webview.create_window(
        title            = "Password Manager",
        url              = f"file://{UI_PATH}",
        js_api           = api,
        width  = 510,
        height = 610,
        min_size = (510, 610),  # lock it to that size
        resizable = False,       # or keep True but set min same as initial
        background_color = "#1a1a1a",
        frameless        = False,
    )
    window.events.resized += lambda: _clamp(window)
    webview.start(debug=False)
