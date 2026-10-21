# DESIGN.md — FORSHA 7 v3

Source of truth for the current page. Read this before changing the look.

## 0. Design read

A class keepsake for twenty people at Bali Crystal College, class of 2026. The
audience opens it on a phone, looks for their own name, and sends it to their
parents. The page has to feel like an event, but finding a name has to stay
instant.

v3 is a deliberate move away from the quiet editorial v2. The reference is the
dark cinematic template language of 21st.dev's gallery (Mosa-style): one big
scene, layered detail, glass controls, real faces, one gold accent. The scene is
built from the class's own portraits, not stock photography.

## 1. Concept: The Corridor

Front Office and Housekeeping are hospitality disciplines. A hotel corridor is
their world. The hero is a dark corridor lined with framed class portraits,
ending in a glowing class pass. The pass is the door into the wall.

- One dominant scene, then layered details. Not a field of unrelated widgets.
- Every face on the page is a real classmate. No stock people, no invented data.
- Gold is the one accent: the pass edge, the active state, the action.
- Cream cards are the photo's own white background turned into an object.

## 2. Tokens

| Token | Value | Role |
|---|---|---|
| `--ink` | `#04070d` | Page ground |
| `--navy` | `#071a31` | Panels, nav |
| `--navy-3` | `#0d2444` | Raised panel |
| `--gold` | `#c9a227` | Accent, active, key word |
| `--gold-2` | `#e8cd7a` | Hover, small highlights |
| `--text` | `#f4f5f7` | Primary text |
| `--muted` | `#93a0b4` | Secondary text |
| `--card` | `#f2eddf` | Portrait cards, class pass |
| `--card-ink` | `#0a1524` | Text on cream |

Surfaces are separated by tone, not by visible borders. Glass is used for
controls over the scene (nav pill, buttons, finder); it is not used to decorate
plain sections.

## 3. Type

- Outfit only, weights 300–700. One family, weight and scale do the work.
- Display: `clamp(36px, 4.8vw, 68px)` section heads; hero `clamp(46px, 7vw, 104px)`.
- Body: 15–19px, line-height 1.55–1.65.
- Names on cards: 15–19px, sentence case, real spelling.
- Small functional labels: 9–11px, uppercase, only for metadata (roles, card
  numbers, section kickers). Never as a decorative eyebrow above every heading.
- No second typeface. No serif accent word.

## 4. Layout

- One 1320px frame, 90vw on small screens.
- Sections: hero, wall, disciplines, plates, about, close.
- The wall is a 5 / 4 / 3 / 2 column grid. Cards are equal height per row; the
  foot sits at the bottom.
- Plates are two full-bleed marquee rows, opposite directions. This is the one
  intentionally loud section.
- The close assembles twenty mini cards into a seven. That is the page's
  signature scroll moment.
- The Cinema Reel and the close share one glyph and one formation routine: the
  reel's seven is the same twenty cards on the same pattern, at projector scale.
- Mobile is its own composition: corridor hidden, blurred portrait field behind
  the copy, the pass above the title, two-column wall, single-column plates.

## 5. Motion

GSAP 3.13 (core + ScrollTrigger) and the Outfit woff2 files are vendored in
`vendor/`. No build step, no CDN, no third-party request.

| Moment | What it does |
|---|---|
| Hero load | corridor lights up, pass settles, title lines rise, nav/chips stagger |
| Hero exit | camera push, copy fades, pass lifts |
| Headings | per-word reveal on first view |
| Wall | cards assemble on scroll |
| Counters | 20 / 02 / 36 / 01 count once on view |
| Close | twenty cards converge into the number 7 |
| Cinema Reel | one continuous sequence: identity card, twenty portraits (a portrait-to-portrait crossfade mid-scene), the seven at the end |
| Micro | pass tilt, card tilt + spotlight, magnetic CTAs, cursor glow, marquees |

Rules:
- Transform and opacity only.
- Nothing essential is hidden if GSAP fails.
- No CSS `scroll-behavior: smooth` — it breaks ScrollTrigger measurement. Anchor
  smoothness comes from `scrollTo({behavior:"smooth"})`.
