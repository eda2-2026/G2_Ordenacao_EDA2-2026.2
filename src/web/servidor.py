"""
Servidor da interface de visualizacao do catalogo.

NAO reimplementa nenhum algoritmo. Ele importa exatamente as mesmas
funcoes que o benchmark usa e as executa sob demanda, instrumentadas.
Essa e a razao de a interface valer alguma coisa como evidencia: o que
a tela mostra e o codigo que esta sendo avaliado, nao uma simulacao
dele.

Usa apenas a biblioteca padrao (http.server). Nenhuma dependencia nova
alem do matplotlib, que ja era usado pelos graficos estaticos.

Rodar:
    python src/web/servidor.py

Depois abrir http://localhost:8002
"""

import json
import os
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(RAIZ))

from contrato import (  # noqa: E402
    Metricas,
    por_album,
    por_artista,
    por_duracao,
    por_nome,
    por_popularidade,
    verificar_ordenado,
)
from dados.carregar import carregar, amostrar, resumo  # noqa: E402
from ordenacao.counting_sort import counting_sort  # noqa: E402
from ordenacao.merge_sort import merge_sort, ordenar_multichave  # noqa: E402
from ordenacao.radix_lsd import digitos_necessarios, radix_lsd  # noqa: E402

ESTATICOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
PORTA = 8002

# Catalogo carregado uma unica vez, na subida do servidor — mesmo ciclo
# de vida do index-store do trabalho anterior.
CATALOGO: List[Any] = []
RESUMO = ""


# ---------------------------------------------------------------------------
# Cenarios
#
# Cada cenario amarra uma tela do catalogo a uma chave e aos algoritmos
# que se aplicam a ela. E a tabela da secao 3 do README, em codigo.
# ---------------------------------------------------------------------------

CENARIOS = {
    "biblioteca": {
        "titulo": "Biblioteca",
        "descricao": "artista, depois album, depois faixa",
        "chave_texto": "tres strings",
        "algoritmos": ["Merge Sort"],
        "motivo_exclusao": "Counting e Radix nao se aplicam a chave string: "
                           "nao existe contagem para texto arbitrario.",
    },
    "popularidade": {
        "titulo": "Top por popularidade",
        "descricao": "popularidade de 0 a 100, do maior para o menor",
        "chave_texto": "inteiro 0..100  (k = 101)",
        "algoritmos": ["Counting Sort", "Merge Sort"],
        "motivo_exclusao": "",
    },
    "duracao": {
        "titulo": "Faixas mais longas",
        "descricao": "duracao em milissegundos",
        "chave_texto": "inteiro ate ~5.000.000",
        "algoritmos": ["Radix LSD", "Merge Sort"],
        "motivo_exclusao": "Counting precisaria de um vetor de contagem de "
                           "5 milhoes de posicoes.",
    },
}

TAMANHOS_ESCALA = [1_000, 2_500, 5_000, 10_000, 25_000, 50_000]


def _executar(algoritmo: str, cenario: str, entrada: List[Any]) -> Dict[str, Any]:
    """Roda um algoritmo sobre a entrada e devolve saida + metricas."""
    m = Metricas()
    inicio = time.perf_counter()

    if cenario == "popularidade":
        if algoritmo == "Counting Sort":
            saida = counting_sort(entrada, por_popularidade, m)
        else:
            saida = merge_sort(entrada, por_popularidade, m)
        chave_verificacao = por_popularidade

    elif cenario == "duracao":
        if algoritmo == "Radix LSD":
            saida = radix_lsd(entrada, por_duracao, m)
        else:
            saida = merge_sort(entrada, por_duracao, m)
        chave_verificacao = por_duracao

    else:  # biblioteca
        saida = ordenar_multichave(
            entrada, [por_artista, por_album, por_nome], m
        )
        chave_verificacao = None

    ms = (time.perf_counter() - inicio) * 1000

    return {
        "algoritmo": algoritmo,
        "ms": round(ms, 3),
        "comparacoes": m.comparacoes,
        "movimentacoes": m.movimentacoes,
        "ordenado": (
            verificar_ordenado(saida, chave_verificacao)
            if chave_verificacao is not None
            else True
        ),
        "saida": saida,
    }


def _serializar(faixas: List[Any], limite: int, inverter: bool) -> List[Dict]:
    sequencia = list(reversed(faixas)) if inverter else faixas
    return [
        {
            "nome": f.nome,
            "artista": f.artista,
            "album": f.album,
            "popularidade": f.popularidade,
            "duracao_ms": f.duracao_ms,
        }
        for f in sequencia[:limite]
    ]


def api_catalogo(params: Dict[str, List[str]]) -> Dict[str, Any]:
    """Ordena e devolve as primeiras faixas, com as metricas da execucao."""
    cenario = params.get("cenario", ["popularidade"])[0]
    if cenario not in CENARIOS:
        raise ValueError(f"cenario desconhecido: {cenario}")

    n = min(int(params.get("n", ["10000"])[0]), len(CATALOGO))
    limite = int(params.get("limite", ["40"])[0])

    entrada = amostrar(CATALOGO, n)
    principal = CENARIOS[cenario]["algoritmos"][0]
    r = _executar(principal, cenario, entrada)

    # "Top por popularidade" e "mais longas" sao do maior para o menor;
    # os algoritmos ordenam crescente, entao a tela inverte.
    inverter = cenario in ("popularidade", "duracao")

    return {
        "cenario": cenario,
        "meta": CENARIOS[cenario],
        "n": n,
        "algoritmo": r["algoritmo"],
        "ms": r["ms"],
        "comparacoes": r["comparacoes"],
        "movimentacoes": r["movimentacoes"],
        "ordenado": r["ordenado"],
        "faixas": _serializar(r["saida"], limite, inverter),
    }


