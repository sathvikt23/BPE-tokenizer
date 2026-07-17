from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from tokenizers import Tokenizer

import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Multilingual BPE Tokenizer")

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)


tokenizer = Tokenizer.from_file(
    os.path.join(BASE_DIR, "tokenizer_file", "tokenizer.json")
)


with open(
    os.path.join(BASE_DIR, "results", "statistics.json"),
    encoding="utf-8"
) as f:
    statistics = json.load(f)
class TokenizeRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "title": "Multilingual BPE Tokenizer",
            "stats": statistics
        }
    )


@app.post("/tokenize")
async def tokenize(req: TokenizeRequest):

    encoding = tokenizer.encode(req.text)

    return {
        "tokens": [
            {
                "token": token,
                "id": token_id,
                "start": start,
                "end": end
            }
            for token, token_id, (start, end) in zip(
                encoding.tokens,
                encoding.ids,
                encoding.offsets
            )
        ],
        "character_count": len(req.text),
        "word_count": len(req.text.split()),
        "token_count": len(encoding.tokens),
    }

@app.get("/statistics")
async def get_statistics():
    return statistics

@app.get("/download/tokenizer")
async def download_tokenizer():
    return FileResponse(
        os.path.join(BASE_DIR, "tokenizer_file", "tokenizer.json"),
        filename="tokenizer.json",
        media_type="application/json"
    )


@app.get("/download/vocabulary")
async def download_vocabulary():
    vocab = tokenizer.get_vocab()
    vocab = sorted(vocab.items(), key=lambda x: x[1])
    data = [{"token": token, "id": idx} for token, idx in vocab]
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": "attachment; filename=vocabulary.json"}
    )


@app.get("/vocabulary")
async def vocabulary():

    vocab = tokenizer.get_vocab()

    vocab = sorted(vocab.items(), key=lambda x: x[1])

    return [
        {
            "token": token,
            "id": idx
        }
        for token, idx in vocab
    ]