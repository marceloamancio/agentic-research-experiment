"""Constrói a rede de personagens a partir das saídas do BookNLP.

Passos:
1. Lê <slug>.tokens (offsets/paragraph_ID de cada token) e <slug>.entities
   (menções de entidades já com COREF, tipo e prop=PROP/NOM/PRON).
2. Seleciona personagens: clusters COREF com cat==PER, com >=1 menção PROP
   (nome próprio) e total de menções acima de um limiar. Rótulo canônico =
   forma própria mais frequente do cluster (resolve ambiguidade de nomes).
   Menções PRON do mesmo cluster (anáfora resolvida pelo BookNLP) contam para
   a presença do personagem no parágrafo.
3. Rede: janela deslizante de 8 parágrafos (passo 1). Dois personagens que
   aparecem na mesma janela ganham +1 de peso na aresta.
4. Centralidades (networkx): betweenness (ponderada por distância=1/peso),
   degree, weighted-degree, closeness, eigenvector. Personagem de maior
   betweenness = resposta do livro.
5. Artefatos: edges.csv, centralities.csv, network.gexf, network.png.
"""

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BOOKNLP_DIR = ROOT / "data" / "booknlp"
OUTPUT_DIR = ROOT / "output"

WINDOW = 8          # janela de contexto em parágrafos
MIN_MENTIONS = 3    # frequência mínima para um personagem entrar na rede


