from tokenizers import Tokenizer
import re

t = Tokenizer.from_file('tokenizer_file/tokenizer.json')

tests = [
    "India's population is 1,428,627,663.",
    "See #cite_ref-1 and https://en.wikipedia.org/wiki/India",
    "Marathi: Maharashtra (महाराष्ट्र)",
    "bharatdesh.org/wiki/India?ref=1&lang=mr#cite_ref-1",
]

print("Roundtrip test:")
for text in tests:
    enc = t.encode(text)
    dec = t.decode(enc.ids).replace("\u2581", " ").strip()
    orig_vis = re.sub(r"\s+", "", text)
    dec_vis  = re.sub(r"\s+", "", dec)
    ok = orig_vis == dec_vis
    status = "PASS" if ok else "FAIL"
    print(f"  {status}  {repr(text[:60])}")
    if not ok:
        print(f"       orig: {repr(orig_vis[:80])}")
        print(f"       dec : {repr(dec_vis[:80])}")
