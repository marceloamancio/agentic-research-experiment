"""Gera figuras (PDF vetorial) e tabelas (LaTeX/booktabs) do paper a partir dos
artefatos de rede em ../output/<slug>/ e dos tokens do BookNLP em
../data/booknlp/<slug>/<slug>.tokens.

Saídas:
  figures/  fig_method.pdf, fig_examples.pdf, fig_top_betweenness.pdf,
            fig_smallworld.pdf, fig_centrality_corr.pdf, fig_pov.pdf,
            net_<slug>.pdf (um por livro, para o apêndice)
  tables/   tab_corpus.tex, tab_metrics.tex, tab_main.tex, appendix_books.tex
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from networkx.algorithms.community import greedy_modularity_communities, modularity

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
BOOKNLP = ROOT / "data" / "booknlp"
FIG = Path(__file__).resolve().parent / "figures"
TAB = Path(__file__).resolve().parent / "tables"
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)

# slug -> (título curto, autor, ano, ponto de vista narrativo)
META = {
    "pride-and-prejudice": ("Pride and Prejudice", "Austen", 1813, "3rd"),
    "moby-dick": ("Moby-Dick", "Melville", 1851, "1st"),
    "frankenstein": ("Frankenstein", "Shelley", 1818, "1st"),
    "a-tale-of-two-cities": ("A Tale of Two Cities", "Dickens", 1859, "3rd"),
    "dracula": ("Dracula", "Stoker", 1897, "1st"),
    "great-expectations": ("Great Expectations", "Dickens", 1861, "1st"),
    "huckleberry-finn": ("Huckleberry Finn", "Twain", 1884, "1st"),
    "sherlock-holmes": ("The Adventures of Sherlock Holmes", "Doyle", 1892, "1st"),
    "emma": ("Emma", "Austen", 1815, "3rd"),
    "jane-eyre": ("Jane Eyre", "Brontë", 1847, "1st"),
}
ORDER = list(META.keys())

# estilo de figura "publicação"
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def load_graph(slug):
    g = nx.read_gexf(OUTPUT / slug / "network.gexf")
    return nx.Graph(g)


def load_cent(slug):
    return pd.read_csv(OUTPUT / slug / "centralities.csv")


def corpus_counts(slug):
    """nº de tokens e parágrafos a partir do .tokens do BookNLP."""
    tpath = BOOKNLP / slug / f"{slug}.tokens"
    df = pd.read_csv(tpath, sep="\t", quoting=3, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    n_tokens = len(df)
    n_paras = int(df["paragraph_ID"].max()) + 1
    return n_tokens, n_paras


def communities(G):
    comms = list(greedy_modularity_communities(G, weight="weight"))
    node2c = {}
    for i, c in enumerate(comms):
        for n in c:
            node2c[n] = i
    q = modularity(G, comms, weight="weight")
    return node2c, len(comms), q


def small_world_sigma(G, n_rand=5, seed=42):
    """sigma = (C/C_rand) / (L/L_rand) no componente gigante."""
    Gc = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    n, m = Gc.number_of_nodes(), Gc.number_of_edges()
    if n < 4 or m == 0:
        return np.nan, np.nan, np.nan
    C = nx.average_clustering(Gc)
    L = nx.average_shortest_path_length(Gc)
    rng = np.random.default_rng(seed)
    Cs, Ls = [], []
    for _ in range(n_rand):
        R = nx.gnm_random_graph(n, m, seed=int(rng.integers(1e9)))
        if not nx.is_connected(R):
            R = R.subgraph(max(nx.connected_components(R), key=len)).copy()
        Cs.append(nx.average_clustering(R))
        Ls.append(nx.average_shortest_path_length(R))
    C_rand = np.mean(Cs) if np.mean(Cs) > 0 else np.nan
    L_rand = np.mean(Ls)
    sigma = (C / C_rand) / (L / L_rand) if C_rand and L_rand else np.nan
    return C, L, sigma


def compute_metrics():
    rows = []
    for slug in ORDER:
        G = load_graph(slug)
        cent = load_cent(slug)
        title, author, year, pov = META[slug]
        n, m = G.number_of_nodes(), G.number_of_edges()
        Gc = G.subgraph(max(nx.connected_components(G), key=len)).copy()
        _, ncomm, q = communities(G)
        C, L, sigma = small_world_sigma(G)
        try:
            assort = nx.degree_assortativity_coefficient(G)
        except Exception:
            assort = np.nan
        n_tokens, n_paras = corpus_counts(slug)
        top_b = cent.sort_values("betweenness", ascending=False).iloc[0]
        top_d = cent.sort_values("degree", ascending=False).iloc[0]
        rows.append(
            {
                "slug": slug,
                "title": title,
                "author": author,
                "year": year,
                "pov": pov,
                "tokens": n_tokens,
                "paragraphs": n_paras,
                "N": n,
                "E": m,
                "density": nx.density(G),
                "avg_degree": 2 * m / n,
                "clustering": C,
                "path": L,
                "diameter": nx.diameter(Gc),
                "assortativity": assort,
                "modularity": q,
                "communities": ncomm,
                "sigma": sigma,
                "top_b_char": top_b["character"],
                "top_b_val": top_b["betweenness"],
                "top_d_char": top_d["character"],
                "top_d_val": top_d["degree"],
            }
        )
    return pd.DataFrame(rows)


# ----------------------------- FIGURAS -----------------------------------------
def draw_network(G, ax, cent, title, n_labels=7, k=None, labels=True):
    node2c, _, _ = communities(G)
    btw = dict(zip(cent["character"], cent["betweenness"]))
    nodes = list(G.nodes())
    if k is None:
        k = 2.2 / np.sqrt(max(G.number_of_nodes(), 2))
    pos = nx.spring_layout(G, weight="weight", seed=7, k=k, iterations=120)
    # escala por sqrt p/ reduzir a dominância visual do hub principal
    sizes = [25 + 1500 * np.sqrt(btw.get(n, 0)) for n in nodes]
    colors = [node2c.get(n, 0) for n in nodes]
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    wmax = max(weights) if weights else 1
    nx.draw_networkx_edges(
        G, pos, ax=ax, alpha=0.18, width=[0.2 + 1.8 * w / wmax for w in weights]
    )
    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_size=sizes, node_color=colors, cmap="tab20",
        alpha=0.9, linewidths=0.3, edgecolors="white",
    )
    if labels:
        top = cent.sort_values("betweenness", ascending=False).head(n_labels)["character"]
        texts = nx.draw_networkx_labels(
            G, pos, ax=ax, labels={n: n for n in top if n in G}, font_size=7
        )
        for t in texts.values():
            t.set_bbox(dict(boxstyle="round,pad=0.15", fc="white", ec="none",
                            alpha=0.75))
    ax.set_title(title)
    ax.axis("off")


def fig_examples(df):
    slugs = ["pride-and-prejudice", "sherlock-holmes", "a-tale-of-two-cities"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2))
    for ax, slug in zip(axes, slugs):
        G = load_graph(slug)
        cent = load_cent(slug)
        draw_network(G, ax, cent, META[slug][0])
    for ax, lab in zip(axes, "abc"):
        ax.text(0.02, 0.98, f"({lab})", transform=ax.transAxes, fontsize=12,
                fontweight="bold", va="top")
    fig.tight_layout()
    fig.savefig(FIG / "fig_examples.pdf")
    plt.close(fig)


def fig_per_book():
    for slug in ORDER:
        G = load_graph(slug)
        cent = load_cent(slug)
        fig, ax = plt.subplots(figsize=(7.5, 6.2))
        draw_network(G, ax, cent, META[slug][0], labels=False)
        fig.tight_layout()
        fig.savefig(FIG / f"net_{slug}.pdf")
        plt.close(fig)


def fig_top_betweenness(df):
    d = df.sort_values("top_b_val")
    labels = [f"{r.top_b_char}\n({r.title})" for r in d.itertuples()]
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#c44e52" if p == "1st" else "#4c72b0" for p in d["pov"]]
    ax.barh(range(len(d)), d["top_b_val"], color=colors)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Betweenness centrality (normalized)")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#4c72b0"),
        plt.Rectangle((0, 0), 1, 1, color="#c44e52"),
    ]
    ax.legend(handles, ["3rd-person narrative", "1st-person narrative"],
              frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig_top_betweenness.pdf")
    plt.close(fig)


def fig_smallworld(df):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.scatter(df["path"], df["clustering"], s=70, c="#4c72b0", zorder=3)
    for r in df.itertuples():
        ax.annotate(META[r.slug][0], (r.path, r.clustering), fontsize=7,
                    xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("Average shortest path length $L$")
    ax.set_ylabel("Average clustering coefficient $C$")
    ax.set_title("Small-world signature of character networks")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "fig_smallworld.pdf")
    plt.close(fig)


def fig_centrality_corr():
    frames = []
    for slug in ORDER:
        c = load_cent(slug)[
            ["betweenness", "degree", "weighted_degree", "closeness", "eigenvector"]
        ]
        frames.append(c)
    allc = pd.concat(frames, ignore_index=True)
    corr = allc.corr(method="spearman")
    labels = ["Betw.", "Degree", "W.degree", "Close.", "Eigen."]
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr, cmap="viridis", vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                    color="white" if corr.iloc[i, j] < 0.6 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, label="Spearman correlation")
    ax.set_title("Centrality correlations (pooled over books)")
    fig.tight_layout()
    fig.savefig(FIG / "fig_centrality_corr.pdf")
    plt.close(fig)


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    return (2 * np.sum((np.arange(1, n + 1)) * x) / (n * x.sum())) - (n + 1) / n


def fig_pov(df):
    """Concentração da betweenness (Gini) por ponto de vista narrativo."""
    ginis = []
    for slug in ORDER:
        ginis.append(gini(load_cent(slug)["betweenness"].values))
    df = df.copy()
    df["gini"] = ginis
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for pov, color, lab in [("1st", "#c44e52", "1st-person"),
                            ("3rd", "#4c72b0", "3rd-person")]:
        sub = df[df["pov"] == pov]
        ax.scatter(sub["gini"], sub["top_b_val"], s=70, c=color, label=lab, zorder=3)
    for r in df.itertuples():
        ax.annotate(META[r.slug][0], (r.gini, r.top_b_val), fontsize=7,
                    xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("Gini of betweenness distribution")
    ax.set_ylabel("Max betweenness in the network")
    ax.set_title("Betweenness concentration vs. narrative point of view")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "fig_pov.pdf")
    plt.close(fig)


def fig_method():
    fig, ax = plt.subplots(figsize=(11, 2.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.axis("off")
    steps = [
        ("Gutenberg\nnovel (text)", "#dfe7f3"),
        ("BookNLP:\nNER + alias\nclustering + coref", "#cdddee"),
        ("Characters per\nparagraph", "#bcd2e8"),
        ("8-paragraph\nsliding window\nco-occurrence", "#a9c6e0"),
        ("Weighted\ncharacter\nnetwork", "#90b4d6"),
        ("Centralities\n(betweenness, ...)", "#7aa6cf"),
    ]
    x = 3
    w = 13
    for i, (txt, col) in enumerate(steps):
        box = FancyBboxPatch((x, 5), w, 10, boxstyle="round,pad=0.3,rounding_size=0.6",
                             fc=col, ec="#33506e", lw=1.0)
        ax.add_patch(box)
        ax.text(x + w / 2, 10, txt, ha="center", va="center", fontsize=8.5)
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.3, 10), (x + w + 2.7, 10),
                         arrowstyle="-|>", mutation_scale=14, color="#33506e"))
        x += w + 3
    fig.tight_layout()
    fig.savefig(FIG / "fig_method.pdf")
    plt.close(fig)


# ----------------------------- TABELAS -----------------------------------------
def esc(s):
    return str(s).replace("&", "\\&").replace("#", "\\#").replace("_", "\\_")


def tab_corpus(df):
    lines = [
        r"\begin{tabular}{llrrrrr}", r"\toprule",
        r"Novel & Author & Year & Tokens & Paragraphs & Characters & Edges \\",
        r"\midrule",
    ]
    for r in df.itertuples():
        lines.append(
            f"{esc(META[r.slug][0])} & {esc(r.author)} & {r.year} & {r.tokens:,} & "
            f"{r.paragraphs:,} & {r.N} & {r.E} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "tab_corpus.tex").write_text("\n".join(lines).replace(",", "{,}"))


def tab_metrics(df):
    lines = [
        r"\begin{tabular}{lrrrrrrrr}", r"\toprule",
        r"Novel & $N$ & $E$ & $\langle k\rangle$ & $C$ & $L$ & $r$ & $Q$ & $\sigma$ \\",
        r"\midrule",
    ]
    for r in df.itertuples():
        lines.append(
            f"{esc(META[r.slug][0])} & {r.N} & {r.E} & {r.avg_degree:.1f} & "
            f"{r.clustering:.2f} & {r.path:.2f} & {r.assortativity:.2f} & "
            f"{r.modularity:.2f} & {r.sigma:.1f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "tab_metrics.tex").write_text("\n".join(lines))


def tab_main(df):
    lines = [
        r"\begin{tabular}{llrlr}", r"\toprule",
        r"Novel & Top betweenness & $C_B$ & Top degree & $k$ \\",
        r"\midrule",
    ]
    for r in df.itertuples():
        lines.append(
            f"{esc(META[r.slug][0])} & {esc(r.top_b_char)} & {r.top_b_val:.3f} & "
            f"{esc(r.top_d_char)} & {int(r.top_d_val)} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "tab_main.tex").write_text("\n".join(lines))


def appendix_books(df):
    parts = []
    for r in df.itertuples():
        slug = r.slug
        title = META[slug][0]
        cent = load_cent(slug).sort_values("betweenness", ascending=False).head(10)
        parts.append(rf"\subsection{{{esc(title)} ({r.author}, {r.year})}}")
        parts.append(
            rf"\begin{{figure}}[H]\centering"
            rf"\includegraphics[width=0.74\textwidth]{{figures/net_{slug}.pdf}}"
            rf"\caption{{Character co-occurrence network of \emph{{{esc(title)}}}. "
            rf"Node size is proportional to betweenness and colours denote communities "
            rf"(greedy modularity); the most central characters are named in the "
            rf"accompanying table.}}\end{{figure}}"
        )
        tbl = [
            r"\begin{table}[H]\centering\small",
            r"\begin{tabular}{lrrrr}", r"\toprule",
            r"Character & $C_B$ & Degree & Closeness & Eigenvector \\", r"\midrule",
        ]
        for c in cent.itertuples():
            tbl.append(
                f"{esc(c.character)} & {c.betweenness:.3f} & {int(c.degree)} & "
                f"{c.closeness:.2f} & {c.eigenvector:.3f} \\\\"
            )
        tbl += [r"\bottomrule", r"\end{tabular}",
                rf"\caption{{Top-10 characters in \emph{{{esc(title)}}} ranked by "
                rf"betweenness.}}\end{{table}}", r"\clearpage"]
        parts.append("\n".join(tbl))
    (TAB / "appendix_books.tex").write_text("\n\n".join(parts))


def main():
    df = compute_metrics()
    df.to_csv(Path(__file__).resolve().parent / "metrics.csv", index=False)
    print("Métricas calculadas:")
    print(df[["title", "N", "E", "clustering", "path", "sigma",
              "top_b_char", "top_b_val"]].to_string(index=False))
    fig_method()
    fig_examples(df)
    fig_per_book()
    fig_top_betweenness(df)
    fig_smallworld(df)
    fig_centrality_corr()
    fig_pov(df)
    tab_corpus(df)
    tab_metrics(df)
    tab_main(df)
    appendix_books(df)
    print(f"\nFiguras em {FIG}\nTabelas em {TAB}")


if __name__ == "__main__":
    main()
