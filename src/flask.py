import threading
import time
import tkinter as tk
import keyboard
from random import uniform
from typing import Optional
from threading import Event


class Flask:
    """Manages flask automation functionality"""
    
    def __init__(self, button_key: Optional[tk.Text],
                 button_delay: Optional[tk.Text],
                 click_flask_button: Optional[tk.Button],
                 flask_hotkey_entry: Optional[tk.Entry],
                 flask_set_button: Optional[tk.Button],
                 flask_status_label: Optional[tk.Label],
                 is_path_of_exile_active_callback,
                 flask_min: int = 8,
                 flask_max: int = 9,
                 save_callback=None,
                 on_flask_started=None,
                 on_flask_stopped=None):
        """
        Initialize flask manager
        
        Args:
            button_key: Text widget for button key input
            button_delay: Text widget for delay input
            click_flask_button: Button to toggle flask automation
            flask_hotkey_entry: Entry widget for hotkey display
            flask_set_button: Button to set hotkey
            flask_status_label: Label for hotkey status
            is_path_of_exile_active_callback: Callback function to check if POE is active
            flask_min: Minimum delay between flask presses
            flask_max: Maximum delay between flask presses
        """
        self.button_key = button_key
        self.button_delay = button_delay
        self.click_flask_button = click_flask_button
        self.flask_hotkey_entry = flask_hotkey_entry
        self.flask_set_button = flask_set_button
        self.flask_status_label = flask_status_label
        self.is_path_of_exile_active = is_path_of_exile_active_callback
        self.FLASK_MIN = flask_min
        self.FLASK_MAX = flask_max
        self.save_callback = save_callback
        self.on_flask_started = on_flask_started
        self.on_flask_stopped = on_flask_stopped
        
        # State variables
        self.flask_event = Event()
        self.flask_thread: Optional[threading.Thread] = None
        self.flask_hotkey: str = ""
        self.flask_hotkey_hook_ids: list = []  # List to store multiple hook IDs
        self.listening_for_flask_hotkey: bool = False
        self.flask_hotkey_listener_callback = None
    
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
        if self.on_flask_started:
            self.on_flask_started()

        self.flask_thread = threading.Thread(target=self.flask_loop)
        self.flask_thread.daemon = True
        self.flask_thread.start()

    def stop_flask(self):
        """Stop flask automation and cleanup resources"""
        self.flask_event.set()
        self.click_flask_button['text'] = 'Start flask'
        self.button_key.config(state='normal')
        self.button_delay.config(state='normal')
        if self.on_flask_stopped:
            self.on_flask_stopped()

    def start_listening_flask_hotkey(self):
        """Start listening for flask hotkey"""
        if self.listening_for_flask_hotkey:
            self.stop_listening_flask_hotkey()
            return
        
        self.listening_for_flask_hotkey = True
        self.flask_set_button.config(text="Cancel", bg="#dc2626", fg="white")
        self.flask_status_label.config(text="Press any key (or Ctrl+key) to set hotkey...", fg='blue')
        
        def on_key_press(event):
            if not self.listening_for_flask_hotkey:
                return
            
            key_name = event.name.lower()
            
            # Track Ctrl key state
            if key_name == 'ctrl' or key_name == 'ctrl left' or key_name == 'ctrl right':
                return
            
            # Skip other modifier keys alone
            if key_name in ['shift', 'alt', 'windows', 'cmd']:
                return
            
            # Check if Ctrl is currently held (using 'ctrl' works for both left and right)
            try:
                is_ctrl_held = keyboard.is_pressed('ctrl')
            except:
                is_ctrl_held = False
            
            # Format hotkey string
            if is_ctrl_held:
                hotkey_str = f"ctrl+{key_name}"
            else:
                hotkey_str = key_name
            
            self.stop_listening_flask_hotkey()
            self.flask_hotkey_entry.config(state='normal')
            self.flask_hotkey_entry.delete(0, tk.END)
            self.flask_hotkey_entry.insert(0, hotkey_str)
            self.flask_hotkey_entry.config(state='readonly')
            self.update_flask_hotkey()
            self.flask_status_label.config(text=f"Hotkey set to: {hotkey_str}", fg='green')
            if self.save_callback:
                self.save_callback()
        
        self.flask_hotkey_listener_callback = keyboard.hook(on_key_press)

    def stop_listening_flask_hotkey(self):
        """Stop listening for flask hotkey"""
        self.listening_for_flask_hotkey = False
        self.flask_set_button.config(text="Set", bg="#e8f0fe", fg="#174ea6")
        if self.flask_hotkey_listener_callback is not None:
            try:
                self.flask_hotkey_listener_callback()
            except:
                pass
            self.flask_hotkey_listener_callback = None

    def update_flask_hotkey(self, event=None):
        """Update flask hotkey binding - registers both normal key and Ctrl+key"""
        new_hotkey = self.flask_hotkey_entry.get().strip().lower()
        
        # Unhook old hotkeys if they exist
        for hook_id in self.flask_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.flask_hotkey_hook_ids = []
        
        # Set new hotkey
        self.flask_hotkey = new_hotkey
        
        # Hook new hotkey if not empty
        if new_hotkey:
            try:
                # If it's already a combination, register it directly
                if '+' in new_hotkey:
                    # Register the combination directly
                    try:
                        hook_id = keyboard.add_hotkey(
                            new_hotkey,
                            self.toggle_flask
                        )
                        self.flask_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting flask hotkey (combination): {ex}")
                else:
                    # For single keys, register only the key
                    try:
                        hook_id = keyboard.on_press_key(
                            new_hotkey,
                            lambda e: self.toggle_flask()
                        )
                        self.flask_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting flask hotkey: {ex}")
            except Exception as ex:
                print(f"Error setting flask hotkey: {ex}")

    def clear_flask_hotkey(self):
        """Clear flask hotkey"""
        self.stop_listening_flask_hotkey()
        self.flask_hotkey_entry.config(state='normal')
        self.flask_hotkey_entry.delete(0, tk.END)
        self.flask_hotkey_entry.config(state='readonly')
        self.update_flask_hotkey()
        self.flask_status_label.config(text="Hotkey cleared", fg='gray')
        if self.save_callback:
            self.save_callback()
    
    def cleanup(self):
        """Cleanup all flask resources"""
        self.stop_flask()
        self.stop_listening_flask_hotkey()
        
        # Unhook all hotkeys
        for hook_id in self.flask_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.flask_hotkey_hook_ids = []

