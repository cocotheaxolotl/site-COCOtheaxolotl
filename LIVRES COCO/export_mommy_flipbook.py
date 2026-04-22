"""
Export Mommy-Loves-You-More-EN-8.5x8.5.pptx slides as PNG images
using PowerPoint COM automation, then generate a self-contained HTML flipbook.
"""
import sys, io, os, base64, comtypes.client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PPTX_PATH = os.path.abspath("prototypes/Mommy-Loves-You-More-EN-8.5x8.5.pptx")
OUT_DIR = os.path.abspath("prototypes/mommy-flipbook-slides")
HTML_OUT = os.path.abspath("prototypes/mommy-loves-you-more-flipbook.html")
DPI_SCALE = 2  # 8.5in * 96dpi * 2 = 1632px

os.makedirs(OUT_DIR, exist_ok=True)

# ── 1. Export slides via PowerPoint COM ─────────────────────────────────────
print("Opening PowerPoint...")
pptApp = comtypes.client.CreateObject("PowerPoint.Application")
pptApp.Visible = True  # needed on some systems

prs = pptApp.Presentations.Open(PPTX_PATH, ReadOnly=True, WithWindow=False)
slide_count = prs.Slides.Count
print(f"Slides: {slide_count}")

png_paths = []
for i in range(1, slide_count + 1):
    out_path = os.path.join(OUT_DIR, f"slide_{i:02d}.png")
    # ExportAsFixedFormat2 / Export: use Export(path, filterName, scaleWidth, scaleHeight)
    width_px = int(8.5 * 96 * DPI_SCALE)
    height_px = int(8.5 * 96 * DPI_SCALE)
    prs.Slides(i).Export(out_path, "PNG", width_px, height_px)
    print(f"  Exported slide {i} → {out_path}")
    png_paths.append(out_path)

prs.Close()
pptApp.Quit()
print("PowerPoint closed.")

# ── 2. Build HTML flipbook ───────────────────────────────────────────────────
print("Building HTML...")

slides_b64 = []
for p in png_paths:
    with open(p, "rb") as f:
        slides_b64.append(base64.b64encode(f.read()).decode())

imgs_js = "[\n" + ",\n".join(f'  "data:image/png;base64,{b64}"' for b64 in slides_b64) + "\n]"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mommy Loves You More — Flipbook</title>
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;700;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:#1a0533;
  min-height:100vh;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  font-family:'Baloo 2',cursive;
  overflow:hidden;
}}

/* ── Title bar ── */
.topbar{{
  position:fixed;top:0;left:0;right:0;
  display:flex;align-items:center;justify-content:center;
  padding:10px 20px;
  background:rgba(26,5,51,.85);
  backdrop-filter:blur(8px);
  z-index:100;
  gap:12px;
}}
.topbar h1{{
  font-size:1em;color:#e9b3ff;font-weight:800;letter-spacing:.03em;
}}
.page-counter{{
  font-size:.85em;color:#c084fc;background:rgba(192,132,252,.15);
  padding:3px 12px;border-radius:20px;
}}

/* ── Book container ── */
.book-wrap{{
  margin-top:56px;
  position:relative;
  display:flex;
  align-items:center;
  justify-content:center;
  width:100vw;
  height:calc(100vh - 56px - 72px);
}}

/* ── Slide image ── */
.slide-container{{
  position:relative;
  height:100%;
  aspect-ratio:1/1;
  max-height:calc(100vh - 56px - 72px);
  max-width:calc(100vw - 120px);
  border-radius:12px;
  overflow:hidden;
  box-shadow:0 20px 60px rgba(0,0,0,.6);
  transition:opacity .2s;
}}
.slide-container img{{
  width:100%;height:100%;object-fit:contain;
  display:block;
  background:#fff;
}}

