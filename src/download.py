"""Download e limpeza de livros do Project Gutenberg.

- Baixa o .txt UTF-8 do Gutenberg.
- Remove o cabeçalho/rodapé padrão ("*** START OF ... ***" ... "*** END OF ... ***").
- Expõe `paragraphs()` que segmenta o texto em parágrafos (separados por linha em
  branco, padrão do Gutenberg) e devolve os offsets de caractere de cada parágrafo,
  necessários para mapear menções de personagens -> parágrafo mais tarde.
"""

import re
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# URLs alternativas (a primeira costuma existir; a segunda é fallback).
URL_TEMPLATES = [
    "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt",
    "https://www.gutenberg.org/files/{id}/{id}-0.txt",
    "https://www.gutenberg.org/files/{id}/{id}.txt",
]

START_RE = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)
END_RE = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)


def fetch_raw(book_id: int) -> str:
    last_err = None
    for tmpl in URL_TEMPLATES:
        url = tmpl.format(id=book_id)
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and len(resp.text) > 1000:
                resp.encoding = "utf-8"
                return resp.text
        except requests.RequestException as exc:  # pragma: no cover
            last_err = exc
    raise RuntimeError(f"Falha ao baixar livro {book_id}: {last_err}")


def strip_boilerplate(text: str) -> str:
    """Remove cabeçalho/rodapé do Gutenberg, mantendo só o corpo da obra."""
    start_m = START_RE.search(text)
    end_m = END_RE.search(text)
    start = start_m.end() if start_m else 0
    end = end_m.start() if end_m else len(text)
    body = text[start:end].strip()
    # Normaliza CRLF -> LF para offsets consistentes.
    return body.replace("\r\n", "\n").replace("\r", "\n")


def paragraphs(text: str):
    """Segmenta em parágrafos por linha(s) em branco.

    Retorna lista de dicts: {index, start, end, text}. start/end são offsets de
    caractere no `text` passado (corpo limpo já normalizado).
    """
    paras = []
    idx = 0
    for m in re.finditer(r"[^\n].*?(?=\n\s*\n|\Z)", text, flags=re.S):
        chunk = m.group(0)
        if chunk.strip():
            paras.append(
                {"index": idx, "start": m.start(), "end": m.end(), "text": chunk}
            )
            idx += 1
    return paras


def download_book(book_id: int, slug: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / f"{slug}.txt"
    if out.exists() and out.stat().st_size > 1000:
        return out
    raw = fetch_raw(book_id)
    body = strip_boilerplate(raw)
    out.write_text(body, encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from books import BOOKS

    for bid, title, slug in BOOKS:
        path = download_book(bid, slug)
        n = len(paragraphs(path.read_text(encoding="utf-8")))
        print(f"{title:40s} -> {path.name} ({n} parágrafos)")
