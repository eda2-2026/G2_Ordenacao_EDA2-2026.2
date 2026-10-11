"""
Executa os cenários de ordenação e grava tempos e métricas em
resultados/benchmark.csv.
"""

import argparse
import csv
import os
import statistics
import sys
import time
from typing import Any, Callable, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from contrato import (  # noqa: E402
    Faixa,
    Metricas,
    por_album,
    por_artista,
    por_duracao,
    por_nome,
    por_popularidade,
    verificar_ordenado,
)
from dados.carregar import amostrar, carregar, resumo  # noqa: E402
from ordenacao.counting_sort import counting_sort  # noqa: E402

# Algoritmos da parte A são opcionais até seus arquivos estarem disponíveis.
try:
    from ordenacao.merge_sort import merge_sort, ordenar_multichave
    from ordenacao.radix_lsd import radix_lsd
    PARTE_A_DISPONIVEL = True
except ImportError:
    PARTE_A_DISPONIVEL = False

TAMANHOS = [1_000, 5_000, 10_000, 25_000, 50_000, 100_000]
TAMANHOS_RAPIDO = [1_000, 5_000, 10_000]
REPETICOES = 5
PASTA_RESULTADOS = "resultados"


def medir(
    funcao: Callable[..., List[Any]],
    entrada: List[Faixa],
    repeticoes: int = REPETICOES,
    **kwargs: Any,
) -> dict:
    """Executa repetidas vezes e retorna a mediana do tempo e as métricas."""
    tempos: List[float] = []
    metricas = Metricas()
    saida: List[Any] = []

    for i in range(repeticoes):
        m = Metricas()
        inicio = time.perf_counter()
        saida = funcao(entrada, metricas=m, **kwargs)
        tempos.append(time.perf_counter() - inicio)
        if i == 0:
            metricas = m

    return {
        "tempo_ms": statistics.median(tempos) * 1000,
        "comparacoes": metricas.comparacoes,
        "movimentacoes": metricas.movimentacoes,
        "saida": saida,
    }


def linha(texto: str = "") -> None:
    print(texto, flush=True)


def executar(tamanhos: List[int]) -> List[dict]:
    linha("Carregando catalogo...")
    catalogo = carregar()
    linha(f"  {resumo(catalogo)}")
    linha()

    if not PARTE_A_DISPONIVEL:
        linha("AVISO: merge_sort.py e radix_lsd.py ainda nao estao no projeto.")
        linha("       Rodando apenas o Counting Sort.")
        linha()

    resultados: List[dict] = []

    for n in tamanhos:
        entrada = amostrar(catalogo, n)
        linha(f"n = {n:,}".replace(",", "."))

        # --- Cenario 1: popularidade (k = 101) ---------------------------
        r = medir(counting_sort, entrada, chave=por_popularidade)
        assert verificar_ordenado(r["saida"], por_popularidade)
        resultados.append({
            "n": n, "cenario": "popularidade", "algoritmo": "Counting Sort",
            "tempo_ms": r["tempo_ms"], "comparacoes": r["comparacoes"],
            "movimentacoes": r["movimentacoes"],
        })
        linha(f"  Counting (popularidade) : {r['tempo_ms']:8.2f} ms | "
              f"{r['comparacoes']:>10,} comp | {r['movimentacoes']:>10,} mov"
              .replace(",", "."))

        if PARTE_A_DISPONIVEL:
            r = medir(merge_sort, entrada, chave=por_popularidade)
            assert verificar_ordenado(r["saida"], por_popularidade)
            resultados.append({
                "n": n, "cenario": "popularidade", "algoritmo": "Merge Sort",
                "tempo_ms": r["tempo_ms"], "comparacoes": r["comparacoes"],
                "movimentacoes": r["movimentacoes"],
            })
            linha(f"  Merge    (popularidade) : {r['tempo_ms']:8.2f} ms | "
                  f"{r['comparacoes']:>10,} comp | {r['movimentacoes']:>10,} mov"
                  .replace(",", "."))

            # --- Cenario 2: duracao (k ~ 5.000.000) ----------------------
            r = medir(radix_lsd, entrada, chave=por_duracao)
            assert verificar_ordenado(r["saida"], por_duracao)
            resultados.append({
                "n": n, "cenario": "duracao", "algoritmo": "Radix LSD",
                "tempo_ms": r["tempo_ms"], "comparacoes": r["comparacoes"],
                "movimentacoes": r["movimentacoes"],
            })
            linha(f"  Radix    (duracao)      : {r['tempo_ms']:8.2f} ms | "
                  f"{r['comparacoes']:>10,} comp | {r['movimentacoes']:>10,} mov"
                  .replace(",", "."))

            r = medir(merge_sort, entrada, chave=por_duracao)
            assert verificar_ordenado(r["saida"], por_duracao)
            resultados.append({
                "n": n, "cenario": "duracao", "algoritmo": "Merge Sort",
                "tempo_ms": r["tempo_ms"], "comparacoes": r["comparacoes"],
                "movimentacoes": r["movimentacoes"],
            })
            linha(f"  Merge    (duracao)      : {r['tempo_ms']:8.2f} ms | "
                  f"{r['comparacoes']:>10,} comp | {r['movimentacoes']:>10,} mov"
                  .replace(",", "."))

            # --- Cenario 3: biblioteca (chave string, multi-chave) -------
            r = medir(
                ordenar_multichave,
                entrada,
                repeticoes=max(1, REPETICOES // 2),
                chaves=[por_artista, por_album, por_nome],
            )
            resultados.append({
                "n": n, "cenario": "biblioteca", "algoritmo": "Merge Sort (3 chaves)",
                "tempo_ms": r["tempo_ms"], "comparacoes": r["comparacoes"],
                "movimentacoes": r["movimentacoes"],
            })
            linha(f"  Merge    (biblioteca)   : {r['tempo_ms']:8.2f} ms | "
                  f"{r['comparacoes']:>10,} comp | {r['movimentacoes']:>10,} mov"
                  .replace(",", "."))

        linha()

    return resultados


def salvar(resultados: List[dict]) -> str:
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    caminho = os.path.join(PASTA_RESULTADOS, "benchmark.csv")

    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        campos = ["n", "cenario", "algoritmo", "tempo_ms", "comparacoes", "movimentacoes"]
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for r in resultados:
            escritor.writerow({c: r[c] for c in campos})

    return caminho


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark de ordenacao do catalogo")
    parser.add_argument("--rapido", action="store_true",
                        help="roda apenas os tamanhos pequenos")
    args = parser.parse_args()

    tamanhos = TAMANHOS_RAPIDO if args.rapido else TAMANHOS

    resultados = executar(tamanhos)
    caminho = salvar(resultados)

    linha(f"Resultados salvos em {caminho}")
    linha("Para gerar os graficos: python src/graficos.py")


if __name__ == "__main__":
    main()
