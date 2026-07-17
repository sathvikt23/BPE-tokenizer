import json
import math
import os
import re

from tokenizers import Tokenizer

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
TOKENIZER_PATH = os.path.join(os.path.dirname(BASE_DIR), "tokenizer_file", "tokenizer.json")
CORPUS_DIR    = os.path.join(BASE_DIR, "corpus")
RESULTS_DIR   = os.path.join(os.path.dirname(BASE_DIR), "results")

os.makedirs(RESULTS_DIR, exist_ok=True)

tokenizer = Tokenizer.from_file(TOKENIZER_PATH)

# ---------------------------------------------------------------------------
# Faithful unit counter
# A faithful unit is either:
#   (a) a maximal run of Unicode letters/marks/numbers (category L*, M*, N*)
#   (b) a single visible non-space punctuation or symbol (category P*, S*)
# ---------------------------------------------------------------------------
_FAITHFUL_UNIT_RE = re.compile(
    r"[\w\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF"
    r"\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF"
    r"\u0D00-\u0D7F\u0D80-\u0DFF]+"  # word-char + Indic script runs
    r"|[^\s]",                         # OR any single visible non-space char
    re.UNICODE,
)


def count_faithful_units(text: str) -> int:
    """Count faithful units in text."""
    return len(_FAITHFUL_UNIT_RE.findall(text))


# ---------------------------------------------------------------------------
# Roundtrip check helper
# ---------------------------------------------------------------------------
def check_roundtrip(text: str) -> bool:
    """
    Verify decode(encode(text)) preserves visible non-whitespace characters.
    Strips the leading Metaspace ▁ before comparison.
    """
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded.ids)
    # Metaspace prepends ▁ to the first token; strip it
    decoded = decoded.replace("▁", " ").strip()

    orig_visible  = re.sub(r"\s+", "", text)
    dec_visible   = re.sub(r"\s+", "", decoded)
    return orig_visible == dec_visible


# ---------------------------------------------------------------------------
# Evaluate each language corpus
# ---------------------------------------------------------------------------
SKIP_FILES = {"combined.txt", "training.txt"}

results = {}
fertilities = {}

print("=" * 80)
print(f"{'Language':<14} {'Tokens':>10} {'Faithful Units':>16} {'Fertility':>10}")
print("=" * 80)

for fname in sorted(os.listdir(CORPUS_DIR)):
    if fname in SKIP_FILES or not fname.endswith(".txt"):
        continue

    language = fname[:-4]
    fpath    = os.path.join(CORPUS_DIR, fname)

    with open(fpath, encoding="utf-8") as f:
        text = f.read()

    # Count faithful units
    fu_count = count_faithful_units(text)

    # Tokenize
    encoding    = tokenizer.encode(text)
    token_count = len(encoding.tokens)

    fertility = token_count / fu_count if fu_count > 0 else float("inf")

    fertilities[language] = fertility
    results[language] = {
        "tokens":          token_count,
        "faithful_units":  fu_count,
        "fertility":       round(fertility, 6),
    }

    print(f"{language:<14} {token_count:>10,} {fu_count:>16,} {fertility:>10.6f}")

    # Quick roundtrip spot check on first 2000 chars
    sample = text[:2000]
    if not check_roundtrip(sample):
        print(f"  ⚠️  ROUNDTRIP FAILED for {language}!")

# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------
if len(fertilities) >= 2:
    max_f = max(fertilities.values())
    min_f = min(fertilities.values())
    spread = max_f - min_f
    raw_score = float("inf") if spread == 0 else 1000 / spread

    hindi_f = fertilities.get("hindi", fertilities.get("hi", None))
    if hindi_f is not None:
        hindi_penalty = math.exp(max(0.0, hindi_f / 1.2 - 1.0))
        hindi_adjusted = raw_score / hindi_penalty
    else:
        hindi_penalty = 1.0
        hindi_adjusted = raw_score

    summary = {
        "max_fertility":        round(max_f, 6),
        "min_fertility":        round(min_f, 6),
        "spread":               round(spread, 6),
        "raw_score":            round(raw_score, 2),
        "hindi_penalty_factor": round(hindi_penalty, 6),
        "hindi_adjusted_score": round(hindi_adjusted, 2),
    }

    print("=" * 80)
    print(f"\nSpread            = {spread:.6f}")
    print(f"Raw score         = {raw_score:.2f}")
    print(f"Hindi penalty     = {hindi_penalty:.6f}")
    print(f"Hindi-adj score   = {hindi_adjusted:.2f}")

    results["summary"] = summary
else:
    print("Not enough language files to compute score.")
    results["summary"] = {}

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------
out_path = os.path.join(RESULTS_DIR, "statistics.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"\nSaved → {out_path}")