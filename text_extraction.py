from paddleocr import PaddleOCR, draw_ocr
from googletrans import Translator
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')
img_path = '/Users/rchembula/Desktop/PaddleOCR/TestFiles/sample4.c68c31b95ffb.jpg'
result = ocr.ocr(img_path, cls=True)

# Load the original image
image = Image.open(img_path).convert('RGB')
draw = ImageDraw.Draw(image)

# Initialize translator
translator = Translator()

# Arabic font (replace with a valid Arabic font path)
# Download a font like "Arial Unicode MS" or "Noto Sans Arabic"
font_path = '/Users/rchembula/Desktop/PaddleOCR/TestFiles/NotoSansArabic-VariableFont_wdth,wght.ttf'  # Update this path
font_size = 12
font = ImageFont.truetype(font_path, font_size)

# Process each detected text box
for line in result[0]:
    box = line[0]  # Bounding box coordinates
    text = line[1][0]  # Extracted text
    confidence = line[1][1]  # Confidence score

    # Translate the text to Arabic
    translated_text = translator.translate(text, src='en', dest='ar').text

    # Reshape and apply bidirectional algorithm for Arabic
    reshaped_text = arabic_reshaper.reshape(translated_text)
    bidi_text = get_display(reshaped_text)

    # Calculate the position to place the translated text (use the top-left corner of the original box)
    x1, y1 = box[0]  # Top-left corner
    x2, y2 = box[2]  # Bottom-right corner

    # Draw a white rectangle to cover the original text (optional)
    draw.rectangle([x1, y1, x2, y2], fill='white')

    # Draw the translated Arabic text
    draw.text((x1, y1), bidi_text, fill='black', font=font)

# Save the result
output_path = 'translated_output.jpg'
image.save(output_path)
print(f"Translated image saved to: {output_path}")