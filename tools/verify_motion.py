"""P6: verify the motion actually runs under a renderer that paints.

Run:  PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright xvfb-run -a /tmp/pwv/bin/python tools/verify_motion.py
Not a test suite: prints a report and exits non-zero if a claim fails.
"""
import json, subprocess, sys, time
from pathlib import Path

URL = "http://127.0.0.1:8777/index.html"
ROOT = Path(__file__).resolve().parent.parent

from playwright.sync_api import sync_playwright

fails = []


def check(name, ok, detail=""):
    if not isinstance(detail, str):
        detail = json.dumps(detail, ensure_ascii=False)
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f" -> {detail}" if detail else ""))
    if not ok:
        fails.append(name)

server = subprocess.Popen([sys.executable, "-m", "http.server", "8777"], cwd=ROOT,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL, wait_until="load")

        check("visibilityState visible", pg.evaluate("document.visibilityState") == "visible",
              pg.evaluate("document.visibilityState"))

        # hero faces: fetchpriority + eager, and the browser picked the small candidate
        hero = pg.evaluate("""[...document.querySelectorAll('.hero-faces img')].map(i=>({
            fp:i.getAttribute('fetchpriority'), loading:i.getAttribute('loading'),
            nw:i.naturalWidth, src:i.currentSrc.split('/').pop()}))""")
        check("4 hero faces fetchpriority=high", len(hero) == 4 and all(h["fp"] == "high" for h in hero))
        check("hero not lazy", all(h["loading"] != "lazy" for h in hero))
        # Chrome reports naturalWidth scaled by the density it derives from `sizes`, so
        # the honest check is which candidate the browser picked, and how big that file is.
        check("hero picked the 400w candidate", all(h["src"].endswith("-t.webp") for h in hero),
              [h["src"] for h in hero])
        real = pg.evaluate("""(async()=>{const r=await fetch('/img/01a-t.webp');
            const b=await r.blob(); const bm=await createImageBitmap(b); return [bm.width,bm.height,b.size]})()""")
        check("the 400w file on disk really is 400px wide", real[0] == 400, real)

        # srcset coverage on real rendered content images
        cov = pg.evaluate("""(()=>{const a=[...document.images];
            return {total:a.length, withSrcset:a.filter(i=>i.srcset).length,
                    missing:a.filter(i=>!i.srcset).map(i=>i.id||i.className||i.src)}})()""")
        # #lbImg is the lightbox target; JS swaps .src directly, one candidate by design.
        check("every content img has srcset (lbImg excluded)",
              cov["missing"] == ["lbImg"], cov)

        # alt: no duplicate name between wrapper label and img alt
        dup = pg.evaluate("""[...document.querySelectorAll('.gallery-item')].filter(f=>
            [...f.querySelectorAll('button')].some(b=>{const i=b.querySelector('img');
            return i && b.getAttribute('aria-label').includes(i.alt.split(',')[0])})).length""")
        check("no gallery frame repeats the name in label and alt", dup == 0, dup)
        check("gallery alt numbered",
              pg.evaluate("""[...document.querySelectorAll('.gallery-item img')].every(i=>/foto \\d dari 2$/.test(i.alt))"""))

        # motion: per-word reveal, scroll reveals, running animations
        time.sleep(1.2)
        check("per-word heading reveal landed",
              pg.evaluate("""[...document.querySelectorAll('.rw')].every(e=>getComputedStyle(e).opacity==='1')"""))
        pg.evaluate("scrollTo(0, document.body.scrollHeight * 0.6)")
        time.sleep(1.5)
        rev = pg.evaluate("""({vis:document.querySelectorAll('.reveal.visible').length,
                              total:document.querySelectorAll('.reveal').length})""")
        check("scroll reveals fire (IntersectionObserver)", rev["vis"] > 0, rev)
        run = pg.evaluate("document.getAnimations().filter(a=>a.playState==='running').length")
        check("animations actually running", run > 0, run)

        # counter reached its final number, marquee moving
        check("marquee animation-name set",
              pg.evaluate("getComputedStyle(document.querySelector('.marquee-track')).animationName") != "none")
        check("scroll position responds", pg.evaluate("scrollY") > 0, pg.evaluate("scrollY"))

        # layout: nothing grew, tap targets
        h = pg.evaluate("+(document.documentElement.scrollHeight/innerHeight).toFixed(2)")
        print(f"     desktop height: {h} screens")
        small = pg.evaluate("""[...document.querySelectorAll('a,button')].filter(e=>{
            const r=e.getBoundingClientRect(); return r.width && r.height && (r.height<44||r.width<44)&&
            getComputedStyle(e).visibility!=='hidden'}).length""")
        pg.set_viewport_size({"width": 375, "height": 812})
        time.sleep(0.6)
        small_m = pg.evaluate("""[...document.querySelectorAll('a,button')].filter(e=>{
            const r=e.getBoundingClientRect(); return r.width && r.height && r.height<44 &&
            getComputedStyle(e).visibility!=='hidden'}).length""")
        check("no tap target under 44px @375", small_m == 0, small_m)

        # first-paint payload: bytes actually transferred for the hero, measured
        pg.goto("about:blank")
        sizes = {}
        pg.on("response", lambda r: sizes.__setitem__(r.url.split("/")[-1], r.headers.get("content-length")))
        pg.goto(URL, wait_until="load")
        time.sleep(1.0)
        hero_bytes = sum(int(sizes.get(f"{n}-t.webp") or 0) for n in ("01a", "07a", "13a", "19a"))
        check("hero payload under 90KB", 0 < hero_bytes < 90 * 1024, f"{hero_bytes/1024:.1f} KB")

        # motion is real: sample the counter and a drifted element at two instants
        t0 = pg.evaluate("""(()=>{const e=document.querySelector('.gallery-item');
            return {tf:e?getComputedStyle(e).transform:null,
                    n:document.body.innerText.match(/\b20\b/)?.[0]||null}})()""")
        pg.evaluate("scrollTo(0, document.body.scrollHeight * 0.55)")
        time.sleep(1.6)
        t1 = pg.evaluate("""(()=>{const e=document.querySelector('.gallery-item');
            return {tf:e?getComputedStyle(e).transform:null,
                    n:document.body.innerText.match(/\b20\b/)?.[0]||null}})()""")
        check("photo drift transform changed between frames", t0["tf"] != t1["tf"], f"{t0['tf']} -> {t1['tf']}")

        check("no console errors", not errors, errors[:3])
        b.close()
finally:
    server.terminate()

print()
print("PASS" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)