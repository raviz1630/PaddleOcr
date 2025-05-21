import json
import uuid
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from azure.storage.blob import BlobServiceClient
import os
import re

# Azure Blob Storage credentials
storage_account_name = "nonpoaiplay"
storage_account_key = "QCxdq0lJ5j6xn84DwkvJcEalRkLfcYNyAZQZnCx23+0XqxrF1KUr9ASiuKiSk0URtHyXXBTZ0SNi+AStlmlXFg=="
container_name = "arabic"

input_json_folder = "translated_json_folder"
input_image_folder = "segmented_images"
output_image_folder = "translated_images"

def get_blob_service_client():
    return BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=storage_account_key
    )

def download_blob_to_memory(container, blob_name):
    blob_client = container.get_blob_client(blob_name)
    data = blob_client.download_blob().readall()
    return data

def upload_image_to_blob(container, img: Image.Image, blob_name: str):
    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    blob_client = container.get_blob_client(blob_name)
    blob_client.upload_blob(output, overwrite=True)
    print(f"✅ Uploaded: {blob_name}")

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

def calculate_required_font_sizes(draw, text_boxes, font_path, padding=4, min_font=6, max_font=72):
    """Calculate required font sizes for all text boxes and return the maximum size that fits all"""
    font_sizes = []
    
    for box in text_boxes:
        text, (x0, y0, x1, y1) = box
        width = x1 - x0 - 2 * padding
        height = y1 - y0 - 2 * padding
        
        # Binary search to find maximum font size for this box
        low, high = min_font, max_font
        best_size = min_font
        
        while low <= high:
            mid = (low + high) // 2
            font = ImageFont.truetype(font_path, size=mid)
            lines = wrap_text(draw, text, width, font)
            line_height = measure_text(draw, "Ay", font)[1]
            total_height = len(lines) * line_height
            
            if total_height <= height:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1
        
        font_sizes.append(best_size)
    
    # Return the smallest font size that fits all boxes
    return min(font_sizes) if font_sizes else 12

def main():
    blob_service = get_blob_service_client()
    container = blob_service.get_container_client(container_name)
    blobs = container.list_blobs(name_starts_with=input_json_folder + "/")
    
    font_path = "/Users/rchembula/Desktop/PaddleOCR/TestFiles/simfang.ttf"
    padding = 4
    blur_radius = 4
    alpha_rect = (255, 255, 255, 200)

    for blob in blobs:
        json_blob_name = blob.name
        if not json_blob_name.endswith(".json"):
            continue

        print(f"🔍 Processing: {json_blob_name}")
        json_bytes = download_blob_to_memory(container, json_blob_name)
        data = json.loads(json_bytes)

        # Attempt to find matching image
        json_page_match = re.search(r'page_\d+', json_blob_name)
        image_blob_name = None

        if json_page_match:
            page_key = json_page_match.group()
            image_blobs = {
                re.search(r'page_\d+', b.name).group(): b.name
                for b in container.list_blobs(name_starts_with=input_image_folder + "/")
                if re.search(r'page_\d+', b.name)
            }
            image_blob_name = image_blobs.get(page_key)

        if not image_blob_name:
            json_base_name = os.path.splitext(os.path.basename(json_blob_name))[0]
            json_keyword = json_base_name.split("_")[0]
            image_candidates = list(container.list_blobs(name_starts_with=input_image_folder + "/"))
            for b in image_candidates:
                img_name = os.path.basename(b.name)
                if json_keyword in img_name:
                    image_blob_name = b.name
                    break

        if not image_blob_name:
            print(f"⚠️ No matching image found for {json_blob_name}")
            continue

        try:
            image_bytes = download_blob_to_memory(container, image_blob_name)
        except Exception as e:
            print(f"⚠️ Could not find matching image for {json_blob_name}: {e}")
            continue

        for page in data.get("pages", []):
            orig = Image.open(BytesIO(image_bytes)).convert("RGBA")
            overlay = Image.new("RGBA", orig.size, (255, 255, 255, 0))
            text_layer = Image.new("RGBA", orig.size, (255, 255, 255, 0))
            draw_rect = ImageDraw.Draw(overlay)
            draw_text = ImageDraw.Draw(text_layer)

            # First pass: Collect all text boxes and calculate required font sizes
            text_boxes = []
            
            # Process paragraphs
            for para in data.get("paragraphs", []):
                txt = para.get("translatedContent", "").strip()
                if not txt: continue
                for region in para["boundingRegions"]:
                    flat = region["polygon"]
                    xs, ys = flat[0::2], flat[1::2]
                    box = (min(xs), min(ys), max(xs), max(ys))
                    text_boxes.append((txt, box))

            # Process table cells
            for tbl in data.get("tables", []):
                for cell in tbl.get("cells", []):
                    txt = cell.get("translatedContent", "").strip()
                    if not txt: continue
                    for region in cell.get("boundingRegions", []):
                        flat = region["polygon"]
                        xs, ys = flat[0::2], flat[1::2]
                        box = (min(xs), min(ys), max(xs), max(ys))
                        text_boxes.append((txt, box))

            # Calculate universal font size
            universal_font_size = calculate_required_font_sizes(
                draw_text, text_boxes, font_path, padding
            )
            universal_font = ImageFont.truetype(font_path, size=universal_font_size)
            print(f"📏 Using universal font size: {universal_font_size}pt")

            # Blur regions
            for col in ("paragraphs", "tables"):
                items = page.get(col, [])
                if col == "tables":
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
                    patch = orig.crop(box)
                    blurred = patch.filter(ImageFilter.GaussianBlur(blur_radius))
                    orig.paste(blurred, box)

            # Second pass: Render all text with the universal font size
            for txt, (x0, y0, x1, y1) in text_boxes:
                draw_rect.rectangle([x0, y0, x1, y1], fill=alpha_rect)
                inner_w = (x1 - x0) - 2 * padding
                inner_h = (y1 - y0) - 2 * padding
                
                lines = wrap_text(draw_text, txt, inner_w, universal_font)
                lh = measure_text(draw_text, "Ay", universal_font)[1]
                start_y = y0 + padding

                # Center text vertically if there's extra space
                total_text_height = len(lines) * lh
                if total_text_height < inner_h:
                    start_y = y0 + (y1 - y0 - total_text_height) // 2

                for i, line in enumerate(lines):
                    y = start_y + i * lh
                    if y + lh > y1 - padding:
                        break
                    draw_text.text((x0 + padding, y), line, font=universal_font, fill="black")

            # Draw table borders
            for tbl in data.get("tables", []):
                for region in tbl.get("boundingRegions", []):
                    flat = region["polygon"]
                    pts = [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
                    draw_rect.line(pts + [pts[0]], fill="green", width=2)

            bright_text = ImageEnhance.Brightness(text_layer).enhance(1.8)
            combined = Image.alpha_composite(orig, overlay)
            combined = Image.alpha_composite(combined, bright_text).convert("RGB")

            base_name = os.path.splitext(os.path.basename(image_blob_name))[0]
            output_blob_name = f"{output_image_folder}/{base_name}.png"
            upload_image_to_blob(container, combined, output_blob_name)

if __name__ == "__main__":
    main()