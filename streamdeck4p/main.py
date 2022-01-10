import glob
import os
import sys
import threading
import re
import json
import subprocess
from signal import signal, SIGUSR1, SIGTERM, SIGINT
from time import sleep

import pynput
from pynput.keyboard import Controller

from pathlib import Path
from typing import Dict

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck
from yad import YAD

from streamdeck4p import utils

state: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
decks: StreamDeck = []
key_board: Controller
yad: YAD = YAD()


def replace_with_state(deck_id: str, page: str, line: str) -> str:
    groups = re.search("\\$_(.*)_(.*)_\\$", line)
    if not groups:
        return line
    state_arr = groups.group(1)
    new_key = groups.group(2)
    resolved_btn = state[deck_id][page][new_key]

    first_replacement = replace_now(line, new_key, resolved_btn, state_arr, "$")

    groups = re.search("!_(.*)_(.*)_!", line)
    if not groups:
        return first_replacement
    state_arr = groups.group(1)
    new_key = groups.group(2)
    resolved_btn = state[deck_id][page][new_key]

    return replace_now(first_replacement, new_key, resolved_btn, state_arr, "!")


def replace_now(line, new_key, resolved_btn, state_arr, sym: str):
    if state_arr == "input":
        resolved_state = resolved_btn[state_arr]
    else:
        resolved_state = resolved_btn[state_arr][resolved_btn["toggle_index"]]
    return line.replace(f"{sym}_{state_arr}_{new_key}_{sym}", resolved_state)


def execute_command(deck_id: str, page: str, btn_state: Dict[str, str]) -> bool:
    print("Executing command.")
    command = btn_state["command"]
    fixed_command = replace_with_state(deck_id, page, command)

    if "notification" in btn_state and btn_state["notification"]:
        utils.message("StreamDeck4p", "Starting process")

    process = subprocess.run(fixed_command.split(" "))

    if "notification" in btn_state and btn_state["notification"]:
        if process.returncode == 0:
            utils.message("StreamDeck4p", "Ending process")
        else:
            utils.message("StreamDeck4p", "Ending process", )

    return True


def toggle(btn: Dict[str, str]):
    if "toggle_index" in btn:
        btn["toggle_index"] += 1
        btn["toggle_index"] %= len(btn["state"])


def save_file():
    print("Saving file.")
    with open('streamdeck4p.json', 'w') as f:
        f.write(json.dumps(state, indent=2))


def press_keys(deck_id: str, page: str, btn_id: str):
    text_speed = 0.01
    btn = state[deck_id][page][btn_id]
    if "input_speed" in btn:
        text_speed = btn["input_speed"]

    print(f"Pressing keys with speed {text_speed}.")
    replaced_keys = replace_with_state(deck_id, page, btn["keys"])
    for frame_key in replaced_keys.split(","):
        if frame_key.startswith("sep->"):
            frame_key = ",".join(frame_key[5:])
        for fixed_frame_key in frame_key.split(","):
            if "delay" == fixed_frame_key:
                sleep(0.25)
                continue
            for key in pynput.keyboard.HotKey.parse(fixed_frame_key):
                key_board.press(key)
            sleep(text_speed)
            for key in pynput.keyboard.HotKey.parse(fixed_frame_key):
                key_board.release(key)


def button_activated(deck_id: str, page: str, key: str):
    try:
        command_worked = True
        deck = state[deck_id]
        btn = deck[page][key]
        toggle_mode = "simple" if "toggle_mode" not in btn else btn["toggle_mode"]
        yad_command = [] if "yad_additions" not in btn else btn["yad_additions"].copy()
        if toggle_mode == "button_selection":
            for index in range(len(btn["state"])):
                yad_command.append(f"--button={btn['state'][index]}:{index}")
            btn["toggle_index"] = execute_yad(yad_command, 0)
        if "ask_for_input" in btn:

            ask_for_input = btn['ask_for_input']

            if ask_for_input.startswith("sh->"):
                ask_command = ask_for_input[4:].split(" ")
                with subprocess.Popen(ask_command, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
                    readlines = p.communicate()[0]
                    btn["input"] = readlines.strip("\n")
                    if toggle_mode == "script":
                        btn["toggle_index"] = int(p.returncode)
            else:
                yad_command.append("--entry")
                yad_command.append(f"--text={ask_for_input}")
                btn["input"] = execute_yad(yad_command, 1)
        if "command" in btn:
            command_worked = execute_command(deck_id, page, btn)
        if "keys" in btn:
            press_keys(deck_id, page, key)

        if command_worked:
            if toggle_mode == "simple":
                toggle(btn)

        if "next_page" in btn:
            if btn["next_page"] in deck[page]:
                deck["current_page"] = btn["next_page"]
        save_file()
        render_gui('', '')
    except Exception as e:
        print(f"Button pressed and got error while executing process: {e}")


def execute_yad(yad_command, offset: int) -> str:
    result = yad.execute(yad_command)
    return result[len(result) - 1 - offset]


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
            key = str(key)
            deck_id = deck.get_serial_number()
            deck_state = state[deck_id]
            page_name = str(deck_state["current_page"])

            if page_name in deck_state and key in deck_state[page_name]:
                page = deck_state[page_name]
                btn = page[key]
                replaced_img = None if "image_url" not in btn else replace_with_state(deck_id, page_name, btn["image_url"])
                mode = "" if "image_mode" not in btn else btn["image_mode"]
                text = "" if "text" not in btn else replace_with_state(deck_id, page_name, btn["text"])
                image = utils.generate_image(deck, replaced_img, text, mode, btn)
                with deck:
                    deck.set_key_image(int(key), image)
            else:
                with deck:
                    deck.set_key_image(int(key), 0x00)


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

        if str(next_page) in state[deck_id]:
            if str(next_page) != state[deck_id]["current_page"]:
                print(f"Switching to page {next_page}")
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


def main_loop():
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


def start():
    if not cli_switches():
        try:
            main_loop()
        except KeyboardInterrupt:
            print("Got keyboard interrupted. Closing now gracefully.")
            for deck in decks:
                with deck:
                    deck.reset()
                    deck.close()
            sys.exit()


if __name__ == '__main__':
    start()
