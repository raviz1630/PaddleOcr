import json
from PIL import Image, ImageDraw


with open("analysis_result.json", encoding="utf-8") as f:
    data = json.load(f)


canvases = {} 
for p in data["pages"]:
    pn = p["pageNumber"]
    w, h = int(p["width"]), int(p["height"])
    img = Image.new("RGB", (w, h), "white")
    canvases[pn] = (img, ImageDraw.Draw(img))


for para in data.get("paragraphs", []):
    for region in para["boundingRegions"]:
        pn = region["pageNumber"]
        flat = region["polygon"]                       
        pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        _, draw = canvases[pn]
        draw.polygon(pts, outline="blue", width=2)


for table in data.get("tables", []):
   
    for region in table.get("boundingRegions", []):
        pn = region["pageNumber"]
        flat = region["polygon"]
        pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
        _, draw = canvases[pn]
        draw.polygon(pts, outline="green", width=3)
   
    for cell in table.get("cells", []):
        for region in cell.get("boundingRegions", []):
            pn = region["pageNumber"]
            flat = region["polygon"]
            pts  = [(flat[i], flat[i+1]) for i in range(0, len(flat), 2)]
            _, draw = canvases[pn]
            draw.polygon(pts, outline="red", width=1)


for pn, (img, _) in canvases.items():
    out = f"page_{pn}_layout.png"
    img.save(out)
    print(f"Wrote {out}")