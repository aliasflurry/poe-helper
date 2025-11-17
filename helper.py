import subprocess
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from random import uniform
import psutil
import pyautogui
import keyboard
import win32process
from typing import Optional
from threading import Event

try:
    import win32gui
except ImportError:
    print("Warning: pywin32 not installed. Window detection will not work.")
    win32gui = None


class PathOfExileHelper:
    def __init__(self):
        self.root = tk.Tk("PGame Helper")
        self.root.geometry("500x300")

        # Threading control
        self.flask_event = Event()
        self.weapon_swap_event = Event()
        self.flask_thread: Optional[threading.Thread] = None

        # State variables
        self.poe1_enabled = True
        self.poe2_enabled = True

        # Constants
        self.FLASK_MIN = 8
        self.FLASK_MAX = 9

        # UI Elements
        self.button_key: Optional[tk.Text] = None
        self.button_delay: Optional[tk.Text] = None
        self.weapon_key: Optional[tk.Text] = None
        self.click_flask_button: Optional[tk.Button] = None
        self.click_weapon_swap_button: Optional[tk.Button] = None

        self.setup_ui()
        # Register cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)

    def setup_ui(self):
        """Initialize all UI elements"""
        tab_control = ttk.Notebook(self.root)
        main_tab = ttk.Frame(tab_control)
        tab_control.add(main_tab, text='Main')

        # POE Version Checkboxes
        self.setup_poe_checkboxes(main_tab)

        # Flask Controls
        self.setup_flask_controls(main_tab)

        # Weapon Swap Controls
        self.setup_weapon_swap_controls(main_tab)

        tab_control.pack(expand=1, fill='both')
        self.root.attributes('-topmost', True)

    def setup_poe_checkboxes(self, parent):
        poe1_checkbox_var = tk.BooleanVar(value=True)
        poe1_checkbox = tk.Checkbutton(
            parent,
            text="Only work in Path of Exile",
            variable=poe1_checkbox_var,
            command=lambda: self.set_poe1_enabled(poe1_checkbox_var.get())
        )
        poe1_checkbox.pack(pady=2)

        poe2_checkbox_var = tk.BooleanVar(value=True)
        poe2_checkbox = tk.Checkbutton(
            parent,
            text="Only work in Path of Exile 2",
            variable=poe2_checkbox_var,
            command=lambda: self.set_poe2_enabled(poe2_checkbox_var.get())
        )
        poe2_checkbox.pack(pady=2)

    def setup_flask_controls(self, parent):
        # Button Key Frame
        button_key_frame = tk.Frame(parent)
        button_key_frame.pack()
        tk.Label(button_key_frame, text="Button").pack(side='left', padx=5)
        self.button_key = tk.Text(button_key_frame, height=1, width=5, bg="white")
        self.button_key.pack(side='left')

        # Button Delay Frame
        button_delay_frame = tk.Frame(parent)
        button_delay_frame.pack()
        tk.Label(button_delay_frame, text="Delay").pack(side='left', padx=5)
        self.button_delay = tk.Text(button_delay_frame, height=1, width=5, bg="white")
        self.button_delay.pack(side='left')

        self.click_flask_button = tk.Button(
            parent,
            text="Start flask",
            command=self.toggle_flask,
            width=20,
            height=5,
            padx=10,
            pady=10
        )
        self.click_flask_button.pack()

    def setup_weapon_swap_controls(self, parent):
        weapon_key_frame = tk.Frame(parent)
        weapon_key_frame.pack(pady=(20, 0))
        tk.Label(weapon_key_frame, text="Button").pack(side='left', padx=5)
        self.weapon_key = tk.Text(weapon_key_frame, height=1, width=5, bg="white")
        self.weapon_key.pack(side='left')

        self.click_weapon_swap_button = tk.Button(
            parent,
            text="Start weapon swap",
            command=self.toggle_weapon_swap,
            width=20,
            height=5,
            padx=10,
            pady=10
        )
        self.click_weapon_swap_button.pack()

    def get_root_window(self, hwnd):
        """Get the root window handle"""
        try:
            parent = win32gui.GetParent(hwnd)
            while parent != 0:
                hwnd = parent
                parent = win32gui.GetParent(hwnd)
            return hwnd
        except Exception as e:
            print(f"Error getting root window: {e}")
            return None

    def is_path_of_exile_active(self) -> bool:
        """Check if POE window is active"""
        try:
            if not win32gui:
                return False

            hwnd = win32gui.GetForegroundWindow()
            hwnd_root = self.get_root_window(hwnd)
            if not hwnd_root:
                return False

            pid = win32process.GetWindowThreadProcessId(hwnd_root)[1]
            process_name = psutil.Process(pid).name().lower()

            return (
                    (self.poe1_enabled and process_name.startswith("pathofexile") and
                     not process_name.startswith("pathofexile2")) or
                    (self.poe2_enabled and process_name.startswith("pathofexile2"))
            )
        except Exception as e:
            print(f"Detection error: {e}")
            return False

    def flask_loop(self):
        """Main flask loop with proper resource management"""
        try:
            button_keys = self.button_key.get(1.0, "end-1c").split()
            delays = self.button_delay.get(1.0, "end-1c").split()
            min_delay = float(delays[0]) if delays else self.FLASK_MIN
            max_delay = float(delays[1]) if len(delays) > 1 else self.FLASK_MAX

            while not self.flask_event.is_set():
                if keyboard.is_pressed('f11'):
                    print("F11 pressed")
                    break

                if not self.is_path_of_exile_active():
                    time.sleep(0.5)
                    continue

                for key in button_keys:
                    if self.flask_event.is_set():
                        break
                    keyboard.press_and_release(key)

                time.sleep(uniform(min_delay, max_delay))
        finally:
            self.stop_flask()

    def toggle_flask(self):
        """Toggle flask automation"""
        if self.click_flask_button['text'] == 'Start flask':
            self.start_flask()
        else:
            self.stop_flask()

    def start_flask(self):
        """Start flask automation with proper thread management"""
        self.flask_event.clear()
        self.click_flask_button['text'] = 'Stop flask'
        self.button_key.config(state='disabled')
        self.button_delay.config(state='disabled')

        self.flask_thread = threading.Thread(target=self.flask_loop)
        self.flask_thread.daemon = True
        self.flask_thread.start()

    def stop_flask(self):
        """Stop flask automation and cleanup resources"""
        self.flask_event.set()
        self.click_flask_button['text'] = 'Start flask'
        self.button_key.config(state='normal')
        self.button_delay.config(state='normal')

    def execute_weapon_swap(self, e):
        """Execute weapon swap sequence"""
        if self.weapon_swap_event.is_set() or not self.is_path_of_exile_active():
            return

        try:
            weapon_keys = ['X', 'X'] + self.weapon_key.get(1.0, "end-1c").split()
            for key in weapon_keys:
                keyboard.press_and_release(key)
                time.sleep(0.2)
        except Exception as e:
            print(f"Weapon swap error: {e}")

    def toggle_weapon_swap(self):
        """Toggle weapon swap functionality"""
        if self.click_weapon_swap_button['text'] == 'Start weapon swap':
            self.start_weapon_swap()
        else:
            self.stop_weapon_swap()

    def start_weapon_swap(self):
        """Start weapon swap with proper resource management"""
        self.weapon_swap_event.clear()
        self.click_weapon_swap_button['text'] = 'Stop weapon swap'
        self.weapon_key.config(state='disabled')
        keyboard.on_press_key('a', self.execute_weapon_swap)

    def stop_weapon_swap(self):
        """Stop weapon swap and cleanup resources"""
        self.weapon_swap_event.set()
        self.click_weapon_swap_button['text'] = 'Start weapon swap'
        self.weapon_key.config(state='normal')
        keyboard.unhook_key('a')

    def set_poe1_enabled(self, value: bool):
        """Set POE1 enabled state"""
        self.poe1_enabled = value

    def set_poe2_enabled(self, value: bool):
        """Set POE2 enabled state"""
        self.poe2_enabled = value

    def cleanup_and_close(self):
        """Cleanup all resources before closing"""
        print("Cleaning up resources...")
        # Stop all running operations
        self.stop_flask()
        self.stop_weapon_swap()

        # Remove all keyboard hooks
        keyboard.unhook_all()

        # Destroy all widgets
        self.root.destroy()

    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            self.cleanup_and_close()
if __name__ == "__main__":
    app = PathOfExileHelper()
    app.run()