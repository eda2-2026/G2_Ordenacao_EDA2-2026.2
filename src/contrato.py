"""
Tipos e funções compartilhados pelas implementações de ordenação e pelo
benchmark. Cada algoritmo recebe uma sequência, uma chave e métricas, e
devolve uma nova lista sem alterar a entrada.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Sequence

Chave = Callable[[Any], Any]


@dataclass
class Faixa:
    """
    Uma faixa do catalogo.

    Os campos correspondem as colunas do Spotify Tracks Dataset que
    interessam a ordenacao. As demais colunas do CSV (danceability,
    energy, loudness...) sao descartadas na carga: nao sao chaves de
    ordenacao e so ocupariam memoria.
    """

    track_id: str
    nome: str
    artista: str
    album: str
    popularidade: int   # inteiro 0..100  -> chave do Counting Sort
    duracao_ms: int     # inteiro grande  -> chave do Radix LSD
    genero: str

    def __repr__(self) -> str:
        return f"Faixa({self.artista!r}, {self.album!r}, {self.nome!r}, pop={self.popularidade})"


@dataclass
class Metricas:
    """
    Conta comparações entre chaves e escritas de elementos em posições.
    """

    comparacoes: int = 0
    movimentacoes: int = 0

    def zerar(self) -> None:
        self.comparacoes = 0
        self.movimentacoes = 0

    def __str__(self) -> str:
        return (
            f"{self.comparacoes:,} comparacoes, "
            f"{self.movimentacoes:,} movimentacoes"
        ).replace(",", ".")


def identidade(x: Any) -> Any:
    """Chave padrao: o proprio elemento."""
    return x


def por_popularidade(f: Faixa) -> int:
    return f.popularidade


def por_duracao(f: Faixa) -> int:
    return f.duracao_ms


def por_artista(f: Faixa) -> str:
    return f.artista.lower()


def por_album(f: Faixa) -> str:
    return f.album.lower()


def por_nome(f: Faixa) -> str:
    return f.nome.lower()


def verificar_ordenado(lista: Sequence[Any], chave: Chave = identidade) -> bool:
    """Confere que a lista esta nao-decrescente segundo a chave."""
    for i in range(1, len(lista)):
        if chave(lista[i]) < chave(lista[i - 1]):
            return False
    return True


def e_estavel(original: Sequence[Any], ordenada: Sequence[Any], chave: Chave) -> bool:
    """Verifica a estabilidade comparando a saída com `sorted`."""
    referencia: List[Any] = sorted(original, key=chave)
    if len(referencia) != len(ordenada):
        return False
    return all(a is b for a, b in zip(referencia, ordenada))
