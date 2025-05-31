import os
import json
import textwrap
import re
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Azure Storage Configuration
storage_account_name = "nonpoaiplay"
storage_account_key = "QCxdq0lJ5j6xn84DwkvJcEalRkLfcYNyAZQZnCx23+0XqxrF1KUr9ASiuKiSk0URtHyXXBTZ0SNi+AStlmlXFg=="
container_name = "arabic"

# Constants
PADDING = 4
BLUR_RADIUS = 4
ALPHA_RECT = (255, 255, 255, 200)
FONT_PATH = "/Users/rchembula/Desktop/PaddleOCR/TestFiles/simfang.ttf"
INPUT_IMAGE_FOLDER = "segmented_images"
INPUT_JSON_FOLDER = "translated_json_folder"
OUTPUT_FOLDER = "final_results"
FINAL_PDF_NAME = "combined_translated_document.pdf"

# Initialize Azure Blob Service
blob_service_client = BlobServiceClient(
    f"https://{storage_account_name}.blob.core.windows.net",
    credential=storage_account_key
)
container_client = blob_service_client.get_container_client(container_name)

# Helpers
def combine_images_to_pdf():
    # List all images in the final_results folder
    blobs = container_client.list_blobs(name_starts_with=OUTPUT_FOLDER + "/")
    image_files = []
    
    for blob in blobs:
        if blob.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_files.append(blob.name)
    
    if not image_files:
        print("⚠️ No images found in final_results folder to combine into PDF.")
        return
    
    # Sort the images by page number
    image_files.sort(key=lambda x: int(re.search(r'page_(\d+)', x).group(1)))
    
    # Download all images and store in memory
    images = []
    for img_blob in image_files:
        try:
            blob_client = container_client.get_blob_client(img_blob)
            stream = blob_client.download_blob()
            img = Image.open(BytesIO(stream.readall()))
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            print(f"⚠️ Error processing {img_blob}: {e}")
    
    if not images:
        print("⚠️ No valid images could be loaded for PDF creation.")
        return
    
    # Create a temporary file in memory for the PDF
    pdf_buffer = BytesIO()
    
    # Save the first image as PDF and append the rest
    images[0].save(
        pdf_buffer,
        format="PDF",
        save_all=True,
        append_images=images[1:] if len(images) > 1 else None,
        quality=100
    )
    
    pdf_buffer.seek(0)
    
    # Upload the PDF to Azure
    blob_client = container_client.get_blob_client(FINAL_PDF_NAME)
    blob_client.upload_blob(pdf_buffer, overwrite=True)
    print(f"✅ Successfully created and uploaded combined PDF: {FINAL_PDF_NAME}")

def measure_text(draw, text, font):
    try:
        x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=font)
        return x1 - x0, y1 - y0
    except AttributeError:
        return font.getsize(text)

