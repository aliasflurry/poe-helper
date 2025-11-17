import subprocess
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from random import randint, uniform

import psutil
import pyautogui
import keyboard
import win32process

try:
    import win32gui
except ImportError:
    print("Warning: pywin32 not installed. Window detection will not work.")
    win32gui = None

global running_flask
global running_weapon_swap
global scroll_running
running_mana = True
FLASK_MIN = 8
FLASK_MAX = 9
poe1_enabled = True  # Path of Exile 1 checkbox enabled by default
poe2_enabled = True  # Path of Exile 2 checkbox enabled by default


def get_root_window(hwnd):
    """Fallback replacement for win32gui.GetAncestor"""
    parent = win32gui.GetParent(hwnd)
    while parent != 0:
        hwnd = parent
        parent = win32gui.GetParent(hwnd)
    return hwnd


def is_path_of_exile_active():
    global poe1_enabled, poe2_enabled

    try:
        hwnd = win32gui.GetForegroundWindow()
        hwnd_root = get_root_window(hwnd)

        pid = win32process.GetWindowThreadProcessId(hwnd_root)[1]
        process_name = psutil.Process(pid).name().lower()

        # Path of Exile 1 checks
        if poe1_enabled and (
            process_name.startswith("pathofexile") and
            not process_name.startswith("pathofexile2")
        ):
            return True

        # Path of Exile 2 checks
        if poe2_enabled and process_name.startswith("pathofexile2"):
            return True

        return False

    except Exception as e:
        print("Detection error:", e)
        return False


def loop_flask():
    click_flask_button.focus()
    global running_flask
    button_key_label = button_key.get(1.0, "end-1c")
    button_key_list = button_key_label.split(" ")
    button_delay_label = button_delay.get(1.0, "end-1c")
    button_delay_list = button_delay_label.split(" ")
    min_delay = button_delay_list[0] if len(button_delay_list) >= 1 else FLASK_MIN
    max_delay = button_delay_list[1] if len(button_delay_list) >= 2 else FLASK_MAX
    while running_flask:
        if keyboard.is_pressed('f11'):
            print("F11 pressed")
            stop_flask()
            break
        if not is_path_of_exile_active():
            print("Path of Exile window not active, skipping...")
            time.sleep(0.5)
            continue
        for button_key_entry in button_key_list:
            button_key_press = str(button_key_entry) if len(button_key_entry) > 0 else "1"

            keyboard.press_and_release(button_key_press)
        print("Sleep " + str(min_delay) + " " + str(max_delay))
        time.sleep(uniform(float(min_delay), float(max_delay)))
        # keyboard.release("1")1
        # time.sleep(3.5)


def run_loop_flask():
    global running_flask
    if click_flask_button['text'] != 'Stop flask':
        start_flask()
    else:
        stop_flask()


def start_flask():
    global running_flask
    running_flask = True
    print("Start flask")
    click_flask_button['text'] = 'Stop flask'
    button_key.config(state='disabled')
    button_delay.config(state='disabled')
    thread = threading.Thread(target=loop_flask)
    thread.start()


def stop_flask():
    global running_flask
    print("Stop flask")
    click_flask_button['text'] = 'Start flask'
    running_flask = False
    button_key.config(state='normal')
    button_delay.config(state='normal')


def execute_weapon_swap_sequence():
    global running_weapon_swap
    try:
        if not running_weapon_swap:
            print("Weapon swap not running, skipping...")
            return
        if not is_path_of_exile_active():
            print("Path of Exile window not active, skipping weapon swap...")
            return
        weapon_key_label = weapon_key.get(1.0, "end-1c")
        weapon_key_list = weapon_key_label.split(" ")
        weapon_key_list.insert(0, "X")
        weapon_key_list.insert(1, "X")
        for weapon_key_entry in weapon_key_list:
            weapon_key_press = str(weapon_key_entry) if len(weapon_key_entry) > 0 else "1"
            keyboard.press_and_release(weapon_key_press)
            time.sleep(0.2)  # 0.2 second delay between key presses
    except Exception as e:
        print(f"Error in execute_weap1on_swap_sequence: {e}")
        # Hotkey will continue to work after exception


def run_loop_weapon_swap():
    global running_weapon_swap
    if click_weapon_swap_button['text'] != 'Stop weapon swap':
        start_weapon_swap()
    else:
        stop_weapon_swap()


def start_weapon_swap():
    global running_weapon_swap
    running_weapon_swap = True
    print("Start weapon swap - Press 'A' to execute")
    click_weapon_swap_button['text'] = 'Stop weapon swap'
    weapon_key.config(state='disabled')
    keyboard.add_hotkey('a', execute_weapon_swap_sequence)


