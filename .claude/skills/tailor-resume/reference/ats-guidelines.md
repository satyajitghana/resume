# ATS guidelines (distilled, 2024–2026)

Keep all of these true when tailoring. Sources: Jobscan, Indeed, Teal, Kickresume.

## Structure & format
- Single column. No tables/text-boxes/sidebars for layout (parsers read top-to-bottom,
  left-to-right and interleave columns into nonsense).
- Real, selectable text — never text rendered as an image/outline.
- Standard headings only: **Experience / Work Experience, Education, Skills, Summary,
  Projects, Certifications**. No cute headings.
- Contact details (name, email, phone, location, links) in the **body**, not in a page
  header/footer region — those layers are routinely skipped.
- Embed fonts (Tectonic does this). Body 10–12 pt, headings larger.
- Round `•` bullets that are real glyphs (so they extract). No icons standing in for words.
- ASCII-safe symbols: write `+/-`, `x`, `%` as text; avoid `±`, `×`, smart quotes, emojis,
  degree/math symbols (they can decode to garbage / PUA).
- `Mon YYYY` dates (e.g. `Apr 2023 – Present`), consistent throughout; include the month.

## Links
- Show the human-readable URL as the visible text AND hyperlink it
  (`\href{https://linkedin.com/in/...}{linkedin.com/in/...}`). No "click here", no shorteners.

## Content & keywords
- Mirror the JD's exact hard skills, tools, and (where honest) the role title.
- Spell out an acronym with its full term at least once.
- Quantify achievements (numbers, %, scale) — only true ones.
- Skills as comma- or pipe-separated text on single lines, never a grid.

## Submission
- Submit the **`-ats.pdf`** (no background watermark) to ATS/portals; the watermarked
  display PDF is for humans/portfolio.
- Verify with `scripts/ats_check.py` (target ≈ 100; for a specific JD, aim for ≥ 75–80%
  keyword overlap without stuffing).

## Honesty
Never add skills/experience the candidate lacks. Re-emphasize and re-word true content;
record genuine gaps in the match report rather than papering over them.
