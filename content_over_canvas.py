import json
from PIL import Image, ImageDraw, ImageFont

# 1. Load your OCR output
with open("analysis_result.json", encoding="utf-8") as f:
    data = json.load(f)

# 2. Prepare one blank canvas per page
canvases = {}
for p in data["pages"]:
    pn = p["pageNumber"]
    w, h = int(p["width"]), int(p["height"])
    img = Image.new("RGB", (w, h), "white")
    canvases[pn] = (img, ImageDraw.Draw(img))

# 3. Choose a font
#    You can replace "arial.ttf" with any .ttf on your system, or
#    fall back to the default bitmap font if it’s not found.
try:
    font = ImageFont.truetype("/Users/rchembula/Desktop/PaddleOCR/TestFiles/NotoSansArabic-VariableFont_wdth,wght.ttf", size=11)
except IOError:
    font = ImageFont.load_default()

# 4. Draw paragraphs: box + content
for para in data.get("paragraphs", []):
    text = para.get("content", "")
    for region in para["boundingRegions"]:
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        img, draw = canvases[pn]

        # outline
        draw.polygon(pts, outline="blue", width=2)

        # position text at the top‐left of the box
        xs, ys = zip(*pts)
        draw.text((min(xs), min(ys)), text, fill="black", font=font)

# 5. Draw tables (whole + cells) with content
for table in data.get("tables", []):
    # whole‐table outline in green
    for region in table.get("boundingRegions", []):
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        img, draw = canvases[pn]
        draw.polygon(pts, outline="green", width=3)

    # individual cells in red, with their text
    for cell in table.get("cells", []):
        text = cell.get("content", "")
        for region in cell.get("boundingRegions", []):
            pn = region["pageNumber"]
            flat = region["polygon"]
            pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
            img, draw = canvases[pn]

            draw.polygon(pts, outline="red", width=1)
            xs, ys = zip(*pts)
            draw.text((min(xs), min(ys)), text, fill="black", font=font)

# 6. Save results
for pn, (img, _) in canvases.items():
    out = f"page_{pn}_with_text.png"
    img.save(out)
    print(f"Wrote {out}")
