# G02_Ordenacao_EDA2-2026.2 — Ordenação do catálogo musical

**Disciplina:** Estruturas de Dados 2 (EDA2) — 2026.2
**Professor:** Maurício Serrano
**Trabalho:** T2 — Algoritmos de Ordenação
**Dupla:** João Pedro Araújo de Freitas Lyra (232003661) e Rivadalvio Joaquim da Silva Filho (232024026)

**Vídeo de apresentação:** https://youtu.be/LLaiw2vLdsU

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

Sobre as 113.999 faixas do catálogo, isso significa que a escolha do algoritmo
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
4. Tornar os algoritmos **observáveis em execução**, numa interface que roda as
   funções reais do projeto e expõe as métricas de cada chamada;
5. Mostrar o caso em que o algoritmo comparativo é a **única** opção, e não
   apenas o mais lento — a conclusão não é "o linear ganha", é que cada formato
   de chave pede um algoritmo.

## 3. O que o software faz

O projeto entrega duas formas de executar os mesmos algoritmos: uma interface
web, para inspeção interativa, e um benchmark de linha de comando, para a
coleta sistemática que alimenta o relatório.

### 3.1 Interface

Servida por `src/web/servidor.py` em `http://localhost:8000`, com três abas:

| Aba | O que faz |
|---|---|
| **Catálogo** | Ordena e lista as faixas pela tela escolhida. O rodapé mostra algoritmo, tempo, comparações e movimentações daquela execução. |
| **Comparar** | Roda todos os algoritmos aplicáveis sobre a **mesma** entrada, confere que as saídas são idênticas e mostra tempo e comparações lado a lado. |
| **Escala** | Executa em tamanhos crescentes e desenha tempo × n e comparações × n. |

Um controle deslizante ajusta o número de faixas de 1.000 a 50.000, e cada
mudança dispara uma execução nova.

**A interface não reimplementa nada.** O servidor importa `merge_sort`,
`counting_sort`, `radix_lsd` e `carregar` — exatamente os mesmos módulos que o
benchmark usa — e os executa sob demanda com o contador `Metricas` ligado. Os
números na tela são medições de verdade, não valores pré-computados. É essa
propriedade que faz a interface valer como evidência: alterar um algoritmo
altera a tela.

### 3.2 Cenários

| Cenário | Chave | Algoritmos comparados |
|---|---|---|
| `popularidade` | inteiro 0..100 | Counting Sort × Merge Sort |
| `duracao` | inteiro até ~5.000.000 | Radix LSD × Merge Sort |
| `biblioteca` | três strings | Merge Sort multi-chave (sozinho) |

O terceiro cenário não tem competidor **de propósito**: nem Counting nem Radix
se aplicam a chave string, e a interface mostra isso como resultado — exibe o
motivo da exclusão em vez de deixar a lacuna sem explicação.

### 3.3 Suíte de testes

`tests/test_estabilidade.py` valida os três algoritmos contra o `sorted()` do
CPython, que usa Timsort e é garantidamente estável por especificação da
linguagem.

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

### 4.5 Como a interface executa os algoritmos

`src/web/servidor.py` expõe três rotas, todas chamando as funções originais:

| Rota | O que executa |
|---|---|
| `/api/catalogo` | uma execução do algoritmo principal do cenário |
| `/api/comparar` | todos os algoritmos do cenário sobre a mesma entrada, mais a verificação de equivalência |
| `/api/escala` | uma execução por tamanho, para cada algoritmo |

**Verificação de equivalência.** Antes de exibir qualquer tempo, a rota
`/api/comparar` confere que as saídas dos algoritmos são idênticas elemento a
elemento, **por identidade de objeto** (`is`, não `==`). Isso prova duas coisas
ao mesmo tempo: que os algoritmos concordam, e que ambos são estáveis — duas
ordenações estáveis da mesma entrada são necessariamente idênticas, inclusive
nos empates. Se a verificação falhasse, os tempos não significariam nada.

**Aquecimento.** O servidor executa cada algoritmo uma vez na subida, antes de
atender a primeira requisição. Sem isso, a primeira medição exibida carregaria
custos de inicialização do interpretador que não têm relação com o algoritmo.

O catálogo é carregado uma única vez, na subida do servidor, e as amostras saem
da mesma função `amostrar()` com semente fixa que o benchmark usa — então a
interface e o benchmark medem exatamente as mesmas entradas.

## 5. Experimento

Dataset: **Spotify Tracks Dataset**, 125 gêneros. O arquivo traz 114.000
linhas; uma é descartada na carga por ter `duration_ms` inválido, restando
**113.999 faixas**, com 17.648 artistas e 46.589 álbuns distintos. Durações de
8.586 a 5.237.295 ms.
Fonte: https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset

