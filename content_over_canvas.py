import json
from PIL import Image, ImageDraw, ImageFont


with open("analysis_result.json", encoding="utf-8") as f:
    data = json.load(f)


canvases = {}
for p in data["pages"]:
    pn = p["pageNumber"]
    w, h = int(p["width"]), int(p["height"])
    img = Image.new("RGB", (w, h), "white")
    canvases[pn] = (img, ImageDraw.Draw(img))


try:
    font = ImageFont.truetype("/Users/rchembula/Desktop/PaddleOCR/TestFiles/NotoSansArabic-VariableFont_wdth,wght.ttf", size=11)
except IOError:
    font = ImageFont.load_default()


for para in data.get("paragraphs", []):
    text = para.get("content", "")
    for region in para["boundingRegions"]:
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        img, draw = canvases[pn]

      
        draw.polygon(pts, outline="blue", width=2)

        
        xs, ys = zip(*pts)
        draw.text((min(xs), min(ys)), text, fill="black", font=font)


for table in data.get("tables", []):
    
    for region in table.get("boundingRegions", []):
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        img, draw = canvases[pn]
        draw.polygon(pts, outline="green", width=3)

    
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


for pn, (img, _) in canvases.items():
    out = f"page_{pn}_with_text.png"
    img.save(out)
    print(f"Wrote {out}")
