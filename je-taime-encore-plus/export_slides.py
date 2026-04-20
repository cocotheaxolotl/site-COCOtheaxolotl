"""Export Je-t'aime-encore-plus FR pptx slides as JPG."""
import os, sys, io, comtypes.client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PPTX = os.path.abspath(r"../LIVRES COCO/I love you more/Je t'aime-encore-plus -FR-8.5x11.pptx")
OUT = os.path.abspath("pages")
os.makedirs(OUT, exist_ok=True)

DPI_SCALE = 2
W = int(8.5 * 96 * DPI_SCALE)   # 1632
H = int(11  * 96 * DPI_SCALE)   # 2112

print("Opening PowerPoint...")
app = comtypes.client.CreateObject("PowerPoint.Application")
app.Visible = True
prs = app.Presentations.Open(PPTX, ReadOnly=True, WithWindow=False)
n = prs.Slides.Count
print(f"Slides: {n}")
for i in range(1, n + 1):
    out = os.path.join(OUT, f"slide_{i:02d}.jpg")
    prs.Slides(i).Export(out, "JPG", W, H)
    print(f"  {i}/{n}  {out}")
prs.Close()
app.Quit()
print("Done.")
