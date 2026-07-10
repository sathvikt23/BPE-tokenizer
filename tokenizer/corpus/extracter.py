import os
import re
import requests
from bs4 import BeautifulSoup

# Language -> Wikipedia page title
PAGES = {
    "english": ("en", "India"),
    "hindi": ("hi", "भारत"),
    "telugu": ("te", "భారతదేశం"),
    "marathi": ("mr", "भारत"),
}

OUTPUT_DIR = "corpus"
os.makedirs(OUTPUT_DIR, exist_ok=True)


import requests

def fetch_article(lang, title):
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/html/{title}"

    response = requests.get(
        url,
        headers={
            "User-Agent": "TokenizerAssignment/1.0"
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.text

def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag in soup([
        "table",
        "style",
        "script",
        "sup",
        "math",
        "figure",
        "img",
        "noscript"
    ]):
        tag.decompose()

    paragraphs = []

    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)

        if len(text) < 30:
            continue

        paragraphs.append(text)

    article = "\n\n".join(paragraphs)

    # Remove citation markers like [1], [12]
    article = re.sub(r"\[\d+\]", "", article)

    # Normalize whitespace
    article = re.sub(r"\n{3,}", "\n\n", article)

    return article.strip()


def save_article(language, text):
    path = os.path.join(OUTPUT_DIR, f"{language}.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved {language}: {path}")
    print(f"Characters: {len(text):,}")
    print("-" * 50)


def main():
    for language, (lang_code, title) in PAGES.items():
        print(f"Fetching {language}...")

        html = fetch_article(lang_code, title)
        article = clean_html(html)

        save_article(language, article)

    print("Done!")


if __name__ == "__main__":
    main()