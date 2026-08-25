# Modern Alpine design system

Modern Alpine is a quiet, 2026-leaning hiking interface on a soft warm ground: Manrope for both headings and body, bold compact headings, clear metadata, hairline rules, and color applied as restrained gold accents. Surfaces stay light and functional, with restrained borders, crisp controls, and enough weight for Cyrillic text to read cleanly on mobile.

## How to use this

- Link the one stylesheet from every page — `<link rel="stylesheet" href="styles.css">` (adjust the relative path) — and take every color, font, spacing, radius and shadow from its variables (`var(--color-*)`, `var(--font-*)`, `var(--space-*)`, `var(--radius-*)`, `var(--shadow-*)`). Never hard-code a hex, a font name or a px value the tokens already carry.
- Build with the classes below rather than inventing parallel ones; the component pages are plain HTML, so view source and copy the markup.
- `templates/` holds starting points a consuming project can copy whole.
- The whole system was derived from `theme.json`. To change the look, edit the tokens at the top of `styles.css` — every page, the thumbnail and this guide read from them — and keep `theme.json` and the written guidance in step so they don't drift from what the CSS actually does.

## Direction

Functional, outdoorsy, and modern, while keeping the original warm color mood. Keep layouts scan-friendly, use hairline dividers (`var(--color-divider)`) between major sections, and let bold headings establish hierarchy. Apply color as borders, rules, markers, and small UI accents rather than large decorative fills. Buttons are outlined or ghosted, with compact geometry and clear hover states.

## Color

A light ground (`--color-bg` #f3f2f2) with `--color-text` #201f1d, a gold accent #b68235, and a secondary warm accent #ac803e. Each role carries a 100-900 tonal ramp (`--color-neutral-100` ... `--color-accent-2-900`) so tint, border, and pressed states stay consistent. Use light steps (100-300) for tints and hovers, 500/600 for the base accent, and dark steps (700-900) for readable text on tinted fills.

## Type

Manrope is used for both headings and body text, loaded as `--font-heading` / `--font-body`. Headings use the bold token (`--font-heading-weight`) and body copy defaults to a medium-weight cut for readability. Avoid decorative italics for interface text; use weight, size, and muted color to create hierarchy. Numbers set tabular wherever they stand as figures or columns. Density 1.15x and the radius scale are baked into the `--space-*` / `--radius-*` tokens.

## Icons

Use Lucide icons (https://lucide.dev) throughout.

## Interaction states

Interactive states are themed, never browser defaults: give every interactive element a `:hover` tint and a pressed state from the accent ramp (one step past the base — `--color-accent-600` on a light ground, `--color-accent-400` on a dark one, or a `color-mix()` tint for outlined/ghost variants), and style keyboard focus with `:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }` — never leave the default blue focus ring.

## Components

| Class | What it is | Shown in |
| --- | --- | --- |
| `.btn` with `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-icon`, `.btn-block` | Actions — the primary is an accent outline, never a fill | components/buttons.html |
| `.tag` with `.tag-accent`, `.tag-accent-2`, `.tag-neutral`, `.tag-outline` | Small labels tinted from the ramps (mono palette: accent-2 reads the same as accent) | components/buttons.html |
| `.field` + `label`, `.input`, `.radio` + `.dot`, `.seg` + `.seg-opt` | Form fields and choices on native elements — no script | components/forms.html |
| `.card` with `.card-kicker`, `.card-title`, `.card-body`, `.card-meta`; `.elev-sm/md/lg` | Bordered, unfilled content surfaces; elevation utilities | components/cards.html |
| `.nav` + `.nav-brand` | The header bar | components/navigation.html |
| `.table` | Data tables with themed header and row rules | components/table.html |
| `.dialog-backdrop` + `.dialog` (+ `.dialog-title/-body/-actions`) | A modal at the top elevation | components/dialog.html |
| `.hr` | A hairline horizontal rule | foundations/layout.html |
| `.plate` | The image wrapper — every content photograph goes through it | foundations/image.html |

States are built in: hovers and pressed states come from the accent ramp, keyboard focus is the 2px accent `:focus-visible` ring, `::selection` is an accent tint, and disabled controls drop to 45% opacity. Don't restyle them per page. The accent-to-ground pair is tuned to at least 3:1 — enough for icons, large text and interface chrome, not for body copy — so for paragraph-size text in the accent use a deep ramp step (`--color-accent-700` on this ground) rather than the accent itself.

## Do

- Keep text scan-friendly and direct.
- Use bold headings and medium supporting copy.
- Draw with borders, rules, markers and underlines; keep large fills off the page.
- Give controls stable dimensions and enough touch target space.

## Don't

- Do not bring back serif display faces for interface hierarchy.
- Do not rely on italics for metadata.
- Do not use heavy drop shadows.
- Do not crowd Macedonian/Cyrillic labels; keep line-height comfortable.

## Files

- `styles.css` — the only stylesheet: the token sheet (`:root` variables, ramps, base type) plus the component layer. Link it from every page.
- `readme.md` — this guide.
- `theme.json` — the parameters these files were derived from (a machine-readable record of the theme).
- `thumbnail.html` — the project cover (brand mark + swatches).
- `foundations/type.html` — the type scale and the heading/body pairing at real sizes.
- `foundations/color.html` — color roles and the 100-900 tonal ramps, with usage notes.
- `foundations/layout.html` — the spacing scale, the grid and how edges are drawn.
- `foundations/icons.html` — the icon set at interface sizes, inline and in buttons.
- `foundations/image.html` — how photographs and figures are treated.
- `components/buttons.html` — buttons, icon buttons and tags in every variant and state.
- `components/forms.html` — text fields, radios and the segmented control on native elements.
- `components/cards.html` — content cards and the elevation steps.
- `components/navigation.html` — the header bar pattern.
- `components/table.html` — a data table with the themed header and row rules.
- `components/dialog.html` — a modal over its backdrop at the top elevation.
- `theme.html` — the theme's parameters rendered as a reference sheet.
- `templates/landing/` — a starter page consuming the system the intended way (`index.html`, its `ds-base.js` loader, and the vendored `image-slot.js` its photograph mounts).
- `assets/photo.jpg` — the reference photograph the imagery page treats.
