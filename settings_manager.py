import json
import os
import tkinter as tk
from typing import Optional


class SettingsManager:
    """Manages saving and loading of application settings"""
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
    
    def save_settings(self, button_key: Optional[tk.Text], button_delay: Optional[tk.Text], weapon_key: Optional[tk.Text] = None, flask_hotkey: Optional[tk.Entry] = None, weapon_swap_hotkey: Optional[tk.Entry] = None):
        """Save text box values to settings file"""
        try:
            button_key_value = ""
            button_delay_value = ""
            weapon_key_value = ""
            flask_hotkey_value = ""
            weapon_swap_hotkey_value = ""
            
            if button_key:
                button_key_value = button_key.get(1.0, "end-1c").strip()
            if button_delay:
                button_delay_value = button_delay.get(1.0, "end-1c").strip()
            if weapon_key:
                weapon_key_value = weapon_key.get(1.0, "end-1c").strip()
            if flask_hotkey:
                flask_hotkey_value = flask_hotkey.get().strip()
            if weapon_swap_hotkey:
                weapon_swap_hotkey_value = weapon_swap_hotkey.get().strip()
            
            settings = {
                "button_key": button_key_value,
                "button_delay": button_delay_value,
                "weapon_key": weapon_key_value,
                "flask_hotkey": flask_hotkey_value,
                "weapon_swap_hotkey": weapon_swap_hotkey_value
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def load_settings(self, button_key: Optional[tk.Text], button_delay: Optional[tk.Text], weapon_key: Optional[tk.Text] = None, flask_hotkey: Optional[tk.Entry] = None, weapon_swap_hotkey: Optional[tk.Entry] = None):
        """Load text box values from settings file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    if "button_key" in settings and button_key:
                        button_key.delete(1.0, tk.END)
                        button_key.insert(1.0, settings["button_key"])
                    if "button_delay" in settings and button_delay:
                        button_delay.delete(1.0, tk.END)
                        button_delay.insert(1.0, settings["button_delay"])
                    if "weapon_key" in settings and weapon_key:
                        weapon_key.delete(1.0, tk.END)
                        weapon_key.insert(1.0, settings["weapon_key"])
                    if "flask_hotkey" in settings and flask_hotkey:
                        flask_hotkey.config(state='normal')
                        flask_hotkey.delete(0, tk.END)
                        flask_hotkey.insert(0, settings["flask_hotkey"])
                        flask_hotkey.config(state='readonly')
                    if "weapon_swap_hotkey" in settings and weapon_swap_hotkey:
                        weapon_swap_hotkey.config(state='normal')
                        weapon_swap_hotkey.delete(0, tk.END)
                        weapon_swap_hotkey.insert(0, settings["weapon_swap_hotkey"])
                        weapon_swap_hotkey.config(state='readonly')
        except Exception as e:
            print(f"Error loading settings: {e}")

