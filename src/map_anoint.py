import time
import tkinter as tk
import keyboard
import pyautogui
import os
from typing import Optional, List, Tuple, TYPE_CHECKING
from threading import Event

if TYPE_CHECKING:
    import numpy as np

try:
    import cv2
    import numpy as np
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    np = None  # Set to None so type hints can use it
    print("Warning: opencv-python, numpy, or Pillow not installed. Image detection will not work.")


class MapAnoint:
    """Manages map anointing functionality"""
    
    def __init__(self, 
                 click_map_anoint_button: Optional[tk.Button],
                 map_anoint_hotkey_entry: Optional[tk.Entry],
                 map_anoint_set_button: Optional[tk.Button],
                 map_anoint_status_label: Optional[tk.Label],
                 is_path_of_exile_active_callback,
                 save_callback=None):
        """
        Initialize map anoint manager
        
        Args:
            click_map_anoint_button: Button to trigger map anointing
            map_anoint_hotkey_entry: Entry widget for hotkey display
            map_anoint_set_button: Button to set hotkey
            map_anoint_status_label: Label for hotkey status
            is_path_of_exile_active_callback: Callback function to check if POE is active
        """
        self.click_map_anoint_button = click_map_anoint_button
        self.map_anoint_hotkey_entry = map_anoint_hotkey_entry
        self.map_anoint_set_button = map_anoint_set_button
        self.map_anoint_status_label = map_anoint_status_label
        self.is_path_of_exile_active = is_path_of_exile_active_callback
        self.save_callback = save_callback
        
        # State variables
        self.map_anoint_event = Event()
        self.map_anoint_hotkey: str = ""
        self.map_anoint_hotkey_hook_ids: list = []  # List to store multiple hook IDs
        self.listening_for_map_anoint_hotkey: bool = False
        self.map_anoint_hotkey_listener_callback = None
        
        # Oil configuration
        # 3 teal, 1 opalescence, 2 golden, 2 silver
        self.oil_sequence = [
            'teal', 'teal', 'teal',
            'opalescence',
            'golden', 'golden',
            'silver', 'silver'
        ]
    
    def execute_map_anoint(self, e=None):
        """
        Execute map anointing sequence
        
        This function will:
        1. Right-click on the map (map should be under cursor or in inventory/stash)
        2. Wait for anointing interface to open
        3. Left-click on oils in the blight stash tab in sequence: 3 teal, 1 opalescence, 2 golden, 2 silver
        
        Note: This assumes:
        - The blight stash tab is open and visible
        - Oils are positioned in the stash tab in the correct order
        - Your cursor will be positioned over each oil in sequence (or oils are in fixed stash positions)
        """
        if self.map_anoint_event.is_set() or not self.is_path_of_exile_active():
            return

        try:
            # Right-click to pick up/open the map (assuming map is under cursor or in inventory/stash)
            # If map is in inventory/stash, position cursor over it first
            pyautogui.rightClick()
            time.sleep(0.5)
            
            # Wait for anointing interface to open
            time.sleep(1.5)
            
            # Apply oils in sequence from blight stash tab
            # In Path of Exile, when anointing interface is open, you left-click oils in stash to apply them
            # This implementation assumes oils are in your blight stash tab and you'll position
            # your cursor over each oil in sequence, or oils are in fixed stash positions
            
            print(f"Applying {len(self.oil_sequence)} oils from blight stash tab: {', '.join(self.oil_sequence)}")
            
            for i, oil in enumerate(self.oil_sequence):
                if self.map_anoint_event.is_set():
                    break
                
                # Left-click to apply oil from stash tab
                # Note: Position your cursor over the oil in the blight stash tab before each click
                # The oils should be in order: 3 teal, 1 opalescence, 2 golden, 2 silver
                pyautogui.click()  # Left-click to apply oil from stash
                time.sleep(0.4)  # Delay between oil applications
                print(f"Applied {oil} oil ({i+1}/{len(self.oil_sequence)})")
            
            # Close the anointing interface (press Escape)
            time.sleep(0.5)
            keyboard.press_and_release('escape')
            time.sleep(0.3)
            
            print("Map anointing completed!")
            
        except Exception as ex:
            print(f"Map anoint error: {ex}")
    
    def toggle_map_anoint(self):
        """Toggle map anointing functionality"""
        if self.click_map_anoint_button['text'] == 'Anoint Map':
            self.execute_map_anoint()
        else:
            # If we add continuous mode later
            pass
    
    def start_listening_map_anoint_hotkey(self):
        """Start listening for map anoint hotkey"""
        if self.listening_for_map_anoint_hotkey:
            self.stop_listening_map_anoint_hotkey()
            return
        
        self.listening_for_map_anoint_hotkey = True
        self.map_anoint_set_button.config(text="Cancel", bg="red")
        self.map_anoint_status_label.config(text="Press any key (or Ctrl+key) to set hotkey...", fg='blue')
        
        def on_key_press(event):
            if not self.listening_for_map_anoint_hotkey:
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
            
            self.stop_listening_map_anoint_hotkey()
            self.map_anoint_hotkey_entry.config(state='normal')
            self.map_anoint_hotkey_entry.delete(0, tk.END)
            self.map_anoint_hotkey_entry.insert(0, hotkey_str)
            self.map_anoint_hotkey_entry.config(state='readonly')
            self.update_map_anoint_hotkey()
            self.map_anoint_status_label.config(text=f"Hotkey set to: {hotkey_str}", fg='green')
            if self.save_callback:
                self.save_callback()
        
        self.map_anoint_hotkey_listener_callback = keyboard.hook(on_key_press)

    def stop_listening_map_anoint_hotkey(self):
        """Stop listening for map anoint hotkey"""
        self.listening_for_map_anoint_hotkey = False
        self.map_anoint_set_button.config(text="Set", bg="SystemButtonFace")
        if self.map_anoint_hotkey_listener_callback is not None:
            try:
                self.map_anoint_hotkey_listener_callback()
            except:
                pass
            self.map_anoint_hotkey_listener_callback = None

    def update_map_anoint_hotkey(self, event=None):
        """Update map anoint hotkey binding - registers both normal key and Ctrl+key"""
        new_hotkey = self.map_anoint_hotkey_entry.get().strip().lower()
        
        # Unhook old hotkeys if they exist
        for hook_id in self.map_anoint_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.map_anoint_hotkey_hook_ids = []
        
        # Set new hotkey
        self.map_anoint_hotkey = new_hotkey
        
        # Hook new hotkey if not empty
        if new_hotkey:
            try:
                # If it's already a combination, register it directly
                if '+' in new_hotkey:
                    # Register the combination directly
                    try:
                        hook_id = keyboard.add_hotkey(
                            new_hotkey,
                            self.execute_map_anoint
                        )
                        self.map_anoint_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting map anoint hotkey (combination): {ex}")
                else:
                    # For single keys, register only the key
                    try:
                        hook_id = keyboard.on_press_key(
                            new_hotkey,
                            lambda e: self.execute_map_anoint()
                        )
                        self.map_anoint_hotkey_hook_ids.append(hook_id)
                    except Exception as ex:
                        print(f"Error setting map anoint hotkey: {ex}")
            except Exception as ex:
                print(f"Error setting map anoint hotkey: {ex}")

    def clear_map_anoint_hotkey(self):
        """Clear map anoint hotkey"""
        self.stop_listening_map_anoint_hotkey()
        self.map_anoint_hotkey_entry.config(state='normal')
        self.map_anoint_hotkey_entry.delete(0, tk.END)
        self.map_anoint_hotkey_entry.config(state='readonly')
        self.update_map_anoint_hotkey()
        self.map_anoint_status_label.config(text="Hotkey cleared", fg='gray')
        if self.save_callback:
            self.save_callback()
    
    def detect_blight_maps(self, 
                          image_path: str = "assets/blight_maps.png",
                          confidence_threshold: float = 0.7,
                          use_color_detection: bool = False,
                          use_template_matching: bool = True,
                          template_path: Optional[str] = "assets/blight_map.png") -> List[Tuple[int, int, int, int]]:
        """
        Detect all blight maps in the given image file using template matching.
        
        Uses blight_map.png as a template to find all blight maps in blight_maps.png.
        
        Args:
            image_path: Path to the image file containing blight maps (default: assets/blight_maps.png)
            confidence_threshold: Minimum confidence for detection (0.0-1.0, default: 0.7)
            use_color_detection: Use color-based detection for blight maps (default: False)
            use_template_matching: Use template matching if template is provided (default: True)
            template_path: Path to template image for template matching (default: assets/blight_map.png)
            
        Returns:
            List of tuples containing (x, y, width, height) for each detected blight map
            Returns empty list if image processing is not available or image not found
        """
        if not IMAGE_PROCESSING_AVAILABLE:
            print("Image processing libraries not available. Please install opencv-python, numpy, and Pillow.")
            return []
        
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return []
        
        try:
            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Failed to load image: {image_path}")
                return []
            
            detected_maps = []
            
            # Method 1: Template matching (primary method, uses blight_map.png as template)
            if use_template_matching:
                if template_path is None:
                    template_path = "assets/blight_map.png"
                
                if os.path.exists(template_path):
                    template_detections = self._detect_by_template(image, template_path, confidence_threshold)
                    detected_maps.extend(template_detections)
                    print(f"Template matching found {len(template_detections)} potential blight map(s)")
                else:
                    print(f"Template file not found: {template_path}")
            
            # Method 2: Color-based detection (optional fallback)
            if use_color_detection:
                color_detections = self._detect_by_color(image, confidence_threshold)
                detected_maps.extend(color_detections)
                print(f"Color detection found {len(color_detections)} potential blight map(s)")
            
            # Remove duplicate detections (overlapping bounding boxes)
            detected_maps = self._remove_duplicate_detections(detected_maps)
            
            print(f"Detected {len(detected_maps)} blight map(s) in {image_path}")
            return detected_maps
            
        except Exception as ex:
            print(f"Error detecting blight maps: {ex}")
            return []
    
    def _detect_by_color(self, image, confidence_threshold: float) -> List[Tuple[int, int, int, int]]:
        """
        Detect blight maps using color-based detection.
        Blight maps in Path of Exile typically have distinctive color schemes.
        """
        if not IMAGE_PROCESSING_AVAILABLE or np is None:
            return []
        
        detected = []
        
        try:
            # Convert to HSV color space for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define color ranges for blight maps
            # Blight maps often have orange/yellow tints and dark backgrounds
            # Adjust these ranges based on actual blight map appearance
            
            # Orange/yellow range (common in blight-themed items)
            lower_orange = np.array([10, 100, 100])
            upper_orange = np.array([30, 255, 255])
            mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
            
            # Yellow/gold range
            lower_yellow = np.array([20, 50, 50])
            upper_yellow = np.array([40, 255, 255])
            mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
            
            # Combine masks
            mask = cv2.bitwise_or(mask_orange, mask_yellow)
            
            # Apply morphological operations to clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size and aspect ratio (maps are typically square-ish)
            min_area = 500  # Minimum area for a map
            max_area = 50000  # Maximum area for a map
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h if h > 0 else 0
                    
                    # Maps are typically roughly square (aspect ratio between 0.7 and 1.4)
                    if 0.7 <= aspect_ratio <= 1.4:
                        detected.append((x, y, w, h))
            
        except Exception as ex:
            print(f"Error in color-based detection: {ex}")
        
        return detected
    
    def _detect_by_template(self, image, template_path: str, confidence_threshold: float) -> List[Tuple[int, int, int, int]]:
        """
        Detect blight maps using template matching.
        Uses non-maximum suppression to avoid duplicate detections of the same map.
        """
        if not IMAGE_PROCESSING_AVAILABLE or np is None:
            return []
        
        detected = []
        
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                print(f"Failed to load template: {template_path}")
                return detected
            
            # Convert to grayscale for template matching
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Perform template matching
            result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            # Find all locations where the match exceeds the threshold
            locations = np.where(result >= confidence_threshold)
            
            template_h, template_w = template_gray.shape
            
            # Extract all matches with their confidence scores
            matches = []
            for pt in zip(*locations[::-1]):  # Switch x and y coordinates
                x, y = pt
                confidence = result[y, x]
                matches.append((x, y, confidence))
            
            # Sort by confidence (highest first)
            matches.sort(key=lambda m: m[2], reverse=True)
            
            # Apply non-maximum suppression to remove overlapping detections
            # Keep only the highest confidence detection in each area
            for x, y, confidence in matches:
                # Check if this detection overlaps significantly with any existing detection
                is_duplicate = False
                for existing_x, existing_y, existing_w, existing_h in detected:
                    # Calculate overlap
                    x_overlap = max(0, min(x + template_w, existing_x + existing_w) - max(x, existing_x))
                    y_overlap = max(0, min(y + template_h, existing_y + existing_h) - max(y, existing_y))
                    overlap_area = x_overlap * y_overlap
                    template_area = template_w * template_h
                    
                    # If overlap is more than 30% of template area, consider it a duplicate
                    if overlap_area > 0.3 * template_area:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    detected.append((x, y, template_w, template_h))
            
        except Exception as ex:
            print(f"Error in template matching: {ex}")
            import traceback
            traceback.print_exc()
        
        return detected
    
    def _remove_duplicate_detections(self, detections: List[Tuple[int, int, int, int]], 
                                     overlap_threshold: float = 0.5) -> List[Tuple[int, int, int, int]]:
        """
        Remove duplicate/overlapping detections.
        
        Args:
            detections: List of (x, y, w, h) bounding boxes
            overlap_threshold: Minimum overlap ratio to consider as duplicate
            
        Returns:
            Filtered list of detections
        """
        if not detections:
            return []
        
        # Sort by area (largest first) to keep the most confident detections
        detections_with_area = [(det, det[2] * det[3]) for det in detections]
        detections_with_area.sort(key=lambda x: x[1], reverse=True)
        
        filtered = []
        
        for det, _ in detections_with_area:
            x1, y1, w1, h1 = det
            is_duplicate = False
            
            for existing_det in filtered:
                x2, y2, w2, h2 = existing_det
                
                # Calculate intersection
                x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                intersection = x_overlap * y_overlap
                
                # Calculate union
                area1 = w1 * h1
                area2 = w2 * h2
                union = area1 + area2 - intersection
                
                # Calculate overlap ratio
                if union > 0:
                    overlap_ratio = intersection / union
                    if overlap_ratio > overlap_threshold:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                filtered.append(det)
        
        return filtered
    
    def test_blight_map_detection(self, 
                                  image_path: str = "assets/blight_maps.png",
                                  template_path: str = "assets/blight_map.png",
                                  confidence_threshold: float = 0.7,
                                  save_result_image: bool = True,
                                  result_image_path: str = "assets/blight_maps_detected.png") -> List[Tuple[int, int, int, int]]:
        """
        Test function to detect blight maps and optionally visualize the results.
        
        Args:
            image_path: Path to the image file containing blight maps (default: assets/blight_maps.png)
            template_path: Path to template image for template matching (default: assets/blight_map.png)
            confidence_threshold: Minimum confidence for detection (0.0-1.0, default: 0.7)
            save_result_image: Whether to save an image with bounding boxes drawn (default: True)
            result_image_path: Path to save the result image with detections marked (default: assets/blight_maps_detected.png)
            
        Returns:
            List of tuples containing (x, y, width, height) for each detected blight map
        """
        if not IMAGE_PROCESSING_AVAILABLE:
            print("Image processing libraries not available. Please install opencv-python, numpy, and Pillow.")
            return []
        
        print("=" * 60)
        print("Testing Blight Map Detection")
        print("=" * 60)
        print(f"Image path: {image_path}")
        print(f"Template path: {template_path}")
        print(f"Confidence threshold: {confidence_threshold}")
        print("-" * 60)
        
        # Detect blight maps using template matching
        detected_maps = self.detect_blight_maps(
            image_path=image_path,
            confidence_threshold=confidence_threshold,
            use_template_matching=True,
            template_path=template_path,
            use_color_detection=False
        )
        
        if not detected_maps:
            print("\nNo blight maps detected!")
            return []
        
        print(f"\n✓ Successfully detected {len(detected_maps)} blight map(s)")
        print("\nDetection details:")
        for i, (x, y, w, h) in enumerate(detected_maps, 1):
            print(f"  Map {i}: Position=({x}, {y}), Size={w}x{h}")
        
        # Optionally save result image with bounding boxes
        if save_result_image and IMAGE_PROCESSING_AVAILABLE:
            try:
                image = cv2.imread(image_path)
                if image is not None:
                    # Draw bounding boxes on the image
                    for x, y, w, h in detected_maps:
                        # Draw rectangle
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        # Draw label
                        cv2.putText(image, f"Blight Map", (x, y - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Save the result image
                    result_dir = os.path.dirname(result_image_path)
                    if result_dir and not os.path.exists(result_dir):
                        os.makedirs(result_dir, exist_ok=True)
                    
                    cv2.imwrite(result_image_path, image)
                    print(f"\n✓ Saved result image with detections: {result_image_path}")
                else:
                    print(f"\n⚠ Could not load image for visualization: {image_path}")
            except Exception as ex:
                print(f"\n⚠ Error saving result image: {ex}")
        
        print("=" * 60)
        return detected_maps
    
    def cleanup(self):
        """Cleanup all map anoint resources"""
        self.stop_listening_map_anoint_hotkey()
        
        # Unhook all hotkeys
        for hook_id in self.map_anoint_hotkey_hook_ids:
            try:
                # add_hotkey returns a callback function, on_press_key returns an int
                if callable(hook_id):
                    hook_id()  # Call the callback to remove the hotkey
                else:
                    keyboard.unhook_key(hook_id)
            except:
                pass
        self.map_anoint_hotkey_hook_ids = []

