# Redes de personagens — resumo dos livros

Rede construída conectando personagens que co-ocorrem dentro de uma janela deslizante de **8 parágrafos**. Personagens identificados, desambiguados (aliases) e com anáfora resolvida via **BookNLP**; só entram na rede clusters do tipo pessoa com nome próprio e ≥3 menções.

**Betweenness centrality**: fração de caminhos mínimos entre todos os pares de personagens que passam por um dado nó — mede quem faz a *ponte* entre diferentes grupos da narrativa.

| # | Livro | Nós | Arestas | Maior betweenness | Valor |
|---|-------|-----|---------|-------------------|-------|
| 1 | Pride and Prejudice | 94 | 1741 | **Elizabeth** | 0.876 |
| 2 | Moby Dick | 245 | 2716 | **Ahab** | 0.663 |
| 3 | Frankenstein | 50 | 297 | **Elizabeth** | 0.550 |
| 4 | A Tale of Two Cities | 91 | 769 | **Mr. Lorry** | 0.695 |
| 5 | Dracula | 112 | 1019 | **Jonathan** | 0.589 |
| 6 | Great Expectations | 121 | 1182 | **Joe** | 0.496 |
| 7 | The Adventures of Huckleberry Finn | 124 | 893 | **Jim** | 0.901 |
| 8 | The Adventures of Sherlock Holmes | 105 | 531 | **Holmes** | 0.971 |
| 9 | Emma | 120 | 2031 | **Emma** | 0.861 |
| 10 | Jane Eyre | 147 | 1420 | **Jane** | 0.662 |

## Observações

- **Narração em 1ª pessoa**: quando o protagonista narra ("I"), ele aparece sobretudo como pronome e não como nome próprio, então outro personagem central tende a liderar o betweenness — ex.: *Huckleberry Finn* → **Jim** (não Huck), *Great Expectations* → **Joe** (não Pip), *Frankenstein* → **Elizabeth** (não Victor).
- **Antologias / estrutura episódica**: em *Sherlock Holmes*, Holmes e Watson ligam os elencos de cada conto, dominando o betweenness.
- **Artefatos de NER** (baixo betweenness, não afetam a resposta): topônimos ocasionais marcados como pessoa (ex.: "Briony Lodge"), numerais de capítulo ("IX") e clusters de correferência divididos (sufixo `(#id)`).
