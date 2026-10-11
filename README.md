# G02_Ordenacao_EDA2-2026.2 — Ordenação do catálogo musical

**Disciplina:** Estruturas de Dados 2 (EDA2) — 2026.2
**Professor:** Maurício Serrano
**Trabalho:** T2 — Algoritmos de Ordenação
**Dupla:** João Pedro Araújo de Freitas Lyra (232003661) e Rivadalvio Joaquim da Silva Filho (232024026)

**Vídeo de apresentação:** _(a gravar)_

---

## 1. Problema

Um catálogo musical não tem uma ordenação — tem várias, e cada tela pede a sua:

| Tela | Ordena por | Formato da chave |
|---|---|---|
| Biblioteca | artista, depois álbum, depois faixa | três strings |
| Top por popularidade | `popularity` | inteiro 0..100 |
| Faixas mais longas | `duration_ms` | inteiro até ~5.000.000 |

O caminho default é chamar o `sorted()` da linguagem nas três e seguir a vida.
Funciona, e é o que a maioria dos sistemas faz. Mas esconde duas coisas.

**Primeira:** ordenação por comparação está presa ao limite inferior de
Ω(n log n). Esse limite é um teorema sobre a árvore de decisão de qualquer
algoritmo que só pergunta "a é menor que b?" — com n! folhas possíveis, a
altura mínima é log₂(n!) = Θ(n log n). Duas das três telas acima têm chave
**inteira com intervalo conhecido**, e para elas o teorema simplesmente não se
aplica: dá para ordenar em tempo linear sem nunca comparar dois elementos.

**Segunda:** a tela da biblioteca não é só uma questão de velocidade. Ordenar
por três chaves em passadas sucessivas exige que cada passada seja **estável** —
que preserve a ordem relativa dos empates. Com um algoritmo instável a tela sai
**errada**: as faixas aparecem embaralhadas dentro de cada álbum. Não é um
resultado mais lento, é um resultado incorreto.

Sobre as 114.000 faixas do catálogo, isso significa que a escolha do algoritmo
não é otimização prematura — é requisito funcional em um caso e ganho
assintótico em dois.

## 2. Objetivo e contribuição

Implementar do zero os algoritmos de ordenação que um catálogo real usaria em
cada uma das três telas, e medir o custo de cada um sobre o mesmo dataset.

A contribuição não é "implementar Merge Sort". É:

1. Identificar, para cada tela do catálogo, qual propriedade da chave determina
   o algoritmo adequado — intervalo, tipo e necessidade de estabilidade;
2. Implementar três algoritmos com **assinatura única**, instrumentados para
   contar comparações e movimentações separadamente;
3. **Provar a estabilidade** dos três contra uma referência inquestionável
   antes de comparar tempos, porque um benchmark que compara saídas diferentes
   não mede nada;
4. Mostrar o caso em que o algoritmo comparativo é a **única** opção, e não
   apenas o mais lento — a conclusão não é "o linear ganha", é que cada formato
   de chave pede um algoritmo.

## 3. O que o software faz

Três cenários de ordenação sobre o mesmo catálogo carregado do CSV, cada um
rodando o algoritmo que a tela correspondente usaria:

| Cenário | Chave | Algoritmos comparados |
|---|---|---|
| `popularidade` | inteiro 0..100 | Counting Sort × Merge Sort |
| `duracao` | inteiro até ~5.000.000 | Radix LSD × Merge Sort |
| `biblioteca` | três strings | Merge Sort multi-chave (sozinho) |

O terceiro cenário não tem competidor **de propósito**: nem Counting nem Radix
se aplicam a chave string, e o benchmark registra isso como resultado, não como
lacuna.

A suíte de testes (`tests/test_estabilidade.py`) valida os três contra o
`sorted()` do CPython, que usa Timsort e é garantidamente estável por
especificação da linguagem.

## 4. Núcleo técnico

Toda função de ordenação obedece à mesma assinatura, definida em
`src/contrato.py`:

```python
ordenar(lista, chave, metricas) -> list
```

Nenhuma ordena no lugar; todas devolvem lista nova. Isso custa memória, mas
torna o benchmark honesto: cada execução parte exatamente da mesma entrada, sem
o efeito de "já estava quase ordenado da rodada anterior".

O contador `Metricas` separa **comparações** de **movimentações**. A separação
importa: é ela que expõe o zero dos algoritmos não comparativos.

### 4.1 Counting Sort — chave inteira de intervalo pequeno
_(João Pedro)_