def api_comparar(params: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Roda TODOS os algoritmos aplicaveis ao cenario sobre a MESMA entrada
    e confere que produzem exatamente a mesma saida.

    A conferencia vem antes da comparacao de tempos, pelo mesmo motivo
    do trabalho anterior: comparar tempos de saidas diferentes nao mede
    nada. A verificacao e por identidade de objeto, elemento a elemento,
    entao ela tambem prova estabilidade — duas ordenacoes estaveis da
    mesma entrada sao necessariamente identicas.
    """
    cenario = params.get("cenario", ["popularidade"])[0]
    if cenario not in CENARIOS:
        raise ValueError(f"cenario desconhecido: {cenario}")

    n = min(int(params.get("n", ["10000"])[0]), len(CATALOGO))
    entrada = amostrar(CATALOGO, n)

    execucoes = [
        _executar(alg, cenario, entrada)
        for alg in CENARIOS[cenario]["algoritmos"]
    ]

    identicas = True
    if len(execucoes) > 1:
        referencia = execucoes[0]["saida"]
        for outra in execucoes[1:]:
            if len(outra["saida"]) != len(referencia):
                identicas = False
                break
            if not all(a is b for a, b in zip(referencia, outra["saida"])):
                identicas = False
                break

    extra = {}
    if cenario == "duracao" and entrada:
        maior = max(por_duracao(f) for f in entrada)
        extra["passadas_radix"] = digitos_necessarios(maior, 10)
        extra["maior_duracao"] = maior

    return {
        "cenario": cenario,
        "meta": CENARIOS[cenario],
        "n": n,
        "identicas": identicas,
        "resultados": [
            {k: v for k, v in r.items() if k != "saida"} for r in execucoes
        ],
        **extra,
    }


def api_escala(params: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Roda os algoritmos do cenario em tamanhos crescentes.

    E o que alimenta o grafico de comparacoes x n: a curva do Merge
    cresce como n log n enquanto Counting e Radix ficam fixos em zero.
    """
    cenario = params.get("cenario", ["popularidade"])[0]
    if cenario not in CENARIOS:
        raise ValueError(f"cenario desconhecido: {cenario}")

    teto = min(int(params.get("teto", ["25000"])[0]), len(CATALOGO))
    tamanhos = [t for t in TAMANHOS_ESCALA if t <= teto]

    series: Dict[str, List[Dict]] = {
        alg: [] for alg in CENARIOS[cenario]["algoritmos"]
    }

    for n in tamanhos:
        entrada = amostrar(CATALOGO, n)
        for alg in CENARIOS[cenario]["algoritmos"]:
            r = _executar(alg, cenario, entrada)
            series[alg].append({
                "n": n,
                "ms": r["ms"],
                "comparacoes": r["comparacoes"],
                "movimentacoes": r["movimentacoes"],
            })

    return {"cenario": cenario, "tamanhos": tamanhos, "series": series}


ROTAS = {
    "/api/catalogo": api_catalogo,
    "/api/comparar": api_comparar,
    "/api/escala": api_escala,
}


class Handler(BaseHTTPRequestHandler):

    def _json(self, dados: Dict, status: int = 200) -> None:
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _arquivo(self, caminho: str) -> None:
        tipos = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }
        extensao = os.path.splitext(caminho)[1]

        try:
            with open(caminho, "rb") as arquivo:
                corpo = arquivo.read()
        except FileNotFoundError:
            self._json({"erro": "nao encontrado"}, 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", tipos.get(extensao, "text/plain"))
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)

        if url.path in ROTAS:
            try:
                self._json(ROTAS[url.path](parse_qs(url.query)))
            except Exception as erro:  # devolve o erro para a tela
                self._json({"erro": str(erro)}, 400)
            return

        if url.path == "/api/info":
            self._json({
                "resumo": RESUMO,
                "total": len(CATALOGO),
                "cenarios": CENARIOS,
                "tamanhos": TAMANHOS_ESCALA,
            })
            return

        nome = "index.html" if url.path == "/" else url.path.lstrip("/")
        self._arquivo(os.path.join(ESTATICOS, os.path.basename(nome)))

    def log_message(self, formato: str, *args: Any) -> None:
        return  # silencia o log de requisicao, que polui a demonstracao


def main() -> None:
    global CATALOGO, RESUMO

    print("Carregando catalogo...")
    try:
        CATALOGO = carregar()
    except FileNotFoundError as erro:
        print(erro)
        sys.exit(1)

    RESUMO = resumo(CATALOGO)
    print(f"  {RESUMO}")

    # Aquecimento: a primeira execucao de qualquer funcao Python paga
    # custos de inicializacao que nao tem nada a ver com o algoritmo.
    # Sem isso, o primeiro numero que a tela mostra e sempre o pior, e
    # numa gravacao isso aparece.
    print("Aquecendo...")
    amostra = amostrar(CATALOGO, min(2000, len(CATALOGO)))
    for cenario in CENARIOS:
        for alg in CENARIOS[cenario]["algoritmos"]:
            _executar(alg, cenario, amostra)

    endereco = f"http://localhost:{PORTA}"
    print(f"\nServidor em {endereco}\nCtrl+C para parar.\n")

    try:
        webbrowser.open(endereco)
    except Exception:
        pass

    HTTPServer(("", PORTA), Handler).serve_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServidor parado.")
