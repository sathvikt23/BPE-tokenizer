import json
import os

from tokenizers import Tokenizer

TOKENIZER_PATH = r"tokenizer\tokenizer_file\tokenizer.json"
DATA_DIR = r"tsai\tokenizer\corpus"

tokenizer = Tokenizer.from_file(TOKENIZER_PATH)

results = {}

print("-" * 80)
print(f'{"Language":<12} {"Words":>10} {"Tokens":>10} {"Ratio":>10}')
print("-" * 80)

ratios = []

for file in sorted(os.listdir(DATA_DIR)):

    if file in ["combined.txt", "training.txt"]:
        continue

    if not file.endswith(".txt"):
        continue

    language = file[:-4]

    with open(os.path.join(DATA_DIR, file), encoding="utf-8") as f:
        text = f.read()

    words = text.split()

    encoding = tokenizer.encode(text)

    total_words = len(words)
    total_tokens = len(encoding.tokens)

    ratio = total_tokens / total_words

    ratios.append(ratio)

    results[language] = {
        "words": total_words,
        "tokens": total_tokens,
        "ratio": round(ratio, 4)
    }

    print(f"{language:<12} {total_words:>10} {total_tokens:>10} {ratio:>10.4f}")

largest = max(ratios)
smallest = min(ratios)

difference = largest - smallest

score = float("inf") if difference == 0 else 1000 / difference

summary = {
    "largest_ratio": round(largest, 4),
    "smallest_ratio": round(smallest, 4),
    "difference": round(difference, 4),
    "score": round(score, 2)
}

print("-" * 80)
print(summary)

results["summary"] = summary

os.makedirs("results", exist_ok=True)

with open("results/statistics.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\nSaved results/statistics.json")