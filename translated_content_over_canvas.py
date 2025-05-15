import json
from PIL import Image, ImageDraw, ImageFont

def measure_text(draw, text, font):
    try:
        x0,y0,x1,y1 = draw.textbbox((0,0), text, font=font)
        return x1-x0, y1-y0
    except AttributeError:
        return font.getsize(text)

def wrap_text_to_box(draw, text, max_width, font):
    """
    Break `text` at word boundaries so each line <= max_width.
    """
    import textwrap
    # very rough first cut at chars/line
    wM,_ = measure_text(draw, "M", font)
    est = max(1, max_width // wM)
    rough = textwrap.wrap(text, width=est)
    lines = []
    for line in rough:
        w,_ = measure_text(draw, line, font)
        if w <= max_width:
            lines.append(line)
        else:
            # word-by-word fallback
            words, cur = line.split(), ""
            for w0 in words:
                cand = (cur + " " + w0).strip()
                wc,_ = measure_text(draw, cand, font)
                if wc <= max_width:
                    cur = cand
                else:
                    lines.append(cur)
                    cur = w0
            if cur:
                lines.append(cur)
    return lines

# load your translated JSON
with open("translated_results.json", encoding="utf-8") as f:
    data = json.load(f)

# prepare canvases per page
canvases = {}
for p in data["pages"]:
    pn, w, h = p["pageNumber"], int(p["width"]), int(p["height"])
    img = Image.new("RGB", (w, h), "white")
    canvases[pn] = (img, ImageDraw.Draw(img))

# pick a font (monospace often helps alignment)
try:
    font = ImageFont.truetype("Consola.ttf", 12)
except IOError:
    font = ImageFont.load_default()

padding = 6  # px of margin inside each box

# draw paragraphs
for para in data.get("paragraphs", []):
    text = para.get("translatedContent", "").strip()
    if not text: continue

    for region in para["boundingRegions"]:
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        xs, ys = zip(*pts)
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)

        img, draw = canvases[pn]
        # outline
        draw.polygon(pts, outline="blue", width=2)

        # compute inner box
        inner_w  = (x1 - x0) - 2*padding
        inner_h  = (y1 - y0) - 2*padding
        if inner_w <= 0 or inner_h <= 0:
            continue  # too small to draw text

        # wrap text to that width
        lines = wrap_text_to_box(draw, text, inner_w, font)
        line_h = measure_text(draw, "Ay", font)[1]
        block_h = line_h * len(lines)

        # vertically center the block
        start_y = y0 + padding + max(0, (inner_h - block_h)//2)
        start_x = x0 + padding

        # draw each line, left-aligned
        for i, line in enumerate(lines):
            y = start_y + i*line_h
            if y + line_h > y0 + padding + inner_h:
                break
            draw.text((start_x, y), line, font=font, fill="black")

# (Repeat the same approach for table cells, using a red outline, etc.)

# save
for pn, (img, _) in canvases.items():
    img.save(f"page_{pn}_translated_english_on_canvas.png")
    print("Wrote page", pn)
