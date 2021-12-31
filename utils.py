from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper


def update_list(original, update):
    # Make sure the order is equal, otherwise it is hard to compare the items.
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

        # Add new key values
        if key not in original:
            original[key] = update[key]
            continue

        # Update the old key values with the new key values
        if key in original:
            if isinstance(value, dict):
                update_dict(original[key], update[key])
            if isinstance(value, list):
                update_list(original[key], update[key])
            if isinstance(value, (str, int, float)):
                original[key] = update[key]
    return original


def generate_image(deck, icon_filename, text: str) -> Image:
    icon = Image.open(icon_filename)
    bottom_margin = 5
    if text:
        bottom_margin = 20
    image = PILHelper.create_scaled_image(deck, icon, margins=[5, 5, bottom_margin, 5])
    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("./fonts/roboto/Roboto-Regular.ttf", 14)
    draw.text((image.width / 2, image.height - 5), text=text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)