- `prefers-reduced-motion: reduce` removes all travel: static hero, no marquee
  movement (hero, menu and gallery rows), the 7 already formed, all content
  visible.
- Under reduced motion the Cinema Reel still runs, but as cuts: no travel, no
  reveal delays (animation and transition delays collapse to zero), and the final
  seven is placed statically. Nothing is left animating.
- No sound, no scroll hijack on touch, no custom cursor on touch.

## 6. Interaction

- **Find your name**: command palette (`/` or the nav button). Type, arrow,
  Enter. This is the utility the page exists for.
- **Wall card**: hover flips to the second portrait; click opens the profile.
  On touch, tap opens the profile; the profile shows both portraits.
- **Profile**: dialog with focus trap, Esc, a sticky close on mobile, two
  portrait thumbnails, next classmate.
- **Plates**: full-image lightbox with arrows and Esc.
- **Filters**: Everyone / Committee / Members, live count, `aria-pressed`.
- **Cinema Reel**: opens from the hero or the menu overlay. One overlay, one
  continuous sequence, no control bar and no progress UI. Space or a tap holds
  it, arrows step (clamped at both ends, no wrap), swipe on touch, Esc exits; the
  end offers Replay and Close. The `#reel` hash deep-links to it, and closing
  restores the previous hash.

## 7. Accessibility

- Real `<button>` / `<a>` elements, visible `:focus-visible`.
- Dialogs use `role="dialog"`, `aria-modal`, `aria-labelledby`, focus trap,
  `inert` on the page behind, and focus restoration.
- Images have alt text; decorative scene images are empty alt inside
  `aria-hidden` containers.
- Every reachable control has an accessible name. The icon-only find button
  carries `aria-label="Find your name"` because its visible label is hidden
  under 960px.
- Every visible target is at least 24x24 CSS px (WCAG 2.5.8); primary actions
  are 40–48px tall. Measured at 375px, the smallest is 29px.
- The Cinema Reel focuses its own dialog root (not a control), so Space holds the
  reel instead of activating Close, and the dialog is what a screen reader
  announces.
- Contrast: body text on dark is ≥ 7:1; cream cards use navy ink.
- The page works without JS above the fold; the wall, plates and close are
  rendered from `PEOPLE` (same decision as v2, documented in PRD).

## 8. Performance

- 36 portrait files, `srcset` with 400/800/1125 widths, `loading="lazy"` below
  the fold.
- Hero corridor images are `fetchpriority="low"`; the pass and title lead.
- Full-size photos load only in the profile and lightbox.
- Cinema Reel portraits attach on demand: all 22 scenes exist in the DOM from the
  start, but each frame keeps its `data-src` until its scene is warmed, so the
  reel adds no image request until it is opened (the first three portraits lead).
- Everything is same-origin: GSAP, ScrollTrigger, the font and every image.
  Nothing is fetched from a third party, so the page works offline.
- Measured on a cold cache:
  - 1440x900: 480 KB total, 250 KB of images, 36 unique files.
  - 390x844: 455 KB total, 224 KB of images, 32 files; lazy loading still defers
    14 images that only load on scroll.
- No console errors, no failed requests.
- The font is a preloaded 32 KB woff2 (latin) plus a 15 KB latin-ext fallback.

## 9. Verification

`tools/verify_motion.py` re-asserts the claims above in a real browser: motion
(GSAP/ScrollTrigger land where they should), image weights and candidate
selection, accessible names and target sizes, the closing formation, the Cinema
Reel (including proof that its seven is the same glyph as the closing one),
reduced motion, horizontal overflow at 320/390/820/1440, and third-party
requests. 92 checks, exits non-zero on failure. Run it before shipping a change.

## 10. Content rules

- Real names, real roles, real numbers. Two classmates have no photos yet; they
  render as initial cards, and the copy never apologises for it.
- No invented quotes, statistics, clients or reviews.
- English UI copy; Indonesian role names stay as they are (`Korti`, `Anggota`).
- No em-dashes in page copy.

## 11. If someone edits this

Keep the corridor scene and the wall. If a change makes the page more impressive
but slower to find a name, it is wrong. If it makes a classmate feel seen, it is
probably right.
