"""Orquestra o pipeline completo: download -> BookNLP -> rede -> resumo.

Uso:
  python -m src.pipeline --only 1342     # um livro (id ou slug)
  python -m src.pipeline --all           # todos os 10 livros
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from books import BOOKS  # noqa: E402
from src.download import download_book  # noqa: E402
from src.run_booknlp import run_booknlp  # noqa: E402
from src.build_network import process_book, OUTPUT_DIR, WINDOW, MIN_MENTIONS  # noqa: E402


def run_one(bid, title, slug):
    print(f"\n=== {title} (id={bid}) ===")
    txt = download_book(bid, slug)
    print(f"  [1/3] texto: {txt}")
    run_booknlp(txt, slug)
    print("  [2/3] BookNLP: ok")
    res = process_book(slug, title)
    print(
        f"  [3/3] rede: nós={res['nodes']} arestas={res['edges']} | "
        f"maior betweenness: {res['top_betweenness_character']} "
        f"({res['top_betweenness']:.3f})"
    )
    return res


def write_summary(results):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Redes de personagens — resumo dos livros",
        "",
        "Rede construída conectando personagens que co-ocorrem dentro de uma janela "
        f"deslizante de **{WINDOW} parágrafos**. Personagens identificados, "
        "desambiguados (aliases) e com anáfora resolvida via **BookNLP**; só entram "
        f"na rede clusters do tipo pessoa com nome próprio e ≥{MIN_MENTIONS} menções.",
        "",
        "**Betweenness centrality**: fração de caminhos mínimos entre todos os pares "
        "de personagens que passam por um dado nó — mede quem faz a *ponte* entre "
        "diferentes grupos da narrativa.",
        "",
        "| # | Livro | Nós | Arestas | Maior betweenness | Valor |",
        "|---|-------|-----|---------|-------------------|-------|",
    ]
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r['title']} | {r['nodes']} | {r['edges']} | "
            f"**{r['top_betweenness_character']}** | {r['top_betweenness']:.3f} |"
        )
    lines += [
        "",
        "## Observações",
        "",
        "- **Narração em 1ª pessoa**: quando o protagonista narra (\"I\"), ele aparece "
        "sobretudo como pronome e não como nome próprio, então outro personagem central "
        "tende a liderar o betweenness — ex.: *Huckleberry Finn* → **Jim** (não Huck), "
        "*Great Expectations* → **Joe** (não Pip), *Frankenstein* → **Elizabeth** (não Victor).",
        "- **Antologias / estrutura episódica**: em *Sherlock Holmes*, Holmes e Watson "
        "ligam os elencos de cada conto, dominando o betweenness.",
        "- **Artefatos de NER** (baixo betweenness, não afetam a resposta): topônimos "
        "ocasionais marcados como pessoa (ex.: \"Briony Lodge\"), numerais de capítulo "
        "(\"IX\") e clusters de correferência divididos (sufixo `(#id)`).",
    ]
    (OUTPUT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nResumo escrito em {OUTPUT_DIR / 'summary.md'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="id ou slug de um único livro")
    ap.add_argument("--all", action="store_true", help="todos os livros")
    args = ap.parse_args()

    results = []
    for bid, title, slug in BOOKS:
        if args.only and str(bid) != args.only and slug != args.only:
            continue
        try:
            results.append(run_one(bid, title, slug))
        except Exception as exc:  # tolerante a falha por livro
            print(f"  ERRO em {title}: {exc}")
    if args.all and results:
        write_summary(results)


if __name__ == "__main__":
    main()
