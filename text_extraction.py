import json
from PIL import Image, ImageDraw
import os
from paddlex import create_model
import glob
from paddleocr import PaddleOCR


model = create_model(model_name="PP-OCRv4_mobile_det")
output = model.predict("/Users/rchembula/Desktop/PaddleOCR/TestFiles/test_image1.jpeg", batch_size=1)
for res in output:
    res.print()
    res.save_to_img(save_path="./output/")
    res.save_to_json(save_path="./output/res.json")

# Load detection results
with open("./output/res.json", "r") as f:
    data = json.load(f)

# Open image
img = Image.open("/Users/rchembula/Desktop/PaddleOCR/TestFiles/test_image1.jpeg")

# Prepare output folder
os.makedirs("./output/bboxes_pil", exist_ok=True)

for i, poly in enumerate(data["dt_polys"]):
    # compute bounding box of polygon
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)

    # crop the rectangle region
    crop_rect = img.crop((left, top, right, bottom))

    # create a mask
    mask = Image.new("L", crop_rect.size, 0)
    shifted_poly = [(x - left, y - top) for x, y in poly]
    ImageDraw.Draw(mask).polygon(shifted_poly, outline=255, fill=255)

    # apply mask to get an exact quadrilateral with transparency
    crop_poly = Image.new("RGBA", crop_rect.size)
    crop_poly.paste(crop_rect, (0, 0), mask=mask)

    # save
    crop_poly.save(f"./output/bboxes_pil/bbox_{i:03d}.png")

# 1) Load detection polygons
with open("./output/res.json", "r") as f:
    data = json.load(f)
polygons = data["dt_polys"]

# 2) Init the OCR recognizer
ocr = PaddleOCR(use_angle_cls=True, lang='ar')  # adjust `lang` as needed

final_results = []

# 3) For each polygon-crop, recognize text
for i, poly in enumerate(polygons):
    img_path = f"./output/bboxes_pil/bbox_{i:03d}.png"
    # det=False: skip detection, cls=True: use angle classifier
    rec = ocr.ocr(img_path, det=False, cls=True)

    # rec is a list of lists; each inner list is [(text, confidence), ...]
    if rec and rec[0]:
        text, confidence = rec[0][0]
    else:
        text, confidence = "", 0.0

    final_results.append({
        "pt_poly": poly,
        "text": text,
        "confidence": float(confidence)
    })

with open("./output/final_results.json", "w", encoding="utf-8") as f:
    json.dump({"results": final_results}, f, ensure_ascii=False, indent=2)

print(f"Done! {len(final_results)} items -> ./output/final_results.json")