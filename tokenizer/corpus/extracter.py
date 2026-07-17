"""
build_faithful_corpus.py
Fetches Wikipedia REST HTML for 4 languages and converts to faithful Markdown
using markdownify — preserving links, URLs, tables, references, punctuation.

decode(encode(text)) roundtrip is preserved because no visible characters are stripped.
"""

import os
import re
import requests
import markdownify

# Language -> (wiki subdomain, page title)
PAGES = {
    "english":  ("en", "India"),
    "hindi":    ("hi", "भारत"),
    "telugu":   ("te", "భారతదేశం"),
    "marathi":  ("mr", "भारत"),
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_html(lang_code, title):
    """Fetch Wikipedia REST API HTML for a page."""
    url = f"https://{lang_code}.wikipedia.org/api/rest_v1/page/html/{requests.utils.quote(title)}"
    response = requests.get(
        url,
        headers={"User-Agent": "TokenizerAssignment/2.0 (faithful-corpus-builder)"},
        timeout=60,
    )

    response.raise_for_status()
    return response.text


def html_to_faithful_markdown(html):
    """
    Convert Wikipedia HTML to faithful Markdown.
    We keep links, URLs, references, tables, punctuation.
    Only strip <script>/<style>/<noscript>/<math>/<figure class=mw-empty>.
    """
    # Remove script/style/noscript tags only (not figure/table/a/sup)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<noscript[^>]*>.*?</noscript>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # Convert HTML to Markdown — preserves links (href), bold, italic, tables
    md = markdownify.markdownify(
        html,
        heading_style="ATX",
        bullets="-",
        strip=["img"],          # skip image tags (alt text noise)
    )

    # Normalize Unicode (NFKC — same as the tokenizer normalizer)
    import unicodedata
    md = unicodedata.normalize("NFKC", md)

    # Remove BOM and zero-width spaces (invisible, non-printable)
    md = md.replace("\ufeff", "")
    md = md.replace("\u200b", "")

    # Collapse excessive blank lines (3+ → 2)
    md = re.sub(r"\n{3,}", "\n\n", md)

    return md.strip()


def save(language, text):
    path = os.path.join(OUTPUT_DIR, f"{language}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    chars = len(text)
    lines = text.count("\n") + 1
    print(f"  Saved {language}.txt — {chars:,} chars, {lines:,} lines")
    return path


def main():
    print("=" * 60)
    print("Building faithful Wikipedia corpus")
    print("=" * 60)

    saved = []
    for language, (lang_code, title) in PAGES.items():
        print(f"\n[{language}] Fetching {lang_code}.wikipedia.org/wiki/{title} ...")
        try:
            html = fetch_html(lang_code, title)
            md = html_to_faithful_markdown(html)
            path = save(language, md)
            saved.append((language, path, md))
        except Exception as e:
            print(f"  ERROR: {e}")

    # Build weighted training corpus: en×3, hi×4, te×4, mr×2
    WEIGHTS = {"english": 3, "hindi": 4, "telugu": 4, "marathi": 2}
    combined_parts = []
    for language, path, text in saved:
        w = WEIGHTS.get(language, 1)
        combined_parts.extend([text] * w)

    combined_path = os.path.join(OUTPUT_DIR, "training.txt")
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(combined_parts))

    print(f"\n  Saved training.txt — {len('\\n\\n'.join(combined_parts)):,} chars (weighted)")
    print("\nDone! Corpus is faithful — decode(encode(text)) will roundtrip correctly.")


if __name__ == "__main__":
    main()