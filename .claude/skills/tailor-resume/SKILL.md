---
name: tailor-resume
description: >-
  Tailor Satyajit's LaTeX resume to a specific job description and draft a matching
  cover letter. Use when the user pastes or points to a job description / job posting
  and asks to "tailor my resume", "make a resume for this job/JD", "apply to this role",
  "write a cover letter for this", or similar. Produces a tailored ATS + display + one-page
  PDF and a cover-letter.md in applications/<company-role>/. Only for THIS resume repo.
---

# Tailor résumé + cover letter to a job description

You adapt the canonical résumé in this repo to a given job description (JD), build
tailored PDFs, and draft a cover letter — **without ever fabricating experience**.

## Inputs
The user gives a JD as pasted text, a file path, or a URL (fetch it). If essential
fields are missing (company, role title), ask once; otherwise infer and proceed.

## Hard rules
1. **Never invent** roles, employers, dates, degrees, metrics, or skills the candidate
   doesn't have. You may only re-emphasize, reorder, and re-word TRUE content from
   `src/sections/`. If the JD wants something absent, note it in the match report — do
   not add it to the resume.
2. **Mirror the JD's real keywords** (exact tools/skills/titles) wherever they are
   genuinely true of the candidate — this is what ATS keyword-matching rewards.
3. Keep every ATS rule in `reference/ats-guidelines.md` intact (single column, standard
   headings, real text, ASCII symbols, no header/footer contact, etc.).
4. The canonical `src/sections/*.tex` and `src/resume-body.tex` must stay **unchanged** —
   tailoring happens on COPIES in the application folder.

## Workflow

### 1. Analyse the JD
Extract and note: company, role title, location, seniority, must-have skills, nice-to-have
skills, key responsibilities, domain keywords, and tone (corporate / startup / research).
List the JD's top ~15 keywords.

### 2. Create the application folder
Slugify as `<company>-<role>` (lowercase, hyphens), then:
```bash
SLUG=acme-senior-ml-engineer          # example
mkdir -p applications/$SLUG/sections
cp src/sections/*.tex applications/$SLUG/sections/
```

### 3. Tailor the copies in `applications/$SLUG/sections/`
- **summary.tex** — rewrite the 2–3 line summary to lead with the role and the JD's top
  true keywords. Keep it honest and specific.
- **skills.tex** — reorder categories and items so JD-matched skills appear first; drop
  rows irrelevant to the role if space is tight. Don't add untrue skills.
- **experience.tex** — reorder bullets within each role to lead with the most
  JD-relevant, true achievements. You may re-word for keyword match. Adjust which bullets
  are wrapped in `\verbose{}` so the one-pager keeps the most JD-relevant ones.
- **education.tex** — usually unchanged.
- Choose a tailored tagline for the header (see step 4).

### 4. Build the tailored PDFs
Write temporary wrappers in `src/` that point `\secdir` at the tailored sections and set
the tagline, build from `src/` (so bundled fonts/assets resolve), copy the named PDFs into
the application folder, then remove the temp wrappers:
```bash
TAG='Senior ML Engineer \textperiodcentered\ 3D Vision \textperiodcentered\ MLOps'
for V in "ats:\\def\\ATSMODE{}" "display:" "onepager:\\def\\ONEPAGER{}"; do
  NAME=${V%%:*}; FLAG=${V#*:}
  cat > src/_app-$NAME.tex <<EOF
\\documentclass[11pt]{article}
$FLAG
\\def\\secdir{../applications/$SLUG/sections/}
\\def\\resumetagline{$TAG}
\\input{style.tex}
\\input{resume-body.tex}
EOF
  ( cd src && tectonic _app-$NAME.tex --outdir ../build )
  rm src/_app-$NAME.tex
done
cp build/_app-ats.pdf      "applications/$SLUG/$SLUG-resume-ats.pdf"
cp build/_app-display.pdf  "applications/$SLUG/$SLUG-resume.pdf"
cp build/_app-onepager.pdf "applications/$SLUG/$SLUG-resume-one-pager.pdf"
```
(Use the repo's `tectonic` — it's on PATH at `~/.local/bin`.)

### 5. Verify ATS
Run the checker on the tailored ATS PDF and confirm it still scores ~100:
```bash
uv run --no-project --with pdfminer.six --with pymupdf --with spacy \
  --with "en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" \
  python scripts/ats_check.py "applications/$SLUG/$SLUG-resume-ats.pdf"
```

### 6. Cover letter
Copy `templates/cover-letter.md` to `applications/$SLUG/cover-letter.md` and fill it in:
specific to the company and role, grounded ONLY in true achievements, weaving in 3–5 JD
keywords naturally. Keep it to ~250–350 words, confident but not boastful.

### 7. Match report
Write `applications/$SLUG/match-report.md`: JD top keywords, which are covered (and where),
which are genuine gaps, and any honesty caveats. Tell the user the ATS score and the gaps.

## Output (in `applications/<company-role>/`)
- `<slug>-resume.pdf`, `<slug>-resume-ats.pdf`, `<slug>-resume-one-pager.pdf`
- `sections/` (the tailored source)
- `cover-letter.md`
- `match-report.md`
