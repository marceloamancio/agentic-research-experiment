"""Catálogo dos 10 livros do Project Gutenberg usados no projeto.

Cada entrada: (gutenberg_id, título, slug). O slug é usado para nomear
diretórios e arquivos de saída.
"""

BOOKS = [
    (1342, "Pride and Prejudice", "pride-and-prejudice"),
    (2701, "Moby Dick", "moby-dick"),
    (84, "Frankenstein", "frankenstein"),
    (98, "A Tale of Two Cities", "a-tale-of-two-cities"),
    (345, "Dracula", "dracula"),
    (1400, "Great Expectations", "great-expectations"),
    (76, "The Adventures of Huckleberry Finn", "huckleberry-finn"),
    (1661, "The Adventures of Sherlock Holmes", "sherlock-holmes"),
    (158, "Emma", "emma"),
    (1260, "Jane Eyre", "jane-eyre"),
]


def by_id(book_id):
    for bid, title, slug in BOOKS:
        if bid == book_id:
            return (bid, title, slug)
    raise KeyError(f"Livro {book_id} não está no catálogo (books.py).")
