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
        self.tab_control: Optional[ttk.Notebook] = None
        
        # Hotkey settings
        self.flask_hotkey: str = ""
        self.weapon_swap_hotkey: str = ""
        self.flask_hotkey_entry: Optional[tk.Entry] = None
        self.weapon_swap_hotkey_entry: Optional[tk.Entry] = None
        self.flask_hotkey_hook_id: Optional[int] = None
        self.weapon_swap_hotkey_hook_id: Optional[int] = None
        self.weapon_swap_a_key_hook_id: Optional[int] = None
        self.listening_for_flask_hotkey: bool = False
        self.listening_for_weapon_swap_hotkey: bool = False
        self.flask_hotkey_listener_callback = None
        self.weapon_swap_hotkey_listener_callback = None
        self._cleaning_up = False

        self.setup_ui()
        # Register cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)

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
        if self.flask_hotkey:
            self.flask_hotkey_entry.config(state='normal')
            self.flask_hotkey_entry.insert(0, self.flask_hotkey)
            self.flask_hotkey_entry.config(state='readonly')
        
        self.flask_set_button = tk.Button(
            flask_input_frame,
            text="Set",
            command=self.start_listening_flask_hotkey,
            width=10
        )
        self.flask_set_button.pack(side='left', padx=5)
        
        tk.Button(
            flask_input_frame,
            text="Clear",
            command=self.clear_flask_hotkey,
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
        if self.weapon_swap_hotkey:
            self.weapon_swap_hotkey_entry.config(state='normal')
            self.weapon_swap_hotkey_entry.insert(0, self.weapon_swap_hotkey)
            self.weapon_swap_hotkey_entry.config(state='readonly')
        
        self.weapon_swap_set_button = tk.Button(
            weapon_swap_input_frame,
            text="Set",
            command=self.start_listening_weapon_swap_hotkey,
            width=10
        )
        self.weapon_swap_set_button.pack(side='left', padx=5)
        
        tk.Button(
            weapon_swap_input_frame,
            text="Clear",
            command=self.clear_weapon_swap_hotkey,
            width=10
        ).pack(side='left', padx=5)
        
        self.weapon_swap_status_label = tk.Label(
            weapon_swap_hotkey_frame,
            text="Click 'Set' and press a key to assign hotkey",
            font=('Arial', 8),
            fg='gray'
        )
        self.weapon_swap_status_label.pack(anchor='w', pady=(5, 0))

    def start_listening_flask_hotkey(self):
        """Start listening for flask hotkey"""
        if self.listening_for_flask_hotkey:
            self.stop_listening_flask_hotkey()
            return
        
        self.listening_for_flask_hotkey = True
        self.flask_set_button.config(text="Cancel", bg="red")
        self.flask_status_label.config(text="Press any key to set hotkey...", fg='blue')
        
        def on_key_press(event):
            if not self.listening_for_flask_hotkey:
                return
            
            key_name = event.name.lower()
            # Skip modifier keys alone
            if key_name in ['shift', 'ctrl', 'alt', 'windows', 'cmd']:
                return
            
            self.stop_listening_flask_hotkey()
            self.flask_hotkey_entry.config(state='normal')
            self.flask_hotkey_entry.delete(0, tk.END)
            self.flask_hotkey_entry.insert(0, key_name)
            self.flask_hotkey_entry.config(state='readonly')
            self.update_flask_hotkey()
            self.flask_status_label.config(text=f"Hotkey set to: {key_name}", fg='green')
        
        self.flask_hotkey_listener_callback = keyboard.hook(on_key_press)

    def stop_listening_flask_hotkey(self):
        """Stop listening for flask hotkey"""
        self.listening_for_flask_hotkey = False
        self.flask_set_button.config(text="Set", bg="SystemButtonFace")
        if self.flask_hotkey_listener_callback is not None:
            try:
                self.flask_hotkey_listener_callback()
            except:
                pass
            self.flask_hotkey_listener_callback = None

    def start_listening_weapon_swap_hotkey(self):
        """Start listening for weapon swap hotkey"""
        if self.listening_for_weapon_swap_hotkey:
            self.stop_listening_weapon_swap_hotkey()
            return
        
        self.listening_for_weapon_swap_hotkey = True
        self.weapon_swap_set_button.config(text="Cancel", bg="red")
        self.weapon_swap_status_label.config(text="Press any key to set hotkey...", fg='blue')
        
        def on_key_press(event):
            if not self.listening_for_weapon_swap_hotkey:
                return
            
            key_name = event.name.lower()
            # Skip modifier keys alone
            if key_name in ['shift', 'ctrl', 'alt', 'windows', 'cmd']:
                return
            
            self.stop_listening_weapon_swap_hotkey()
            self.weapon_swap_hotkey_entry.config(state='normal')
            self.weapon_swap_hotkey_entry.delete(0, tk.END)
            self.weapon_swap_hotkey_entry.insert(0, key_name)
            self.weapon_swap_hotkey_entry.config(state='readonly')
            self.update_weapon_swap_hotkey()
            self.weapon_swap_status_label.config(text=f"Hotkey set to: {key_name}", fg='green')
        
        self.weapon_swap_hotkey_listener_callback = keyboard.hook(on_key_press)

    def stop_listening_weapon_swap_hotkey(self):
        """Stop listening for weapon swap hotkey"""
        self.listening_for_weapon_swap_hotkey = False
        self.weapon_swap_set_button.config(text="Set", bg="SystemButtonFace")
        if self.weapon_swap_hotkey_listener_callback is not None:
            try:
                self.weapon_swap_hotkey_listener_callback()
            except:
                pass
            self.weapon_swap_hotkey_listener_callback = None

    def update_flask_hotkey(self, event=None):
        """Update flask hotkey binding"""
        new_hotkey = self.flask_hotkey_entry.get().strip().lower()
        
        # Unhook old hotkey if exists
        if self.flask_hotkey and self.flask_hotkey_hook_id is not None:
            try:
                keyboard.unhook_key(self.flask_hotkey_hook_id)
            except:
                pass
            self.flask_hotkey_hook_id = None
        
        # Set new hotkey
        self.flask_hotkey = new_hotkey
        
        # Hook new hotkey if not empty
        if new_hotkey:
            try:
                self.flask_hotkey_hook_id = keyboard.on_press_key(
                    new_hotkey,
                    lambda e: self.toggle_flask()
                )
            except Exception as ex:
                print(f"Error setting flask hotkey: {ex}")

    def update_weapon_swap_hotkey(self, event=None):
        """Update weapon swap hotkey binding"""
        new_hotkey = self.weapon_swap_hotkey_entry.get().strip().lower()
        
        # Unhook old hotkey if exists
        if self.weapon_swap_hotkey and self.weapon_swap_hotkey_hook_id is not None:
            try:
                keyboard.unhook_key(self.weapon_swap_hotkey_hook_id)
            except:
                pass
            self.weapon_swap_hotkey_hook_id = None
        
        # Set new hotkey
        self.weapon_swap_hotkey = new_hotkey
        
        # Hook new hotkey if not empty
        if new_hotkey:
            try:
                self.weapon_swap_hotkey_hook_id = keyboard.on_press_key(
                    new_hotkey,
                    lambda e: self.toggle_weapon_swap()
                )
            except Exception as ex:
                print(f"Error setting weapon swap hotkey: {ex}")

    def clear_flask_hotkey(self):
        """Clear flask hotkey"""
        self.stop_listening_flask_hotkey()
        self.flask_hotkey_entry.config(state='normal')
        self.flask_hotkey_entry.delete(0, tk.END)
        self.flask_hotkey_entry.config(state='readonly')
        self.update_flask_hotkey()
        self.flask_status_label.config(text="Hotkey cleared", fg='gray')

    def clear_weapon_swap_hotkey(self):
        """Clear weapon swap hotkey"""
        self.stop_listening_weapon_swap_hotkey()
        self.weapon_swap_hotkey_entry.config(state='normal')
        self.weapon_swap_hotkey_entry.delete(0, tk.END)
        self.weapon_swap_hotkey_entry.config(state='readonly')
        self.update_weapon_swap_hotkey()
        self.weapon_swap_status_label.config(text="Hotkey cleared", fg='gray')

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
        self.weapon_swap_a_key_hook_id = keyboard.on_press_key('a', self.execute_weapon_swap)

    def stop_weapon_swap(self):
        """Stop weapon swap and cleanup resources"""
        self.weapon_swap_event.set()
        self.click_weapon_swap_button['text'] = 'Start weapon swap'
        self.weapon_key.config(state='normal')
        if self.weapon_swap_a_key_hook_id is not None:
            try:
                keyboard.unhook_key(self.weapon_swap_a_key_hook_id)
            except:
                pass
            self.weapon_swap_a_key_hook_id = None

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
        
        try:
            # Stop all running operations
            self.stop_flask()
            self.stop_weapon_swap()

            # Stop listening for hotkeys
            self.stop_listening_flask_hotkey()
            self.stop_listening_weapon_swap_hotkey()

            # Unhook hotkey hooks
            if self.flask_hotkey_hook_id is not None:
                try:
                    keyboard.unhook_key(self.flask_hotkey_hook_id)
                except:
                    pass
                self.flask_hotkey_hook_id = None
            
            if self.weapon_swap_hotkey_hook_id is not None:
                try:
                    keyboard.unhook_key(self.weapon_swap_hotkey_hook_id)
                except:
                    pass
                self.weapon_swap_hotkey_hook_id = None

            # Unhook weapon swap 'a' key if active
            if self.weapon_swap_a_key_hook_id is not None:
                try:
                    keyboard.unhook_key(self.weapon_swap_a_key_hook_id)
                except:
                    pass
                self.weapon_swap_a_key_hook_id = None

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