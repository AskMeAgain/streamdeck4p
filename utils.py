import os

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper


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


def generate_image(deck, icon_filename, text: str, image_mode: str) -> Image:
    icon = Image.open(icon_filename)
    normal_margin = 5
    if image_mode == "full":
        normal_margin = 0
    bottom_margin = normal_margin
    if text and image_mode != "full":
        bottom_margin += 15
    image = PILHelper.create_scaled_image(deck, icon, margins=[normal_margin,normal_margin, bottom_margin, normal_margin])
    text_height = image.height - 5
    if image_mode == "full":
        text_height = image.height / 2 + 5

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("./fonts/Roboto-Regular.ttf", 14)
    draw.text((image.width / 2, text_height), text=text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)


def message(title, message):
  os.system('notify-send "'+title+'" "'+message+'"')
