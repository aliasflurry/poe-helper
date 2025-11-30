import time
import tkinter as tk
import keyboard
from typing import Optional
from threading import Event


class WeaponSwap:
    """Manages weapon swap functionality"""
    
    def __init__(self, weapon_key: Optional[tk.Text], 
                 click_weapon_swap_button: Optional[tk.Button],
                 weapon_swap_hotkey_entry: Optional[tk.Entry],
                 weapon_swap_set_button: Optional[tk.Button],
                 weapon_swap_status_label: Optional[tk.Label],
                 is_path_of_exile_active_callback,
                 save_callback=None):
        """
        Initialize weapon swap manager
        
        Args:
            weapon_key: Text widget for weapon key input
            click_weapon_swap_button: Button to toggle weapon swap
            weapon_swap_hotkey_entry: Entry widget for hotkey display
            weapon_swap_set_button: Button to set hotkey
            weapon_swap_status_label: Label for hotkey status
            is_path_of_exile_active_callback: Callback function to check if POE is active
        """
        self.weapon_key = weapon_key
        self.click_weapon_swap_button = click_weapon_swap_button
        self.weapon_swap_hotkey_entry = weapon_swap_hotkey_entry
        self.weapon_swap_set_button = weapon_swap_set_button
        self.weapon_swap_status_label = weapon_swap_status_label
        self.is_path_of_exile_active = is_path_of_exile_active_callback
        self.save_callback = save_callback
        
        # State variables
        self.weapon_swap_event = Event()
        self.weapon_swap_hotkey: str = ""
        self.weapon_swap_hotkey_hook_ids: list = []  # List to store multiple hook IDs
        self.weapon_swap_a_key_hook_id: Optional[int] = None
        self.listening_for_weapon_swap_hotkey: bool = False
        self.weapon_swap_hotkey_listener_callback = None
    
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

    def start_listening_weapon_swap_hotkey(self):
        """Start listening for weapon swap hotkey"""
        if self.listening_for_weapon_swap_hotkey:
            self.stop_listening_weapon_swap_hotkey()
            return
        
        self.listening_for_weapon_swap_hotkey = True
        self.weapon_swap_set_button.config(text="Cancel", bg="red")
        self.weapon_swap_status_label.config(text="Press any key (or Ctrl+key) to set hotkey...", fg='blue')
        
        def on_key_press(event):
            if not self.listening_for_weapon_swap_hotkey:
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
            
            self.stop_listening_weapon_swap_hotkey()
            self.weapon_swap_hotkey_entry.config(state='normal')
            self.weapon_swap_hotkey_entry.delete(0, tk.END)
            self.weapon_swap_hotkey_entry.insert(0, hotkey_str)
            self.weapon_swap_hotkey_entry.config(state='readonly')
            self.update_weapon_swap_hotkey()
            self.weapon_swap_status_label.config(text=f"Hotkey set to: {hotkey_str}", fg='green')
            if self.save_callback:
                self.save_callback()
        
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

    def update_weapon_swap_hotkey(self, event=None):
        """Update weapon swap hotkey binding - registers both normal key and Ctrl+key"""
        new_hotkey = self.weapon_swap_hotkey_entry.get().strip().lower()
        
        # Unhook old hotkeys if they exist
        for hook_id in self.weapon_swap_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.weapon_swap_hotkey_hook_ids = []
        
        # Set new hotkey
        self.weapon_swap_hotkey = new_hotkey
        
        # Hook new hotkey if not empty
        if new_hotkey:
            try:
                # If it's already a combination, register it directly
                if '+' in new_hotkey:
                    # Register the combination directly
                    try:
                        hook_id = keyboard.add_hotkey(
                            new_hotkey,
                            self.toggle_weapon_swap
                        )
                        self.weapon_swap_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting weapon swap hotkey (combination): {ex}")
                else:
                    # For single keys, register only the key
                    try:
                        hook_id = keyboard.on_press_key(
                            new_hotkey,
                            lambda e: self.toggle_weapon_swap()
                        )
                        self.weapon_swap_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting weapon swap hotkey: {ex}")
            except Exception as ex:
                print(f"Error setting weapon swap hotkey: {ex}")

    def clear_weapon_swap_hotkey(self):
        """Clear weapon swap hotkey"""
        self.stop_listening_weapon_swap_hotkey()
        self.weapon_swap_hotkey_entry.config(state='normal')
        self.weapon_swap_hotkey_entry.delete(0, tk.END)
        self.weapon_swap_hotkey_entry.config(state='readonly')
        self.update_weapon_swap_hotkey()
        self.weapon_swap_status_label.config(text="Hotkey cleared", fg='gray')
        if self.save_callback:
            self.save_callback()
    
    def cleanup(self):
        """Cleanup all weapon swap resources"""
        self.stop_weapon_swap()
        self.stop_listening_weapon_swap_hotkey()
        
        # Unhook all hotkeys
        for hook_id in self.weapon_swap_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.weapon_swap_hotkey_hook_ids = []
        
        if self.weapon_swap_a_key_hook_id is not None:
            try:
                keyboard.unhook_key(self.weapon_swap_a_key_hook_id)
            except:
                pass
            self.weapon_swap_a_key_hook_id = None

