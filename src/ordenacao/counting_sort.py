"""
Counting Sort estável para chaves inteiras em um intervalo conhecido.
Complexidade: O(n + k) em tempo e espaço, onde k = maximo - minimo + 1.
"""

from typing import Any, Callable, List, Sequence

try:
    from src.contrato import Metricas
except ImportError:  # permite rodar o arquivo direto, sem pacote
    from contrato import Metricas  # type: ignore

ChaveInteira = Callable[[Any], int]


def counting_sort(
    lista: Sequence[Any],
    chave: ChaveInteira,
    metricas: Metricas | None = None,
    minimo: int = 0,
    maximo: int = 100,
) -> List[Any]:
    """
    Ordena por chave inteira no intervalo [minimo, maximo].

    O intervalo e parametro, e nao descoberto a partir dos dados, de
    proposito: no catalogo ele e conhecido pelo dominio (popularidade
    do Spotify vai de 0 a 100). Descobrir o minimo e o maximo custaria
    uma passada extra sobre a entrada sem necessidade.
    """
    if maximo < minimo:
        raise ValueError("maximo precisa ser >= minimo")

    m = metricas if metricas is not None else Metricas()
    entrada = list(lista)
    n = len(entrada)

    if n == 0:
        return []

    k = maximo - minimo + 1
    contagem = [0] * k

    for elemento in entrada:
        valor = chave(elemento)
        if valor < minimo or valor > maximo:
            raise ValueError(
                f"chave {valor} fora do intervalo [{minimo}, {maximo}]"
            )
        contagem[valor - minimo] += 1

    for i in range(1, k):
        contagem[i] += contagem[i - 1]

    # A distribuição inversa preserva a ordem relativa das chaves iguais.
    saida: List[Any] = [None] * n  # type: ignore[list-item]
    for i in range(n - 1, -1, -1):
        elemento = entrada[i]
        indice = chave(elemento) - minimo
        contagem[indice] -= 1
        saida[contagem[indice]] = elemento
        m.movimentacoes += 1

    return saida


def top_n_por_popularidade(
    lista: Sequence[Any],
    n: int,
    chave: ChaveInteira,
    metricas: Metricas | None = None,
) -> List[Any]:
    """
    Os n mais populares, do maior para o menor.

    Ordena crescente com o Counting e inverte a fatia final. Inverter
    uma lista e O(n) e nao desfaz a estabilidade de forma relevante
    aqui, porque a fatia ja esta na ordem desejada dentro de cada valor
    de popularidade.
    """
    ordenada = counting_sort(lista, chave, metricas)
    return list(reversed(ordenada))[:n]
