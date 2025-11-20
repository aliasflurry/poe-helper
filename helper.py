import subprocess
import tkinter as tk
import tkinter.ttk as ttk

import darkdetect
import psutil
import pyautogui
import keyboard
import win32process
from typing import Optional
from threading import Event
from settings_manager import SettingsManager
from weapon_swap import WeaponSwap
from flask import Flask

try:
    import win32gui
except ImportError:
    print("Warning: pywin32 not installed. Window detection will not work.")
    win32gui = None


class PathOfExileHelper:
    def __init__(self):
        self.root = tk.Tk("PGame Helper")
        self.root.geometry("500x300")

        # Settings manager
        self.settings_manager = SettingsManager("settings.json")

        # Threading control (flask thread managed by Flask class)

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
        self.weapon_swap_hotkey_entry: Optional[tk.Entry] = None
        self.weapon_swap_set_button: Optional[tk.Button] = None
        self.weapon_swap_status_label: Optional[tk.Label] = None
        self.tab_control: Optional[ttk.Notebook] = None
        
        # Hotkey settings
        self.flask_hotkey_entry: Optional[tk.Entry] = None
        self.flask_set_button: Optional[tk.Button] = None
        self.flask_status_label: Optional[tk.Label] = None
        self._cleaning_up = False

        self.setup_ui()
        
        # Initialize flask manager after UI is set up
        self.flask = Flask(
            self.button_key,
            self.button_delay,
            self.click_flask_button,
            self.flask_hotkey_entry,
            self.flask_set_button,
            self.flask_status_label,
            self.is_path_of_exile_active,
            self.FLASK_MIN,
            self.FLASK_MAX,
            save_callback=lambda: self.settings_manager.save_settings(self.button_key, self.button_delay, self.weapon_key, self.flask_hotkey_entry, self.weapon_swap_hotkey_entry)
        )
        # Update button commands now that flask is initialized
        self.click_flask_button.config(command=self.flask.toggle_flask)
        self.flask_set_button.config(command=self.flask.start_listening_flask_hotkey)
        
        # Initialize weapon swap manager after UI is set up
        self.weapon_swap = WeaponSwap(
            self.weapon_key,
            self.click_weapon_swap_button,
            self.weapon_swap_hotkey_entry,
            self.weapon_swap_set_button,
            self.weapon_swap_status_label,
            self.is_path_of_exile_active,
            save_callback=lambda: self.settings_manager.save_settings(self.button_key, self.button_delay, self.weapon_key, self.flask_hotkey_entry, self.weapon_swap_hotkey_entry)
        )
        # Update button commands now that weapon_swap is initialized
        self.click_weapon_swap_button.config(command=self.weapon_swap.toggle_weapon_swap)
        self.weapon_swap_set_button.config(command=self.weapon_swap.start_listening_weapon_swap_hotkey)
        # Load saved settings
        self.settings_manager.load_settings(self.button_key, self.button_delay, self.weapon_key, self.flask_hotkey_entry, self.weapon_swap_hotkey_entry)
        # Restore hotkey bindings after loading settings
        if self.flask_hotkey_entry.get().strip():
            self.flask.update_flask_hotkey()
        if self.weapon_swap_hotkey_entry.get().strip():
            self.weapon_swap.update_weapon_swap_hotkey()
        # Register cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)
    
    def _toggle_flask_wrapper(self):
        """Wrapper for toggle_flask (used before flask is initialized)"""
        if hasattr(self, 'flask'):
            self.flask.toggle_flask()
    
    def _start_listening_flask_hotkey_wrapper(self):
        """Wrapper for start_listening_flask_hotkey (used before flask is initialized)"""
        if hasattr(self, 'flask'):
            self.flask.start_listening_flask_hotkey()
    
    def _clear_flask_hotkey_wrapper(self):
        """Wrapper for clear_flask_hotkey (used before flask is initialized)"""
        if hasattr(self, 'flask'):
            self.flask.clear_flask_hotkey()
    
    def _toggle_weapon_swap_wrapper(self):
        """Wrapper for toggle_weapon_swap (used before weapon_swap is initialized)"""
        if hasattr(self, 'weapon_swap'):
            self.weapon_swap.toggle_weapon_swap()
    
    def _start_listening_weapon_swap_hotkey_wrapper(self):
        """Wrapper for start_listening_weapon_swap_hotkey (used before weapon_swap is initialized)"""
        if hasattr(self, 'weapon_swap'):
            self.weapon_swap.start_listening_weapon_swap_hotkey()
    
    def _clear_weapon_swap_hotkey_wrapper(self):
        """Wrapper for clear_weapon_swap_hotkey (used before weapon_swap is initialized)"""
        if hasattr(self, 'weapon_swap'):
            self.weapon_swap.clear_weapon_swap_hotkey()

    def setup_ui(self):
        """Initialize all UI elements"""
        self.tab_control = ttk.Notebook(self.root)
        main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(main_tab, text='Main')

        # POE Version Checkboxes
        self.setup_poe_checkboxes(main_tab)

        # Flask Controls
        self.setup_flask_controls(main_tab)

        # Weapon Swap Controls
        self.setup_weapon_swap_controls(main_tab)

        # Settings Tab
        settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(settings_tab, text='Settings')
        self.setup_hotkey_settings(settings_tab)

        self.tab_control.pack(expand=1, fill='both')
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
        self.button_key.bind('<KeyRelease>', lambda e: self.settings_manager.save_settings(self.button_key, self.button_delay, self.weapon_key, self.flask_hotkey_entry, self.weapon_swap_hotkey_entry))

        # Button Delay Frame
        button_delay_frame = tk.Frame(parent)
        button_delay_frame.pack()
        tk.Label(button_delay_frame, text="Delay").pack(side='left', padx=5)
        self.button_delay = tk.Text(button_delay_frame, height=1, width=5, bg="white")
        self.button_delay.pack(side='left')
        self.button_delay.bind('<KeyRelease>', lambda e: self.settings_manager.save_settings(self.button_key, self.button_delay, self.weapon_key, self.flask_hotkey_entry, self.weapon_swap_hotkey_entry))

        self.click_flask_button = tk.Button(
            parent,
            text="Start flask",
            command=self._toggle_flask_wrapper,
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
        self.weapon_key.bind('<KeyRelease>', lambda e: self.settings_manager.save_settings(self.button_key, self.button_delay, self.weapon_key, self.flask_hotkey_entry, self.weapon_swap_hotkey_entry))

        self.click_weapon_swap_button = tk.Button(
            parent,
            text="Start weapon swap",
            command=self._toggle_weapon_swap_wrapper,
            width=20,
            height=5,
            padx=10,
            pady=10
        )
        self.click_weapon_swap_button.pack()

    def setup_hotkey_settings(self, parent):
        """Setup hotkey configuration UI"""
        # Flask Hotkey Section
        flask_hotkey_frame = tk.Frame(parent)
        flask_hotkey_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(
            flask_hotkey_frame,
            text="Flask Toggle Hotkey:",
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        flask_input_frame = tk.Frame(flask_hotkey_frame)
        flask_input_frame.pack(fill='x')
        
        self.flask_hotkey_entry = tk.Entry(flask_input_frame, width=20, state='readonly')
        self.flask_hotkey_entry.pack(side='left', padx=5)
        
        self.flask_set_button = tk.Button(
            flask_input_frame,
            text="Set",
            command=self._start_listening_flask_hotkey_wrapper,
            width=10
        )
        self.flask_set_button.pack(side='left', padx=5)
        
        tk.Button(
            flask_input_frame,
            text="Clear",
            command=self._clear_flask_hotkey_wrapper,
            width=10
        ).pack(side='left', padx=5)
        
        self.flask_status_label = tk.Label(
            flask_hotkey_frame,
            text="Click 'Set' and press a key to assign hotkey",
            font=('Arial', 8),
            fg='gray'
        )
        self.flask_status_label.pack(anchor='w', pady=(5, 0))
        
        # Weapon Swap Hotkey Section
        weapon_swap_hotkey_frame = tk.Frame(parent)
        weapon_swap_hotkey_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(
            weapon_swap_hotkey_frame,
            text="Weapon Swap Toggle Hotkey:",
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        weapon_swap_input_frame = tk.Frame(weapon_swap_hotkey_frame)
        weapon_swap_input_frame.pack(fill='x')
        
        self.weapon_swap_hotkey_entry = tk.Entry(weapon_swap_input_frame, width=20, state='readonly')
        self.weapon_swap_hotkey_entry.pack(side='left', padx=5)
        
        self.weapon_swap_set_button = tk.Button(
            weapon_swap_input_frame,
            text="Set",
            command=self._start_listening_weapon_swap_hotkey_wrapper,
            width=10
        )
        self.weapon_swap_set_button.pack(side='left', padx=5)
        
        tk.Button(
            weapon_swap_input_frame,
            text="Clear",
            command=self._clear_weapon_swap_hotkey_wrapper,
            width=10
        ).pack(side='left', padx=5)
        
        self.weapon_swap_status_label = tk.Label(
            weapon_swap_hotkey_frame,
            text="Click 'Set' and press a key to assign hotkey",
            font=('Arial', 8),
            fg='gray'
        )
        self.weapon_swap_status_label.pack(anchor='w', pady=(5, 0))


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



    def set_poe1_enabled(self, value: bool):
        """Set POE1 enabled state"""
        self.poe1_enabled = value

    def set_poe2_enabled(self, value: bool):
        """Set POE2 enabled state"""
        self.poe2_enabled = value

    def cleanup_and_close(self):
        """Cleanup all resources before closing"""
        if self._cleaning_up:
            return
        
        self._cleaning_up = True
        print("Cleaning up resources...")
        
        # Save settings before closing
        self.settings_manager.save_settings(self.button_key, self.button_delay, self.weapon_key, self.flask_hotkey_entry, self.weapon_swap_hotkey_entry)
        
        try:
            # Stop all running operations
            if hasattr(self, 'flask'):
                self.flask.cleanup()
            if hasattr(self, 'weapon_swap'):
                self.weapon_swap.cleanup()

            # Note: We skip keyboard.unhook_all() since we've already unhooked all our specific hooks
            # Calling unhook_all() can sometimes block, and since we manage all hooks explicitly,
            # it's not necessary. The OS will clean up any remaining hooks when the process exits.
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Destroy all widgets
            try:
                if self.root.winfo_exists():
                    self.root.quit()
                    self.root.destroy()
            except:
                pass

    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            # Cleanup is handled by protocol handler, but ensure it runs if mainloop exits abnormally
            if not self._cleaning_up:
                self.cleanup_and_close()
if __name__ == "__main__":
    app = PathOfExileHelper()
    app.run()