def _load_token_paragraphs(tokens_path: Path) -> dict:
    """token_ID_within_document -> paragraph_ID."""
    df = pd.read_csv(tokens_path, sep="\t", quoting=3, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    tok_col = "token_ID_within_document"
    par_col = "paragraph_ID"
    return dict(zip(df[tok_col].astype(int), df[par_col].astype(int)))


def _load_entities(entities_path: Path) -> pd.DataFrame:
    df = pd.read_csv(entities_path, sep="\t", quoting=3, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    return df


def select_characters(entities: pd.DataFrame):
    """Devolve (coref -> nome_canonico) para clusters que são personagens."""
    per = entities[entities["cat"] == "PER"]
    names = {}
    for coref, grp in per.groupby("COREF"):
        total = len(grp)
        props = grp[grp["prop"] == "PROP"]["text"].tolist()
        if not props or total < MIN_MENTIONS:
            continue
        # nome canônico = forma própria mais frequente (mais longa em empate)
        counts = Counter(t.strip() for t in props if t.strip())
        if not counts:
            continue
        best = max(counts.items(), key=lambda kv: (kv[1], len(kv[0])))[0]
        names[int(coref)] = best
    # resolve colisões de rótulo (corefs distintos com mesmo nome)
    seen = {}
    labels = {}
    for coref, name in names.items():
        if name in seen:
            labels[coref] = f"{name} (#{coref})"
        else:
            seen[name] = coref
            labels[coref] = name
    return labels


def build_graph(entities: pd.DataFrame, tok2par: dict, labels: dict):
    """Constrói grafo ponderado por co-ocorrência em janelas de WINDOW parágrafos."""
    # presença: parágrafo -> conjunto de corefs de personagens
    para_chars = defaultdict(set)
    char_paras = defaultdict(set)
    per = entities[entities["cat"] == "PER"]
    for _, row in per.iterrows():
        coref = int(row["COREF"])
        if coref not in labels:
            continue
        par = tok2par.get(int(row["start_token"]))
        if par is None:
            continue
        para_chars[par].add(coref)
        char_paras[coref].add(par)

    if not para_chars:
        return nx.Graph(), {}

    max_par = max(para_chars)
    edge_w = Counter()
    # janela deslizante: cada janela é o conjunto de personagens em [s, s+WINDOW-1]
    for start in range(0, max_par + 1):
        present = set()
        for p in range(start, start + WINDOW):
            present |= para_chars.get(p, set())
        for a, b in combinations(sorted(present), 2):
            edge_w[(a, b)] += 1

    G = nx.Graph()
    for coref, label in labels.items():
        if coref in char_paras:
            G.add_node(label, mentions=len(char_paras[coref]))
    for (a, b), w in edge_w.items():
        G.add_edge(labels[a], labels[b], weight=w, distance=1.0 / w)
    return G, char_paras


def compute_centralities(G: nx.Graph) -> pd.DataFrame:
    if G.number_of_nodes() == 0:
        return pd.DataFrame()
    btw = nx.betweenness_centrality(G, weight="distance", normalized=True)
    deg = dict(G.degree())
    wdeg = dict(G.degree(weight="weight"))
    clo = nx.closeness_centrality(G, distance="distance")
    try:
        eig = nx.eigenvector_centrality(G, weight="weight", max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        eig = {n: float("nan") for n in G}
    rows = [
        {
            "character": n,
            "degree": deg[n],
            "weighted_degree": wdeg[n],
            "betweenness": btw[n],
            "closeness": clo[n],
            "eigenvector": eig[n],
        }
        for n in G.nodes()
    ]
    df = pd.DataFrame(rows).sort_values("betweenness", ascending=False)
    return df.reset_index(drop=True)


def _draw(G: nx.Graph, cent: pd.DataFrame, title: str, png_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if G.number_of_nodes() == 0:
        return
    pos = nx.spring_layout(G, weight="weight", seed=42, k=0.6)
    deg = dict(G.degree())
    sizes = [80 + 40 * deg[n] for n in G.nodes()]
    top = set(cent.head(15)["character"]) if not cent.empty else set()
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    wmax = max(weights) if weights else 1
    plt.figure(figsize=(14, 11))
    nx.draw_networkx_edges(
        G, pos, alpha=0.25, width=[0.3 + 2.5 * w / wmax for w in weights]
    )
    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color="#4c72b0", alpha=0.85)
    nx.draw_networkx_labels(
        G, pos, labels={n: n for n in G.nodes() if n in top}, font_size=9
    )
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(png_path, dpi=130)
    plt.close()


def process_book(slug: str, title: str) -> dict:
    in_dir = BOOKNLP_DIR / slug
    tokens_path = in_dir / f"{slug}.tokens"
    entities_path = in_dir / f"{slug}.entities"
    if not entities_path.exists():
        raise FileNotFoundError(f"Saída do BookNLP ausente para {slug}: {entities_path}")

    tok2par = _load_token_paragraphs(tokens_path)
    entities = _load_entities(entities_path)
    labels = select_characters(entities)
    G, _ = build_graph(entities, tok2par, labels)
    cent = compute_centralities(G)

    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    edges = pd.DataFrame(
        [(u, v, d["weight"]) for u, v, d in G.edges(data=True)],
        columns=["source", "target", "weight"],
    ).sort_values("weight", ascending=False)
    edges.to_csv(out_dir / "edges.csv", index=False)
    cent.to_csv(out_dir / "centralities.csv", index=False)
    nx.write_gexf(G, out_dir / "network.gexf")
    _draw(G, cent, f"{title} — rede de personagens", out_dir / "network.png")

    top_char = cent.iloc[0]["character"] if not cent.empty else None
    top_btw = float(cent.iloc[0]["betweenness"]) if not cent.empty else float("nan")
    return {
        "slug": slug,
        "title": title,
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "top_betweenness_character": top_char,
        "top_betweenness": top_btw,
    }


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(ROOT))
    from books import BOOKS

    target = sys.argv[1] if len(sys.argv) > 1 else None
    for bid, title, slug in BOOKS:
        if target and str(bid) != target and slug != target:
            continue
        res = process_book(slug, title)
        print(
            f"{title:40s} | nós={res['nodes']:3d} arestas={res['edges']:4d} "
            f"| maior betweenness: {res['top_betweenness_character']} "
            f"({res['top_betweenness']:.3f})"
        )
