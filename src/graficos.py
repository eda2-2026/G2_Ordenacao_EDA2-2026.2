"""
Gera gráficos de tempo e comparações a partir de resultados/benchmark.csv.
"""

import csv
import os
import sys
from collections import defaultdict

try:
    import matplotlib
    matplotlib.use("Agg")  # backend sem janela, funciona em qualquer ambiente
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib nao esta instalado. Rode: pip install matplotlib")
    sys.exit(1)

PASTA = "resultados"
ENTRADA = os.path.join(PASTA, "benchmark.csv")

CORES = {
    "Counting Sort": "#2563eb",
    "Radix LSD": "#16a34a",
    "Merge Sort": "#dc2626",
    "Merge Sort (3 chaves)": "#9333ea",
}
MARCADORES = {
    "Counting Sort": "o",
    "Radix LSD": "s",
    "Merge Sort": "^",
    "Merge Sort (3 chaves)": "D",
}


def ler():
    if not os.path.exists(ENTRADA):
        print(f"Nao encontrei '{ENTRADA}'. Rode antes: python src/benchmark.py")
        sys.exit(1)

    dados = defaultdict(lambda: defaultdict(list))
    with open(ENTRADA, encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            cenario = linha["cenario"]
            algoritmo = linha["algoritmo"]
            dados[cenario][algoritmo].append({
                "n": int(linha["n"]),
                "tempo_ms": float(linha["tempo_ms"]),
                "comparacoes": int(linha["comparacoes"]),
                "movimentacoes": int(linha["movimentacoes"]),
            })
    return dados


def grafico_tempo(dados, cenario: str, titulo: str, arquivo: str) -> None:
    if cenario not in dados:
        print(f"  (sem dados para '{cenario}', pulando)")
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    for algoritmo, pontos in sorted(dados[cenario].items()):
        pontos.sort(key=lambda p: p["n"])
        ax.plot(
            [p["n"] for p in pontos],
            [p["tempo_ms"] for p in pontos],
            marker=MARCADORES.get(algoritmo, "o"),
            color=CORES.get(algoritmo),
            linewidth=2,
            markersize=6,
            label=algoritmo,
        )

    ax.set_xlabel("n (numero de faixas)")
    ax.set_ylabel("tempo (ms)")
    ax.set_title(titulo)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    destino = os.path.join(PASTA, arquivo)
    fig.savefig(destino, dpi=150)
    plt.close(fig)
    print(f"  {destino}")


def grafico_comparacoes(dados) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    tem_dado = False

    for cenario, algoritmos in dados.items():
        for algoritmo, pontos in algoritmos.items():
            pontos.sort(key=lambda p: p["n"])
            comparacoes = [max(p["comparacoes"], 0.5) for p in pontos]  # log nao aceita 0
            ax.plot(
                [p["n"] for p in pontos],
                comparacoes,
                marker=MARCADORES.get(algoritmo, "o"),
                color=CORES.get(algoritmo),
                linewidth=2,
                markersize=6,
                label=f"{algoritmo} ({cenario})",
                alpha=0.85,
            )
            tem_dado = True

    if not tem_dado:
        plt.close(fig)
        return

    ax.set_yscale("log")
    ax.set_xlabel("n (numero de faixas)")
    ax.set_ylabel("comparacoes (escala log)")
    ax.set_title("Comparacoes entre elementos\n"
                 "Counting e Radix ficam em zero: nao sao algoritmos comparativos")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    destino = os.path.join(PASTA, "comparacoes.png")
    fig.savefig(destino, dpi=150)
    plt.close(fig)
    print(f"  {destino}")


def main() -> None:
    dados = ler()
    print("Gerando graficos:")

    grafico_tempo(
        dados, "popularidade",
        "Ordenacao por popularidade (chave inteira 0..100, k=101)",
        "tempo-popularidade.png",
    )
    grafico_tempo(
        dados, "duracao",
        "Ordenacao por duracao (chave inteira ate ~5.000.000)",
        "tempo-duracao.png",
    )
    grafico_comparacoes(dados)


if __name__ == "__main__":
    main()
