import os
import re
import unicodedata

INPUT_DIR = r"tokenizer\corpus"
OUTPUT_DIR = r"tokenizer\processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Unicode punctuation normalization
PUNCT_MAP = {
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "–": "-",
    "—": "-",
    "…": "...",
    "‐": "-",
}


def clean(text):
    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Remove BOM
    text = text.replace("\ufeff", "")

    # Remove zero-width spaces (keep ZWJ/ZWNJ because they can be meaningful
    # in Indic scripts)
    text = text.replace("\u200b", "")

    # Normalize punctuation
    for old, new in PUNCT_MAP.items():
        text = text.replace(old, new)

    # Remove Wikipedia citation markers
    # [1] [23] [105]
    text = re.sub(r"\[\d+\]", "", text)

    # Remove empty brackets/parentheses
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Normalize spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Remove trailing spaces
    text = re.sub(r"[ \t]+\n", "\n", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


combined = []

print("-" * 70)
print(f'{"Language":<12} {"Characters":>12} {"Words":>12}')
print("-" * 70)

for file in sorted(os.listdir(INPUT_DIR)):

    if not file.endswith(".txt"):
        continue

    in_path = os.path.join(INPUT_DIR, file)

    with open(in_path, "r", encoding="utf-8") as f:
        text = clean(f.read())

    out_path = os.path.join(OUTPUT_DIR, file)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    combined.append(text)

    chars = len(text)
    words = len(re.findall(r"\S+", text))

    print(f"{file[:-4]:<12} {chars:>12,} {words:>12,}")

with open(os.path.join(OUTPUT_DIR, "combined.txt"), "w", encoding="utf-8") as f:
    f.write("\n\n".join(combined))

print("-" * 70)
print("Preprocessing complete.")