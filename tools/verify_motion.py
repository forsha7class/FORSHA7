"""Verify the FORSHA 7 claims against the real page in a renderer that paints.

Run:
    python3 -m pip install playwright
    python3 -m playwright install chromium
    python3 tools/verify_motion.py

Not a test suite: it prints a report and exits non-zero if a claim fails.
Set PW_PORT to move the preview server off 8777.

Why the HTTP server is threaded: the page opens ~30 images at once, and
`http.server` handles one request at a time, so a single-threaded server
aborts the rest of the first paint and every media claim below goes wrong.
"""

import json
import os
import sys
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("PW_PORT", "8777"))
URL = f"http://127.0.0.1:{PORT}/"

fails = []


def check(name, ok, detail=""):
    if not isinstance(detail, (str, int, float)):
        detail = json.dumps(detail, ensure_ascii=False)
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f" -> {detail}" if detail != "" else ""))
    if not ok:
        fails.append(name)


# --- environment bootstrap -------------------------------------------------
# Some sandboxes ship the browser under a different revision directory than the
# installed Python package expects, and keep the shared libraries outside the
# loader path. Both are detected; on a normal machine this is a no-op.

def bootstrap_env():
    note = []
    deps = Path.home() / ".local" / "playwright-deps" / "usr" / "lib" / "x86_64-linux-gnu"
    if deps.is_dir():
        cur = os.environ.get("LD_LIBRARY_PATH", "")
        if str(deps) not in cur.split(":"):
            os.environ["LD_LIBRARY_PATH"] = f"{deps}:{cur}" if cur else str(deps)
            note.append(f"added {deps} to LD_LIBRARY_PATH")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        want = Path(p.chromium.executable_path).parents[1].name  # e.g. chromium-1248

    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return note
    cache = Path.home() / ".cache" / "ms-playwright"
    if not cache.is_dir() or (cache / want).exists():
        return note

    have = sorted(d.name for d in cache.glob("chromium-*") if d.is_dir())
    if len(have) != 1:
        note.append(f"expected {want}, found {have or 'nothing'} in {cache}")
        return note

    farm = Path(tempfile.mkdtemp(prefix="pw-browsers-"))
    rev = want.split("-", 1)[1]
    (farm / f"chromium-{rev}").symlink_to(cache / have[0])
    shells = sorted(d.name for d in cache.glob("chromium_headless_shell-*") if d.is_dir())
    for sh in shells:
        (farm / f"chromium_headless_shell-{rev}").symlink_to(cache / sh)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(farm)
    note.append(f"served {want} from {have[0]} via {farm}")
    return note


for line in bootstrap_env():
    print(f"     note: {line}")

from playwright.sync_api import sync_playwright  # noqa: E402


# --- preview server --------------------------------------------------------

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the report readable
        pass


