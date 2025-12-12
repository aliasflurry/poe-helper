import tkinter as tk
import pyautogui
import time
import keyboard
from typing import Optional
from threading import Event


class BoxSelector:
    """Class to handle box selection and clicking"""
    
    def __init__(self):
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.drawing = False
        self.canvas = None
        self.root = None

    def create_overlay(self):
        self.root = tk.Tk()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.attributes('-topmost', True)

        # This is enough. DO NOT use -transparentcolor — it breaks fullscreen on Windows
        try:
            self.root.attributes('-alpha', 0.3)
        except:
            pass

        # background must be non-transparent
        self.root.configure(bg='black')

        self.root.deiconify()
        self.root.update()

        # FULLSCREEN CANVAS
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            bg="black",
            cursor="crosshair"
        )
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Draw instructions
        self.canvas.create_text(
            screen_width // 2,
            50,
            text="Click and drag to draw a box. Press ESC to cancel.",
            fill='yellow',
            font=('Arial', 16, 'bold')
        )

        # Event binds
        self.root.bind_all('<Button-1>', self.on_button_press)
        self.root.bind_all('<B1-Motion>', self.on_move_press)
        self.root.bind_all('<ButtonRelease-1>', self.on_button_release)
        self.root.bind('<Escape>', self.cancel_selection)

        self.root.focus_force()
        self.root.mainloop()

    def on_button_press(self, event):
        """Handle mouse button press"""
        # Use screen coordinates for fullscreen window
        # For fullscreen at 0,0, x_root and y_root are the same as relative coordinates
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.drawing = True
        
    def on_move_press(self, event):
        """Handle mouse drag"""
        if self.drawing:
            # Get current screen coordinates
            current_x = event.x_root
            current_y = event.y_root
            # Clear previous rectangle
            self.canvas.delete('selection')
            # Draw new rectangle using screen coordinates
            self.canvas.create_rectangle(
                self.start_x, self.start_y, current_x, current_y,
                outline='yellow', width=3, tags='selection'
            )
            
    def on_motion(self, event):
        """Handle mouse motion"""
        pass
        
    def on_button_release(self, event):
        """Handle mouse button release"""
        if self.drawing:
            # Get screen coordinates
            self.end_x = event.x_root
            self.end_y = event.y_root
            self.drawing = False
            
            # Normalize coordinates (ensure start is top-left, end is bottom-right)
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
            
            self.start_x = x1
            self.start_y = y1
            self.end_x = x2
            self.end_y = y2
            
            # Close the overlay
            self.root.quit()
            self.root.destroy()
            
    def cancel_selection(self, event):
        """Cancel selection on ESC"""
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.root.quit()
        self.root.destroy()
        
    def get_box_coordinates(self):
        """Get the selected box coordinates"""
        return (self.start_x, self.start_y, self.end_x, self.end_y)


