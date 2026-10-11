"""
Validacao do Merge Sort e do Radix LSD contra uma referencia confiavel.

A ideia e a mesma do script de validacao da busca binaria no trabalho
anterior: nao confiar que "o resultado parece certo". Aqui a referencia
e o `sorted()` do CPython, que usa Timsort e e GARANTIDAMENTE estavel —
isso esta na especificacao da linguagem, nao e detalhe de implementacao.

Tres niveis de verificacao, do mais fraco ao mais forte:

  1. ESTA ORDENADO   — a saida e nao-decrescente. Fraco: um algoritmo que
                       descartasse elementos passaria.
  2. MESMO CONTEUDO  — a saida e uma permutacao da entrada. Pega perda e
                       duplicacao de elementos.
  3. ESTAVEL         — a saida e identica, OBJETO A OBJETO (`is`), a do
                       sorted(). Este e o unico que pega troca de ordem
                       entre empates, que e o bug silencioso que motiva
                       o teste inteiro.

O nivel 3 usa identidade de objeto de proposito. Comparar por valor
(`==`) nao serviria: dois registros com a mesma chave sao iguais o
bastante para passar, e e exatamente a ordem entre eles que queremos
verificar.

Rodar:
    python -m unittest discover -s tests -v
ou
    python tests/test_estabilidade.py
"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from contrato import Faixa, Metricas, verificar_ordenado  # noqa: E402
from ordenacao.merge_sort import merge_sort, ordenar_multichave  # noqa: E402
from ordenacao.radix_lsd import digitos_necessarios, radix_lsd  # noqa: E402

SEMENTE = 42


def catalogo_sintetico(n: int, semente: int = SEMENTE) -> list[Faixa]:
    """
    Gera um catalogo com MUITOS empates de proposito.

    Poucos artistas e poucos albuns garantem que as chaves se repitam
    bastante. Sem empates em quantidade, nenhum teste de estabilidade
    tem o que testar — uma lista sem chaves repetidas tem uma unica
    ordenacao possivel, e ate um algoritmo instavel acerta.
    """
    rng = random.Random(semente)
    artistas = [f"Artista {chr(65 + i)}" for i in range(8)]
    albuns = [f"Album {i}" for i in range(12)]
    generos = ["rock", "pop", "jazz", "mpb"]

    return [
        Faixa(
            track_id=f"t{i:06d}",
            nome=f"Faixa {i:05d}",
            artista=rng.choice(artistas),
            album=rng.choice(albuns),
            popularidade=rng.randint(0, 100),
            duracao_ms=rng.randint(30_000, 600_000),
            genero=rng.choice(generos),
        )
        for i in range(n)
    ]


class TestMergeSort(unittest.TestCase):

    def test_ordena_e_preserva_conteudo(self):
        for n in (0, 1, 2, 3, 17, 1000):
            with self.subTest(n=n):
                entrada = catalogo_sintetico(n)
                saida = merge_sort(entrada, chave=lambda f: f.popularidade)

                self.assertEqual(len(saida), n)
                self.assertTrue(
                    verificar_ordenado(saida, lambda f: f.popularidade)
                )
                self.assertCountEqual(
                    [f.track_id for f in entrada],
                    [f.track_id for f in saida],
                )

    def test_nao_modifica_a_entrada(self):
        entrada = catalogo_sintetico(500)
        copia_ids = [f.track_id for f in entrada]

        merge_sort(entrada, chave=lambda f: f.popularidade)

        self.assertEqual([f.track_id for f in entrada], copia_ids)

    def test_estabilidade_contra_sorted(self):
        """
        O teste central. `is` em vez de `==`, por identidade de objeto.
        """
        entrada = catalogo_sintetico(2000)
        chave = lambda f: f.popularidade  # noqa: E731

        nossa = merge_sort(entrada, chave=chave)
        referencia = sorted(entrada, key=chave)

        for i, (a, b) in enumerate(zip(nossa, referencia)):
            self.assertIs(a, b, f"divergencia na posicao {i}")

    def test_entradas_degeneradas(self):
        """
        Ja ordenada, inversa e toda igual. O Merge Sort nao tem pior
        caso de entrada, entao os tres devem passar — e as metricas
        devem ficar na mesma ordem de grandeza, o que e justamente o
        argumento a favor dele.
        """
        base = catalogo_sintetico(1000)
        chave = lambda f: f.popularidade  # noqa: E731

        casos = {
            "aleatoria": base,
            "ja_ordenada": sorted(base, key=chave),
            "inversa": sorted(base, key=chave, reverse=True),
            "toda_igual": [
                Faixa(f"t{i}", f"n{i}", "A", "X", 50, 1000, "rock")
                for i in range(1000)
            ],
        }

        for nome, entrada in casos.items():
            with self.subTest(caso=nome):
                m = Metricas()
                saida = merge_sort(entrada, chave=chave, metricas=m)
                self.assertTrue(verificar_ordenado(saida, chave))
                self.assertEqual(len(saida), len(entrada))

    def test_multichave_agrupa_corretamente(self):
        """
        Artista -> album -> nome. Verifica que as tres chaves valem
        simultaneamente com a precedencia certa.
        """
        entrada = catalogo_sintetico(3000)
        saida = ordenar_multichave(
            entrada,
            [
                lambda f: f.artista.lower(),
                lambda f: f.album.lower(),
                lambda f: f.nome.lower(),
            ],
        )

        for i in range(1, len(saida)):
            ant, atual = saida[i - 1], saida[i]
            chave_ant = (ant.artista.lower(), ant.album.lower(), ant.nome.lower())
            chave_atual = (atual.artista.lower(), atual.album.lower(), atual.nome.lower())
            self.assertLessEqual(chave_ant, chave_atual, f"fora de ordem em {i}")


class TestRadixLSD(unittest.TestCase):

    def test_ordena_por_duracao(self):
        for n in (0, 1, 2, 500, 5000):
            with self.subTest(n=n):
                entrada = catalogo_sintetico(n)
                saida = radix_lsd(entrada, chave=lambda f: f.duracao_ms)

                self.assertEqual(len(saida), n)
                self.assertTrue(verificar_ordenado(saida, lambda f: f.duracao_ms))

    def test_estabilidade_contra_sorted(self):
        """
        Estabilidade no Radix nao e bonus, e requisito: sem ela as
        passadas seguintes produzem lixo. Com duracoes sorteadas num
        intervalo estreito forcamos empates suficientes para o teste
        ter o que verificar.
        """
        rng = random.Random(SEMENTE)
        entrada = [
            Faixa(f"t{i}", f"n{i}", "A", "X", 50, rng.randint(1, 50), "rock")
            for i in range(3000)
        ]
        chave = lambda f: f.duracao_ms  # noqa: E731

        nossa = radix_lsd(entrada, chave=chave)
        referencia = sorted(entrada, key=chave)

        for i, (a, b) in enumerate(zip(nossa, referencia)):
            self.assertIs(a, b, f"divergencia na posicao {i}")

    def test_bases_diferentes_dao_o_mesmo_resultado(self):
        entrada = catalogo_sintetico(2000)
        chave = lambda f: f.duracao_ms  # noqa: E731
        referencia = sorted(entrada, key=chave)

        for base in (2, 10, 16, 256):
            with self.subTest(base=base):
                saida = radix_lsd(entrada, chave=chave, base=base)
                for i, (a, b) in enumerate(zip(saida, referencia)):
                    self.assertIs(a, b, f"base {base}, posicao {i}")

    def test_nao_faz_comparacoes(self):
        """
        O contador de comparacoes tem que terminar em zero. E a prova
        empirica de que o algoritmo nao e comparativo, e portanto nao
        esta sujeito ao limite de Omega(n log n).
        """
        entrada = catalogo_sintetico(5000)
        m = Metricas()

        radix_lsd(entrada, chave=lambda f: f.duracao_ms, metricas=m)

        self.assertEqual(m.comparacoes, 0)
        self.assertGreater(m.movimentacoes, 0)

    def test_rejeita_chave_negativa(self):
        entrada = [Faixa("t1", "n1", "A", "X", 50, -5, "rock")]
        with self.assertRaises(ValueError):
            radix_lsd(entrada, chave=lambda f: f.duracao_ms)

    def test_contagem_de_digitos(self):
        self.assertEqual(digitos_necessarios(0), 1)
        self.assertEqual(digitos_necessarios(9), 1)
        self.assertEqual(digitos_necessarios(10), 2)
        self.assertEqual(digitos_necessarios(600_000), 6)
        self.assertEqual(digitos_necessarios(255, base=256), 1)
        self.assertEqual(digitos_necessarios(256, base=256), 2)


class TestComparacaoEntreOsDois(unittest.TestCase):
    """
    Merge e Radix ordenando a MESMA chave devem produzir a MESMA saida,
    inclusive na ordem dos empates. Se divergirem, um dos dois perdeu a
    estabilidade.
    """

    def test_mesma_saida_na_mesma_chave(self):
        entrada = catalogo_sintetico(4000)
        chave = lambda f: f.duracao_ms  # noqa: E731

        por_merge = merge_sort(entrada, chave=chave)
        por_radix = radix_lsd(entrada, chave=chave)

        for i, (a, b) in enumerate(zip(por_merge, por_radix)):
            self.assertIs(a, b, f"Merge e Radix divergem na posicao {i}")

    def test_relatorio_de_metricas(self):
        """
        Nao e assercao de desempenho — e so para o relatorio. Imprime o
        contraste entre um algoritmo comparativo e um nao comparativo
        sobre a mesma entrada.
        """
        entrada = catalogo_sintetico(10_000)
        chave = lambda f: f.duracao_ms  # noqa: E731

        m_merge = Metricas()
        merge_sort(entrada, chave=chave, metricas=m_merge)

        m_radix = Metricas()
        radix_lsd(entrada, chave=chave, metricas=m_radix)

        print(f"\n  n = 10.000, chave = duracao_ms")
        print(f"  Merge Sort : {m_merge}")
        print(f"  Radix LSD  : {m_radix}")
        print(f"  (Radix faz {m_radix.comparacoes} comparacoes: nao e comparativo)")

        self.assertGreater(m_merge.comparacoes, 0)
        self.assertEqual(m_radix.comparacoes, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
