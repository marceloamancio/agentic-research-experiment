# Character networks — 10 Project Gutenberg novels

An independent research experiment (not a peer-reviewed publication) that
builds the **character co-occurrence network** of 10 classic English novels
and identifies, for each book, the character with the highest **betweenness
centrality** — the character who most often sits on the shortest path between
other characters, i.e. the narrative "bridge".

Two characters are connected if they are mentioned within the same **sliding
window of 8 paragraphs**. Character identification, name disambiguation
(*Elizabeth* / *Lizzy* / *Miss Bennet* → 1 character) and anaphora resolution
(pronouns → the right character) are all handled by **BookNLP**.

## Key findings

| Book | Highest-betweenness character | Value |
|------|-------------------------------|-------|
| Pride and Prejudice | **Elizabeth** | 0.876 |
| Moby Dick | **Ahab** | 0.663 |
| Frankenstein | **Elizabeth** | 0.550 |
| A Tale of Two Cities | **Mr. Lorry** | 0.695 |
| Dracula | **Jonathan** | 0.589 |
| Great Expectations | **Joe** | 0.496 |
| The Adventures of Huckleberry Finn | **Jim** | 0.901 |
| The Adventures of Sherlock Holmes | **Holmes** | 0.971 |
| Emma | **Emma** | 0.861 |
| Jane Eyre | **Jane** | 0.662 |

Betweenness centrality measures how often a character sits on the shortest
path between other characters — i.e. who structurally connects different
groups in the story, as opposed to who simply appears most often.

The most striking pattern shows up in **first-person narratives**: when the
protagonist narrates as "I", they're mentioned mostly through pronouns rather
than their proper name, so a *secondary* character ends up leading
betweenness instead — **Jim** in *Huckleberry Finn* (not Huck), **Joe** in
*Great Expectations* (not Pip), **Elizabeth** in *Frankenstein* (not Victor).
In episodic/anthology structures like *Sherlock Holmes*, Holmes and Watson
dominate betweenness because they're the constant thread linking every
story's otherwise disjoint cast.

Across all ten books, the resulting networks show a clear small-world
signature (high clustering, short average path lengths) and disassortative
degree mixing, and betweenness turns out to be the centrality measure least
correlated with the others — confirming it captures a distinct,
mediation-oriented notion of importance rather than just popularity. Full
methodology, statistics and discussion are in the [paper](paper/main.pdf);
per-book numbers are in [`output/summary.md`](output/summary.md).

## Methodology

1. **Character detection (NER).** BookNLP runs named-entity recognition over
   the raw novel text and tags every mention of a `PER` (person) entity.
2. **Alias clustering.** BookNLP clusters proper-name variants of the same
   character into a single ID (e.g. *Elizabeth*, *Lizzy*, *Miss Bennet* all
   collapse into one node), using its built-in coreference model.
3. **Anaphora resolution.** The same coreference model resolves pronouns
   (*she*, *he*, *her*) back to the character they refer to, so a character
   who is mostly referred to by pronoun (common for first-person narrators)
   still accumulates mentions correctly.
4. **Paragraph mapping.** Every resolved mention is mapped to the paragraph
   it occurs in, using token offsets from BookNLP's tokenizer output.
5. **Network construction.** Two characters become linked (with a weight that
   increases with co-occurrence frequency) whenever they are both mentioned
   inside the same sliding window of 8 consecutive paragraphs.
6. **Centrality analysis.** `networkx` computes degree, weighted degree,
   betweenness, closeness and eigenvector centrality for every node in the
   resulting graph. The character with the highest betweenness is reported as
   the book's structural "connector".

## Pipeline

1. `src/download.py` — downloads the book's `.txt` from Project Gutenberg and
   strips the header/footer boilerplate.
2. `src/run_booknlp.py` — runs BookNLP (character NER + alias clustering +
   coreference/anaphora resolution).
3. `src/build_network.py` — maps mentions to paragraphs, builds the
   co-occurrence graph over 8-paragraph windows, and computes centralities
   with `networkx`.
4. `src/pipeline.py` — orchestrates the full pipeline and writes
   `output/summary.md`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # BookNLP dependency
```

> On first run, BookNLP downloads a few hundred MB of models to
> `~/booknlp_models/` (no monetary cost).

A `Makefile` wraps the commands above and below — see [Quick start with
`make`](#quick-start-with-make).

## Running

```bash
# a single book (for validation)
python -m src.pipeline --only 1342

# all 10 books + comparative summary
python -m src.pipeline --all
```

## Quick start with `make`

```bash
make venv    # create .venv and install dependencies
make run BOOK=1342   # single book
make all     # full 10-book pipeline
make paper   # regenerate paper figures/tables and recompile the PDF
make clean   # remove regenerable build artifacts
```

## Outputs (per book, in `output/<slug>/`)

- `edges.csv` — edge list (source, target, weight).
- `centralities.csv` — degree, weighted_degree, betweenness, closeness,
  eigenvector.
- `network.gexf` — graph file for [Gephi](https://gephi.org).
- `network.png` — network visualization.

Plus `output/summary.md` with the final table: book → highest-betweenness
character.

## Reproducibility

- `data/raw/` (the downloaded Gutenberg `.txt` files) ships with the repo, so
  the exact corpus used is always available.
- `data/booknlp/` (BookNLP's per-book intermediate output — entities, tokens,
  coreference clusters) is **not** committed: it's bulky (~180MB) and fully
  regenerable. Running `python -m src.run_booknlp` (or the full pipeline)
  recreates it, downloading BookNLP's own models to `~/booknlp_models/`
  automatically on first run.
- `output/` (final CSVs, GEXF graphs, PNGs, summary) is committed as-is, so
  results are visible without rerunning anything.

## Paper

The scientific manuscript (English, Elsevier `elsarticle` class, targeting
*Physica A*) with the results is in [`paper/`](paper/) — see `paper/main.pdf`
and `paper/README.md`. Author: Marcelo Amancio (Inoama Research). Includes
original figures, a bibliography with downloaded reference PDFs, and a
per-book appendix after the references.

This is an independent research experiment, shared for transparency and
reproducibility — it has not been submitted to or reviewed by any journal.

## The 10 books

Pride and Prejudice · Moby Dick · Frankenstein · A Tale of Two Cities ·
Dracula · Great Expectations · The Adventures of Huckleberry Finn · The
Adventures of Sherlock Holmes · Emma · Jane Eyre.