A popularidade do Spotify é um inteiro de 0 a 100. Com apenas 101 valores
possíveis, dá para contar quantas faixas têm cada valor e montar a saída direto:

1. Conta ocorrências de cada chave em um vetor de tamanho k = 101;
2. Soma de prefixos: `contagem[i]` vira a posição final exclusiva daquela chave;
3. Distribui os elementos nas posições calculadas.

O passo 3 percorre a entrada **de trás para a frente** enquanto decrementa o
índice acumulado. É isso que garante a estabilidade: o último elemento de uma
chave repetida vai para a última posição da faixa, o penúltimo para a anterior,
preservando a ordem de entrada. De frente para trás inverteria os empates.

O intervalo `[0, 100]` é parâmetro da função, não descoberto a partir dos dados
— no catálogo ele é conhecido pelo domínio, e descobri-lo custaria uma passada
extra sem necessidade.

**Onde não serve.** Não ordena por nome de artista: não existe contagem para
string arbitrária, e mesmo mapeando strings para inteiros o intervalo seria o
tamanho do alfabeto elevado ao comprimento. E não ordena `duration_ms` direto:
k seria da ordem de 5.000.000 e o vetor de contagem gastaria mais memória que o
catálogo inteiro.

### 4.2 Radix Sort LSD — chave inteira de intervalo grande
_(Rivadalvio)_

É a resposta ao segundo limite do Counting. Em vez de um vetor de 5 milhões de
posições, o Radix processa a chave em dígitos: cada passada é um Counting Sort
sobre **um** dígito, com k = base.

Com base 10 e duração de até 7 dígitos, são 7 passadas sobre um vetor de
contagem de 10 posições.

As passadas vão do dígito **menos** significativo para o mais (LSD). A ordem
importa e depende inteiramente da estabilidade: a passada do dígito i+1 só
produz resultado correto porque a passada do dígito i deixou os empates na
ordem certa. Um Radix com passada instável devolve lixo — aqui a estabilidade
não é um bônus, é o que faz o algoritmo funcionar.

A base é parâmetro (`base=10` por padrão, testado também com 2, 16 e 256). Mais
base significa menos passadas com vetor de contagem maior; é um trade-off
mensurável e a curva não é monótona.

### 4.3 Merge Sort — chave comparável, estabilidade garantida
_(Rivadalvio)_

Divide ao meio, ordena recursivamente, intercala. O(n log n) em **todos** os
casos — melhor, médio e pior — porque a divisão independe do conteúdo. Não
existe entrada que degrade o Merge Sort, e é por isso que ele é a referência do
trabalho.

O detalhe que decide a estabilidade está em uma única linha da intercalação:

```python
if chave(direita[j]) < chave(esquerda[i]):   # menor ESTRITO
```

Consumimos da direita apenas quando ela é estritamente menor; no empate, o
`else` consome da esquerda. Como a metade esquerda vem antes no vetor original,
desempatar pela esquerda preserva a ordem de entrada.

Com `<=` no lugar de `<`, o algoritmo continuaria ordenando corretamente e
deixaria de ser estável — sem nenhum sintoma visível até alguém fazer ordenação
multi-chave. É exatamente o tipo de bug que motiva a seção 5.1.

**Ordenação multi-chave.** A biblioteca é ordenada por artista → álbum → faixa
aplicando as passadas na ordem **inversa**: primeiro nome, depois álbum, por
último artista. Cada passada estável preserva a ordem imposta pelas anteriores,
então ao final as três chaves valem simultaneamente com a precedência correta.

Isso é a mesma ideia do Radix LSD, com os "dígitos" sendo campos do registro e
a passada sendo um Merge Sort em vez de um Counting Sort. Os dois algoritmos do
trabalho que parecem mais distantes são, na estrutura, o mesmo método.

### 4.4 Comparações: o zero que importa

Counting e Radix nunca comparam dois elementos entre si — leem um valor e o
usam como índice de vetor. O contador de comparações termina em **zero**, e é a
evidência empírica de que o limite de Ω(n log n) não se aplica a eles.

Vale ser preciso na formulação: os dois não "quebram" o limite inferior. O
teorema é sobre ordenação **por comparação**, e eles estão fora do escopo da
hipótese. Em troca, pagam o preço de só funcionarem com chave inteira de
intervalo tratável — que é exatamente a restrição que o Merge Sort não tem.

## 5. Experimento