def stop_weapon_swap():
    global running_weapon_swap
    print("Stop weapon swap")
    click_weapon_swap_button['text'] = 'Start weapon swap'
    running_weapon_swap = False
    weapon_key.config(state='normal')
    keyboard.remove_hotkey('a')


def record_mouse():
    # Code to run when the "Stop" button is pressed
    global running_mana
    # if record_button['text'] != 'Stop':
    #     running_mana = True
    #     print("Start mana")
    #     record_button['text'] = 'Stop'
    #     thread = threading.Thread(target=run_loop_manabond)
    #     thread.start()
    # else:
    #     print("Stop mana")
    #     record_button['text'] = 'Start mana'
    #     running_mana = False


def open_app():
    subprocess.Popen(["start",
                      '"D:\\Awakened POE Trade\\Awakened PoE Trade.exe"'],
                     shell=True)  # replace "TextEdit" with the name of the app you want to open


def record_mouse_activity(filename):
    """
    Record mouse clicks and positions and save them to a file.

    :param filename: The name of the file to save the recorded activities.
    """
    mouse_activities = []

    try:
        while True:
            x, y = pyautogui.position()
            event = pyautogui.mouseInfo()
            mouse_activities.append((x, y, event))

            time.sleep(0.1)  # Adjust the delay according to your needs

    except KeyboardInterrupt:
        with open(filename, 'w') as file:
            for activity in mouse_activities:
                file.write(f"{activity[0]},{activity[1]},{activity[2]}\n")


def replay_mouse_activity(filename):
    """
    Replay the recorded mouse activities.

    :param filename: The name of the file containing the recorded activities.
    """
    with open(filename, 'r') as file:
        mouse_activities = [tuple(map(int, line.strip().split(','))) for line in file]

    for activity in mouse_activities:
        x, y, event = activity
        pyautogui.moveTo(x, y)
        pyautogui.click() if 'down' in event else pyautogui.click(
            button='right') if 'right' in event else pyautogui.click(button='middle')

        # Adjust the delay according to your needs
        time.sleep(0.1)


def play_recorded_mouse():
    return


root = tk.Tk("PGame Helper")
root.geometry("500x300")

tab_control = ttk.Notebook(root)

main_tab = ttk.Frame(tab_control)
tab_control.add(main_tab, text='Main')


def set_poe1_enabled(value):
    global poe1_enabled
    poe1_enabled = value


def set_poe2_enabled(value):
    global poe2_enabled
    poe2_enabled = value


poe1_checkbox_var = tk.BooleanVar(value=True)
poe1_checkbox = tk.Checkbutton(main_tab, text="Only work in Path of Exile", variable=poe1_checkbox_var,
                               command=lambda: set_poe1_enabled(poe1_checkbox_var.get()))
poe1_checkbox.pack(pady=2)

poe2_checkbox_var = tk.BooleanVar(value=True)
poe2_checkbox = tk.Checkbutton(main_tab, text="Only work in Path of Exile 2", variable=poe2_checkbox_var,
                               command=lambda: set_poe2_enabled(poe2_checkbox_var.get()))
poe2_checkbox.pack(pady=2)

button_key_frame = tk.Frame(main_tab)
button_key_frame.pack()
button_key_label = tk.Label(button_key_frame, text="Button")
button_key_label.pack(side='left', padx=5)
button_key = tk.Text(button_key_frame, height=1, width=5, bg="white")
button_key.pack(side='left')

button_delay_frame = tk.Frame(main_tab)
button_delay_frame.pack()
button_delay_label = tk.Label(button_delay_frame, text="Delay")
button_delay_label.pack(side='left', padx=5)
button_delay = tk.Text(button_delay_frame, height=1, width=5, bg="white")
button_delay.pack(side='left')

click_flask_button = tk.Button(main_tab, text="Start flask", command=run_loop_flask, width=20, height=5, padx=10,
                               pady=10)
click_flask_button.pack()

weapon_key_frame = tk.Frame(main_tab)
weapon_key_frame.pack(pady=(20, 0))
weapon_key_label = tk.Label(weapon_key_frame, text="Button")
weapon_key_label.pack(side='left', padx=5)
weapon_key = tk.Text(weapon_key_frame, height=1, width=5, bg="white")
weapon_key.pack(side='left')

click_weapon_swap_button = tk.Button(main_tab, text="Start weapon swap", command=run_loop_weapon_swap, width=20,
                                     height=5, padx=10, pady=10)
click_weapon_swap_button.pack()

tab_control.pack(expand=1, fill='both')
root.attributes('-topmost', True)
root.mainloop()