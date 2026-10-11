"""
Carrega do CSV os campos usados pelo catálogo e pela ordenação.
Quando há vários artistas, usa o primeiro nome da coluna `artists`.
"""

import csv
import os
import random
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.contrato import Faixa

# Alguns campos do CSV excedem o limite padrão de tamanho do módulo csv.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

CAMINHO_PADRAO = os.path.join("dados", "dataset.csv")


def carregar(caminho: str = CAMINHO_PADRAO, limite: int | None = None) -> List[Faixa]:
    """
    Le o CSV e devolve a lista de faixas.

    `limite` corta a leitura nas primeiras N linhas validas — util para
    testar rapido sem carregar as 114 mil.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Nao encontrei '{caminho}'.\n\n"
            "Baixe o dataset em:\n"
            "  https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset\n"
            f"e salve o arquivo como '{caminho}'."
        )

    faixas: List[Faixa] = []
    descartadas = 0

    with open(caminho, encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)

        for linha in leitor:
            try:
                popularidade = int(linha["popularity"])
                duracao = int(linha["duration_ms"])
            except (KeyError, ValueError, TypeError):
                descartadas += 1
                continue

            # O Radix exige chaves não negativas.
            if duracao <= 0:
                descartadas += 1
                continue

            if not (0 <= popularidade <= 100):
                descartadas += 1
                continue

            artistas_bruto = (linha.get("artists") or "").strip()
            artista = artistas_bruto.split(";")[0].strip() or "(desconhecido)"

            faixas.append(
                Faixa(
                    track_id=(linha.get("track_id") or "").strip(),
                    nome=(linha.get("track_name") or "").strip(),
                    artista=artista,
                    album=(linha.get("album_name") or "").strip(),
                    popularidade=popularidade,
                    duracao_ms=duracao,
                    genero=(linha.get("track_genre") or "").strip(),
                )
            )

            if limite is not None and len(faixas) >= limite:
                break

    if descartadas:
        print(f"  (descartadas {descartadas} linhas invalidas na carga)")

    return faixas


def amostrar(faixas: List[Faixa], n: int, semente: int = 42) -> List[Faixa]:
    """Amostra faixas; se n exceder o catálogo, repete e embaralha os dados."""
    rng = random.Random(semente)

    if n <= len(faixas):
        return rng.sample(faixas, n)

    repetido: List[Faixa] = []
    while len(repetido) < n:
        repetido.extend(faixas)
    repetido = repetido[:n]
    rng.shuffle(repetido)
    return repetido


def resumo(faixas: List[Faixa]) -> str:
    """Uma linha com as estatisticas que o relatorio precisa."""
    if not faixas:
        return "catalogo vazio"

    artistas = len({f.artista for f in faixas})
    albuns = len({f.album for f in faixas})
    dur_min = min(f.duracao_ms for f in faixas)
    dur_max = max(f.duracao_ms for f in faixas)

    return (
        f"{len(faixas):,} faixas | {artistas:,} artistas | {albuns:,} albuns | "
        f"duracao {dur_min:,}..{dur_max:,} ms"
    ).replace(",", ".")


if __name__ == "__main__":
    catalogo = carregar()
    print(resumo(catalogo))