server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(QuietHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        console_errors, failed_requests = [], []
        requests = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        page.on("request", lambda r: requests.append(r.url))
        page.on("response", lambda r: failed_requests.append(f"{r.status} {r.url}") if r.status >= 400 else None)

        page.goto(URL, wait_until="load")
        page.wait_for_timeout(200)

        check("visibilityState visible", page.evaluate("document.visibilityState") == "visible",
              page.evaluate("document.visibilityState"))
        check("GSAP core loaded from vendor/",
              page.evaluate("typeof window.gsap") == "object")
        check("ScrollTrigger loaded from vendor/",
              page.evaluate("typeof window.ScrollTrigger") == "function")

        # --- hero corridor -------------------------------------------------
        corridor = page.evaluate(
            """[...document.querySelectorAll('.corridor-card img')].map(i=>({
                 loading:i.getAttribute('loading'), fp:i.getAttribute('fetchpriority'),
                 nw:i.naturalWidth, src:i.currentSrc.split('/').pop()}))"""
        )
        check("18 hero corridor frames", len(corridor) == 18, len(corridor))
        check("corridor frames are eager", all(i["loading"] == "eager" for i in corridor))
        check("corridor frames carry fetchpriority", all(i["fp"] for i in corridor),
              sorted({i["fp"] for i in corridor}))
        check("corridor frames resolve to a real file", all(i["nw"] > 0 for i in corridor),
              [i["src"] for i in corridor if i["nw"] == 0])
        check("corridor picked the 400w candidate",
              all(i["src"].endswith("-t.webp") for i in corridor),
              sorted({i["src"] for i in corridor})[:4])

        real = page.evaluate(
            """(async()=>{const r=await fetch('/img/01a-t.webp');const b=await r.blob();
                 const bm=await createImageBitmap(b);return [bm.width,bm.height,b.size]})()"""
        )
        check("the 400w file on disk really is 400px wide", real[0] == 400, real)

        # --- the wall ------------------------------------------------------
        cards = page.evaluate("document.querySelectorAll('.pcard').length")
        check("20 class cards on the wall", cards == 20, cards)

        # Scroll the whole page slowly so every ScrollTrigger start is crossed.
        page.evaluate(
            """async () => {
                 await new Promise(res => {
                   let y = 0;
                   const step = () => {
                     y += innerHeight * 0.6;
                     scrollTo(0, y);
                     if (y < document.body.scrollHeight) setTimeout(step, 120);
                     else setTimeout(res, 400);
                   };
                   step();
                 });
               }"""
        )
        page.wait_for_timeout(1600)

        settled = page.evaluate(
            """[...document.querySelectorAll('.pcard')].map(c=>{
                 const s=getComputedStyle(c);
                 const m = s.transform === 'none' ? null : new DOMMatrixReadOnly(s.transform);
                 return {op:s.opacity,
                         tx:m?m.m41:0, ty:m?m.m42:0,
                         skew:!!m && (Math.abs(m.b) > 0.001 || Math.abs(m.c) > 0.001),
                         scale:m?[m.a,m.d]:[1,1]};})"""
        )
        check("every wall card faded in (ScrollTrigger.batch ran)",
              all(abs(float(c["op"]) - 1) < 0.001 for c in settled),
              sorted({c["op"] for c in settled}))
        check("every wall card returned to its resting position",
              all(abs(c["tx"]) < 0.5 and abs(c["ty"]) < 0.5 and not c["skew"]
                  and abs(c["scale"][0] - 1) < 0.001 and abs(c["scale"][1] - 1) < 0.001
                  for c in settled),
              sorted({(round(c["tx"], 1), round(c["ty"], 1)) for c in settled})[:3])

        # --- disciplines ---------------------------------------------------
        strips = page.evaluate(
            """['foStrip','hkStrip'].map(id=>{const s=document.getElementById(id);
                 const imgs=[...s.querySelectorAll('img')];
                 return {id, n:imgs.length, loaded:imgs.filter(i=>i.naturalWidth>0).length};})"""
        )
        check("both discipline panels show 4 portraits",
              all(s["n"] == 4 for s in strips), strips)
        check("discipline portraits all loaded",
              all(s["loaded"] == s["n"] for s in strips), strips)

        # --- gallery / plates ----------------------------------------------
        plates = page.evaluate("document.querySelectorAll('.plate').length")
        check("72 gallery frames (36 portraits, both rows doubled)", plates == 2 * 36, plates)
        cov = page.evaluate(
            """(()=>{const a=[...document.querySelectorAll('.plate img')];
                 return {total:a.length, withSrcset:a.filter(i=>i.srcset).length,
                         withSizes:a.filter(i=>i.sizes).length,
                         noAlt:a.filter(i=>!i.hasAttribute('alt')).length,
                         unloaded:a.filter(i=>i.naturalWidth===0).length}})()"""
        )
        check("every gallery frame has srcset", cov["withSrcset"] == cov["total"], cov)
        check("every gallery frame declares sizes", cov["withSizes"] == cov["total"], cov)
        check("every gallery frame has an alt attribute", cov["noAlt"] == 0, cov["noAlt"])
        check("every gallery frame loaded", cov["unloaded"] == 0, cov["unloaded"])

        marquee = page.evaluate(
            """[...document.querySelectorAll('.marquee-row .track')].map(t=>{
                 const s=getComputedStyle(t);
                 return {name:s.animationName, dir:s.animationDirection, dur:s.animationDuration};})"""
        )
        check("both gallery marquees animate",
              len(marquee) == 2 and all(m["name"] != "none" for m in marquee), marquee)
        check("the two marquees run in opposite directions",
              {m["dir"] for m in marquee} == {"normal", "reverse"}, marquee)

        # --- about counters -------------------------------------------------
        counters = page.evaluate(
            """[...document.querySelectorAll('[data-count]')].map(e=>({
                 want:String(+e.dataset.count).padStart(+(e.dataset.pad||0),'0'),
                 got:e.textContent.trim()}))"""
        )
        check("all four counters count up to their real values",
              all(c["want"] == c["got"] for c in counters), counters)

        # --- close: twenty cards become a seven ------------------------------
        stage = page.evaluate(
            """(()=>{const s=document.getElementById('sevenStage');
                 const m=[...s.querySelectorAll('.mini')];
                 return {n:m.length, pos:m.map(c=>{const r=c.getBoundingClientRect();
                        return [Math.round(r.left),Math.round(r.top)];})}})()"""
        )
        check("closing formation has 20 cards", stage["n"] == 20, stage["n"])
        check("closing cards land on distinct cells",
              len({tuple(p) for p in stage["pos"]}) == 20,
              len({tuple(p) for p in stage["pos"]}))

        mini_op = page.evaluate(
            """[...document.querySelectorAll('.mini')].map(c=>getComputedStyle(c).opacity)"""
        )
        check("closing cards are fully visible at the end",
              all(abs(float(o) - 1) < 0.01 for o in mini_op), sorted(set(mini_op)))

        # --- finder ---------------------------------------------------------
        page.evaluate("scrollTo(0,0)")
        page.wait_for_timeout(300)
        page.keyboard.press("/")
        page.wait_for_timeout(500)
        check("'/' opens the finder", page.evaluate("document.getElementById('finder').classList.contains('open')"))
        check("the finder puts focus in its input",
              page.evaluate("document.activeElement && document.activeElement.id === 'finderInput'"))
        page.fill("#finderInput", "putu")
        page.wait_for_timeout(400)
        check("typing filters the class list",
              page.evaluate("document.querySelectorAll('#finderList .finder-item').length") > 0,
              page.evaluate("document.querySelectorAll('#finderList .finder-item').length"))
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        page.wait_for_timeout(700)
        chosen = page.evaluate("document.getElementById('profileName').textContent.trim()")
        check("ArrowDown + Enter opens the selected classmate",
              page.evaluate("document.getElementById('profile').classList.contains('open')") and bool(chosen),
              chosen)
        check("the opened profile is a Putu",
              chosen.startswith(("I Putu", "Ni Putu")), chosen)

        # --- profile --------------------------------------------------------
        thumbs = page.evaluate("document.querySelectorAll('#profileThumbs button').length")
        check("profile shows both portraits as thumbs", thumbs == 2, thumbs)
        page.click("#profileFlip")
        page.wait_for_timeout(300)
        check("the flip control reports its state",
              page.evaluate("document.getElementById('profileFlip').getAttribute('aria-pressed')") == "true",
              page.evaluate("document.getElementById('profileFlip').getAttribute('aria-pressed')"))
        before = page.evaluate("document.getElementById('profileImg').getAttribute('src')")
        page.click("#profileFlip")
        page.wait_for_timeout(300)
        after = page.evaluate("document.getElementById('profileImg').getAttribute('src')")
        check("flipping actually swaps the photograph", before != after, f"{before} -> {after}")
        name0 = page.evaluate("document.getElementById('profileName').textContent")
        page.click("#profileNext")
        page.wait_for_timeout(400)
        name1 = page.evaluate("document.getElementById('profileName').textContent")
        check("'Next classmate' advances", name0 != name1, f"{name0} -> {name1}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        check("Escape closes the profile",
              not page.evaluate("document.getElementById('profile').classList.contains('open')"))

        # --- lightbox -------------------------------------------------------
        page.evaluate("document.querySelector('.plate').scrollIntoView({block:'center'})")
        page.wait_for_timeout(500)
        page.evaluate("document.querySelector('#galRow1 .plate').click()")
        page.wait_for_timeout(400)
        check("a gallery frame opens the lightbox",
              page.evaluate("document.getElementById('lightbox').classList.contains('open')"))
        lb0 = page.evaluate("document.getElementById('lbImg').getAttribute('src')")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(400)
        lb1 = page.evaluate("document.getElementById('lbImg').getAttribute('src')")
        check("ArrowRight moves to the next plate", lb0 != lb1, f"{lb0} -> {lb1}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # --- filters --------------------------------------------------------
        page.evaluate("document.querySelector('.filters').scrollIntoView({block:'center'})")
        page.wait_for_timeout(400)
        page.click('[data-filter="committee"]')
        page.wait_for_timeout(400)
        shown = page.evaluate(
            """[...document.querySelectorAll('.pcard')].filter(c=>c.getBoundingClientRect().height>0).length"""
        )
        check("the committee filter leaves 4 cards", shown == 4, shown)
        pressed = page.evaluate("""[...document.querySelectorAll('.filter')].map(b=>b.getAttribute('aria-pressed'))""")
        check("the active filter is marked for assistive tech",
              pressed.count("true") == 1 and pressed[1] == "true", pressed)
        page.click('[data-filter="all"]')
        page.wait_for_timeout(400)
        check("clearing the filter restores all 20",
              page.evaluate("""[...document.querySelectorAll('.pcard')].filter(c=>c.getBoundingClientRect().height>0).length""") == 20)

        # --- layout / a11y --------------------------------------------------
        for w in (320, 390, 820, 1440):
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(500)
            over = page.evaluate(
                "(document.documentElement.scrollWidth - document.documentElement.clientWidth)"
            )
            check(f"no horizontal overflow at {w}px", over <= 0, over)

        page.set_viewport_size({"width": 375, "height": 812})
        page.wait_for_timeout(600)
        small = page.evaluate(
            """[...document.querySelectorAll('a,button')].filter(e=>{
                 const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
                 return r.width>0 && r.height>0 && (r.width<24 || r.height<24)
                   && s.visibility!=='hidden' && s.display!=='none' && !e.closest('[aria-hidden="true"]');
               }).map(e=>e.tagName+'.'+(e.className||''))"""
        )
        check("no visible target under 24px (WCAG 2.5.8)", not small, small[:5])

        unnamed = page.evaluate(
            """[...document.querySelectorAll('a[href],button')].filter(e=>{
                 if (e.closest('[aria-hidden="true"]')) return false;
                 if (e.getAttribute('aria-label') || e.getAttribute('title')) return false;
                 if ((e.innerText||'').trim()) return false;
                 const img = e.querySelector('img[alt]:not([alt=""])');
                 return !img;
               }).map(e=>e.tagName+'.'+(e.className||''))"""
        )
        check("every reachable control has an accessible name",
              not unnamed, unnamed[:5])

        check("document language is set", page.evaluate("document.documentElement.lang") == "en",
              page.evaluate("document.documentElement.lang"))
        check("exactly one h1", page.evaluate("document.querySelectorAll('h1').length") == 1)

        # --- reduced motion -------------------------------------------------
        page.emulate_media(reduced_motion="reduce")
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1000)
        reduced = page.evaluate(
            """(()=>{const vis=el=>{const s=getComputedStyle(el);
                 return s.opacity!=='0' && s.visibility!=='hidden' && s.display!=='none';};
                 const cards=[...document.querySelectorAll('.pcard')];
                 const plates=[...document.querySelectorAll('.plate')];
                 return {cards:cards.length, cardsVisible:cards.filter(vis).length,
                         plates:plates.length, platesVisible:plates.filter(vis).length,
                         running:document.getAnimations().filter(a=>a.playState==='running').length,
                         marquee:getComputedStyle(document.querySelector('.marquee-row .track')).animationName,
                         grain:getComputedStyle(document.querySelector('.grain')).display};})()"""
        )
        check("reduced motion keeps all 20 wall cards visible",
              reduced["cardsVisible"] == reduced["cards"] == 20, reduced)
        check("reduced motion keeps all 72 gallery frames visible",
              reduced["platesVisible"] == reduced["plates"] == 72, reduced)
        check("reduced motion stops every animation", reduced["running"] == 0, reduced["running"])
        check("reduced motion stops the marquees", reduced["marquee"] == "none", reduced["marquee"])
        check("reduced motion hides the grain layer", reduced["grain"] == "none", reduced["grain"])
        page.emulate_media(reduced_motion=None)

        # --- first paint payload, measured not estimated ---------------------
        page.goto("about:blank")
        sizes = {}
        page.on("response", lambda r: sizes.__setitem__(r.url, r.headers.get("content-length")))
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1200)
        total = sum(int(v or 0) for v in sizes.values())
        images = sum(int(v or 0) for u, v in sizes.items() if u.endswith((".webp", ".jpg")))
        print(f"     first paint: {total/1024:.1f} KB over {len(sizes)} responses ({images/1024:.1f} KB media)")
        check("first paint stays under 1.5 MB", 0 < total < 1536 * 1024, f"{total/1024:.1f} KB")

        check("no console errors", not console_errors, console_errors[:3])
        check("no failed requests", not failed_requests, failed_requests[:3])

        third_party = sorted({u.split("/")[2] for u in requests if "://" in u and not u.startswith(URL)})
        check("nothing is loaded from a third party (page works offline)",
              not third_party, third_party)
        check("the self-hosted font is actually used",
              page.evaluate("document.fonts.check('400 16px Outfit')"))
        browser.close()
finally:
    server.shutdown()
    server.server_close()

print()
print("PASS" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)