Amostragem com semente fixa (`random.Random(42)`) — quem rodar o benchmark de
novo mede exatamente a mesma entrada. Sem isso, comparar duas execuções não faz
sentido.

Cada medição é a **mediana** de 5 execuções, não a média: uma execução
atrapalhada pelo coletor de lixo distorce a média e não move a mediana.

Linhas com `duration_ms <= 0` são descartadas na carga — existem no dataset e
quebrariam o Radix, que exige chave não-negativa. São dados inválidos de origem,
não decisão de conveniência.

> **Sobre os números da interface.** A tela executa os algoritmos no momento do
> clique e mostra o resultado daquela chamada única, sem repetição nem mediana.
> Serve para inspeção e demonstração. Os valores das tabelas abaixo vêm do
> `benchmark.py`, que repete e tira mediana — são esses que o relatório usa.

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
| 1.000 | 0,25 | 2,52 | 10,1× | 0 | 8.721 |
| 5.000 | 1,78 | 16,96 | 9,5× | 0 | 55.122 |
| 10.000 | 3,17 | 36,64 | 11,6× | 0 | 120.336 |
| 25.000 | 7,53 | 97,43 | 12,9× | 0 | 334.041 |
| 50.000 | 19,24 | 208,15 | 10,8× | 0 | 717.883 |
| 100.000 | 43,77 | 452,91 | 10,3× | 0 | 1.535.664 |

Três leituras:

**O ganho é estável em torno de 10×.** Não cresce com n, e não deveria: ambos
os algoritmos são lineares *na prática* para esta chave — o Counting por ser
O(n+k) com k fixo, e o Merge por ser O(n log n) com log n variando pouco na
faixa medida (de 10 a 17). O que separa os dois é o fator constante, e ele é
constante mesmo.

**As comparações do Merge batem com a teoria.** Dividindo a contagem medida por
n·log₂(n), a razão vai de 0,875 a 0,925 e sobe devagar — exatamente o
comportamento de n·log₂(n) − n + 1, que é a contagem exata do Merge Sort. O
termo −n, que domina em n pequeno, perde peso conforme n cresce.

**As movimentações do Counting são exatamente n.** Mil faixas, mil
movimentações; cem mil faixas, cem mil movimentações. Cada elemento é escrito
uma única vez, na posição que a soma de prefixos calculou. O Merge escreve
1.668.928 vezes para as mesmas 100.000 faixas — dezesseis vezes mais, porque
cada nível da recursão reescreve o vetor inteiro.

### 5.3 Ordenação por duração (k ≈ 5.000.000)

| n | Radix (ms) | Merge (ms) | ganho | passadas | movimentações Radix | movimentações Merge |
|---|---|---|---|---|---|---|
| 1.000 | 1,86 | 2,67 | 1,44× | 7 | 7.000 | 9.976 |
| 5.000 | 12,36 | 18,74 | 1,52× | 7 | 35.000 | 61.808 |
| 10.000 | 28,05 | 38,31 | 1,37× | 7 | 70.000 | 133.616 |
| 25.000 | 58,06 | 103,50 | 1,78× | 7 | 175.000 | 367.232 |
| 50.000 | 173,99 | 229,44 | 1,32× | 7 | 350.000 | 784.464 |
| 100.000 | 396,29 | 495,44 | 1,25× | 7 | 700.000 | 1.668.928 |

**O resultado mais interessante do trabalho é este, e ele contraria a
expectativa.** O Radix é O(n) e o Merge é O(n log n), mas o ganho medido fica
entre 1,25× e 1,78× — contra os 10× do Counting, que tem a mesma complexidade
assintótica linear.

A explicação está no fator constante, e ela é instrutiva. A maior duração do
catálogo é 5.237.295 ms, que tem 7 dígitos, então o Radix faz **7 passadas**
completas. Cada passada percorre os n elementos três vezes: uma para contar,
uma para somar prefixos, uma para distribuir — e em cada elemento chama a
função extratora de chave e executa uma divisão inteira e um módulo.

O resultado são 700.000 movimentações contra as 1.668.928 do Merge: só 2,4×
menos, não a ordem de grandeza que "linear contra n log n" sugere. E as
operações do Radix são individualmente mais caras em Python, onde cada chamada
de função e cada operação aritmética passa pelo interpretador.

A conclusão correta não é "o Radix decepcionou". É que **complexidade
assintótica descreve o crescimento, não o custo**. Com d = 7 passadas e
log₂(100.000) ≈ 17, o Radix executa 7 passadas onde o Merge executa 17 níveis —
uma vantagem de pouco mais de 2×, não de uma ordem de grandeza. Para a
vantagem assintótica aparecer de verdade seria preciso n muito maior, ou uma
base maior que reduzisse o número de passadas.

