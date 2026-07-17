from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.normalizers import NFKC
from tokenizers.pre_tokenizers import Metaspace
from tokenizers.trainers import BpeTrainer
from tokenizers import decoders
import os 
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(BASE_DIR, "corpus")
TRAIN_FILE = os.path.join(CORPUS_DIR, "training.txt")
OUT_DIR    = os.path.join(os.path.dirname(BASE_DIR), "tokenizer_file")

os.makedirs(OUT_DIR, exist_ok=True)

# --- Build tokenizer ---
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))

# NFKC only — same normalization applied to corpus
tokenizer.normalizer = NFKC()

# Metaspace: splits on whitespace, marks word-start with ▁
# This is the KEY fix — WhitespaceSplit + BPEDecoder drops punctuation/URL chars
tokenizer.pre_tokenizer = Metaspace(replacement="▁", prepend_scheme="always")

# Matching Metaspace decoder — guarantees decode(encode(x)) == x for visible chars
tokenizer.decoder = decoders.Metaspace(replacement="▁", prepend_scheme="always")

trainer = BpeTrainer(
    vocab_size=10_000,
    min_frequency=1,          # reference uses 1 (not 2)
    special_tokens=["[UNK]", "[PAD]", "[CLS]", "[SEP]", "[MASK]"],
    show_progress=True,
)

print(f"Training on: {TRAIN_FILE}")
tokenizer.train([TRAIN_FILE], trainer)

out_path = os.path.join(OUT_DIR, "tokenizer.json")
tokenizer.save(out_path)

print(f"Saved tokenizer → {out_path}")
print(f"Vocabulary size: {tokenizer.get_vocab_size():,}")

# Quick roundtrip sanity check
test_cases = [
    "India's population is 1,428,627,663.",
    "See [[#cite_ref-1]] and https://en.wikipedia.org/wiki/India",
    "भारत एक लोकतांत्रिक गणराज्य है।",
]
print("\nRoundtrip sanity check:")
all_passed = True
for text in test_cases:
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded.ids)
    # Strip leading ▁ if present (Metaspace prepends it)
    decoded = decoded.lstrip("▁").strip()
    passed = decoded == text.strip()
    status = "✓" if passed else "✗ FAIL"
    print(f"  {status}  {repr(text[:60])}")
    if not passed:
        print(f"       → got: {repr(decoded[:60])}")
        all_passed = False

if all_passed:
    print("\nAll roundtrip checks passed!")
else:
    print("\nSome roundtrip checks FAILED — investigate before submitting.")