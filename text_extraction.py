from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont

# 1. run OCR
ocr = PaddleOCR(ocr_version='PP-OCRv4', use_angle_cls=True, lang='en')
img_path = '/Users/rchembula/Desktop/PaddleOCR/TestFiles/stock_gs200.jpg'
result = ocr.ocr(img_path, cls=True)[0]    # result is a list of [box, (txt, score)]

# 2. load original to get size
orig = Image.open(img_path)
W, H = orig.size

# 3. make a blank white canvas
canvas = Image.new('RGB', (W, H), (255, 255, 255))
draw = ImageDraw.Draw(canvas)

# 4. choose a font (you can substitute any .ttf you like)
font = ImageFont.truetype(
    '/Users/rchembula/Desktop/PaddleOCR/TestFiles/simfang.ttf',
    size=16
)

# 5. draw each box + text
for box, (txt, score) in result:
    # box is four corner points [[x1,y1],…,[x4,y4]]
    pts = [tuple(map(int, pt)) for pt in box]
    
    # text at top-left of box, offset a little above
    x0, y0 = pts[0]
    # if text would go off-canvas, bump it down
    text_y = max(0, y0 - 20)
    draw.text((x0, text_y), txt, font=font, fill='darkgreen')

# 6. save
canvas.save('reconstructed_layout.jpg')
print("Wrote reconstructed_layout.jpg")
