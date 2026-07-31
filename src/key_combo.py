import time
import tkinter as tk
from threading import Event
from typing import Optional

import keyboard


class KeyCombo:
    """Binds one key to a sequence of key presses."""

    def __init__(
        self,
        trigger_key: Optional[tk.Text],
        combo_keys: Optional[tk.Text],
        click_key_combo_button: Optional[tk.Button],
        is_path_of_exile_active_callback,
        interval: float = 0.2,
        save_callback=None,
    ):
        self.trigger_key = trigger_key
        self.combo_keys = combo_keys
        self.click_key_combo_button = click_key_combo_button
        self.is_path_of_exile_active = is_path_of_exile_active_callback
        self.interval = interval
        self.save_callback = save_callback

        self.key_combo_event = Event()
        self.key_combo_hook_id = None

    def execute_key_combo(self, e=None):
        """Press combo keys in order with a fixed interval between each key."""
        if self.key_combo_event.is_set() or not self.is_path_of_exile_active():
            return

        try:
            keys = self.combo_keys.get(1.0, "end-1c").split()
            for key in keys:
                keyboard.press_and_release(key)
                time.sleep(self.interval)
        except Exception as ex:
            print(f"Key combo error: {ex}")

    def toggle_key_combo(self):
        """Toggle key combo binding."""
        if self.click_key_combo_button["text"] == "Start key bind":
            self.start_key_combo()
        else:
            self.stop_key_combo()

    def start_key_combo(self):
        """Bind the trigger key to the configured combo."""
        trigger = self.trigger_key.get(1.0, "end-1c").strip().lower()
        if not trigger:
            print("No trigger key set for key combo")
            return

        if self.key_combo_hook_id is not None:
            self.stop_key_combo()

        self.key_combo_event.clear()
        self.click_key_combo_button["text"] = "Stop key bind"
        self.trigger_key.config(state="disabled")
        self.combo_keys.config(state="disabled")
        self.key_combo_hook_id = keyboard.on_press_key(trigger, self.execute_key_combo)

    def stop_key_combo(self):
        """Stop key combo binding and cleanup resources."""
        self.key_combo_event.set()
        self.click_key_combo_button["text"] = "Start key bind"
        self.trigger_key.config(state="normal")
        self.combo_keys.config(state="normal")
        if self.key_combo_hook_id is not None:
            try:
                keyboard.unhook_key(self.key_combo_hook_id)
            except:
                pass
            self.key_combo_hook_id = None

    def cleanup(self):
        """Cleanup key combo resources."""
        self.stop_key_combo()
