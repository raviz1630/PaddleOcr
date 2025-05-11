import json
from PIL import Image, ImageDraw
import os
from paddlex import create_model


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
img = Image.open("/Users/rchembula/Desktop/PaddleOCR/TestFiles/test_image1.jpeg").convert("RGBA")

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
