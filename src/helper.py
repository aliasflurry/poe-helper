import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import ctypes
import os
import tempfile
import webbrowser
from typing import Optional

import psutil
import win32process
from PIL import Image, ImageDraw, ImageTk

from app_config import APP_NAME, APP_VERSION
from dump_items import DumpItems
from flask import Flask
from key_combo import KeyCombo
from map_anoint import MapAnoint
from settings_manager import SettingsManager
from updater import check_for_update_async
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
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("680x600")
        self.root.minsize(620, 560)

        # Settings manager
        self.settings_manager = SettingsManager("settings.json")

        # Threading control (flask thread managed by Flask class)

        # State variables
        self.poe1_enabled = True
        self.poe2_enabled = True
        self.poe1_checkbox_var: Optional[tk.BooleanVar] = None
        self.poe2_checkbox_var: Optional[tk.BooleanVar] = None

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
        self.update_status_label: Optional[tk.Label] = None
        self.check_updates_button: Optional[tk.Button] = None
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
        self.root.after(1500, lambda: self.check_for_updates(manual=False))
    
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
        self._configure_theme()
        self.root.configure(bg="#f4f6f8")

        app_shell = tk.Frame(self.root, bg="#f4f6f8")
        app_shell.pack(fill="both", expand=True, padx=18, pady=16)

        header = tk.Frame(app_shell, bg="#f4f6f8")
        header.pack(fill="x", pady=(0, 12))
        tk.Label(
            header,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold"),
            bg="#f4f6f8",
            fg="#17202a",
        ).pack(anchor="w")
        tk.Label(
            header,
            text=f"Automation controls for Path of Exile sessions - v{APP_VERSION}",
            font=("Segoe UI", 9),
            bg="#f4f6f8",
            fg="#5f6b7a",
        ).pack(anchor="w", pady=(2, 0))

        self.tab_control = ttk.Notebook(app_shell)
        dashboard_tab = self._create_tab(self.tab_control)
        hotkeys_tab = self._create_tab(self.tab_control)
        tools_tab = self._create_tab(self.tab_control)
        self.tab_control.add(dashboard_tab, text="Dashboard")
        self.tab_control.add(hotkeys_tab, text="Hotkeys")
        self.tab_control.add(tools_tab, text="Tools")

        dashboard_body = tk.Frame(dashboard_tab, bg="#f4f6f8")
        dashboard_body.pack(fill="both", expand=True)
        self.setup_poe_checkboxes(dashboard_body)

        dashboard_columns = tk.Frame(dashboard_body, bg="#f4f6f8")
        dashboard_columns.pack(fill="both", expand=True)
        dashboard_columns.columnconfigure(0, weight=1)
        dashboard_columns.columnconfigure(1, weight=1)
        left_column = tk.Frame(dashboard_columns, bg="#f4f6f8")
        right_column = tk.Frame(dashboard_columns, bg="#f4f6f8")
        left_column.grid(row=0, column=0, sticky="new", padx=(0, 6))
        right_column.grid(row=0, column=1, sticky="new", padx=(6, 0))

        self.setup_key_combo_controls(left_column)
        self.setup_weapon_swap_controls(left_column)
        self.setup_flask_controls(right_column)
        self.setup_hotkey_settings(hotkeys_tab)
        self.setup_map_anoint_controls(tools_tab)
        self.setup_dump_items_tools(tools_tab)
        self.setup_update_controls(tools_tab)

        self.tab_control.pack(expand=1, fill='both')

    def _configure_theme(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background="#f4f6f8", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 9, "bold"))
        style.configure("TFrame", background="#f4f6f8")

    def _create_tab(self, notebook):
        tab = ttk.Frame(notebook)
        tab.columnconfigure(0, weight=1)
        return tab

    def _section(self, parent, title, subtitle=None, accent="#1f6feb"):
        section = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", highlightthickness=0)
        section.pack(fill="x", padx=2, pady=6)
        section.columnconfigure(1, weight=1)

        tk.Frame(section, bg=accent, width=5).grid(row=0, column=0, rowspan=2, sticky="ns")

        header = tk.Frame(section, bg="#ffffff")
        header.grid(row=0, column=1, sticky="ew", padx=14, pady=(10, 5))
        tk.Label(
            header,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#17202a",
        ).pack(anchor="w")
        if subtitle:
            tk.Label(
                header,
                text=subtitle,
                font=("Segoe UI", 8),
                bg="#ffffff",
                fg="#657384",
            ).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(section, bg="#ffffff")
        body.grid(row=1, column=1, sticky="ew", padx=14, pady=(0, 12))
        body.columnconfigure(0, weight=1)
        return body

    def _field_row(self, parent, label_text):
        row = tk.Frame(parent, bg="#ffffff")
        row.pack(fill="x", pady=4)
        tk.Label(
            row,
            text=label_text,
            width=14,
            anchor="w",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#334155",
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        return row

    def _text_field(self, parent, width):
        field = tk.Text(
            parent,
            height=1,
            width=width,
            bg="#f8fafc",
            fg="#111827",
            relief="solid",
            bd=1,
            padx=6,
            pady=3,
            font=("Segoe UI", 10),
        )
        field.grid(row=0, column=1, sticky="w")
        field.bind("<KeyRelease>", lambda e: self.save_all_settings())
        return field

    def _action_button(self, parent, text, command, width=20, color="#1f6feb", active_color="#1557b0"):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            height=1,
            bg=color,
            fg="white",
            activebackground=active_color,
            activeforeground="white",
            relief="flat",
            padx=10,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        return button

    def setup_poe_checkboxes(self, parent):
        body = self._section(
            parent,
            "Session Guard",
            "Run automation only when the selected game client is active.",
            accent="#2563eb"
        )
        self.poe1_checkbox_var = tk.BooleanVar(value=True)
        self.poe2_checkbox_var = tk.BooleanVar(value=True)

        for label, variable, command in [
            ("Path of Exile", self.poe1_checkbox_var, lambda: self.set_poe1_enabled(self.poe1_checkbox_var.get())),
            ("Path of Exile 2", self.poe2_checkbox_var, lambda: self.set_poe2_enabled(self.poe2_checkbox_var.get())),
        ]:
            tk.Checkbutton(
                body,
                text=label,
                variable=variable,
                command=command,
                bg="#ffffff",
                fg="#1f2937",
                activebackground="#ffffff",
                font=("Segoe UI", 9),
            ).pack(side="left", padx=(0, 18))

    def setup_flask_controls(self, parent):
        body = self._section(
            parent,
            "Flask Automation",
            "Press configured flask keys on a randomized delay.",
            accent="#16a34a"
        )
        self.button_key = self._text_field(self._field_row(body, "Flask keys"), 10)
        self.button_delay = self._text_field(self._field_row(body, "Delay range"), 10)
        self.click_flask_button = self._action_button(
            body,
            "Start flask",
            self._toggle_flask_wrapper,
            color="#16a34a",
            active_color="#15803d"
        )
        self.click_flask_button.pack(anchor="e", pady=(10, 0))

    def setup_weapon_swap_controls(self, parent):
        body = self._section(
            parent,
            "Weapon Swap",
            "Bind the in-game action key and run the swap sequence on A.",
            accent="#7c3aed"
        )
        self.weapon_key = self._text_field(self._field_row(body, "After swap"), 10)
        self.click_weapon_swap_button = self._action_button(
            body,
            "Start weapon swap",
            self._toggle_weapon_swap_wrapper,
            color="#7c3aed",
            active_color="#6d28d9"
        )
        self.click_weapon_swap_button.pack(anchor="e", pady=(10, 0))

    def setup_key_combo_controls(self, parent):
        body = self._section(
            parent,
            "Key Bind",
            "Bind one trigger key to a timed sequence such as A -> X F.",
            accent="#f97316"
        )
        self.key_combo_trigger_key = self._text_field(self._field_row(body, "Bind key"), 10)
        self.key_combo_keys = self._text_field(self._field_row(body, "Press keys"), 10)
        self.click_key_combo_button = self._action_button(
            body,
            "Start key bind",
            self._toggle_key_combo_wrapper,
            color="#f97316",
            active_color="#ea580c"
        )
        self.click_key_combo_button.pack(anchor="e", pady=(10, 0))
    
    def setup_map_anoint_controls(self, parent):
        body = self._section(parent, "Map Anoint", "Run the configured oil sequence.", accent="#0891b2")
        self.click_map_anoint_button = self._action_button(
            body,
            "Anoint Map",
            self._toggle_map_anoint_wrapper,
            color="#0891b2",
            active_color="#0e7490"
        )
        self.click_map_anoint_button.pack(anchor="w")

    def setup_dump_items_tools(self, parent):
        body = self._section(parent, "Dump Items", "Select inventory bounds for stash dumping.", accent="#db2777")
        self.dump_items_coords_button = self._action_button(
            body,
            "Select Coordinates",
            self._select_dump_items_coords_wrapper,
            width=22,
            color="#db2777",
            active_color="#be185d"
        )
        self.dump_items_coords_button.pack(anchor="w")

    def setup_update_controls(self, parent):
        body = self._section(parent, "Updates", "Check GitHub Releases for a newer installer.", accent="#0f766e")
        self.check_updates_button = self._action_button(
            body,
            "Check for updates",
            lambda: self.check_for_updates(manual=True),
            width=20,
            color="#0f766e",
            active_color="#115e59",
        )
        self.check_updates_button.pack(anchor="w")
        self.update_status_label = tk.Label(
            body,
            text=f"Current version: {APP_VERSION}",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#ffffff",
        )
        self.update_status_label.pack(anchor="w", pady=(8, 0))

    def setup_hotkey_settings(self, parent):
        """Setup hotkey configuration UI"""
        body = self._section(
            parent,
            "Global Hotkeys",
            "Set shortcuts for toggles and one-shot tools.",
            accent="#475569"
        )
        self.flask_hotkey_entry, self.flask_set_button, self.flask_status_label = self._hotkey_row(
            body,
            "Flask toggle",
            self._start_listening_flask_hotkey_wrapper,
            self._clear_flask_hotkey_wrapper,
        )
        self.weapon_swap_hotkey_entry, self.weapon_swap_set_button, self.weapon_swap_status_label = self._hotkey_row(
            body,
            "Weapon swap",
            self._start_listening_weapon_swap_hotkey_wrapper,
            self._clear_weapon_swap_hotkey_wrapper,
        )
        self.map_anoint_hotkey_entry, self.map_anoint_set_button, self.map_anoint_status_label = self._hotkey_row(
            body,
            "Map anoint",
            self._start_listening_map_anoint_hotkey_wrapper,
            self._clear_map_anoint_hotkey_wrapper,
        )
        self.dump_items_hotkey_entry, self.dump_items_set_button, self.dump_items_status_label = self._hotkey_row(
            body,
            "Dump items",
            self._start_listening_dump_items_hotkey_wrapper,
            self._clear_dump_items_hotkey_wrapper,
        )

    def _hotkey_row(self, parent, label_text, set_command, clear_command):
        row = tk.Frame(parent, bg="#ffffff")
        row.pack(fill="x", pady=8)

        tk.Label(
            row,
            text=label_text,
            width=14,
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#334155",
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        entry = tk.Entry(row, width=11, state="readonly", relief="solid", bd=1, font=("Segoe UI", 10))
        entry.grid(row=0, column=1, sticky="w", padx=(0, 8))

        set_button = tk.Button(
            row,
            text="Set",
            command=set_command,
            width=8,
            bg="#e8f0fe",
            fg="#174ea6",
            activebackground="#d2e3fc",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        set_button.grid(row=0, column=2, padx=(0, 6))

        tk.Button(
            row,
            text="Clear",
            command=clear_command,
            width=8,
            bg="#f1f5f9",
            fg="#334155",
            activebackground="#e2e8f0",
            relief="flat",
            font=("Segoe UI", 9),
        ).grid(row=0, column=3)

        status = tk.Label(
            row,
            text="No hotkey set",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#ffffff",
        )
        status.grid(row=1, column=1, columnspan=3, sticky="w", pady=(4, 0))
        return entry, set_button, status

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

    def check_for_updates(self, manual: bool = False):
        """Check GitHub Releases for a newer app version."""
        if self._cleaning_up:
            return

        if self.update_status_label:
            self.update_status_label.config(text="Checking for updates...", fg="#475569")
        if self.check_updates_button:
            self.check_updates_button.config(state="disabled")

        def on_result(result):
            self.root.after(0, lambda: self._handle_update_result(result, manual))

        check_for_update_async(on_result)

    def _handle_update_result(self, result: dict, manual: bool):
        if self._cleaning_up:
            return

        if self.check_updates_button:
            self.check_updates_button.config(state="normal")

        if not result.get("ok"):
            error_text = str(result.get("error") or "Could not check for updates.")
            if self.update_status_label:
                self.update_status_label.config(text=error_text, fg="#b45309")
            if manual:
                messagebox.showwarning("Update check", error_text, parent=self.root)
            return

        latest_version = str(result.get("latest_version"))
        if not result.get("update_available"):
            status = f"You're up to date: v{APP_VERSION}"
            if self.update_status_label:
                self.update_status_label.config(text=status, fg="#15803d")
            if manual:
                messagebox.showinfo("Update check", status, parent=self.root)
            return

        download_url = result.get("download_url") or result.get("html_url")
        status = f"New version available: v{latest_version}"
        if self.update_status_label:
            self.update_status_label.config(text=status, fg="#1d4ed8")

        if messagebox.askyesno(
            "Update available",
            f"{APP_NAME} v{latest_version} is available.\n\nOpen the download page now?",
            parent=self.root,
        ):
            if download_url:
                webbrowser.open(str(download_url))

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
