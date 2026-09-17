# PRD — FORSHA 7 v2

Status: phases 1-5 done on branch `v2`. P1 and P6 remain open.

Verified by `tools/verify_motion.py` (18 checks, PASS): hero payload measured 30.2 KB,
desktop height 9.88 screens, 0 tap targets under 44px at 375, 0 console errors,
58 of 59 rendered images have srcset (the 59th is `#lbImg` by design).
Baseline: commit `df75c50`. `index.html` 975 lines / 57KB, `DESIGN.md` 133 lines,
`img/` 1.5 MB across 72 files. Zero dependencies, no build step.

Read `DESIGN.md` first. It holds the design contract (dials, palette, banned
patterns, accessibility floor). This document holds the work, not the taste.

## Goal

Ship the version that is fast on a phone and correct when someone shares the
link in a WhatsApp group. Nothing on this list is a new feature; it is the set
of things the page currently gets wrong or leaves unfinished.

## Non-goals

- No framework, no bundler, no npm. The page stays one HTML file plus images.
- No analytics, no cookie banner, no contact form.
- No new sections. The page got 4 screens shorter on purpose; it does not grow back.

## Metrics

| Metric | Now | Target |
|---|---|---|
| Hero images on first paint (mobile 375px) | 42 KB (4 hero thumbs, 525x700) | < 90 KB |
| Content images with `srcset` | 0 | 100% except `#lbImg` (single `src` by design) |
| Console errors | 0 | 0 |
| Desktop height | unmeasured (no baseline tool) | must not grow |
| Tap targets under 44px | 0 | 0 |
| Placeholder metadata | canonical + og:image + og:url | all real |

## Work

### P1 — Two members have no photos (blocked on assets)

#12 I Made Yogi Tresna and #14 I Nyoman Giong Arismawan fall back to initial
letters. In a class page, two people rendered as letters among eighteen faces
is the single most visible defect. Not fixable in code: the photos do not exist.

Every other item on this list is cosmetic next to this one. If the photos arrive,
they are processed (three widths each, same as P2) and dropped into `img/` as
`12a/12b/12a-t/12b-t.webp`. The `PEOPLE` array already handles presence and
absence, so no code changes.

### P2 — Responsive images

Photos are 1125x1500 full and 525x700 thumbnail. A 375px viewport needs roughly
340px, so every phone currently downloads more pixels than it can display, in
views where 4 to 32 photos are on screen at once.

Add intermediate widths and let the browser pick:

- `-t` files stay as the small end but are regenerated at 400w
- new `-m` variant at 800w (new files: 72 -> 144, `img/` ~1.5 MB -> ~2.4 MB)
- full file stays 1125w

Wire `srcset` and `sizes` on every content image. The hero gets
`fetchpriority="high"` and no `loading="lazy"`; everything below the fold keeps
`loading="lazy"` and `decoding="async"`.

### P3 — Image priority

Four hero faces are the largest contentful paint. They currently queue behind
whatever the browser resolves first and there are no `preload` hints. Give them
`fetchpriority="high"` plus the matching `srcset` so the preloaded candidate is
the same one the browser would have chosen.

### P4 — Metadata

- `canonical` and `og:url`: `https://forsha7class.github.io/FORSHA7/`
  (canonical currently points at the wrong host: `https://forsha7.example/`)
- `og:image`: absolute URL to a real 1200x630 crop, not a relative path to a
  3:4 portrait. Generate the crop once and commit it.
- `twitter:image` alongside `twitter:card`
- keep `og:title` / `og:description` as they are; both are already accurate

Why it matters: the link gets shared into group chats. A relative `og:image`
resolves differently per crawler, and a 3:4 portrait gets cropped badly by every
preview card.

### P5 — Alt text

A gallery frame has both a wrapper `aria-label` ("Perbesar foto X, 1 dari 2") and
an `img alt="X"`, so the name is announced twice per frame, twice per person.
Drop the name from the wrapper label (keep "Perbesar foto, 1 dari 2"); number the
image alt ("X, foto 1 dari 2"). The list
avatars keep `alt=""` (correct: the name is adjacent text, otherwise it is read
twice), and the hero faces keep `alt=""` (decorative, parent is `aria-hidden`).

### P6 — Verify the motion actually runs — DONE

Resolved with Playwright (fresh venv, no repo dependency) driving the bundled
Chromium under `xvfb-run`. `tools/verify_motion.py` is the check; it exits
non-zero if any claim fails. Photo drift was sampled at two instants
(`translateY(18px)` -> `translateY(-12.14px)`), scroll reveals fire, 29 animations
run. Two checker bugs were found by running it and are noted in the commit.

### P6 (original write-up, kept for context)

Per-word heading reveal, `animation-timeline` scroll reveals, photo drift, the
counter, the marquee, and hero face drift have never been observed moving. The
headless browser reports `visibilityState: hidden`, so `IntersectionObserver`
never fires and the animation clock stays at 0. The CSS is correct (proven by
`getAnimations().finish()` landing on the right end state) but "correct CSS" and
"the user sees motion" are different claims.

Fix by running a real render: `xvfb-run` with a headed Chromium. `xvfb-run` is
present on the target box; `chromium` is NOT installed, so installing it is a
prerequisite of this phase. Otherwise the user opens the page and reports.
Until one of those happens, treat this as open.

### P7 — Gallery count claim

The heading says "Twenty names. One identity." and the gallery shows 16 people
because two have no photos. Once P1 lands this resolves itself. Until then, do
not add a caveat, do not change the copy: an apology on the page is worse than
the gap, and the gap is closing.

### P8 — A 404 page

GitHub Pages serves its own 404 (white, unbranded) for any mistyped path. One
`404.html` at the repo root, sharing the palette and a single link back home.
Cheap, and the link circulates in chat.

### P9 — No-JS fallback: REJECTED

All roster and gallery content is rendered by JS from the `PEOPLE` array. With JS
off, the page below the hero is empty.

Rejected deliberately. A static fallback means writing 20 names and 18 photo
tiles as HTML *in addition to* the array, and the two copies drift the moment
anyone edits a name. That is a permanent maintenance cost paid by whoever edits
this next, to serve a case (JS disabled) that does not occur for the audience
this page has. The array already keeps one source of truth; duplicating it to
be robust against a scenario nobody hits makes the page worse for everyone who
does use it.

If it ever needs to change: the correct fix is not a second copy in HTML, it is
`<noscript>` pointing at a plain text list generated at build time, which means
adding a build step, which contradicts the non-goals.

### P10 — README

The README is 9 bytes. Replace it with: what the page is, how to open it
locally (`python3 -m http.server`, no build), where the content lives (the
`PEOPLE` array), how to add a photo (four files, naming convention), and a
pointer to `DESIGN.md` as the design contract.

## Order

| Phase | Content | Commit |
|---|---|---|
| 1 | P2 + P3: widths, `srcset`, priority | `perf: responsive images` |
| 2 | P4: canonical, og:url, absolute og:image, twitter:image, 1200x630 crop | `fix: metadata` |
| 3 | P5: alt text | `fix: a11y` |
| 4 | P8 + P10: 404 page, real README | `docs: readme and 404` |
| 5 | P6: verify motion under a real renderer | `chore: verify motion` |
| — | P1: when the two photos arrive | `feat: members 12 and 14` |

Each phase commits on its own so any one can be reverted without touching the
others. Nothing here is allowed to increase page height.

## Open

- P1 is blocked on the user supplying two photos. Every other item is done.
- Verify after any change: `PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright \
  xvfb-run -a /tmp/pwv/bin/python tools/verify_motion.py`