O contraste com a tabela anterior é o que fecha o argumento: o Counting faz
**uma** passada e ganha 10×; o Radix faz **sete** e ganha 1,3×. Os dois são
lineares. O número de passadas é o que decide.

### 5.4 Biblioteca multi-chave (artista → álbum → faixa)

| n | Merge 3 chaves (ms) | comparações | movimentações |
|---|---|---|---|
| 1.000 | 12,69 | 25.919 | 29.928 |
| 5.000 | 82,77 | 164.820 | 185.424 |
| 10.000 | 177,38 | 359.346 | 400.848 |
| 25.000 | 473,66 | 994.879 | 1.101.696 |
| 50.000 | 1.023,11 | 2.133.820 | 2.353.392 |
| 100.000 | 2.231,12 | 4.549.152 | 5.006.784 |

Sem competidor: Counting e Radix não se aplicam a chave string.

O custo é **exatamente três vezes** o de uma ordenação simples — as
movimentações são 3n·log-alguma-coisa com a razão medida em 0,987 a 0,995 do
triplo do Merge de chave única. Era o esperado: são três passadas completas, e
cada uma custa o mesmo que uma ordenação inteira.

Esse é o preço da ordenação multi-chave por passadas estáveis, e ele é
assumido. A alternativa seria uma única passada com função de comparação
composta (comparar artista, desempatar por álbum, desempatar por faixa), que
faria um terço das passadas. Não a adotamos porque a versão em passadas é a que
demonstra a propriedade sob estudo: cada passada depende da estabilidade da
anterior, e é isso que o trabalho quer mostrar. Vale registrar que a decisão
foi didática, não de desempenho.

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

**O fator constante não aparece nesta tabela, e a seção 5.3 mostra por que isso
importa.** Counting e Radix têm a mesma linha de complexidade, mas o Counting
faz uma passada e o Radix faz sete — e o ganho medido difere por quase uma
ordem de grandeza (10× contra 1,3×). A notação assintótica descarta
deliberadamente esses fatores, e é por isso que a medição não substitui a
análise nem a análise substitui a medição.

**Por que não usamos os outros algoritmos do módulo.** Quick Sort e Heap Sort
são instáveis, o que os elimina da tela da biblioteca — o caso que motivou o
trabalho. Bubble, Selection e Insertion são O(n²) e inviáveis em 113.999
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
├── web/
│   ├── servidor.py             servidor HTTP, executa os algoritmos sob demanda
│   └── static/
│       ├── index.html          as três abas
│       ├── estilo.css          paleta validada para daltonismo, claro e escuro
│       └── app.js              gráficos em SVG, sem dependência externa
├── benchmark.py                medição dos três cenários
└── graficos.py                 geração dos PNGs

tests/
└── test_estabilidade.py        13 testes contra o sorted()

dados/
└── dataset.csv                 (não versionado — baixar do Kaggle)

resultados/                     CSV e gráficos gerados pelo benchmark
```

A pasta `src/web/` é estritamente aditiva: nenhuma assinatura dos módulos
existentes foi alterada para acomodá-la.

## 8. Como executar

**Pré-requisitos:** Python 3.10+. O matplotlib é necessário apenas para os
gráficos estáticos do `graficos.py`; a interface não usa nenhuma dependência
externa.

Baixe o dataset do Kaggle e salve como `dados/dataset.csv`. Confirme a carga:

```bash
python src/dados/carregar.py
```

### 8.1 Interface

```bash
python src/web/servidor.py
```

O navegador abre em `http://localhost:8000`. Para parar, `Ctrl+C`.

Se a porta 8000 estiver ocupada, altere a constante `PORTA` no topo de
`src/web/servidor.py`.

### 8.2 Testes

```bash
python tests/test_estabilidade.py
```

### 8.3 Benchmark e gráficos

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
| Interface | ambos | `web/servidor.py`, `web/static/` |

A divisão dos algoritmos é por arquivo, não por tarefa: cada integrante tem
algoritmos que são seus de ponta a ponta e consegue testar sem depender do
outro. A única dependência compartilhada é o `contrato.py`, commitado primeiro.

A interface veio depois dos dois blocos e consome ambos, por isso é conjunta.

## 10. Bibliografia

CORMEN, T. H. et al. *Introduction to Algorithms*. 3ª ed. MIT Press, 2009.
(capítulos de ordenação em tempo linear e limite inferior por comparação)

KNUTH, D. E. *The Art of Computer Programming, Vol. 3: Sorting and Searching*.
2ª ed. Addison-Wesley, 1998.

SEDGEWICK, R.; WAYNE, K. *Algorithms*. 4ª ed. Addison-Wesley, 2011.

PETERS, T. *Timsort description*. CPython, `Objects/listsort.txt`.
(referência de estabilidade usada na validação)

PANDYA, M. *Spotify Tracks Dataset*. Kaggle, 2023.