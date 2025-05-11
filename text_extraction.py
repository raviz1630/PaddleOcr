from paddleocr import PaddleOCR, draw_ocr
from googletrans import Translator
from PIL import Image

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')
img_path = '/Users/rchembula/Desktop/PaddleOCR/TestFiles/sample4.c68c31b95ffb.jpg'
result = ocr.ocr(img_path, cls=True)

# Extract text and scores
extracted_text = []
for idx in range(len(result)):
    res = result[idx]
    for line in res:
        extracted_text.append((line[1][0], line[1][1]))  # (text, confidence)

# Combine all extracted text into a single string
combined_text = ' '.join([text for text, score in extracted_text])

# Translate the combined text to Arabic
translator = Translator()
translated_text = translator.translate(combined_text, src='en', dest='ar').text

# Display the results
print("Original Extracted Text:")
print(combined_text)
print("\nTranslated Text (Arabic):")
print(translated_text)

# Save the translated text to a file
with open('translated_result.txt', 'w', encoding='utf-8') as f:
    f.write("Original Text:\n")
    f.write(combined_text + "\n\n")
    f.write("Translated Text (Arabic):\n")
    f.write(translated_text)

print("\nResults saved to 'translated_result.txt'.")