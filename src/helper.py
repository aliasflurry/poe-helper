import tkinter as tk
import tkinter.ttk as ttk
import ctypes
import os
import tempfile
from typing import Optional

import psutil
import win32process
from PIL import Image, ImageDraw, ImageTk

from dump_items import DumpItems
from flask import Flask
from key_combo import KeyCombo
from map_anoint import MapAnoint
from settings_manager import SettingsManager
from weapon_swap import WeaponSwap

try:
    import win32gui
except ImportError:
    print("Warning: pywin32 not installed. Window detection will not work.")
    win32gui = None


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __init__(self, guid_string: str):
        super().__init__()
        parts = guid_string.strip("{}").split("-")
        self.Data1 = int(parts[0], 16)
        self.Data2 = int(parts[1], 16)
        self.Data3 = int(parts[2], 16)
        data4_bytes = bytes.fromhex(parts[3] + parts[4])
        self.Data4[:] = data4_bytes


class PathOfExileHelper:
    def __init__(self):
        self.root = tk.Tk("PGame Helper")
        self.root.geometry("600x650")

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
        self.key_combo_trigger_key: Optional[tk.Text] = None
        self.key_combo_keys: Optional[tk.Text] = None
        self.click_flask_button: Optional[tk.Button] = None
        self.click_weapon_swap_button: Optional[tk.Button] = None
        self.click_key_combo_button: Optional[tk.Button] = None
        self.weapon_swap_hotkey_entry: Optional[tk.Entry] = None
        self.weapon_swap_set_button: Optional[tk.Button] = None
        self.weapon_swap_status_label: Optional[tk.Label] = None
        self.tab_control: Optional[ttk.Notebook] = None
        
        # Hotkey settings
        self.flask_hotkey_entry: Optional[tk.Entry] = None
        self.flask_set_button: Optional[tk.Button] = None
        self.flask_status_label: Optional[tk.Label] = None
        
        # Map anoint UI elements
        self.click_map_anoint_button: Optional[tk.Button] = None
        self.map_anoint_hotkey_entry: Optional[tk.Entry] = None
        self.map_anoint_set_button: Optional[tk.Button] = None
        self.map_anoint_status_label: Optional[tk.Label] = None
        
        # Dump items UI elements
        self.dump_items_hotkey_entry: Optional[tk.Entry] = None
        self.dump_items_set_button: Optional[tk.Button] = None
        self.dump_items_status_label: Optional[tk.Label] = None
        self.dump_items_coords_button: Optional[tk.Button] = None
        self._status_icon_images = {}
        self._current_status_icon: Optional[ImageTk.PhotoImage] = None
        self._status_icon_paths = {}
        self._status_icon_handles = {}
        self._taskbar_iface = ctypes.c_void_p()
        self._taskbar_overlay_enabled = self._init_taskbar_overlay()
        
        self._cleaning_up = False

        self.setup_ui()
        self._create_status_icon_images()
        self._set_status_icon("stopped")
        
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
            save_callback=lambda: self.save_all_settings(),
            on_flask_started=lambda: self._set_status_icon("running"),
            on_flask_stopped=lambda: self._set_status_icon("stopped")
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
            save_callback=lambda: self.save_all_settings()
        )
        # Update button commands now that weapon_swap is initialized
        self.click_weapon_swap_button.config(command=self.weapon_swap.toggle_weapon_swap)
        self.weapon_swap_set_button.config(command=self.weapon_swap.start_listening_weapon_swap_hotkey)

        self.key_combo = KeyCombo(
            self.key_combo_trigger_key,
            self.key_combo_keys,
            self.click_key_combo_button,
            self.is_path_of_exile_active,
            save_callback=lambda: self.save_all_settings()
        )
        self.click_key_combo_button.config(command=self.key_combo.toggle_key_combo)
        
        # Initialize map anoint manager after UI is set up
        self.map_anoint = MapAnoint(
            self.click_map_anoint_button,
            self.map_anoint_hotkey_entry,
            self.map_anoint_set_button,
            self.map_anoint_status_label,
            self.is_path_of_exile_active,
            save_callback=lambda: self.save_all_settings()
        )
        # Update button commands now that map_anoint is initialized
        self.click_map_anoint_button.config(command=self.map_anoint.toggle_map_anoint)
        self.map_anoint_set_button.config(command=self.map_anoint.start_listening_map_anoint_hotkey)
        
        # Initialize dump items manager after UI is set up
        self.dump_items = DumpItems(
            self.dump_items_hotkey_entry,
            self.dump_items_set_button,
            self.dump_items_status_label,
            self.dump_items_coords_button,
            self.is_path_of_exile_active,
            save_callback=lambda: self.save_all_settings()
        )
        # Update button commands now that dump_items is initialized
        self.dump_items_set_button.config(command=self.dump_items.start_listening_dump_items_hotkey)
        self.dump_items_coords_button.config(command=self.dump_items.select_coordinates)
        
        # Load saved settings
        dump_items_coords = self.settings_manager.load_settings(
            self.button_key,
            self.button_delay,
            self.weapon_key,
            self.flask_hotkey_entry,
            self.weapon_swap_hotkey_entry,
            self.map_anoint_hotkey_entry,
            self.dump_items_hotkey_entry,
            self.key_combo_trigger_key,
            self.key_combo_keys
        )
        # Restore hotkey bindings after loading settings
        if self.flask_hotkey_entry.get().strip():
            self.flask.update_flask_hotkey()
        if self.weapon_swap_hotkey_entry.get().strip():
            self.weapon_swap.update_weapon_swap_hotkey()
        if self.map_anoint_hotkey_entry.get().strip():
            self.map_anoint.update_map_anoint_hotkey()
        if self.dump_items_hotkey_entry.get().strip():
            self.dump_items.update_dump_items_hotkey()
        # Restore coordinates
        if dump_items_coords:
            self.dump_items.set_coords_from_dict(dump_items_coords)
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

    def _toggle_key_combo_wrapper(self):
        """Wrapper for toggle_key_combo (used before key_combo is initialized)"""
        if hasattr(self, 'key_combo'):
            self.key_combo.toggle_key_combo()
    
    def _start_listening_map_anoint_hotkey_wrapper(self):
        """Wrapper for start_listening_map_anoint_hotkey (used before map_anoint is initialized)"""
        if hasattr(self, 'map_anoint'):
            self.map_anoint.start_listening_map_anoint_hotkey()
    
    def _toggle_map_anoint_wrapper(self):
        """Wrapper for toggle_map_anoint (used before map_anoint is initialized)"""
        if hasattr(self, 'map_anoint'):
            self.map_anoint.toggle_map_anoint()
    
    def _clear_map_anoint_hotkey_wrapper(self):
        """Wrapper for clear_map_anoint_hotkey (used before map_anoint is initialized)"""
        if hasattr(self, 'map_anoint'):
            self.map_anoint.clear_map_anoint_hotkey()
    
    def _start_listening_dump_items_hotkey_wrapper(self):
        """Wrapper for start_listening_dump_items_hotkey (used before dump_items is initialized)"""
        if hasattr(self, 'dump_items'):
            self.dump_items.start_listening_dump_items_hotkey()
    
    def _clear_dump_items_hotkey_wrapper(self):
        """Wrapper for clear_dump_items_hotkey (used before dump_items is initialized)"""
        if hasattr(self, 'dump_items'):
            self.dump_items.clear_dump_items_hotkey()
    
    def _select_dump_items_coords_wrapper(self):
        """Wrapper for select_coordinates (used before dump_items is initialized)"""
        if hasattr(self, 'dump_items'):
            self.dump_items.select_coordinates()

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

        # Key Combo Controls
        self.setup_key_combo_controls(main_tab)

        # Map Anoint Controls
        self.setup_map_anoint_controls(main_tab)

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
        self.button_key.bind('<KeyRelease>', lambda e: self.save_all_settings())

        # Button Delay Frame
        button_delay_frame = tk.Frame(parent)
        button_delay_frame.pack()
        tk.Label(button_delay_frame, text="Delay").pack(side='left', padx=5)
        self.button_delay = tk.Text(button_delay_frame, height=1, width=5, bg="white")
        self.button_delay.pack(side='left')
        self.button_delay.bind('<KeyRelease>', lambda e: self.save_all_settings())

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
        self.weapon_key.bind('<KeyRelease>', lambda e: self.save_all_settings())

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

    def setup_key_combo_controls(self, parent):
        key_combo_frame = tk.Frame(parent)
        key_combo_frame.pack(pady=(20, 0))

        trigger_key_frame = tk.Frame(key_combo_frame)
        trigger_key_frame.pack()
        tk.Label(trigger_key_frame, text="Bind").pack(side='left', padx=5)
        self.key_combo_trigger_key = tk.Text(trigger_key_frame, height=1, width=5, bg="white")
        self.key_combo_trigger_key.pack(side='left')
        self.key_combo_trigger_key.bind('<KeyRelease>', lambda e: self.save_all_settings())

        combo_keys_frame = tk.Frame(key_combo_frame)
        combo_keys_frame.pack()
        tk.Label(combo_keys_frame, text="To keys").pack(side='left', padx=5)
        self.key_combo_keys = tk.Text(combo_keys_frame, height=1, width=20, bg="white")
        self.key_combo_keys.pack(side='left')
        self.key_combo_keys.bind('<KeyRelease>', lambda e: self.save_all_settings())

        self.click_key_combo_button = tk.Button(
            parent,
            text="Start key combo",
            command=self._toggle_key_combo_wrapper,
            width=20,
            height=5,
            padx=10,
            pady=10
        )
        self.click_key_combo_button.pack()
    
    def setup_map_anoint_controls(self, parent):
        self.click_map_anoint_button = tk.Button(
            parent,
            text="Anoint Map",
            command=self._toggle_map_anoint_wrapper,
            width=20,
            height=5,
            padx=10,
            pady=10
        )
        # self.click_map_anoint_button.pack(pady=(20, 0))  # Temporarily hidden

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
        
        # Map Anoint Hotkey Section
        map_anoint_hotkey_frame = tk.Frame(parent)
        map_anoint_hotkey_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(
            map_anoint_hotkey_frame,
            text="Map Anoint Hotkey:",
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        map_anoint_input_frame = tk.Frame(map_anoint_hotkey_frame)
        map_anoint_input_frame.pack(fill='x')
        
        self.map_anoint_hotkey_entry = tk.Entry(map_anoint_input_frame, width=20, state='readonly')
        self.map_anoint_hotkey_entry.pack(side='left', padx=5)
        
        self.map_anoint_set_button = tk.Button(
            map_anoint_input_frame,
            text="Set",
            command=self._start_listening_map_anoint_hotkey_wrapper,
            width=10
        )
        self.map_anoint_set_button.pack(side='left', padx=5)
        
        tk.Button(
            map_anoint_input_frame,
            text="Clear",
            command=self._clear_map_anoint_hotkey_wrapper,
            width=10
        ).pack(side='left', padx=5)
        
        self.map_anoint_status_label = tk.Label(
            map_anoint_hotkey_frame,
            text="Click 'Set' and press a key to assign hotkey",
            font=('Arial', 8),
            fg='gray'
        )
        self.map_anoint_status_label.pack(anchor='w', pady=(5, 0))
        
        # Dump Items Section
        dump_items_hotkey_frame = tk.Frame(parent)
        dump_items_hotkey_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(
            dump_items_hotkey_frame,
            text="Dump Items Hotkey:",
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        dump_items_input_frame = tk.Frame(dump_items_hotkey_frame)
        dump_items_input_frame.pack(fill='x')
        
        self.dump_items_hotkey_entry = tk.Entry(dump_items_input_frame, width=20, state='readonly')
        self.dump_items_hotkey_entry.pack(side='left', padx=5)
        
        self.dump_items_set_button = tk.Button(
            dump_items_input_frame,
            text="Set",
            command=self._start_listening_dump_items_hotkey_wrapper,
            width=10
        )
        self.dump_items_set_button.pack(side='left', padx=5)
        
        tk.Button(
            dump_items_input_frame,
            text="Clear",
            command=self._clear_dump_items_hotkey_wrapper,
            width=10
        ).pack(side='left', padx=5)
        
        self.dump_items_status_label = tk.Label(
            dump_items_hotkey_frame,
            text="Click 'Set' and press a key to assign hotkey",
            font=('Arial', 8),
            fg='gray'
        )
        self.dump_items_status_label.pack(anchor='w', pady=(5, 0))
        
        # Coordinates selection button
        coords_frame = tk.Frame(dump_items_hotkey_frame)
        coords_frame.pack(fill='x', pady=(10, 0))
        
        self.dump_items_coords_button = tk.Button(
            coords_frame,
            text="Select Coordinates",
            command=self._select_dump_items_coords_wrapper,
            width=20
        )
        self.dump_items_coords_button.pack()

    def _build_status_icon(self, dot_color: str) -> ImageTk.PhotoImage:
        """Build app icon with top-right status dot."""
        icon_size = 32
        icon = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)

        # Base icon shape
        draw.rounded_rectangle((3, 3, 29, 29), radius=6, fill=(38, 44, 58, 255))
        draw.rounded_rectangle((8, 8, 24, 24), radius=4, fill=(76, 86, 106, 255))

        # Status indicator in the top-right corner
        draw.ellipse((20, 2, 30, 12), fill=dot_color, outline=(240, 240, 240, 255), width=1)
        return ImageTk.PhotoImage(icon)

    def _build_status_icon_image(self, dot_color: str) -> Image.Image:
        """Build PIL image for Windows .ico generation."""
        icon_size = 32
        icon = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)
        draw.rounded_rectangle((3, 3, 29, 29), radius=6, fill=(38, 44, 58, 255))
        draw.rounded_rectangle((8, 8, 24, 24), radius=4, fill=(76, 86, 106, 255))
        draw.ellipse((19, 1, 31, 13), fill=dot_color, outline=(240, 240, 240, 255), width=1)
        return icon

    def _init_taskbar_overlay(self) -> bool:
        """Initialize ITaskbarList3 COM interface for pinned taskbar overlay icons."""
        try:
            self._ole32 = ctypes.OleDLL("ole32")
            self._ole32.CoInitialize(None)

            clsid_taskbar_list = GUID("{56FDF344-FD6D-11d0-958A-006097C9A090}")
            iid_itaskbarlist3 = GUID("{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEA84}")
            CLSCTX_INPROC_SERVER = 0x1

            hr = self._ole32.CoCreateInstance(
                ctypes.byref(clsid_taskbar_list),
                None,
                CLSCTX_INPROC_SERVER,
                ctypes.byref(iid_itaskbarlist3),
                ctypes.byref(self._taskbar_iface),
            )
            if hr != 0 or not self._taskbar_iface:
                return False

            vtbl = ctypes.cast(self._taskbar_iface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            hr_init = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(vtbl[3])
            return hr_init(self._taskbar_iface) == 0
        except Exception:
            return False

    def _prepare_windows_icon_resources(self):
        """Create .ico files and icon handles for reliable taskbar updates."""
        color_by_state = {"stopped": "#d32f2f", "running": "#2e7d32"}
        for state, color in color_by_state.items():
            icon_image = self._build_status_icon_image(color)
            icon_path = os.path.join(tempfile.gettempdir(), f"pgame_helper_{state}.ico")
            icon_image.save(icon_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
            self._status_icon_paths[state] = icon_path

            hicon = ctypes.windll.user32.LoadImageW(
                None,
                icon_path,
                1,  # IMAGE_ICON
                0,
                0,
                0x00000010  # LR_LOADFROMFILE
            )
            if hicon:
                self._status_icon_handles[state] = hicon

    def _create_status_icon_images(self):
        """Create status icon variants once and keep references."""
        self._status_icon_images["stopped"] = self._build_status_icon("#d32f2f")
        self._status_icon_images["running"] = self._build_status_icon("#2e7d32")
        self._prepare_windows_icon_resources()

    def _apply_windows_icon(self, state: str):
        """Set small and big icons directly via Win32 for taskbar reliability."""
        hwnd = self.root.winfo_id()
        hicon = self._status_icon_handles.get(state) or self._status_icon_handles.get("stopped")
        if not hicon or not hwnd:
            return

        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)

    def _apply_taskbar_overlay_icon(self, state: str):
        """Apply overlay icon via ITaskbarList3 for pinned taskbar buttons."""
        if not self._taskbar_overlay_enabled or not self._taskbar_iface:
            return

        hwnd = self.root.winfo_id()
        hicon = self._status_icon_handles.get(state) or self._status_icon_handles.get("stopped")
        if not hwnd or not hicon:
            return

        description = "Flask running" if state == "running" else "Flask stopped"
        try:
            vtbl = ctypes.cast(self._taskbar_iface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            set_overlay_icon = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p
            )(vtbl[18])
            set_overlay_icon(self._taskbar_iface, ctypes.c_void_p(hwnd), ctypes.c_void_p(hicon), description)
        except Exception:
            pass

    def _set_status_icon(self, state: str):
        """Apply icon to title bar/taskbar."""
        icon = self._status_icon_images.get(state) or self._status_icon_images.get("stopped")
        if icon is None:
            return
        self._current_status_icon = icon
        self.root.iconphoto(True, self._current_status_icon)
        self.root.wm_iconphoto(True, self._current_status_icon)
        icon_path = self._status_icon_paths.get(state) or self._status_icon_paths.get("stopped")
        if icon_path:
            try:
                self.root.iconbitmap(default=icon_path)
            except Exception:
                pass
        self._apply_windows_icon(state)
        self._apply_taskbar_overlay_icon(state)
        self.root.update_idletasks()


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
    
    def save_all_settings(self):
        """Helper method to save all settings including dump_items"""
        dump_items_coords = None
        if hasattr(self, 'dump_items'):
            dump_items_coords = self.dump_items.get_coords_dict()
        self.settings_manager.save_settings(
            self.button_key, 
            self.button_delay, 
            self.weapon_key, 
            self.flask_hotkey_entry, 
            self.weapon_swap_hotkey_entry, 
            self.map_anoint_hotkey_entry,
            self.dump_items_hotkey_entry,
            dump_items_coords,
            self.key_combo_trigger_key,
            self.key_combo_keys
        )

    def cleanup_and_close(self):
        """Cleanup all resources before closing"""
        if self._cleaning_up:
            return
        
        self._cleaning_up = True
        print("Cleaning up resources...")
        
        # Save settings before closing
        self.save_all_settings()
        
        try:
            # Stop all running operations
            if hasattr(self, 'flask'):
                self.flask.cleanup()
            if hasattr(self, 'weapon_swap'):
                self.weapon_swap.cleanup()
            if hasattr(self, 'key_combo'):
                self.key_combo.cleanup()
            if hasattr(self, 'map_anoint'):
                self.map_anoint.cleanup()
            if hasattr(self, 'dump_items'):
                self.dump_items.cleanup()

            # Note: We skip keyboard.unhook_all() since we've already unhooked all our specific hooks
            # Calling unhook_all() can sometimes block, and since we manage all hooks explicitly,
            # it's not necessary. The OS will clean up any remaining hooks when the process exits.
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            if self._taskbar_iface:
                try:
                    vtbl = ctypes.cast(self._taskbar_iface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
                    release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])
                    release(self._taskbar_iface)
                except Exception:
                    pass
                self._taskbar_iface = ctypes.c_void_p()
            try:
                if hasattr(self, "_ole32"):
                    self._ole32.CoUninitialize()
            except Exception:
                pass
            for hicon in self._status_icon_handles.values():
                try:
                    ctypes.windll.user32.DestroyIcon(hicon)
                except Exception:
                    pass
            self._status_icon_handles.clear()
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
