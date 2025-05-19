import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

def measure_text(draw, text, font):
    """
    Returns (width, height) of `text` when drawn with `font`.
    Tries draw.textbbox first, falls back to font.getsize.
    """
    try:
        x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=font)
        return x1 - x0, y1 - y0
    except AttributeError:
        return font.getsize(text)

def wrap_text_to_box(draw, text, box, font):
    """
    Given an ImageDraw, a string, a box=(x0,y0,x1,y1), and a font,
    returns a list of lines that will fit into the box width.
    """
    x0, y0, x1, y1 = box
    max_width = x1 - x0
    
    avg_char_w, _ = measure_text(draw, "M", font)
    est_chars = max(1, max_width // avg_char_w)
    rough = textwrap.wrap(text, width=est_chars)

    lines = []
    for line in rough:
        w, _ = measure_text(draw, line, font)
        if w <= max_width:
            lines.append(line)
        else:
           
            words, cur = line.split(), ""
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

# ———————————————————————————————————————————————

with open("analysis_result.json", encoding="utf-8") as f:
    data = json.load(f)

canvases = {}
for p in data["pages"]:
    pn = p["pageNumber"]
    w, h = int(p["width"]), int(p["height"])
    img = Image.new("RGB", (w, h), "white")
    canvases[pn] = (img, ImageDraw.Draw(img))


try:
    font = ImageFont.truetype(
        "/Users/rchembula/Desktop/PaddleOCR/TestFiles/NotoSansArabic-VariableFont_wdth,wght.ttf",
        size=11
    )
except IOError:
    font = ImageFont.load_default()

# ———————————————————————————————————————————————

for para in data.get("paragraphs", []):
    text = para.get("content", "").strip()
    if not text:
        continue
    for region in para["boundingRegions"]:
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        xs, ys = zip(*pts)
        box = (min(xs), min(ys), max(xs), max(ys))
        img, draw = canvases[pn]

        draw.polygon(pts, outline="blue", width=2)

        lines = wrap_text_to_box(draw, text, box, font)
        _, line_h = measure_text(draw, "Ay", font)
        x0, y0, _, y1 = box

        for i, line in enumerate(lines):
            y = y0 + i * line_h
            if y + line_h > y1:
                break
            draw.text((x0, y), line, font=font, fill="black")

# ———————————————————————————————————————————————

for table in data.get("tables", []):
    
    for region in table.get("boundingRegions", []):
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        img, draw = canvases[pn]
        draw.polygon(pts, outline="green", width=2)

    
    for cell in table.get("cells", []):
        text = cell.get("content", "").strip()
        if not text:
            continue
        for region in cell.get("boundingRegions", []):
            pn = region["pageNumber"]
            flat = region["polygon"]
            pts = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
            xs, ys = zip(*pts)
            box = (min(xs), min(ys), max(xs), max(ys))
            img, draw = canvases[pn]

            draw.polygon(pts, outline="red", width=1)

            lines = wrap_text_to_box(draw, text, box, font)
            _, line_h = measure_text(draw, "Ay", font)
            x0, y0, _, y1 = box

            for i, line in enumerate(lines):
                y = y0 + i * line_h
                if y + line_h > y1:
                    break
                draw.text((x0, y), line, font=font, fill="black")

# ———————————————————————————————————————————————

for pn, (img, _) in canvases.items():
    out = f"page_{pn}_wrapped.png"
    img.save(out)
    print(f"Wrote page_{pn}_wrapped.png")
