import os
from PIL import Image, ImageDraw, ImageFont

def make_simple_thumbnail(text: str, out_path: str, size=(1280, 720)):
    img = Image.new("RGB", size, (20, 20, 20))
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()
    margin = 40
    wrapped = []
    words = text.split()
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if len(test) > 25:
            wrapped.append(line)
            line = w
        else:
            line = test
    if line:
        wrapped.append(line)

    y = size[1] // 2 - (len(wrapped) * 20) // 2
    for ln in wrapped:
        bbox = draw.textbbox((0, 0), ln, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        draw.text(((size[0] - w) // 2, y), ln, fill="white", font=font)
        y += h + 10

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path
