import glob
import os
import sys
import threading
import re
import json
import subprocess
from signal import signal, SIGUSR1, SIGUSR2, SIGKILL, SIGTERM, SIGINT
from time import sleep

import pynput
from pynput.keyboard import Controller

from pathlib import Path
from typing import Dict

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck

import utils

state: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
decks: StreamDeck = []
key_board: Controller


def replace_with_state(deck_id: str, page: str, line: str) -> str:
    groups = re.search("\\$_(.*)_(.*)_\\$", line)
    if not groups:
        return line
    state_arr = groups.group(1)
    new_key = groups.group(2)
    resolved_btn = state[deck_id][page][new_key]
    resolved_state = resolved_btn[state_arr][resolved_btn["toggle_index"]]

    return line.replace(f"$_{state_arr}_{new_key}_$", resolved_state)


def execute_command(deck_id: str, page: str, command: str) -> bool:
    print("Executing command.")
    fixed_command = replace_with_state(deck_id, page, command)
    utils.message("StreamDeck4p", "Starting process")
    subprocess.run(fixed_command.split(" "))
    utils.message("StreamDeck4p", "Ending process")
    return True


def toggle(deck_id: str, page: str, key: str):
    if "toggle_index" in state[deck_id][page][key]:
        state[deck_id][page][key]["toggle_index"] += 1
        state[deck_id][page][key]["toggle_index"] %= len(state[deck_id][page][key]["state"])


def save_file():
    print("Saving file.")
    with open('streamdeck4p.json', 'w') as f:
        f.write(json.dumps(state, indent=2))


def press_keys(deck_id: str, page: str, keys: str):
    print("Pressing keys.")
    replaced_keys = replace_with_state(deck_id, page, keys)
    for frame_key in replaced_keys.split(","):
        if frame_key.startswith("sep->"):
            frame_key = ",".join(frame_key[5:])
        for fixed_frame_key in frame_key.split(","):
            for key in pynput.keyboard.HotKey.parse(fixed_frame_key):
                key_board.press(key)
            sleep(0.01)
            for key in pynput.keyboard.HotKey.parse(fixed_frame_key):
                key_board.release(key)


def button_activated(deck_id: str, page: str, key: str):
    try:
        command_worked = True
        if "command" in state[deck_id][page][key]:
            command_worked = execute_command(deck_id, page, state[deck_id][page][key]["command"])
        if "keys" in state[deck_id][page][key]:
            press_keys(deck_id, page, state[deck_id][page][key]["keys"])
        if command_worked:
            toggle(deck_id, page, key)
        if "next_page" in state[deck_id][page][key]:
            state[deck_id]["current_page"] = state[deck_id][page][key]["next_page"]
        save_file()
        render_gui('', '')
    except Exception as e:
        print(f"Button pressed and got error while executing process: {e}")


def key_change_callback(deck, key, button_pressed):
    if button_pressed:
        deck_id = deck.get_serial_number()
        page = state[deck_id]["current_page"]
        if str(key) in state[deck_id][page]:
            button_activated(deck_id, page, str(key))
        else:
            print("no feature!")


def load_state(insert_pid: bool):
    global state
    txt = Path('streamdeck4p.json').read_text()
    state = json.loads(txt)

    json_files = glob.glob('streamdeck4p-*.json')
    for path in json_files:
        txt2 = Path(path).read_text()
        state = utils.update_dict(state, json.loads(txt2))

    if insert_pid:
        state["pid"] = os.getpid()
        save_file()


def render_gui(a, b):
    load_state(False)
    for deck in decks:
        for key in range(deck.key_count()):
            deck_id = deck.get_serial_number()
            deck_state = state[deck_id]
            page = deck_state["current_page"]

            if page in deck_state and str(key) in deck_state[page]:
                replaced_img = None
                if "image_url" in deck_state[page][str(key)]:
                    img_url = deck_state[page][str(key)]["image_url"]
                    replaced_img = replace_with_state(deck_id, page, img_url)
                text = ""
                mode = ""
                if "image_mode" in deck_state[page][str(key)]:
                    mode = deck_state[page][str(key)]["image_mode"]
                if "text" in deck_state[page][str(key)]:
                    text = replace_with_state(deck_id, page, deck_state[page][str(key)]["text"])
                image = utils.generate_image(deck, replaced_img, text, mode)
                with deck:
                    deck.set_key_image(key, image)
            else:
                with deck:
                    deck.set_key_image(key, 0x00)


def cli_switches() -> bool:
    if "--reload-config" in sys.argv:
        load_state(False)
        subprocess.run(["kill", "-USR1", str(state["pid"])])
        return True
    if "--exit" in sys.argv:
        load_state(False)
        subprocess.run(["kill", "-SIGTERM", str(state["pid"])])
        return True
    if "--switch-page" in sys.argv:
        load_state(False)
        deck_id = sys.argv[2]
        next_page = sys.argv[3]
        state[deck_id]["current_page"] = str(next_page)
        save_file()
        subprocess.run(["kill", "-USR1", str(state["pid"])])
        return True
    elif "--show-devices" in sys.argv:
        streamdecks = DeviceManager().enumerate()
        for index, deck in enumerate(streamdecks):
            deck.open()
            print(f"Found StreamDeck of type '{deck.deck_type()}' with SerialId '{deck.get_serial_number()}'")
            with deck:
                deck.close()
        return True
    else:
        return False


def exit_application_sigterm(a, b):
    print("Closing application due to sigterm signal.")
    global decks
    for d in decks:
        with d:
            d.reset()
            d.close()


def exit_application_sigint(a, b):
    print("Closing application due to sigint signal.")
    global decks
    for deck in decks:
        with deck:
            deck.reset()
            deck.close()


def method_name():
    global key_board, decks

    key_board = Controller()
    decks = list()
    load_state(True)
    for index, deck in enumerate(DeviceManager().enumerate()):
        deck.open()
        deck.reset()

        decks.append(deck)

        render_gui("", "")

        deck.set_key_callback(key_change_callback)

        signal(SIGUSR1, render_gui)
        signal(SIGTERM, exit_application_sigterm)
        signal(SIGINT, exit_application_sigint)

        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass


if __name__ == '__main__':

    if not cli_switches():
        try:
            method_name()
        except KeyboardInterrupt:
            print("Got keyboard interrupted. Closing now gracefully.")
            for deck in decks:
                with deck:
                    deck.reset()
                    deck.close()
            sys.exit()