Dataset: **Spotify Tracks Dataset**, 114.000 faixas, 125 gêneros.
Fonte: https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset

Amostragem com semente fixa (`random.Random(42)`) — quem rodar o benchmark de
novo mede exatamente a mesma entrada. Sem isso, comparar duas execuções não faz
sentido.

Cada medição é a **mediana** de 5 execuções, não a média: uma execução
atrapalhada pelo coletor de lixo distorce a média e não move a mediana.

Linhas com `duration_ms <= 0` são descartadas na carga — existem no dataset e
quebrariam o Radix, que exige chave não-negativa. São dados inválidos de origem,
não decisão de conveniência.

### 5.1 Validação de estabilidade

Antes de comparar tempos, verificamos que os algoritmos estão corretos. Três
níveis, do mais fraco ao mais forte:

1. **Está ordenado** — a saída é não-decrescente. Fraco: um algoritmo que
   descartasse elementos passaria.
2. **Mesmo conteúdo** — a saída é permutação da entrada. Pega perda e
   duplicação de elementos.
3. **Estável** — a saída é idêntica **objeto a objeto** (`is`, identidade, não
   `==`) à do `sorted()`. Só este pega troca de ordem entre empates.

O nível 3 usa identidade de propósito: dois registros com a mesma chave são
iguais o bastante para passar numa comparação por valor, e é precisamente a
ordem entre eles que queremos verificar.

O gerador de catálogo sintético dos testes usa poucos artistas e poucos álbuns
deliberadamente. Sem empates em quantidade, um teste de estabilidade não tem o
que testar: uma lista sem chaves repetidas tem uma única ordenação possível, e
até um algoritmo instável acerta.

**Resultado:** 13 testes, 13 passando.

**Um bug encontrado pelos próprios testes.** A validação de chave negativa no
Radix estava posicionada **depois** do atalho para listas de 0 ou 1 elemento,
então nunca executava nesse caso — uma lista unitária com duração negativa
passava silenciosamente e produziria índice inválido na distribuição. O teste
`test_rejeita_chave_negativa` falhou, o atalho foi removido e a validação
passou a rodar sempre. É o argumento concreto a favor de testar contra
referência em vez de inspecionar a saída a olho.

### 5.2 Ordenação por popularidade (k = 101)

| n | Counting (ms) | Merge (ms) | ganho | comparações Counting | comparações Merge |
|---|---|---|---|---|---|
| 1.000 | _(a medir)_ | _(a medir)_ | — | 0 | _(a medir)_ |
| 10.000 | _(a medir)_ | _(a medir)_ | — | 0 | _(a medir)_ |
| 50.000 | _(a medir)_ | _(a medir)_ | — | 0 | _(a medir)_ |
| 100.000 | _(a medir)_ | _(a medir)_ | — | 0 | _(a medir)_ |

### 5.3 Ordenação por duração (k ≈ 5.000.000)

| n | Radix (ms) | Merge (ms) | ganho | passadas do Radix |
|---|---|---|---|---|
| 1.000 | _(a medir)_ | _(a medir)_ | — | _(a medir)_ |
| 10.000 | _(a medir)_ | _(a medir)_ | — | _(a medir)_ |
| 50.000 | _(a medir)_ | _(a medir)_ | — | _(a medir)_ |
| 100.000 | _(a medir)_ | _(a medir)_ | — | _(a medir)_ |

### 5.4 Biblioteca multi-chave (artista → álbum → faixa)

| n | Merge 3 chaves (ms) | comparações | movimentações |
|---|---|---|---|
| 1.000 | _(a medir)_ | _(a medir)_ | _(a medir)_ |
| 10.000 | _(a medir)_ | _(a medir)_ | _(a medir)_ |
| 100.000 | _(a medir)_ | _(a medir)_ | _(a medir)_ |

Sem competidor: Counting e Radix não se aplicam a chave string.

### 5.5 Efeito da base no Radix

| base | passadas | tempo em n=100.000 |
|---|---|---|
| 2 | _(a medir)_ | _(a medir)_ |
| 10 | _(a medir)_ | _(a medir)_ |
| 16 | _(a medir)_ | _(a medir)_ |
| 256 | _(a medir)_ | _(a medir)_ |

> As tabelas acima são preenchidas rodando `python src/benchmark.py`. A métrica
> principal deste trabalho é a **contagem de operações**, não o tempo:
> comparações e movimentações independem de máquina, de linguagem e de ruído do
> sistema operacional. O tempo entra como confirmação, não como evidência
> primária.

