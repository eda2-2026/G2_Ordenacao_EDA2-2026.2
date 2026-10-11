"""
Radix Sort LSD — ordenacao por digitos, estavel, O(d * (n + b)).

Por que este algoritmo esta no catalogo
---------------------------------------
A tela "faixas mais longas" ordena por `duracao_ms`, um inteiro que vai
de alguns milhares a alguns milhoes. Nao da para usar Counting Sort
direto: k seria da ordem de 5.000.000 e o vetor de contagem gastaria
mais memoria que o proprio catalogo.

O Radix LSD resolve isso processando a chave em digitos. Cada passada e
um Counting Sort sobre UM digito, com k = base (10, ou 256 se
trabalharmos em bytes). Em vez de um vetor de 5 milhoes de posicoes,
sao 7 passadas sobre um vetor de 10.

Complexidade
------------
  Tempo  : O(d * (n + b)), onde d = numero de digitos e b = base.
           Com d e b fixos (duracao sempre cabe em 7 digitos decimais),
           isso e O(n) — linear.
  Espaco : O(n + b).
  Estavel: sim, e OBRIGATORIAMENTE. A estabilidade nao e um bonus aqui,
           e o que faz o algoritmo funcionar: a passada do digito i+1 so
           produz resultado correto porque a passada do digito i deixou
           os empates na ordem certa. Um Radix com passada instavel
           devolve lixo.

Comparacoes: ZERO
-----------------
O Radix nunca compara dois elementos entre si. Ele le um digito e usa
esse valor como indice de um vetor. Por isso o contador de comparacoes
termina em zero, e por isso o limite inferior de Omega(n log n) — que
vale para ordenacao POR COMPARACAO — nao se aplica a ele. Nao e que o
algoritmo "quebre" o limite: ele esta fora do escopo do teorema.
"""

from typing import Any, Callable, List, Sequence

try:
    from src.contrato import Metricas
except ImportError:  # permite rodar o arquivo direto, sem pacote
    from contrato import Metricas  # type: ignore

# A chave do Radix precisa devolver inteiro nao-negativo.
ChaveInteira = Callable[[Any], int]


def radix_lsd(
    lista: Sequence[Any],
    chave: ChaveInteira,
    metricas: Metricas | None = None,
    base: int = 10,
) -> List[Any]:
    """
    Ordena por chave inteira nao-negativa, do digito menos significativo
    para o mais significativo.

    `base` controla o numero de passadas: base 10 da mais passadas com
    vetor de contagem pequeno; base 256 da menos passadas com vetor
    maior. Os dois extremos sao bons material de experimento — vale
    medir, e a curva nao e monotona.
    """
    if base < 2:
        raise ValueError("base precisa ser >= 2")

    m = metricas if metricas is not None else Metricas()
    saida = list(lista)

    # A validacao vem ANTES de qualquer atalho por tamanho: uma lista de
    # um unico elemento com chave negativa tambem precisa ser rejeitada.
    # (Este bug existiu nesta funcao e foi pego pelo teste.)
    maximo = 0
    for elemento in saida:
        valor = chave(elemento)
        if valor < 0:
            raise ValueError(
                "Radix LSD desta implementacao nao aceita chave negativa; "
                f"recebeu {valor}"
            )
        if valor > maximo:
            maximo = valor

    # Uma passada por digito, do menos para o mais significativo.
    expoente = 1
    while maximo // expoente > 0:
        saida = _passada_por_digito(saida, chave, expoente, base, m)
        expoente *= base

    return saida


def _passada_por_digito(
    lista: List[Any],
    chave: ChaveInteira,
    expoente: int,
    base: int,
    m: Metricas,
) -> List[Any]:
    """
    Counting Sort estavel sobre um unico digito.

    A estabilidade vem do ultimo laco, que percorre a entrada DE TRAS
    PARA A FRENTE enquanto decrementa o indice acumulado. Percorrer de
    frente para tras inverteria a ordem relativa dos empates e quebraria
    o Radix inteiro.
    """
    n = len(lista)
    contagem = [0] * base

    # 1. Conta quantos elementos tem cada digito.
    for elemento in lista:
        digito = (chave(elemento) // expoente) % base
        contagem[digito] += 1

    # 2. Soma de prefixos: contagem[d] passa a ser a posicao FINAL
    #    (exclusiva) do ultimo elemento de digito d.
    for d in range(1, base):
        contagem[d] += contagem[d - 1]

    # 3. Distribui, de tras para a frente, para preservar estabilidade.
    saida: List[Any] = [None] * n  # type: ignore[list-item]
    for i in range(n - 1, -1, -1):
        elemento = lista[i]
        digito = (chave(elemento) // expoente) % base
        contagem[digito] -= 1
        saida[contagem[digito]] = elemento
        m.movimentacoes += 1

    # Nenhuma comparacao entre elementos foi feita nesta passada.
    return saida


def digitos_necessarios(valor_maximo: int, base: int = 10) -> int:
    """Quantas passadas o Radix fara para um valor maximo dado."""
    if valor_maximo <= 0:
        return 1
    d = 0
    while valor_maximo > 0:
        valor_maximo //= base
        d += 1
    return d