def wrap_text(draw, text, max_width, font):
    wM, _ = measure_text(draw, "M", font)
    est = max(1, max_width // wM)
    lines = []
    for chunk in textwrap.wrap(text, width=est):
        w, _ = measure_text(draw, chunk, font)
        if w <= max_width:
            lines.append(chunk)
        else:
            words, cur = chunk.split(), ""
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

def get_box_from_polygon(polygon):
    xs, ys = polygon[0::2], polygon[1::2]
    return min(xs), min(ys), max(xs), max(ys)

def load_font(size=20):
    try:
        return ImageFont.truetype(FONT_PATH, size=size)
    except IOError:
        return ImageFont.load_default()

def blur_regions(orig, regions):
    for region in regions:
        flat = region["polygon"]
        box = get_box_from_polygon(flat)
        patch = orig.crop(box)
        blurred = patch.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
        orig.paste(blurred, box)

def find_max_font_size(draw, text, box_width, box_height):
    for size in range(30, 5, -1):
        font = load_font(size=size)
        lines = wrap_text(draw, text, box_width - 2 * PADDING, font)
        lh = measure_text(draw, "Ay", font)[1]
        if lh * len(lines) <= box_height - 2 * PADDING:
            return font
    return load_font(size=6)

def draw_text_box(draw_rect, draw_text, text, polygon):
    x0, y0, x1, y1 = get_box_from_polygon(polygon)
    draw_rect.rectangle([x0, y0, x1, y1], fill=ALPHA_RECT)
    box_w, box_h = x1 - x0, y1 - y0
    font = find_max_font_size(draw_text, text, box_w, box_h)
    lines = wrap_text(draw_text, text, box_w - 2 * PADDING, font)
    lh = measure_text(draw_text, "Ay", font)[1]
    start_y = y0 + PADDING
    for i, line in enumerate(lines):
        y = start_y + i * lh
        if y + lh > y1 - PADDING:
            break
        draw_text.text((x0 + PADDING, y), line, font=font, fill="black")

def draw_paragraphs(draw_rect, draw_text, paragraphs):
    for para in paragraphs:
        txt = para.get("translatedContent", "").strip()
        if not txt:
            continue
        for region in para["boundingRegions"]:
            draw_text_box(draw_rect, draw_text, txt, region["polygon"])

def draw_tables(draw_rect, draw_text, tables):
    for tbl in tables:
        for region in tbl.get("boundingRegions", []):
            pts = [(region["polygon"][i], region["polygon"][i + 1]) for i in range(0, len(region["polygon"]), 2)]
            draw_rect.line(pts + [pts[0]], fill="green", width=2)
        for cell in tbl.get("cells", []):
            txt = cell.get("translatedContent", "").strip()
            if not txt:
                continue
            for region in cell["boundingRegions"]:
                draw_text_box(draw_rect, draw_text, txt, region["polygon"])

def download_blob_as_image(blob_path):
    blob_client = container_client.get_blob_client(blob_path)
    stream = blob_client.download_blob()
    return Image.open(BytesIO(stream.readall())).convert("RGBA")

def download_blob_as_json(blob_path):
    blob_client = container_client.get_blob_client(blob_path)
    stream = blob_client.download_blob()
    return json.loads(stream.readall().decode("utf-8"))

def upload_image_to_azure(filename, image):
    output_stream = BytesIO()
    image.save(output_stream, format="PNG")
    output_stream.seek(0)
    blob_client = container_client.get_blob_client(f"{OUTPUT_FOLDER}/{filename}")
    blob_client.upload_blob(output_stream, overwrite=True)

def find_matching_json_file(image_blob_name, all_json_blobs):
    """Find the matching JSON file for a given image blob"""
    # Extract base filename from image path
    # For segmented_images/test_image1.jpg -> test_image1
    image_base_name = os.path.splitext(os.path.basename(image_blob_name))[0]
    
    print(f"🔍 Looking for JSON matching image base name: {image_base_name}")
    
    # Look for exact match first (for single images)
    exact_match = f"{INPUT_JSON_FOLDER}/{image_base_name}.json"
    if exact_match in all_json_blobs:
        print(f"✅ Found exact match: {exact_match}")
        return exact_match
    
    # Look for patterns that might match (for PDFs or other naming patterns)
    possible_matches = []
    for json_blob in all_json_blobs:
        json_base = os.path.splitext(os.path.basename(json_blob))[0]
        
        # Check if the JSON filename contains the image base name
        if image_base_name in json_base:
            possible_matches.append(json_blob)
            print(f"🎯 Found possible match: {json_blob}")
    
    if len(possible_matches) == 1:
        print(f"✅ Using single possible match: {possible_matches[0]}")
        return possible_matches[0]
    elif len(possible_matches) > 1:
        print(f"⚠️ Multiple possible matches found: {possible_matches}")
        # Use the first one or implement more sophisticated matching logic
        return possible_matches[0]
    
    print(f"❌ No matching JSON file found for {image_blob_name}")
    return None

def process_page(page_num):
    image_blob_path = f"{INPUT_IMAGE_FOLDER}/page_{page_num}.jpeg"
    
    # Find the JSON file for this page dynamically
    json_blob_path = None
    blobs = container_client.list_blobs(name_starts_with=INPUT_JSON_FOLDER + "/")
    
    for blob in blobs:
        if blob.name.endswith(f"_page_{page_num}.json"):
            json_blob_path = blob.name
            break
    
    if not json_blob_path:
        print(f"⚠️ No JSON file found for page {page_num}")
        return

    try:
        image = download_blob_as_image(image_blob_path)
        data = download_blob_as_json(json_blob_path)
    except Exception as e:
        print(f"Skipping page {page_num}: {e}")
        return
    
    paragraphs = data.get("paragraphs", [])
    tables = data.get("tables", [])
    regions = [r for para in paragraphs for r in para["boundingRegions"]]
    for t in tables:
        regions += t.get("boundingRegions", [])
        for cell in t.get("cells", []):
            regions += cell.get("boundingRegions", [])
    blur_regions(image, regions)

    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    text_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw_rect = ImageDraw.Draw(overlay)
    draw_text = ImageDraw.Draw(text_layer)

    draw_paragraphs(draw_rect, draw_text, paragraphs)
    draw_tables(draw_rect, draw_text, tables)

    enhancer = ImageEnhance.Brightness(text_layer)
    bright_text = enhancer.enhance(2.8)

    combined = Image.alpha_composite(image, overlay)
    combined = Image.alpha_composite(combined, bright_text).convert("RGB")

    output_filename = f"page_{page_num}_translated_english_on_canvas.png"
    upload_image_to_azure(output_filename, combined)
    print(f"✅ Processed and uploaded: {output_filename}")

def process_single_image(image_blob_name, all_json_blobs):
    """Process a single image file"""
    print(f"🔍 Processing single image: {image_blob_name}")
    
    # Find the matching JSON file
    json_blob_path = find_matching_json_file(image_blob_name, all_json_blobs)
    
    if not json_blob_path:
        print(f"❌ No matching JSON file found for {image_blob_name}")
        print("🔍 Available JSON files:")
        for json_blob in all_json_blobs:
            print(f"  - {json_blob}")
        return

    try:
        print(f"⬇️ Downloading image: {image_blob_name}")
        image = download_blob_as_image(image_blob_name)
        print(f"⬇️ Downloading JSON: {json_blob_path}")
        data = download_blob_as_json(json_blob_path)
    except Exception as e:
        print(f"❌ Error downloading files for {image_blob_name}: {e}")
        return

    # Process the translation data
    print("🌍 Processing translation data...")
    paragraphs = data.get("paragraphs", [])
    tables = data.get("tables", [])
    print(f"📄 Found {len(paragraphs)} paragraphs and {len(tables)} tables")
    
    # Check if we have any translated content
    has_translated_content = False
    for para in paragraphs:
        if para.get("translatedContent", "").strip():
            has_translated_content = True
            break
    
    if not has_translated_content:
        for table in tables:
            for cell in table.get("cells", []):
                if cell.get("translatedContent", "").strip():
                    has_translated_content = True
                    break
            if has_translated_content:
                break
    
    if not has_translated_content:
        print("⚠️ No translated content found in JSON file. Make sure translation step completed successfully.")
        return
    
    regions = [r for para in paragraphs for r in para["boundingRegions"]]
    for t in tables:
        regions += t.get("boundingRegions", [])
        for cell in t.get("cells", []):
            regions += cell.get("boundingRegions", [])
    
    print(f"🔲 Found {len(regions)} regions to blur")
    blur_regions(image, regions)

    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    text_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw_rect = ImageDraw.Draw(overlay)
    draw_text = ImageDraw.Draw(text_layer)

    print("✏️ Drawing paragraphs and tables...")
    draw_paragraphs(draw_rect, draw_text, paragraphs)
    draw_tables(draw_rect, draw_text, tables)

    enhancer = ImageEnhance.Brightness(text_layer)
    bright_text = enhancer.enhance(2.8)

    combined = Image.alpha_composite(image, overlay)
    combined = Image.alpha_composite(combined, bright_text).convert("RGB")

    # Extract base name for output filename
    base_name = os.path.splitext(os.path.basename(image_blob_name))[0]
    output_filename = f"{base_name}_translated_english_on_canvas.png"
    print(f"⬆️ Uploading result: {output_filename}")
    upload_image_to_azure(output_filename, combined)
    print(f"✅ Processed and uploaded: {output_filename}")

def main():
    print("🚀 Starting translation overlay process...")
    
    # Get all available JSON files first
    print("🔍 Loading available JSON files...")
    json_blobs = []
    all_blobs = container_client.list_blobs(name_starts_with=INPUT_JSON_FOLDER + "/")
    for blob in all_blobs:
        if blob.name.endswith(".json"):
            json_blobs.append(blob.name)
    
    print(f"📄 Found {len(json_blobs)} JSON files:")
    for json_blob in json_blobs:
        print(f"  - {json_blob}")
    
    # Get all image files
    blobs = container_client.list_blobs(name_starts_with=INPUT_IMAGE_FOLDER + "/")
    page_nums = []
    single_images = []

    print("🔍 Scanning for images...")
    for blob in blobs:
        print(f"  Found: {blob.name}")
        # Check for PDF pages (page_X.jpeg)
        match = re.search(r'page_(\d+)\.jpeg$', blob.name)
        if match:
            page_nums.append(int(match.group(1)))
            print(f"    -> PDF page {match.group(1)}")
        # Check for single images (any other image file)
        elif blob.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            single_images.append(blob.name)
            print(f"    -> Single image")

    # Process PDF pages
    if page_nums:
        print(f"📄 Processing {len(page_nums)} PDF pages...")
        page_nums.sort()
        for page_num in page_nums:
            process_page(page_num)
        combine_images_to_pdf()
    
    # Process single images
    if single_images:
        print(f"🖼️ Processing {len(single_images)} single images...")
        for img_blob in single_images:
            process_single_image(img_blob, json_blobs)
    
    if not page_nums and not single_images:
        print("⚠️ No images found in segmented_images folder.")
    
    print("🎉 Processing complete!")

if __name__ == "__main__":
    main()