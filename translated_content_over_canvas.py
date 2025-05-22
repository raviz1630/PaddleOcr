# Let's begin by refactoring and improving the script based on the earlier suggestions.
# Key improvements:
# - Dynamic font scaling based on bounding box size.
# - Improved text wrapping.
# - Better handling of bounding regions.
# - Soft blur masking.

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import json
import textwrap

# Constants
PADDING = 4
BLUR_RADIUS = 4
ALPHA_RECT = (255, 255, 255, 200)
FONT_PATH = "/Users/rchembula/Desktop/PaddleOCR/TestFiles/simfang.ttf"
IMAGE_PATH_TEMPLATE = "/Users/rchembula/Desktop/PaddleOCR/TestFiles/page_3.jpeg"
OUTPUT_PATH_TEMPLATE = "page_{pn}_translated_english_on_canvas.png"

# Helpers
def measure_text(draw, text, font):
    try:
        x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=font)
        return x1 - x0, y1 - y0
    except AttributeError:
        return font.getsize(text)

def wrap_text(draw, text, max_width, font):
    wM, _ = measure_text(draw, "M", font)
    est = max(1, max_width // wM)
    lines = []
    for chunk in textwrap.wrap(text, width=est):
        w, _ = measure_text(draw, chunk, font)
        if w <= max_width:
            lines.append(chunk)
        else:
            words, cur = chunk.split(), ""
            for w0 in words:
                cand = (cur + " " + w0).strip()
                wc, _ = measure_text(draw, cand, font)
                if wc <= max_width:
                    cur = cand
                else:
                    lines.append(cur)
                    cur = w0
            if cur:
                lines.append(cur)
    return lines

def get_box_from_polygon(polygon):
    xs, ys = polygon[0::2], polygon[1::2]
    return min(xs), min(ys), max(xs), max(ys)

def load_font(size=20):
    try:
        return ImageFont.truetype(FONT_PATH, size=size)
    except IOError:
        return ImageFont.load_default()

def load_data(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def blur_regions(orig, regions):
    for region in regions:
        flat = region["polygon"]
        box = get_box_from_polygon(flat)
        patch = orig.crop(box)
        blurred = patch.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
        orig.paste(blurred, box)

def find_max_font_size(draw, text, box_width, box_height):
    for size in range(30, 5, -1):
        font = load_font(size=size)
        lines = wrap_text(draw, text, box_width - 2 * PADDING, font)
        lh = measure_text(draw, "Ay", font)[1]
        if lh * len(lines) <= box_height - 2 * PADDING:
            return font
    return load_font(size=6)

def draw_text_box(draw_rect, draw_text, text, polygon):
    x0, y0, x1, y1 = get_box_from_polygon(polygon)
    draw_rect.rectangle([x0, y0, x1, y1], fill=ALPHA_RECT)
    box_w, box_h = x1 - x0, y1 - y0
    font = find_max_font_size(draw_text, text, box_w, box_h)
    lines = wrap_text(draw_text, text, box_w - 2 * PADDING, font)
    lh = measure_text(draw_text, "Ay", font)[1]
    start_y = y0 + PADDING
    for i, line in enumerate(lines):
        y = start_y + i * lh
        if y + lh > y1 - PADDING:
            break
        draw_text.text((x0 + PADDING, y), line, font=font, fill="black")

def draw_paragraphs(draw_rect, draw_text, paragraphs):
    for para in paragraphs:
        txt = para.get("translatedContent", "").strip()
        if not txt:
            continue
        for region in para["boundingRegions"]:
            draw_text_box(draw_rect, draw_text, txt, region["polygon"])

def draw_tables(draw_rect, draw_text, tables):
    for tbl in tables:
        for region in tbl.get("boundingRegions", []):
            pts = [(region["polygon"][i], region["polygon"][i + 1]) for i in range(0, len(region["polygon"]), 2)]
            draw_rect.line(pts + [pts[0]], fill="green", width=2)
        for cell in tbl.get("cells", []):
            txt = cell.get("translatedContent", "").strip()
            if not txt:
                continue
            for region in cell["boundingRegions"]:
                draw_text_box(draw_rect, draw_text, txt, region["polygon"])

def process_page(page, data):
    pn = page["pageNumber"]
    orig = Image.open(IMAGE_PATH_TEMPLATE.replace("1", str(pn))).convert("RGBA")
    paragraphs = data.get("paragraphs", [])
    tables = data.get("tables", [])
    regions = [r for para in paragraphs for r in para["boundingRegions"]]
    for t in tables:
        regions += t.get("boundingRegions", [])
        for cell in t.get("cells", []):
            regions += cell.get("boundingRegions", [])
    blur_regions(orig, regions)

    overlay = Image.new("RGBA", orig.size, (255, 255, 255, 0))
    text_layer = Image.new("RGBA", orig.size, (255, 255, 255, 0))
    draw_rect = ImageDraw.Draw(overlay)
    draw_text = ImageDraw.Draw(text_layer)

    draw_paragraphs(draw_rect, draw_text, paragraphs)
    draw_tables(draw_rect, draw_text, tables)

    enhancer = ImageEnhance.Brightness(text_layer)
    bright_text = enhancer.enhance(2.8)

    combined = Image.alpha_composite(orig, overlay)
    combined = Image.alpha_composite(combined, bright_text).convert("RGB")
    combined.save(OUTPUT_PATH_TEMPLATE.format(pn=pn))

def main():
    data = load_data("translated_results.json")
    for page in data["pages"]:
        process_page(page, data)

if __name__ == "__main__":
    main()

