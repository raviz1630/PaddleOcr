import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# — Helpers from before —————————————————————————————————————————

def measure_text(draw, text, font):
    try:
        x0,y0,x1,y1 = draw.textbbox((0,0), text, font=font)
        return x1-x0, y1-y0
    except AttributeError:
        return font.getsize(text)

def wrap_text(draw, text, max_width, font):
    import textwrap
    wM,_ = measure_text(draw, "M", font)
    est = max(1, max_width // wM)
    lines = []
    for chunk in textwrap.wrap(text, width=est):
        w,_ = measure_text(draw, chunk, font)
        if w <= max_width:
            lines.append(chunk)
        else:
            words, cur = chunk.split(), ""
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

# — Load data & choose font ————————————————————————————————————————

with open("translated_results.json", encoding="utf-8") as f:
    data = json.load(f)

# pick a font that you like
try:
    font = ImageFont.truetype("/Users/rchembula/Desktop/PaddleOCR/TestFiles/simfang.ttf", size=12)
except IOError:
    font = ImageFont.load_default()

padding    = 4
blur_radius= 4
alpha_rect = (255,255,255,200)  # semi‐opaque white

# — Process each page ————————————————————————————————————————————

for page in data["pages"]:
    pn = page["pageNumber"]
    # 1) Load the original scan as RGBA
    orig = Image.open(f"/Users/rchembula/Desktop/PaddleOCR/TestFiles/test_image4.jpeg").convert("RGBA")

    # 2) Blur *underneath* each region
    for col in ("paragraphs","tables"):
        items = data.get(col, [])
        if col == "tables":
            # flatten both whole-table and each cell
            regions = []
            for t in items:
                regions += t.get("boundingRegions", [])
                for cell in t.get("cells", []):
                    regions += cell.get("boundingRegions", [])
        else:
            regions = [r for para in items for r in para["boundingRegions"]]

        for region in regions:
            flat = region["polygon"]
            xs, ys = flat[0::2], flat[1::2]
            box = (min(xs), min(ys), max(xs), max(ys))
            # crop, blur, paste back
            patch   = orig.crop(box)
            blurred = patch.filter(ImageFilter.GaussianBlur(blur_radius))
            orig.paste(blurred, box)

    # 3) Prepare two layers: one for rectangles, one for text
    overlay     = Image.new("RGBA", orig.size, (255,255,255,0))
    text_layer  = Image.new("RGBA", orig.size, (255,255,255,0))
    draw_rect   = ImageDraw.Draw(overlay)
    draw_text   = ImageDraw.Draw(text_layer)

    # 4) Draw paragraphs: white rect + wrapped text
    for para in data.get("paragraphs", []):
        txt = para.get("translatedContent","").strip()
        if not txt: continue
        for region in para["boundingRegions"]:
            flat = region["polygon"]
            xs, ys = flat[0::2], flat[1::2]
            x0,y0,x1,y1 = min(xs),min(ys),max(xs),max(ys)

            # rectangle
            draw_rect.rectangle([x0,y0,x1,y1], fill=alpha_rect)

            # wrap & draw text
            inner_w = (x1-x0) - 2*padding
            lines   = wrap_text(draw_text, txt, inner_w, font)
            lh      = measure_text(draw_text, "Ay", font)[1]
            start_y = y0 + padding

            for i,line in enumerate(lines):
                y = start_y + i*lh
                if y+lh > y1-padding:
                    break
                draw_text.text((x0+padding, y), line, font=font, fill="black")

    # 5) Draw tables: whole‐table optional + cells
    for tbl in data.get("tables", []):
        # whole table in green (optional)
        for region in tbl.get("boundingRegions", []):
            flat = region["polygon"]
            pts  = [(flat[i],flat[i+1]) for i in range(0,len(flat),2)]
            draw_rect.line(pts + [pts[0]], fill="green", width=2)

        # each cell in red + text
        for cell in tbl.get("cells", []):
            txt = cell.get("translatedContent","").strip()
            if not txt: continue
            for region in cell["boundingRegions"]:
                flat = region["polygon"]
                xs, ys = flat[0::2], flat[1::2]
                x0,y0,x1,y1 = min(xs),min(ys),max(xs),max(ys)

                draw_rect.rectangle([x0,y0,x1,y1], outline="red", width=1)

                inner_w = (x1-x0) - 2*padding
                lines   = wrap_text(draw_text, txt, inner_w, font)
                lh      = measure_text(draw_text, "Ay", font)[1]
                start_y = y0 + padding

                for i,line in enumerate(lines):
                    y = start_y + i*lh
                    if y+lh > y1-padding:
                        break
                    draw_text.text((x0+padding, y), line, font=font, fill="black")

    # 6) Brighten just the text layer
    enhancer    = ImageEnhance.Brightness(text_layer)
    bright_text = enhancer.enhance(1.8)  # 1.0 = no change; >1 = brighter

    # 7) Composite everything
    combined = Image.alpha_composite(orig, overlay)
    combined = Image.alpha_composite(combined, bright_text).convert("RGB")

    # 8) Save
    combined.save(f"page_{pn}_translated_english_on_canvas.png")
    print("Saved page", pn)
