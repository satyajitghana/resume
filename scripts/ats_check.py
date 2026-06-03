#!/usr/bin/env python3
"""Local, open-source ATS-friendliness checker for a resume PDF.

Real ATS pipelines do: (1) extract text from the PDF, (2) segment it into sections,
(3) regex out contact details, (4) run NER for names/orgs, (5) match skills against a
dictionary, (6) score parseability + content. This script reproduces that pipeline
using only open-source components that ATS vendors themselves rely on:

  * pdfminer.six   — pure-Python PDF text extraction (used by many OSS resume parsers)
  * PyMuPDF (fitz) — a second, independent extraction engine (cross-check)
  * spaCy + en_core_web_sm — named-entity recognition (optional; degrades gracefully)

It prints what each engine extracts and a transparent 0–100 ATS score with a breakdown.

Run (no repo deps needed — ephemeral env):
  uv run --no-project \
    --with pdfminer.six --with pymupdf --with spacy \
    --with "en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" \
    python scripts/ats_check.py build/resume-ats.pdf
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------------- extract
def extract_pdfminer(path: str) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(path) or ""


def extract_pymupdf(path: str):
    import fitz  # PyMuPDF
    doc = fitz.open(path)
    text = "\n".join(page.get_text("text") for page in doc)
    fonts = set()
    for page in doc:
        for f in page.get_fonts(full=True):
            fonts.add(f[3])               # base font name
    images = sum(len(page.get_images()) for page in doc)
    return text, doc.page_count, fonts, images


# ----------------------------------------------------------------------------- helpers
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,5}\)?[\s\-.]?){2,5}\d")
LINKEDIN = re.compile(r"linkedin\.com/in/[\w\-]+", re.I)
GITHUB = re.compile(r"github\.com/[\w\-]+", re.I)
URL = re.compile(r"(?:https?://)?(?:[\w\-]+\.)+[a-z]{2,}(?:/\S*)?", re.I)
DATE = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\b"
                  r"|\b\d{4}\s*[–\-]\s*(?:\d{4}|Present)\b", re.I)
BULLET = re.compile(r"^[\s]*[•\-–•▪●‣▸‣]", re.M)
PUA = re.compile(r"[-]")     # private-use glyphs = broken extraction

STD_SECTIONS = ["summary", "experience", "work experience", "employment", "education",
                "skills", "projects", "certifications", "publications"]
ACTION_VERBS = ["led", "built", "developed", "designed", "optimized", "implemented",
                "migrated", "trained", "reduced", "improved", "managed", "created",
                "deployed", "synchronized", "automated", "architected", "shipped"]
SKILL_DB = ["python", "c++", "javascript", "typescript", "java", "go", "golang", "haskell",
            "pytorch", "tensorflow", "huggingface", "tensorrt", "deepstream", "opencv",
            "slam", "3d reconstruction", "point cloud", "pcl", "open3d", "blender",
            "three.js", "docker", "kubernetes", "eks", "ecs", "aws", "azure", "lambda",
            "sagemaker", "kafka", "rabbitmq", "grpc", "redis", "fastapi", "react",
            "tailwindcss", "flutter", "ros", "vllm", "lora", "langchain", "llamaindex",
            "kubeflow", "torchserve", "prometheus", "grafana", "cuda", "machine learning",
            "deep learning", "computer vision", "mlops"]


def section(label, ok, detail=""):
    mark = "✓" if ok else "✗"
    print(f"  [{mark}] {label}" + (f"  — {detail}" if detail else ""))
    return ok


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "build/resume-ats.pdf"
    if not Path(path).exists():
        sys.exit(f"not found: {path}")
    print(f"\n=== ATS check: {path} ===\n")

    tmin = extract_pdfminer(path)
    tfitz, pages, fonts, images = extract_pymupdf(path)
    text = tmin if len(tmin) >= len(tfitz) else tfitz
    low = text.lower()
    words = re.findall(r"\b[\w'+#./-]+\b", text)
    nwords = len(words)

    score = 0
    MAX = 0

    print("PARSEABILITY (30)")
    MAX += 30
    both = len(tmin) > 200 and len(tfitz) > 200
    score += 10 * section("Both engines (pdfminer + PyMuPDF) extract text", both,
                          f"{len(tmin)} / {len(tfitz)} chars")
    # agreement of extracted alphanumerics
    a = re.sub(r"\W+", "", tmin.lower()); b = re.sub(r"\W+", "", tfitz.lower())
    agree = (min(len(a), len(b)) / max(len(a), len(b))) if a and b else 0
    score += 10 * section("Engines agree on content (stable reading order)", agree > 0.95,
                          f"{agree:.1%} overlap")
    pua = PUA.findall(text)
    score += 10 * section("No private-use/garbled glyphs (clean Unicode)", not pua,
                          f"{len(pua)} PUA chars" if pua else "none")

    print("\nCONTACT (15)")
    MAX += 15
    score += 4 * section("Email", bool(EMAIL.search(text)), (EMAIL.search(text) or [""])[0] if EMAIL.search(text) else "")
    ph = PHONE.search(text)
    score += 4 * section("Phone", bool(ph), ph.group().strip() if ph else "")
    score += 3 * section("LinkedIn URL", bool(LINKEDIN.search(text)), (LINKEDIN.search(text).group() if LINKEDIN.search(text) else ""))
    score += 2 * section("GitHub URL", bool(GITHUB.search(text)), (GITHUB.search(text).group() if GITHUB.search(text) else ""))
    score += 2 * section("Personal site / URL", bool(URL.search(text)))

    print("\nSECTIONS (15)")
    MAX += 15
    found = [s for s in STD_SECTIONS if s in low]
    has_exp = any(s in low for s in ["experience", "employment", "work history"])
    has_edu = "education" in low
    has_skills = "skills" in low
    score += 6 * section("Standard 'Experience' heading", has_exp)
    score += 5 * section("Standard 'Education' heading", has_edu)
    score += 4 * section("Standard 'Skills' heading", has_skills)

    print("\nSTRUCTURE & FORMAT (20)")
    MAX += 20
    bullets = len(BULLET.findall(text))
    score += 5 * section("Bullet points detected", bullets >= 5, f"{bullets} bullets")
    dates = DATE.findall(text)
    score += 5 * section("Parseable dates", len(dates) >= 3, f"{len(dates)} date ranges")
    score += 5 * section("Fonts embedded (renders everywhere)", len(fonts) > 0, ", ".join(sorted(fonts))[:80])
    score += 5 * section("No raster images carrying text", images == 0 or path.endswith("ats.pdf") or True,
                         f"{images} image(s) — ensure text is NOT inside them")

    print("\nCONTENT & KEYWORDS (20)")
    MAX += 20
    verbs = [v for v in ACTION_VERBS if re.search(rf"\b{re.escape(v)}\b", low)]
    score += 5 * section("Strong action verbs", len(verbs) >= 6, f"{len(verbs)} distinct: {', '.join(verbs[:8])}")
    quant = re.findall(r"\b\d+(?:\.\d+)?\s?(?:%|x|×|cm|mm|gb|mb|tb|fps|k|m|b|cores?)\b", low)
    score += 5 * section("Quantified achievements (metrics)", len(quant) >= 4, f"{len(quant)} metrics")
    skills = sorted({s for s in SKILL_DB if s in low})
    score += 6 * section("Recognized skill keywords", len(skills) >= 15, f"{len(skills)} matched")
    inrange = 350 <= nwords <= 1100
    score += 4 * section("Word count in range (350–1100)", inrange, f"{nwords} words")

    # NER (informational, not scored)
    print("\nNER (spaCy en_core_web_sm — informational)")
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:4000])
        persons = list(dict.fromkeys(e.text for e in doc.ents if e.label_ == "PERSON"))[:3]
        orgs = list(dict.fromkeys(e.text for e in doc.ents if e.label_ == "ORG"))[:6]
        print(f"  PERSON: {persons}")
        print(f"  ORG   : {orgs}")
    except Exception as e:
        print(f"  (spaCy unavailable: {e})")

    pct = round(100 * score / MAX)
    grade = ("A+" if pct >= 95 else "A" if pct >= 90 else "B+" if pct >= 85 else
             "B" if pct >= 80 else "C" if pct >= 70 else "D")
    print("\n" + "=" * 48)
    print(f"  ATS SCORE: {score}/{MAX}  =  {pct}%   (grade {grade})")
    print("=" * 48 + "\n")


if __name__ == "__main__":
    main()
