# DESIGN.md — FORSHA 7

Source of truth for this page. Built with the `design-taste-frontend` (anti-slop)
skill, which enforces a specific premium aesthetic instead of defaulting to the
LLM's usual output. Anything not listed here is a free choice.

## 0. Design read

> Reading this as: a class-identity page for classmates and their families, with a
> dark editorial language, leaning toward native CSS (no framework, no build step)
> plus variable fonts and scroll-driven reveals.

Audience picks the aesthetic. This is not a B2B product page and not a design
portfolio. It is a keepsake: people will open it on a phone, look for their own
name and their own photo, and send it to their parents. That means it has to be
fast, legible at arm's length, and it has to make each person feel individually
seen. Ceremony over density.

## 1. Dials

| Dial | Value | Why |
|---|---|---|
| `DESIGN_VARIANCE` | 8 | Asymmetric layouts. Twenty people is not a symmetric set; forcing symmetry makes them look like a spreadsheet. |
| `MOTION_INTENSITY` | 6 | Fluid CSS motion. Enough to feel alive, not enough to get in the way of finding your own name. |
| `VISUAL_DENSITY` | 4 | 36 photos need room. Every photo is someone's face, not a data point. |

Redesign-overhaul mode: the content and names stay, the visual language is replaced.

## 2. Stack

- One `index.html`. No framework, no bundler, no npm, no build step.
- No animation library. `MOTION_INTENSITY: 6` is the "fluid CSS" band, so CSS
  transitions, `animation-timeline: view()`, and `IntersectionObserver` cover it.
  Framer Motion / GSAP are for stacks that already ship a JS runtime; adding one
  here would cost a network round trip for what a `cubic-bezier` does for free.
- Fonts: Google Fonts `<link>` with `preconnect`. Self-hosting would be better for
  production, but this page has no build step to run `next/font` in.

## 3. Typography

| Role | Font | Notes |
|---|---|---|
| Display | Outfit 600/700 | Sans display. The skill bans reaching for a serif just because the page is creative. |
| Body | Outfit 400/500 | One family, weight-driven hierarchy. |
| Numerals | `font-variant-numeric: tabular-nums` | Names and counts line up. |

Banned here: `Inter` (the default nobody chose), `Fraunces` and `Instrument Serif`
(the two LLM-favourite display serifs), `Times New Roman`, `Georgia`.

Rules:
- Negative tracking on large display text, positive tracking on small labels.
- Emphasis is italic or bold of the *same* family. Never a serif word dropped into
  a sans headline.
- Body max-width 65ch.
- Body text never below 14px, labels never below 11px.
- `text-wrap: balance` on headings to kill orphaned last words.

## 4. Color

One accent. Everything else is neutral.

| Token | Value | Role |
|---|---|---|
| `--ink` | `#04070d` | Page background. Off-black, never `#000000`. |
| `--surface` | `#0a1424` | Raised surfaces, nav. |
| `--line` | `rgba(255,255,255,.10)` | Hairlines, borders. |
| `--text` | `#f4f5f7` | Primary text. Off-white, never `#ffffff`. |
| `--muted` | `#93a0b4` | Secondary text. |
| `--accent` | `#c9a227` | The single accent: gold. Saturation ~72%, under the 80% ceiling. |

The gold is the one luxury signal on the page, so it is rationed: one word per
heading, active states, and nothing else. If gold is on every element, it stops
meaning anything.

Banned: a second accent, purple/blue "AI gradient" glow, neon outer glows,
oversaturated accents, mixing warm and cool greys.

## 5. Layout

- Asymmetric. Variance 8 means the page does not repeat one column rhythm.
- No three-equal-cards row.
- No split-header ("big headline left, small explainer paragraph right"). If a
  section needs both, the headline goes on top and the paragraph goes under it.
- At least four different layout families across the sections.
- Section padding varies by weight. Not every section is 120px.
- Shadows tinted to the background hue, never black at low opacity.
- Shapes: this page is deliberately square (radius 0) because the gold-hairline
  rectangle is the identity. That is the "documented rule" the shape-consistency
  lock allows. Do not add rounded corners to one element.

## 6. Motion

Motion must be motivated. Every animation on this page answers one question:

| Animation | Communicates |
|---|---|
| Per-word heading reveal | Hierarchy: this is the headline, read it first. |
| Card rise on scroll | Storytelling: the page is a sequence, not a wall. |
| Photo drift | Depth: the gallery is a plane, not a grid. |
| Stat count-up | Feedback: the number arrived, it is real. |
| Card tilt on hover | Feedback: this is interactive, it opens. |

No animation "because it looked cool". No `window.addEventListener('scroll')`
doing layout reads. `transform` and `opacity` only. `prefers-reduced-motion`
collapses everything to static, no exceptions.

## 7. Content

- Numbers here are real: 20 people, class 7, 2 photos each. Nothing invented.
  There is no "99.98% UPTIME" on this page and there never will be.
- Names are real classmates. No placeholder names, no stock avatars.
- Copy register is plain and warm. No "Elevate", "Seamless", "Unleash", "Next-Gen".
- Zero em-dashes. Yes, zero. Use a hyphen, a comma, or two sentences.
- No section-number eyebrows (`01 - Identity`), no `Label // Year`, no decorative
  status dots, no scroll cues, no version stamps.
- Max one eyebrow per three sections.

## 8. Accessibility (non-negotiable)

- Interactive elements are real `<button>` / `<a>`, not `<div role="button">`.
- Tap targets at least 44px on mobile.
- Visible `:focus-visible` ring on everything interactive.
- `min-h: 100dvh`, never `100vh`, so iOS Safari does not jump.
- Every image has real alt text.
- Reduced motion is honoured. Reduced transparency gets a solid fallback.
- Contrast: AA for body, AAA target for hero copy.

## 9. If someone edits this

Read section 0 first. The aesthetic is derived from who opens this page and why,
not from a style trend. If a change serves the reader who just wants to find their
own name and show their mother, it is probably right. If it makes the page more
impressive to a designer, it is probably wrong.
