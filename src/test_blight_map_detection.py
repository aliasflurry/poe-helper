"""
Test file for blight map detection functionality.

This script tests the detect_blight_maps() function from the MapAnoint class.
Run this file to verify that the detection function works correctly.

Usage:
    python test_blight_map_detection.py
"""

import os
import sys
from typing import List, Tuple, Optional

# Add the current directory to the path so we can import map_anoint
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from map_anoint import MapAnoint
    import tkinter as tk
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)


def capture_current_screen(save_path: Optional[str] = None) -> Optional[str]:
    """
    Capture the current screen and save it to a file.
    
    Args:
        save_path: Optional path to save the screenshot. If None, saves to assets/blight_screen_capture.png.
        
    Returns:
        Path to the saved screenshot file, or None if capture failed.
    """
    try:
        import pyautogui
        
        # Capture the screen
        screenshot = pyautogui.screenshot()
        
        # Determine save path
        if save_path is None:
            # Save to assets folder by default
            assets_dir = "assets"
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir)
            save_path = os.path.join(assets_dir, "blight_screen_capture.png")
        
        # Save the screenshot
        screenshot.save(save_path)
        print(f"  📸 Screen captured and saved to: {save_path}")
        return save_path
        
    except ImportError:
        print("  ⚠️  pyautogui not available for screen capture")
        return None
    except Exception as e:
        print(f"  ⚠️  Error capturing screen: {e}")
        return None


def test_basic_detection():
    """Test basic blight map detection with default parameters."""
    print("\n" + "="*60)
    print("Test 1: Basic Detection with Default Parameters")
    print("="*60)
    
    # Create a minimal MapAnoint instance (we don't need all UI elements for testing)
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    map_anoint = MapAnoint(
        click_map_anoint_button=None,
        map_anoint_hotkey_entry=None,
        map_anoint_set_button=None,
        map_anoint_status_label=None,
        is_path_of_exile_active_callback=lambda: True,
        save_callback=None
    )
    
    # Capture current screen instead of using static image file
    print("Capturing current screen...")
    image_path = capture_current_screen()
    
    if image_path is None or not os.path.exists(image_path):
        print(f"❌ Failed to capture screen")
        root.destroy()
        return False
    
    print(f"Testing detection on captured screen: {image_path}")
    detected_maps = map_anoint.detect_blight_maps(image_path=image_path)
    
    print(f"\nResults:")
    print(f"  Total blight maps detected: {len(detected_maps)}")
    
    if detected_maps:
        print(f"\n  Detected blight maps:")
        for i, (x, y, w, h) in enumerate(detected_maps, 1):
            print(f"    Map {i}: Position=({x}, {y}), Size={w}x{h}, Area={w*h}")
        print("  ✅ Detection successful!")
    else:
        print("  ⚠️  No blight maps detected.")
        print("     This might be normal if:")
        print("     - The image doesn't contain blight maps")
        print("     - The color thresholds need adjustment")
        print("     - The image quality/resolution is different than expected")
    
    root.destroy()
    return len(detected_maps) > 0


def test_different_confidence_thresholds():
    """Test detection with different confidence thresholds."""
    print("\n" + "="*60)
    print("Test 2: Different Confidence Thresholds")
    print("="*60)
    
    root = tk.Tk()
    root.withdraw()
    
    map_anoint = MapAnoint(
        click_map_anoint_button=None,
        map_anoint_hotkey_entry=None,
        map_anoint_set_button=None,
        map_anoint_status_label=None,
        is_path_of_exile_active_callback=lambda: True,
        save_callback=None
    )
    
    # Capture current screen instead of using static image file
    print("Capturing current screen...")
    image_path = capture_current_screen()
    
    if image_path is None or not os.path.exists(image_path):
        print(f"❌ Failed to capture screen")
        root.destroy()
        return False
    
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    for threshold in thresholds:
        detected_maps = map_anoint.detect_blight_maps(
            image_path=image_path,
            confidence_threshold=threshold,
            use_color_detection=True
        )
        print(f"  Confidence {threshold:.1f}: {len(detected_maps)} maps detected")
    
    root.destroy()
    return True


def test_error_handling():
    """Test error handling for missing files and invalid inputs."""
    print("\n" + "="*60)
    print("Test 3: Error Handling")
    print("="*60)
    
    root = tk.Tk()
    root.withdraw()
    
    map_anoint = MapAnoint(
        click_map_anoint_button=None,
        map_anoint_hotkey_entry=None,
        map_anoint_set_button=None,
        map_anoint_status_label=None,
        is_path_of_exile_active_callback=lambda: True,
        save_callback=None
    )
    
    # Test with non-existent file
    print("  Testing with non-existent file...")
    result = map_anoint.detect_blight_maps(image_path="nonexistent_file.png")
    assert result == [], "Should return empty list for non-existent file"
    print("  ✅ Correctly handles missing file")
    
    # Test with invalid image path
    print("  Testing with invalid path...")
    result = map_anoint.detect_blight_maps(image_path="")
    assert result == [], "Should return empty list for invalid path"
    print("  ✅ Correctly handles invalid path")
    
    root.destroy()
    return True


