import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

def measure_text(draw, text, font):
    """
    Returns (width, height) of `text` when drawn with `font`.
    Tries draw.textbbox first, falls back to font.getsize.
    """
    try:
        # Pillow ≥ 8.0
        x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=font)
        return x1 - x0, y1 - y0
    except AttributeError:
        # Older Pillow
        return font.getsize(text)

def wrap_text_to_box(draw, text, box, font):
    """
    Given an ImageDraw, a string, a box=(x0,y0,x1,y1), and a font,
    returns a list of lines that will fit into the box width.
    """
    x0,y0,x1,y1 = box
    max_width = x1 - x0
    # start by roughly estimating how many chars will fit per line
    # (this is only an initial guess; we re-measure below)
    avg_char_w, _ = measure_text(draw, "M", font)
    est_chars_per_line = max_width // avg_char_w
    # Use textwrap to get initial chunks
    rough_lines = textwrap.wrap(text, width=int(est_chars_per_line))
  
    final_lines = []
    for line in rough_lines:
        # if this line is too wide, split it up
        w, h = measure_text(draw, line, font)
        if w <= max_width:
            final_lines.append(line)
        else:
            # brute-force break into smaller pieces
            words = line.split()
            cur = ""
            for word in words:
                test = (cur + " " + word).strip()
                w_test, _ = measure_text(draw, test, font)
                if w_test <= max_width:
                    cur = test
                else:
                    final_lines.append(cur)
                    cur = word
            if cur:
                final_lines.append(cur)
    return final_lines

# ———————————————————————————————————————————————
# Load JSON & prepare canvases just like before
with open("analysis_result.json", encoding="utf-8") as f:
    data = json.load(f)

# build per-page blank images & draw contexts
canvases = {}
for p in data["pages"]:
    pn = p["pageNumber"]
    img = Image.new("RGB", (int(p["width"]), int(p["height"])), "white")
    canvases[pn] = (img, ImageDraw.Draw(img))

# pick a font
try:
    font = ImageFont.truetype("/Users/rchembula/Desktop/PaddleOCR/TestFiles/NotoSansArabic-VariableFont_wdth,wght.ttf", size=11)
except IOError:
    font = ImageFont.load_default()

# Draw paragraphs + wrapped text
for para in data.get("paragraphs", []):
    text = para.get("content", "").strip()
    if not text:
        continue
    for region in para["boundingRegions"]:
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        xs, ys = zip(*pts)
        box = (min(xs), min(ys), max(xs), max(ys))
        img, draw = canvases[pn]

        # outline box
        draw.polygon(pts, outline="blue", width=2)

        # wrap & draw text inside it
        lines = wrap_text_to_box(draw, text, box, font)
        _, line_h = measure_text(draw, "Ay", font)

        # draw each line until we exceed the bottom of the box
        x0, y0, _, y1 = box
        for i, line in enumerate(lines):
            y = y0 + i * line_h
            if y + line_h > y1:  # ran out of vertical space
                break
            draw.text((x0, y), line, font=font, fill="black")

# (Repeat same pattern for table cells if you want their content wrapped, too.)

# Save pages
for pn, (img, _) in canvases.items():
    img.save(f"page_{pn}_wrapped.png")
    print(f"Wrote page_{pn}_wrapped.png")
