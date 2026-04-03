"""
main.py — Entry point for Password Manager (PyWebView)
Run this file to launch the app.
"""

import os
import threading
import webview
import time
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
    
    def preload():
        import stage_2
        import Stage_1
        stage_2._load_or_init_master_file()   # warm up master file read
        Stage_1.load_passwords()              # pre-load password dict if exists

    t = threading.Thread(target=preload, daemon=True)
    t.start()
    t.join()  # wait until preload finishes
    
    
    
    # Step 2: Now create window — everything is warm
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