/* ── Navigation arrows ── */
.nav-btn{{
  position:absolute;
  top:50%;transform:translateY(-50%);
  width:52px;height:52px;
  background:rgba(255,255,255,.12);
  border:2px solid rgba(255,255,255,.25);
  border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;
  font-size:1.4em;
  color:#fff;
  transition:background .2s,transform .1s;
  user-select:none;
  z-index:10;
}}
.nav-btn:hover{{background:rgba(192,132,252,.4);}}
.nav-btn:active{{transform:translateY(-50%) scale(.92);}}
.nav-btn.prev{{left:10px;}}
.nav-btn.next{{right:10px;}}
.nav-btn:disabled{{opacity:.25;pointer-events:none;}}

/* ── Bottom dots ── */
.bottom-bar{{
  position:fixed;bottom:0;left:0;right:0;
  height:72px;
  display:flex;align-items:center;justify-content:center;
  gap:6px;
  background:rgba(26,5,51,.85);
  backdrop-filter:blur(8px);
  padding:0 20px;
  overflow-x:auto;
}}
.dot{{
  width:8px;height:8px;border-radius:50%;
  background:rgba(255,255,255,.25);
  cursor:pointer;
  transition:background .2s,transform .2s;
  flex-shrink:0;
}}
.dot.active{{
  background:#c084fc;
  transform:scale(1.5);
}}

/* ── Keyboard hint ── */
.key-hint{{
  position:fixed;bottom:80px;right:16px;
  font-size:.7em;color:rgba(255,255,255,.35);
  pointer-events:none;
}}
</style>
</head>
<body>

<div class="topbar">
  <h1>Mommy Loves You More</h1>
  <span class="page-counter" id="counter">1 / {slide_count}</span>
</div>

<div class="book-wrap">
  <button class="nav-btn prev" id="btnPrev" onclick="go(-1)" disabled>&#8249;</button>
  <div class="slide-container">
    <img id="slideImg" src="" alt="Page 1">
  </div>
  <button class="nav-btn next" id="btnNext" onclick="go(1)">&#8250;</button>
</div>

<div class="bottom-bar" id="dots"></div>

<div class="key-hint">← → ou clic pour naviguer</div>

<script>
const slides = {imgs_js};
const total = slides.length;
let cur = 0;

const img = document.getElementById('slideImg');
const counter = document.getElementById('counter');
const btnPrev = document.getElementById('btnPrev');
const btnNext = document.getElementById('btnNext');
const dotsEl = document.getElementById('dots');

// Build dots
slides.forEach((_, i) => {{
  const d = document.createElement('div');
  d.className = 'dot' + (i === 0 ? ' active' : '');
  d.onclick = () => show(i);
  dotsEl.appendChild(d);
}});

function show(n) {{
  cur = Math.max(0, Math.min(total - 1, n));
  img.src = slides[cur];
  img.alt = 'Page ' + (cur + 1);
  counter.textContent = (cur + 1) + ' / ' + total;
  btnPrev.disabled = cur === 0;
  btnNext.disabled = cur === total - 1;
  document.querySelectorAll('.dot').forEach((d, i) => {{
    d.classList.toggle('active', i === cur);
  }});
  // Scroll dot into view
  const activeDot = dotsEl.children[cur];
  if (activeDot) activeDot.scrollIntoView({{inline:'center', behavior:'smooth', block:'nearest'}});
}}

function go(delta) {{ show(cur + delta); }}

// Keyboard
document.addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') go(1);
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') go(-1);
  if (e.key === 'Home') show(0);
  if (e.key === 'End') show(total - 1);
}});

// Touch / swipe
let tx0 = null;
document.addEventListener('touchstart', e => {{ tx0 = e.touches[0].clientX; }}, {{passive:true}});
document.addEventListener('touchend', e => {{
  if (tx0 === null) return;
  const dx = e.changedTouches[0].clientX - tx0;
  if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1);
  tx0 = null;
}});

show(0);
</script>
</body>
</html>
"""

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Done! Flipbook saved to: {HTML_OUT}")