def test_color_detection_only():
    """Test detection using only color-based method."""
    print("\n" + "="*60)
    print("Test 4: Color Detection Only")
    print("="*60)
    
    root = tk.Tk()
    root.withdraw()
    
    map_anoint = MapAnoint(
        click_map_anoint_button=None,
        map_anoint_hotkey_entry=None,
        map_anoint_set_button=None,
        map_anoint_status_label=None,
        is_path_of_exile_active_callback=lambda: True,
        save_callback=None
    )
    
    # Capture current screen instead of using static image file
    print("Capturing current screen...")
    image_path = capture_current_screen()
    
    if image_path is None or not os.path.exists(image_path):
        print(f"❌ Failed to capture screen")
        root.destroy()
        return False
    
    detected_maps = map_anoint.detect_blight_maps(
        image_path=image_path,
        use_color_detection=True,
        use_template_matching=False
    )
    
    print(f"  Detected {len(detected_maps)} maps using color detection")
    
    root.destroy()
    return True


def visualize_detections(image_path: str, detected_maps: List[Tuple[int, int, int, int]]):
    """
    Visualize detected blight maps by drawing bounding boxes.
    Requires opencv-python to be installed.
    Also performs Ctrl + left click on all detected blight maps.
    """
    try:
        import cv2
        import numpy as np
        
        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  ⚠️  Could not load image for visualization: {image_path}")
            return
        
        # Draw bounding boxes on the image
        for x, y, w, h in detected_maps:
            # Draw rectangle
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Add label
            cv2.putText(image, "Blight Map", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Save the result
        output_path = "assets/blight_maps_detected.png"
        cv2.imwrite(output_path, image)
        print(f"  ✅ Visualization saved to: {output_path}")
        
        # Perform Ctrl + left click on all detected blight maps
        if detected_maps:
            try:
                import pyautogui
                import time
                
                print(f"  🖱️  Performing Ctrl + left click on {len(detected_maps)} detected blight map(s)...")
                
                for i, (x, y, w, h) in enumerate(detected_maps, 1):
                    # Calculate center of the detected map
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # Move mouse to the center of the detected map
                    pyautogui.moveTo(center_x, center_y)
                    time.sleep(0.1)  # Small delay to allow mouse to reach position
                    
                    # Press Ctrl key
                    pyautogui.keyDown('ctrl')
                    time.sleep(0.05)  # Small delay to ensure Ctrl is pressed
                    
                    # Left click at current mouse position
                    pyautogui.click()
                    
                    # Release Ctrl key
                    pyautogui.keyUp('ctrl')
                    
                    # Small delay between clicks
                    time.sleep(0.2)
                    
                    print(f"    ✅ Clicked blight map {i}/{len(detected_maps)} at ({center_x}, {center_y})")
                
                print(f"  ✅ Completed clicking on all {len(detected_maps)} blight map(s)")
                
            except ImportError:
                print("  ⚠️  pyautogui not available for clicking")
            except Exception as e:
                print(f"  ⚠️  Error performing clicks: {e}")
        
    except ImportError:
        print("  ⚠️  OpenCV not available for visualization")
    except Exception as e:
        print(f"  ⚠️  Error creating visualization: {e}")


def test_with_visualization():
    """Test detection and create a visualization of results."""
    print("\n" + "="*60)
    print("Test 5: Detection with Visualization")
    print("="*60)
    
    root = tk.Tk()
    root.withdraw()
    
    map_anoint = MapAnoint(
        click_map_anoint_button=None,
        map_anoint_hotkey_entry=None,
        map_anoint_set_button=None,
        map_anoint_status_label=None,
        is_path_of_exile_active_callback=lambda: True,
        save_callback=None
    )
    
    # Capture current screen instead of using static image file
    print("Capturing current screen...")
    image_path = capture_current_screen()
    
    if image_path is None or not os.path.exists(image_path):
        print(f"❌ Failed to capture screen")
        root.destroy()
        return False
    
    detected_maps = map_anoint.detect_blight_maps(image_path=image_path)
    
    if detected_maps:
        print(f"  Creating visualization for {len(detected_maps)} detected maps...")
        visualize_detections(image_path, detected_maps)
    else:
        print("  No maps detected, skipping visualization")
    
    root.destroy()
    return True


def run_all_tests():
    """Run all test functions."""
    print("\n" + "="*60)
    print("BLIGHT MAP DETECTION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Basic Detection", test_basic_detection),
        ("Different Confidence Thresholds", test_different_confidence_thresholds),
        ("Error Handling", test_error_handling),
        ("Color Detection Only", test_color_detection_only),
        ("Visualization", test_with_visualization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    print("\nStarting blight map detection tests...")
    print("Make sure you have installed the required dependencies:")
    print("  pip install opencv-python numpy Pillow")
    print()
    
    success = run_all_tests()
    
    sys.exit(0 if success else 1)

