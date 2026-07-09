"""Executa o BookNLP sobre os textos limpos.

O BookNLP faz, em um passo, tudo que o projeto exige no lado de PLN:
- NER de personagens (entidades PER);
- clustering de aliases (Elizabeth / Lizzy / Miss Bennet -> mesmo COREF id);
- correferência incluindo pronomes (anáfora resolvida -> menções PRON no mesmo cluster);
- gênero/atributos.

Saídas relevantes em data/booknlp/<slug>/:
- <slug>.entities : COREF, start_token, end_token, prop (PROP/NOM/PRON), cat (PER/...), text
- <slug>.tokens   : offsets de cada token no texto original (para mapear -> parágrafo)
- <slug>.book     : json com clusters de personagens agregados
"""

from pathlib import Path

BOOKNLP_DIR = Path(__file__).resolve().parent.parent / "data" / "booknlp"

# "small" = rápido (viável p/ 10 romances em CPU); "big" = mais preciso, porém
# muito mais lento sem GPU. Trocável via env BOOKNLP_MODEL.
import os as _os

DEFAULT_MODEL = _os.environ.get("BOOKNLP_MODEL", "small")


def _patch_torch_strict_load():
    """Compat: BookNLP 1.0.8 traz checkpoints BERT com o buffer não-treinado
    `position_ids`, que o transformers/torch atual não registra mais. Carregar
    com strict=False descarta essa chave extra (recriada na hora) sem afetar os
    pesos aprendidos."""
    import torch

    if getattr(torch.nn.Module.load_state_dict, "_booknlp_patched", False):
        return
    orig = torch.nn.Module.load_state_dict

    def patched(self, state_dict, strict=True, assign=False):
        return orig(self, state_dict, strict=False, assign=assign)

    patched._booknlp_patched = True
    torch.nn.Module.load_state_dict = patched


def run_booknlp(text_path: Path, slug: str, model: str = DEFAULT_MODEL) -> Path:
    out_dir = BOOKNLP_DIR / slug
    entities = out_dir / f"{slug}.entities"
    if entities.exists() and entities.stat().st_size > 0:
        return out_dir  # já processado
    out_dir.mkdir(parents=True, exist_ok=True)

    _patch_torch_strict_load()

    # Import tardio: só carrega torch/transformers quando realmente necessário.
    from booknlp.booknlp import BookNLP

    model_params = {"pipeline": "entity,quote,supersense,event,coref", "model": model}
    booknlp = BookNLP("en", model_params)
    booknlp.process(str(text_path), str(out_dir), slug)
    return out_dir


if __name__ == "__main__":
    import sys

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    from books import BOOKS
    from src.download import download_book

    target = sys.argv[1] if len(sys.argv) > 1 else None
    for bid, title, slug in BOOKS:
        if target and str(bid) != target and slug != target:
            continue
        print(f"== BookNLP: {title} ==")
        txt = download_book(bid, slug)
        run_booknlp(txt, slug)
        print(f"   ok -> {BOOKNLP_DIR / slug}")
