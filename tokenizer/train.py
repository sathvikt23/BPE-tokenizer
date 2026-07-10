from tokenizers import Tokenizer
from tokenizers.models import BPE 
from tokenizers.pre_tokenizers import WhitespaceSplit
from tokenizers.normalizers import Sequence ,NFC 
from tokenizers.trainers import BpeTrainer
from tokenizers.decoders import BPEDecoder


import os 

TRAIN_FILE = r"\corpus\training.txt"

tokenizer =Tokenizer(BPE(unk_token="[UNK]"))

tokenizer.normalizer=Sequence([NFC()])

tokenizer.pre_tokenizer=WhitespaceSplit()

tokenizer.decoder=BPEDecoder()

trainer =BpeTrainer(
    vocab_size=10000,
    min_frequency=2,
    special_tokens=[
        "[UNK]",
        "[PAD]",
        "[CLS]",
        "[SEP]",
        "[MASK]",
    ]
)


tokenizer.train([TRAIN_FILE],trainer)

tokenizer.save(r"tokenizer_file\tokenizer.json")

print("Vocabulary Size:", tokenizer.get_vocab_size())