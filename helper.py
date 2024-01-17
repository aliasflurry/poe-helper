import subprocess
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from random import randint, uniform
import pyautogui
import keyboard
import appdirs

# import pygame
# pyinstaller --onefile --noconsole helper.py

global running_flask
global scroll_running
running_mana = True


def loop_flask():
    click_flask_button.focus()
    global running_flask

    button_key_label = button_key.get(1.0, "end-1c")
    button_key_label = str(button_key_label) if len(button_key_label) > 0 else "1"
    while running_flask:
        keyboard.press_and_release(button_key_label)
        time.sleep(uniform(4, 5))
        # keyboard.release("1")1
        # time.sleep(3.5)


def run_loop_flask():
    global running_flask
    if click_flask_button['text'] != 'Stop flask':
        running_flask = True
        print("Start flask")
        click_flask_button['text'] = 'Stop flask'
        thread = threading.Thread(target=loop_flask)
        thread.start()
    else:
        print("Stop flask")
        click_flask_button['text'] = 'Start flask'
        running_flask = False


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
root.geometry("200x100")

tab_control = ttk.Notebook(root)

main_tab = ttk.Frame(tab_control)
main_tab.grid_rowconfigure(0, weight=1)
main_tab.grid_columnconfigure(0, weight=1)
tab_control.add(main_tab, text='Main')

button_key = tk.Text(main_tab, height=1, width=5, bg="white")

click_flask_button = tk.Button(main_tab, text="Start flask", command=run_loop_flask, width=20, height=5)

inner_frame = ttk.Frame(main_tab)

record_button = tk.Button(inner_frame, text="Record", command=record_mouse, width=20, height=5, )
record_button.grid(row=1, column=0, padx=10, pady=10)

play_button = tk.Button(inner_frame, text="Play", command=play_recorded_mouse, width=20, height=5, )
play_button.grid(row=1, column=1, padx=10, pady=10)

apps_tab = ttk.Frame(tab_control)
tab_control.add(apps_tab, text='Apps')

open_app_button = tk.Button(apps_tab, text="Open App", command=open_app)

tab_control.pack(expand=1, fill='both')
root.attributes('-topmost', True)
root.mainloop()
