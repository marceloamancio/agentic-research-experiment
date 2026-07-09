# Manuscript: character co-occurrence networks

Publication-ready manuscript (Elsevier `elsarticle`, targeting *Physica A:
Statistical Mechanics and its Applications*) reporting the character-network
results computed in the parent project.

- **Author:** Marcelo Amancio (Inoama Research).
- **Output:** `main.pdf` (23 pages: paper + references + per-novel appendix).

## Rebuild

```bash
# 1) regenerate figures/tables from ../output and ../data (uses the project venv)
source ../.venv/bin/activate
python make_paper_assets.py

# 2) compile the PDF (pdflatex + bibtex)
bash build.sh
```

## Files

| Path | Description |
|------|-------------|
| `main.tex` | Manuscript source (elsarticle). Appendix is placed **after** the bibliography. |
| `refs.bib` | Bibliography (14 entries; real, with DOIs). |
| `references/` | Downloaded PDFs of the cited open-access papers. |
| `make_paper_assets.py` | Computes global network metrics and renders all figures (PDF) and tables (LaTeX/booktabs). |
| `figures/` | Vector figures: method schematic, example networks, top-betweenness, small-world, centrality correlation, POV, and one network per novel. |
| `tables/` | `tab_corpus`, `tab_metrics`, `tab_main`, `appendix_books`. |
| `metrics.csv` | Per-novel global metrics (also feeds the tables). |
| `elsarticle.cls`, `elsarticle-num.bst` | Document class/style (from CTAN; kept locally so no install is needed). |
| `build.sh` | `pdflatex; bibtex; pdflatex; pdflatex`. |

## Figures (own, publication quality)

`fig_method` (pipeline), `fig_examples` (3 representative networks),
`fig_top_betweenness` (main result), `fig_smallworld` (C vs L),
`fig_centrality_corr` (Spearman heatmap), `fig_pov` (betweenness concentration vs
narrative point of view), and `net_<slug>` for the appendix.
