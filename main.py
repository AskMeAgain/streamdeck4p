import threading
import re
import json
import os

from pathlib import Path
from typing import Dict

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper


state: Dict[str, Dict[str, Dict[str, str]]] = {}


def replace_with_state(deck_id: str, line: str) -> str:
    groups = re.search("\\$_state_(.*)_\\$", line)
    if not groups:
        return line
    new_key = groups.group(1)
    resolved_btn = state[deck_id][new_key]
    resolved_state = resolved_btn["internal_state"][resolved_btn["toggle_index"]]
    return line.replace(f"$_state_{new_key}_$", resolved_state)


def execute_command(deck_id: str, command: str) -> bool:
    fixed_command = replace_with_state(deck_id, command)
    print(f"Executing command: {fixed_command}")
    return True


def toggle(deck_id: str, key: str):
    if "toggle_index" in state[deck_id][key]:
        state[deck_id][key]["toggle_index"] += 1
        state[deck_id][key]["toggle_index"] %= len(state[deck_id][key]["internal_state"])


def button_activated(deck_id: str, key: str):
    command_worked = True
    if "command" in state[deck_id][key]:
        command_worked = execute_command(deck_id, state[deck_id][key]["command"])
    if command_worked:
        toggle(deck_id, key)
    render(deck)


def key_change_callback(deck, key, button_pressed):
    if button_pressed:
        deck_id = deck.get_serial_number()

        if str(key) in state[deck_id]:
            button_activated(deck_id, str(key))
        else:
            print("no feature!")


def load_state():
    global state
    txt = Path('.streamdeck4p.json').read_text()
    state = json.loads(txt)


def generate_image(deck, icon_filename) -> Image:
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[5, 5, 5, 5])
    return PILHelper.to_native_format(deck, image)


def render(deck):
    for key in range(deck.key_count()):
        deck_id = deck.get_serial_number()

        if str(key) in state[deck_id]:
            if "image_url" in state[deck_id][str(key)]:
                img_url = state[deck_id][str(key)]["image_url"]
                replaced_img = replace_with_state(deck_id, img_url)
                image = generate_image(deck, replaced_img)
                with deck:
                    deck.set_key_image(key, image)


if __name__ == '__main__':
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()

        load_state()
        render(deck)

        deck.set_key_callback(key_change_callback)

        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