## 6. Análise de complexidade

| Algoritmo | Tempo médio | Pior caso | Espaço extra | Estável | Comparativo |
|---|---|---|---|---|---|
| Merge Sort | O(n log n) | O(n log n) | O(n) | sim | sim |
| Counting Sort | O(n + k) | O(n + k) | O(n + k) | sim | **não** |
| Radix LSD | O(d·(n + b)) | O(d·(n + b)) | O(n + b) | sim | **não** |

Onde n é o número de faixas, k o tamanho do intervalo da chave, d o número de
dígitos e b a base.

Com k = 101 fixo, o Counting é O(n). Com d e b fixos (a duração sempre cabe em
7 dígitos decimais), o Radix também é O(n).

**Por que não usamos os outros algoritmos do módulo.** Quick Sort e Heap Sort
são instáveis, o que os elimina da tela da biblioteca — o caso que motivou o
trabalho. Bubble, Selection e Insertion são O(n²) e inviáveis em 114.000
registros, embora o Insertion seja de fato o melhor algoritmo da lista para
entrada quase ordenada, caso que não ocorre neste catálogo. Shell Sort é
instável e tem complexidade dependente da sequência de incrementos, sem
vantagem sobre o Merge aqui. Bucket Sort pressupõe distribuição aproximadamente
uniforme da chave, e popularidade no Spotify é fortemente concentrada perto de
zero — a maioria das faixas tem popularidade baixa, o que degradaria os baldes.
Radix MSD seria aplicável à ordenação por string, mas exige recursão por
prefixo e não traria vantagem sobre o Merge num catálogo cujos títulos são
curtos e heterogêneos.

## 7. Estrutura do projeto

```
src/
├── contrato.py                 Faixa, Metricas, assinatura única, chaves
├── ordenacao/
│   ├── merge_sort.py           Merge Sort estável + multi-chave
│   ├── counting_sort.py        Counting Sort, k conhecido
│   └── radix_lsd.py            Radix LSD, base parametrizável
├── dados/
│   └── carregar.py             leitura do CSV + amostragem com semente
├── benchmark.py                medição dos três cenários
└── graficos.py                 geração dos PNGs

tests/
└── test_estabilidade.py        13 testes contra o sorted()

dados/
└── dataset.csv                 (não versionado — baixar do Kaggle)

resultados/                     CSV e gráficos gerados pelo benchmark
```

## 8. Como executar

**Pré-requisitos:** Python 3.10+ e matplotlib (só para os gráficos).

Baixe o dataset do Kaggle e salve como `dados/dataset.csv`. Confirme a carga:

```bash
python src/dados/carregar.py
```

Rode os testes:

```bash
python tests/test_estabilidade.py
```

Rode o benchmark e gere os gráficos:

```bash
python src/benchmark.py --rapido     # n até 10.000
python src/benchmark.py              # n até 100.000
pip install matplotlib
python src/graficos.py
```

Saída em `resultados/benchmark.csv`, `tempo-popularidade.png`,
`tempo-duracao.png` e `comparacoes.png`.

## 9. Divisão do trabalho

| Parte | Responsável | Arquivos |
|---|---|---|
| Contrato, Counting Sort, carga, benchmark, gráficos | João Pedro | `contrato.py`, `counting_sort.py`, `carregar.py`, `benchmark.py`, `graficos.py` |
| Merge Sort, Radix LSD, testes de estabilidade | Rivadalvio | `merge_sort.py`, `radix_lsd.py`, `test_estabilidade.py` |

A divisão é por arquivo, não por tarefa: cada integrante tem algoritmos que são
seus de ponta a ponta e consegue testar sem depender do outro. A única
dependência compartilhada é o `contrato.py`, commitado primeiro.

## 10. Bibliografia

CORMEN, T. H. et al. *Introduction to Algorithms*. 3ª ed. MIT Press, 2009.
(capítulos de ordenação em tempo linear e limite inferior por comparação)

KNUTH, D. E. *The Art of Computer Programming, Vol. 3: Sorting and Searching*.
2ª ed. Addison-Wesley, 1998.

SEDGEWICK, R.; WAYNE, K. *Algorithms*. 4ª ed. Addison-Wesley, 2011.

PETERS, T. *Timsort description*. CPython, `Objects/listsort.txt`.
(referência de estabilidade usada na validação)

PANDYA, M. *Spotify Tracks Dataset*. Kaggle, 2023.
