"""
Merge Sort — ordenacao por comparacao, estavel, O(n log n) garantido.

Por que este algoritmo esta no catalogo
---------------------------------------
A tela "biblioteca" do catalogo precisa listar as faixas agrupadas por
artista, e dentro de cada artista agrupadas por album. Isso e ordenacao
multi-chave, e multi-chave por passadas sucessivas SO FUNCIONA com um
algoritmo estavel: a passada seguinte precisa preservar a ordem que a
anterior estabeleceu entre elementos de chave igual.

Um algoritmo instavel (Quick Sort, Heap Sort, Shell Sort) embaralharia
as faixas dentro de cada album. Nao e questao de velocidade — e questao
de a saida estar certa ou errada.

Complexidade
------------
  Tempo  : O(n log n) em TODOS os casos (melhor, medio e pior).
           A recursao sempre divide ao meio, independentemente do
           conteudo. Nao existe entrada que degrade o Merge Sort.
  Espaco : O(n) — precisa do vetor auxiliar na intercalacao. E o preco
           que se paga pela garantia acima.
  Estavel: sim, desde que a intercalacao desempate pela esquerda.
"""

from typing import Any, List, Sequence

try:
    from src.contrato import Chave, Metricas, identidade
except ImportError:  # permite rodar o arquivo direto, sem pacote
    from contrato import Chave, Metricas, identidade  # type: ignore


def merge_sort(
    lista: Sequence[Any],
    chave: Chave = identidade,
    metricas: Metricas | None = None,
) -> List[Any]:
    """
    Ordena `lista` segundo `chave` e devolve uma lista nova.

    A entrada nao e modificada.
    """
    m = metricas if metricas is not None else Metricas()
    return _merge_sort(list(lista), chave, m)


def _merge_sort(lista: List[Any], chave: Chave, m: Metricas) -> List[Any]:
    # Caso base: uma lista de 0 ou 1 elemento ja esta ordenada.
    if len(lista) <= 1:
        return lista

    meio = len(lista) // 2
    esquerda = _merge_sort(lista[:meio], chave, m)
    direita = _merge_sort(lista[meio:], chave, m)

    return _intercalar(esquerda, direita, chave, m)


def _intercalar(
    esquerda: List[Any],
    direita: List[Any],
    chave: Chave,
    m: Metricas,
) -> List[Any]:
    """
    Intercala duas listas ja ordenadas.

    O DETALHE QUE DECIDE A ESTABILIDADE esta na condicao abaixo.

    Usamos `chave(direita[j]) < chave(esquerda[i])`, com menor ESTRITO,
    e consumimos da direita apenas quando ela e estritamente menor. No
    empate, o `else` consome da esquerda.

    Como a metade esquerda vem antes da direita no vetor original,
    desempatar pela esquerda preserva a ordem de entrada. Se a condicao
    fosse `<=`, o empate consumiria da direita primeiro e o algoritmo
    deixaria de ser estavel — sem nenhum outro sintoma visivel, porque o
    resultado continuaria ordenado. E um bug que so aparece em
    ordenacao multi-chave.
    """
    saida: List[Any] = []
    i = j = 0

    while i < len(esquerda) and j < len(direita):
        m.comparacoes += 1
        if chave(direita[j]) < chave(esquerda[i]):
            saida.append(direita[j])
            j += 1
        else:
            saida.append(esquerda[i])
            i += 1
        m.movimentacoes += 1

    # Sobras: no maximo uma das duas listas ainda tem elementos.
    while i < len(esquerda):
        saida.append(esquerda[i])
        i += 1
        m.movimentacoes += 1

    while j < len(direita):
        saida.append(direita[j])
        j += 1
        m.movimentacoes += 1

    return saida


def ordenar_multichave(
    lista: Sequence[Any],
    chaves: Sequence[Chave],
    metricas: Metricas | None = None,
) -> List[Any]:
    """
    Ordenacao por varias chaves, da mais significativa para a menos.

        ordenar_multichave(faixas, [por_artista, por_album, por_nome])

    produz a biblioteca agrupada por artista, e dentro de cada artista
    por album, e dentro de cada album por nome da faixa.

    COMO FUNCIONA: as passadas sao aplicadas na ordem INVERSA — primeiro
    a chave menos significativa (nome), por ultimo a mais significativa
    (artista). Cada passada estavel preserva a ordem imposta pelas
    anteriores, entao ao final todas as chaves valem simultaneamente,
    com a precedencia correta.

    Isso e exatamente a mesma ideia do Radix Sort LSD, que processa os
    digitos do menos para o mais significativo pelo mesmo motivo. A
    diferenca e que aqui os "digitos" sao campos do registro, e a
    passada e um Merge Sort em vez de um Counting Sort.

    Depende inteiramente da estabilidade. Com um algoritmo instavel este
    metodo simplesmente nao existe.
    """
    m = metricas if metricas is not None else Metricas()
    saida = list(lista)

    for chave in reversed(list(chaves)):
        saida = merge_sort(saida, chave, m)

    return saida
