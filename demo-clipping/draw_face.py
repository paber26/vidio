"""Gambar wajah ilustrasi sederhana (bukan orang sungguhan) 700x900."""
import sys
from PIL import Image, ImageDraw, ImageFilter
W, H = 700, 900
im = Image.new("RGB", (W, H), (60, 90, 120))
d = ImageDraw.Draw(im)
d.rectangle([0, 620, W, H], fill=(40, 40, 50))                     # bahu/baju
d.ellipse([170, 520, 530, 900], fill=(50, 70, 140))
d.rectangle([300, 470, 400, 580], fill=(225, 180, 145))            # leher
d.ellipse([190, 130, 510, 540], fill=(232, 190, 155))              # kepala
d.chord([180, 100, 520, 380], 180, 360, fill=(45, 30, 25))          # rambut
d.ellipse([170, 290, 205, 380], fill=(225, 180, 145)); d.ellipse([495, 290, 530, 380], fill=(225, 180, 145))
for x in (270, 430):                                               # mata
    d.ellipse([x-38, 300, x+38, 345], fill="white")
    d.ellipse([x-16, 305, x+16, 340], fill=(70, 45, 30))
    d.ellipse([x-7, 315, x+7, 330], fill="black")
    d.arc([x-45, 265, x+45, 300], 200, 340, fill=(45, 30, 25), width=8)  # alis
d.polygon([(350, 340), (325, 420), (375, 420)], fill=(210, 160, 125))  # hidung
d.chord([280, 430, 420, 490], 0, 180, fill=(170, 60, 70))           # mulut
im = im.filter(ImageFilter.GaussianBlur(1.2))
im.save(sys.argv[1])