class DumpItems:
    """Manages dump items functionality"""
    
    def __init__(self,
                 dump_items_hotkey_entry: Optional[tk.Entry],
                 dump_items_set_button: Optional[tk.Button],
                 dump_items_status_label: Optional[tk.Label],
                 dump_items_coords_button: Optional[tk.Button],
                 is_path_of_exile_active_callback,
                 save_callback=None):
        """
        Initialize dump items manager
        
        Args:
            dump_items_hotkey_entry: Entry widget for hotkey display
            dump_items_set_button: Button to set hotkey
            dump_items_status_label: Label for hotkey status
            dump_items_coords_button: Button to select coordinates
            is_path_of_exile_active_callback: Callback function to check if POE is active
            save_callback: Callback function to save settings
        """
        self.dump_items_hotkey_entry = dump_items_hotkey_entry
        self.dump_items_set_button = dump_items_set_button
        self.dump_items_status_label = dump_items_status_label
        self.dump_items_coords_button = dump_items_coords_button
        self.is_path_of_exile_active = is_path_of_exile_active_callback
        self.save_callback = save_callback
        
        # State variables
        self.dump_items_hotkey: str = ""
        self.dump_items_hotkey_hook_ids: list = []  # List to store multiple hook IDs
        self.listening_for_dump_items_hotkey: bool = False
        self.dump_items_hotkey_listener_callback = None
        
        # Box coordinates (x1, y1, x2, y2)
        self.box_coords = None  # Will store (x1, y1, x2, y2) or None
        
        # Grid dimensions (hardcoded to 5 rows x 12 columns)
        self.grid_rows = 5
        self.grid_cols = 12
    
    def divide_box_into_grid(self, x1, y1, x2, y2):
        """
        Divide a box into a grid of sub-boxes
        
        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            
        Returns:
            List of (center_x, center_y) tuples for each sub-box
        """
        width = x2 - x1
        height = y2 - y1
        
        cell_width = width / self.grid_cols
        cell_height = height / self.grid_rows
        
        centers = []
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                if (row == 0 and row == 1) and col == 0:
                    continue
                
                # Calculate center of each cell
                center_x = x1 + (col + 0.5) * cell_width
                center_y = y1 + (row + 0.5) * cell_height
                centers.append((int(center_x), int(center_y)))
        
        return centers
    
    def ctrl_click_all_points(self, points, delay=0.01, move_duration=0.1):
        """
        Perform Ctrl+click on all points with smooth mouse movement
        
        Args:
            points: List of (x, y) tuples
            delay: Delay between clicks in seconds
            move_duration: Duration for smooth mouse movement in seconds
        """
        print(f"\nStarting to Ctrl+click on {len(points)} points...")
        print("Press ESC to stop clicking\n")
        
        # Flag to track if Esc was pressed
        esc_pressed = Event()
        unhook_callback = None
        
        # Set up Esc key listener
        def on_esc_press(event):
            if event.name == 'esc':
                esc_pressed.set()
        
        # Hook the Esc key and store the unhook callback
        try:
            unhook_callback = keyboard.hook(on_esc_press)
        except Exception as e:
            print(f"Warning: Could not set up ESC key listener: {e}")
        
        # Hold Ctrl key down at the start
        pyautogui.keyDown('ctrl')
        
        try:
            for i, (x, y) in enumerate(points, 1):
                # Check if Esc was pressed
                if esc_pressed.is_set():
                    print("\n⚠️  Stopped by user (ESC pressed)")
                    break
                
                # Smoothly move mouse to the center of the box
                pyautogui.moveTo(x, y, duration=move_duration)
                
                # Check again before clicking
                if esc_pressed.is_set():
                    print("\n⚠️  Stopped by user (ESC pressed)")
                    break
                
                # Click at the current mouse position (Ctrl is already held down)
                pyautogui.click()
                
                # Small delay between clicks
                time.sleep(delay)
                
                print(f"  ✅ Clicked {i}/{len(points)} at center ({x}, {y})")
            
            if not esc_pressed.is_set():
                print(f"\n✅ Completed clicking on all {len(points)} points")
            
        except KeyboardInterrupt:
            print("\n⚠️  Cancelled by user")
        except Exception as e:
            print(f"\n⚠️  Error performing clicks: {e}")
        finally:
            # Always release Ctrl key when done (whether finished, stopped, or error)
            try:
                pyautogui.keyUp('ctrl')
            except:
                pass
            
            # Unhook the keyboard listener
            try:
                if unhook_callback:
                    unhook_callback()
            except:
                pass
    
    def toggle_dump_items(self, e=None):
        """Execute dump items clicking sequence"""
        if not self.is_path_of_exile_active():
            print("Path of Exile is not active")
            return
        
        if self.box_coords is None:
            print("No coordinates set. Please select coordinates first.")
            return
        
        x1, y1, x2, y2 = self.box_coords
        
        # Divide box into grid
        points = self.divide_box_into_grid(x1, y1, x2, y2)
        print(f"✅ Generated {len(points)} click points")
        
        # Perform Ctrl+click on all points
        self.ctrl_click_all_points(points, delay=0.01, move_duration=0.01)
    
    def get_coords_dict(self):
        """Get coordinates as a dict for saving"""
        if self.box_coords is None:
            return None
        x1, y1, x2, y2 = self.box_coords
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    
    def set_coords_from_dict(self, coords_dict):
        """Set coordinates from a dict"""
        if coords_dict is None:
            self.box_coords = None
            return
        if isinstance(coords_dict, dict) and "x1" in coords_dict and "y1" in coords_dict and "x2" in coords_dict and "y2" in coords_dict:
            self.box_coords = (coords_dict["x1"], coords_dict["y1"], coords_dict["x2"], coords_dict["y2"])
    
    def select_coordinates(self):
        """Open box selector to get coordinates"""
        selector = BoxSelector()
        selector.create_overlay()
        
        # Get box coordinates
        x1, y1, x2, y2 = selector.get_box_coordinates()
        
        if x1 is None or y1 is None or x2 is None or y2 is None:
            print("\n⚠️  Selection cancelled")
            return
        
        # Save coordinates
        self.box_coords = (x1, y1, x2, y2)
        print(f"\n✅ Box selected:")
        print(f"   Top-left: ({x1}, {y1})")
        print(f"   Bottom-right: ({x2}, {y2})")
        print(f"   Width: {x2 - x1}px, Height: {y2 - y1}px")
        
        # Save settings
        if self.save_callback:
            self.save_callback()
    
    def start_listening_dump_items_hotkey(self):
        """Start listening for dump items hotkey"""
        if self.listening_for_dump_items_hotkey:
            self.stop_listening_dump_items_hotkey()
            return
        
        self.listening_for_dump_items_hotkey = True
        self.dump_items_set_button.config(text="Cancel", bg="red")
        self.dump_items_status_label.config(text="Press any key (or Ctrl+key) to set hotkey...", fg='blue')
        
        def on_key_press(event):
            if not self.listening_for_dump_items_hotkey:
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
            
            self.stop_listening_dump_items_hotkey()
            self.dump_items_hotkey_entry.config(state='normal')
            self.dump_items_hotkey_entry.delete(0, tk.END)
            self.dump_items_hotkey_entry.insert(0, hotkey_str)
            self.dump_items_hotkey_entry.config(state='readonly')
            self.update_dump_items_hotkey()
            self.dump_items_status_label.config(text=f"Hotkey set to: {hotkey_str}", fg='green')
            if self.save_callback:
                self.save_callback()
        
        self.dump_items_hotkey_listener_callback = keyboard.hook(on_key_press)

    def stop_listening_dump_items_hotkey(self):
        """Stop listening for dump items hotkey"""
        self.listening_for_dump_items_hotkey = False
        self.dump_items_set_button.config(text="Set", bg="SystemButtonFace")
        if self.dump_items_hotkey_listener_callback is not None:
            try:
                self.dump_items_hotkey_listener_callback()
            except:
                pass
            self.dump_items_hotkey_listener_callback = None

    def update_dump_items_hotkey(self, event=None):
        """Update dump items hotkey binding - registers both normal key and Ctrl+key"""
        new_hotkey = self.dump_items_hotkey_entry.get().strip().lower()
        
        # Unhook old hotkeys if they exist
        for hook_id in self.dump_items_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.dump_items_hotkey_hook_ids = []
        
        # Set new hotkey
        self.dump_items_hotkey = new_hotkey
        
        # Hook new hotkey if not empty
        if new_hotkey:
            try:
                # If it's already a combination, register it directly
                if '+' in new_hotkey:
                    # Register the combination directly
                    try:
                        hook_id = keyboard.add_hotkey(
                            new_hotkey,
                            self.toggle_dump_items
                        )
                        self.dump_items_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting dump items hotkey (combination): {ex}")
                else:
                    # For single keys, register only the key
                    try:
                        hook_id = keyboard.on_press_key(
                            new_hotkey,
                            lambda e: self.toggle_dump_items()
                        )
                        self.dump_items_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting dump items hotkey: {ex}")
            except Exception as ex:
                print(f"Error setting dump items hotkey: {ex}")

    def clear_dump_items_hotkey(self):
        """Clear dump items hotkey"""
        self.stop_listening_dump_items_hotkey()
        self.dump_items_hotkey_entry.config(state='normal')
        self.dump_items_hotkey_entry.delete(0, tk.END)
        self.dump_items_hotkey_entry.config(state='readonly')
        self.update_dump_items_hotkey()
        self.dump_items_status_label.config(text="Hotkey cleared", fg='gray')
        if self.save_callback:
            self.save_callback()
    
    def cleanup(self):
        """Cleanup all dump items resources"""
        self.stop_listening_dump_items_hotkey()
        
        # Unhook all hotkeys
        for hook_id in self.dump_items_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.dump_items_hotkey_hook_ids = []

