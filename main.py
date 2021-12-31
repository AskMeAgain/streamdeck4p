import glob
import os
import sys
import threading
import re
import json
import subprocess
from signal import signal, SIGUSR1, SIGTERM
from time import sleep

import pynput
from pynput.keyboard import Key, Controller, KeyCode

from pathlib import Path
from typing import Dict

import psutil
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck
from StreamDeck.ImageHelpers import PILHelper

import utils

state: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
decks: StreamDeck = []
key_board: Controller


def replace_with_state(deck_id: str, page: str, line: str, comma_separated: bool) -> str:
    groups = re.search("\\$_state_(.*)_\\$", line)
    if not groups:
        return line
    new_key = groups.group(1)
    resolved_btn = state[deck_id][page][new_key]
    resolved_state = resolved_btn["internal_state"][resolved_btn["toggle_index"]]

    if comma_separated:
        resolved_state = ",".join(resolved_state)

    return line.replace(f"$_state_{new_key}_$", resolved_state)


def execute_command(deck_id: str, page: str, command: str) -> bool:
    fixed_command = replace_with_state(deck_id, page, command, False)
    print(f"Executing command: {fixed_command}")
    subprocess.run(fixed_command.split(" "))
    return True


def toggle(deck_id: str, page: str, key: str):
    if "toggle_index" in state[deck_id][page][key]:
        state[deck_id][page][key]["toggle_index"] += 1
        state[deck_id][page][key]["toggle_index"] %= len(state[deck_id][page][key]["internal_state"])


def save_file():
    with open(os.path.join(Path.home(), 'streamdeck/streamdeck4p.json'), 'w') as f:
        f.write(json.dumps(state, indent=2))


def press_keys(deck_id: str, page: str, keys: str):
    replaced_keys = replace_with_state(deck_id, page, keys, True)
    for frame_key in replaced_keys.split(","):
        for key in pynput.keyboard.HotKey.parse(frame_key):
            keyboard.press(key)
        sleep(0.01)
        for key in pynput.keyboard.HotKey.parse(frame_key):
            keyboard.release(key)


def button_activated(deck_id: str, page: str, key: str):
    command_worked = True
    if "command" in state[deck_id][page][key]:
        command_worked = execute_command(deck_id, page, state[deck_id][page][key]["command"])
    if command_worked:
        toggle(deck_id, page, key)
    if "keys" in state[deck_id][page][key]:
        press_keys(deck_id, page, state[deck_id][page][key]["keys"])
    if "next_page" in state[deck_id][page][key]:
        state[deck_id]["current_page"] = state[deck_id][page][key]["next_page"]
    save_file()
    render_gui('', '')


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
    txt = Path(os.path.join(Path.home(), 'streamdeck/streamdeck4p.json')).read_text()
    state = json.loads(txt)

    json_files = glob.glob(os.path.join(Path.home() , 'streamdeck/streamdeck4p-*.json'))
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

            if page in deck_state and str(key) in deck_state[page] and "image_url" in deck_state[page][str(key)]:
                img_url = deck_state[page][str(key)]["image_url"]
                replaced_img = replace_with_state(deck_id, page, img_url, False)
                text = ""
                if "text" in deck_state[page][str(key)]:
                    text = deck_state[page][str(key)]["text"]
                replaced_text = replace_with_state(deck_id, page, text, False)
                image = utils.generate_image(deck, replaced_img, replaced_text)
                with deck:
                    deck.set_key_image(key, image)
            else:
                with deck:
                    deck.set_key_image(key, 0x00)


def cli_switches() -> bool:
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
            print(f"Found StreamDeck: {deck.get_serial_number()}")
            deck.close()
        return True
    else:
        return False


if __name__ == '__main__':

    if not cli_switches():
        streamdecks = DeviceManager().enumerate()

        keyboard = Controller()
        decks = list()
        load_state(True)

        for index, deck in enumerate(streamdecks):
            deck.open()
            deck.reset()

            decks.append(deck)

            render_gui("", "")

            deck.set_key_callback(key_change_callback)
            signal(SIGUSR1, render_gui)

            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue

                if t.is_alive():
                    t.join()
