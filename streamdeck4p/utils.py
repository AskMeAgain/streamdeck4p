import os
from typing import Dict

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

image_cache: Dict[str, memoryview] = {}


def update_list(original, update):
    assert len(original) == len(update), "Can only handle equal length lists."

    for idx, (val_original, val_update) in enumerate(zip(original, update)):
        if not isinstance(val_original, type(val_update)):
            raise ValueError(f"Different types! {type(val_original)}, {type(val_update)}")
        if isinstance(val_original, dict):
            original[idx] = update_dict(original[idx], update[idx])
        if isinstance(val_original, (tuple, list)):
            original[idx] = update_list(original[idx], update[idx])
        if isinstance(val_original, (str, int, float)):
            original[idx] = val_update
    return original


def update_dict(original, update):
    for key, value in update.items():

        if key not in original:
            original[key] = update[key]
            continue

        if key in original:
            if isinstance(value, dict):
                update_dict(original[key], update[key])
            if isinstance(value, list):
                update_list(original[key], update[key])
            if isinstance(value, (str, int, float)):
                original[key] = update[key]
    return original


def generate_image(deck, icon_filename: str, text: str, image_mode: str, btn_state: Dict[str, str]) -> Image:
    global image_cache
    hash = f"{icon_filename}||{text}||{image_mode}"
    if hash in image_cache:
        return image_cache[hash]

    if icon_filename:
        if icon_filename.startswith("bg->"):
            if icon_filename.startswith("bg->#"):
                color = tuple(map(int, icon_filename[5:].split(",")))
            else:
                color = icon_filename[4:]
            icon = Image.new('RGB', (100, 100), color)
        else:
            icon = Image.open(icon_filename)
    else:
        icon = PILHelper.create_image(deck)
    n_margin = 5
    if image_mode == "full":
        n_margin = 0
    bottom_margin = n_margin
    if text and image_mode != "full":
        bottom_margin += 15
    image = PILHelper.create_scaled_image(deck, icon, margins=[n_margin, n_margin, bottom_margin, n_margin])
    text_height = image.height - 5
    if image_mode == "full":
        text_height = image.height / 2

    draw = ImageDraw.Draw(image)

    text_font_size = 15
    fa_font_size = 30

    if "text_size" in btn_state:
        text_font_size = btn_state["text_size"]
        fa_font_size = btn_state["text_size"]

    if text.startswith("fa->"):
        font = ImageFont.truetype("./fonts/fa-regular-400.ttf", fa_font_size)
        text = text[4:]
        text_height += fa_font_size / 4
    else:
        font = ImageFont.truetype("./fonts/Roboto-Regular.ttf", text_font_size)
        text_height += text_font_size / 3

    textcolor = "white"
    if "text_color" in btn_state:
        textcolor = btn_state["text_color"]

    draw.text((image.width / 2, text_height), text=text, font=font, anchor="ms", fill=textcolor)

    result_image = PILHelper.to_native_format(deck, image)

    image_cache[hash] = result_image

    return result_image


def message(title: str, message: str):
    os.system('notify-send "' + title + '" "' + message + '"')
