/*
 * Interface do catalogo. Nenhum algoritmo roda aqui: tudo e pedido ao
 * servidor, que executa as funcoes reais do projeto.
 *
 * Cor por ENTIDADE, fixa: Merge azul, Counting laranja, Radix verde-agua.
 * Um algoritmo que some do cenario nao repinta os outros.
 */

const COR = {
  "Merge Sort": "var(--merge)",
  "Counting Sort": "var(--counting)",
  "Radix LSD": "var(--radix)",
};
const CLASSE = {
  "Merge Sort": "merge",
  "Counting Sort": "counting",
  "Radix LSD": "radix",
};

const fmt = (v) => v.toLocaleString("pt-BR");
const fmtMs = (v) =>
  v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const $ = (id) => document.getElementById(id);

async function pedir(rota, params) {
  const url = new URL(rota, location.origin);
  Object.entries(params || {}).forEach(([k, v]) => url.searchParams.set(k, v));
  const resposta = await fetch(url);
  const dados = await resposta.json();
  if (dados.erro) throw new Error(dados.erro);
  return dados;
}

/* ---------------------------------------------------------------- abas */

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((a) =>
      a.setAttribute("aria-selected", String(a === aba))
    );
    document.querySelectorAll(".painel").forEach((p) => {
      p.hidden = p.id !== `painel-${aba.dataset.painel}`;
    });
  });
});

/* ------------------------------------------------------------- legenda */

function legenda(alvo, algoritmos) {
  alvo.innerHTML = algoritmos
    .map(
      (a) =>
        `<li><span class="marca ${CLASSE[a]}"></span>${a}</li>`
    )
    .join("");
}

/* -------------------------------------------------------------- barras
 * Barras horizontais, ponta arredondada de 4px ancorada na linha de base,
 * rotulo direto em cada barra (nunca so a cor carregando o significado).
 */

function barras(alvo, itens, formatar) {
  if (!itens.length) { alvo.innerHTML = ""; return; }

  const maximo = Math.max(...itens.map((i) => i.valor), 1);
  const alturaBarra = 34;
  const espaco = 12;
  const rotuloLargura = 132;
  const altura = itens.length * (alturaBarra + espaco);
  const largura = 760;
  const util = largura - rotuloLargura - 110;

  const linhas = itens
    .map((item, i) => {
      const y = i * (alturaBarra + espaco);
      const w = Math.max((item.valor / maximo) * util, item.valor > 0 ? 3 : 0);
      return `
      <g>
        <text x="0" y="${y + alturaBarra / 2 + 5}" font-size="13"
              fill="var(--tinta-2)">${item.nome}</text>
        <rect x="${rotuloLargura}" y="${y + 4}" width="${w}" height="${alturaBarra - 8}"
              rx="4" fill="${COR[item.nome]}"></rect>
        <text x="${rotuloLargura + w + 10}" y="${y + alturaBarra / 2 + 5}"
              font-size="13" font-weight="600" fill="var(--tinta)"
              font-family="var(--mono)">${formatar(item.valor)}</text>
      </g>`;
    })
    .join("");

  alvo.innerHTML = `<svg class="grafico" viewBox="0 0 ${largura} ${altura}"
       role="img" aria-label="comparação entre algoritmos">${linhas}</svg>`;
}

/* ------------------------------------------------------------- catalogo */

async function carregarCatalogo() {
  const cenario = $("cenario-catalogo").value;
  const n = $("n-catalogo").value;
  $("tabela-catalogo").innerHTML = `<p class="carregando">ordenando…</p>`;

  let d;
  try {
    d = await pedir("/api/catalogo", { cenario, n, limite: 40 });
  } catch (e) {
    $("tabela-catalogo").innerHTML = `<p class="aviso">${e.message}</p>`;
    return;
  }

  $("titulo-catalogo").textContent = d.meta.titulo;
  $("nota-catalogo").textContent =
    `${d.meta.descricao} · chave: ${d.meta.chave_texto} · ${d.algoritmo}`;

  const zero = d.comparacoes === 0 ? " zero" : "";
  $("metricas-catalogo").innerHTML = `
    <div class="metrica">
      <span class="rotulo">Algoritmo</span>
      <span class="numero" style="font-size:15px">${d.algoritmo}</span>
    </div>
    <div class="metrica">
      <span class="rotulo">Faixas ordenadas</span>
      <span class="numero">${fmt(d.n)}</span>
    </div>
    <div class="metrica">
      <span class="rotulo">Tempo</span>
      <span class="numero">${fmtMs(d.ms)} ms</span>
    </div>
    <div class="metrica">
      <span class="rotulo">Comparações</span>
      <span class="numero${zero}">${fmt(d.comparacoes)}</span>
    </div>
    <div class="metrica">
      <span class="rotulo">Movimentações</span>
      <span class="numero">${fmt(d.movimentacoes)}</span>
    </div>`;

  const ehBiblioteca = d.cenario === "biblioteca";
  let anterior = null;

  const linhas = d.faixas
    .map((f, i) => {
      const troca = ehBiblioteca && f.artista !== anterior;
      anterior = f.artista;
      const minutos = Math.floor(f.duracao_ms / 60000);
      const segundos = String(Math.floor((f.duracao_ms % 60000) / 1000)).padStart(2, "0");
      return `
      <tr class="${troca && i > 0 ? "troca-artista" : ""}">
        <td class="indice">${i + 1}</td>
        <td class="titulo">${escapar(f.nome)}</td>
        <td class="secundario">${escapar(f.artista)}</td>
        <td class="secundario esconde-estreito">${escapar(f.album)}</td>
        <td class="num">${f.popularidade}</td>
        <td class="num">${minutos}:${segundos}</td>
      </tr>`;
    })
    .join("");

  $("tabela-catalogo").innerHTML = `
    <table>
      <thead><tr>
        <th>#</th><th>Faixa</th><th>Artista</th>
        <th class="esconde-estreito">Álbum</th>
        <th style="text-align:right">Pop.</th>
        <th style="text-align:right">Duração</th>
      </tr></thead>
      <tbody>${linhas}</tbody>
    </table>`;
}

function escapar(texto) {
  const d = document.createElement("div");
  d.textContent = texto ?? "";
  return d.innerHTML;
}

/* ------------------------------------------------------------- comparar */

async function carregarComparar() {
  const cenario = $("cenario-comparar").value;
  const n = $("n-comparar").value;

  let d;
  try {
    d = await pedir("/api/comparar", { cenario, n });
  } catch (e) {
    $("aviso-comparar").innerHTML = `<p class="aviso">${e.message}</p>`;
    return;
  }

  $("aviso-comparar").innerHTML = d.meta.motivo_exclusao
    ? `<p class="aviso">${d.meta.motivo_exclusao}</p>`
    : "";

  if (d.resultados.length > 1) {
    $("selo-comparar").innerHTML = d.identicas
      ? `<div class="metricas"><span class="selo">saídas idênticas — mesmos
         ${fmt(d.n)} elementos, mesma ordem, inclusive nos empates</span></div>`
      : `<div class="metricas"><span class="selo falha">saídas divergentes</span></div>`;
  } else {
    $("selo-comparar").innerHTML = "";
  }

  const algoritmos = d.resultados.map((r) => r.algoritmo);
  legenda($("legenda-comparar"), algoritmos);
  legenda($("legenda-comparacoes"), algoritmos);

  barras(
    $("barras-tempo"),
    d.resultados.map((r) => ({ nome: r.algoritmo, valor: r.ms })),
    (v) => `${fmtMs(v)} ms`
  );
  barras(
    $("barras-comparacoes"),
    d.resultados.map((r) => ({ nome: r.algoritmo, valor: r.comparacoes })),
    (v) => fmt(v)
  );
}

/* --------------------------------------------------------------- escala
 * Linhas com marcadores de 9px, rotulo direto no ultimo ponto e eixo y
 * linear. Uma serie constante em zero fica no eixo — que e exatamente o
 * que se quer ver.
 */

function linhas(alvo, series, campo, formatar) {
  const nomes = Object.keys(series);
  const pontos = nomes.flatMap((nome) => series[nome]);
  if (!pontos.length) return;

  const maxN = Math.max(...pontos.map((p) => p.n));
  const maxY = Math.max(...pontos.map((p) => p[campo]), 1);

  const largura = 760, altura = 320;
  const m = { topo: 16, dir: 92, baixo: 40, esq: 64 };
  const util = { x: largura - m.esq - m.dir, y: altura - m.topo - m.baixo };

  const px = (n) => m.esq + (n / maxN) * util.x;
  const py = (v) => m.topo + util.y - (v / maxY) * util.y;

  const grade = [0, 0.25, 0.5, 0.75, 1]
    .map((f) => {
      const y = m.topo + util.y - f * util.y;
      return `<line x1="${m.esq}" y1="${y}" x2="${largura - m.dir}" y2="${y}"
               stroke="var(--borda)" stroke-width="1"></line>
              <text x="${m.esq - 10}" y="${y + 4}" font-size="11" text-anchor="end"
               fill="var(--tinta-3)" font-family="var(--mono)">${formatar(maxY * f)}</text>`;
    })
    .join("");

  const marcasX = series[nomes[0]]
    .map((p) => `<text x="${px(p.n)}" y="${altura - 14}" font-size="11"
                   text-anchor="middle" fill="var(--tinta-3)"
                   font-family="var(--mono)">${fmt(p.n)}</text>`)
    .join("");

  const traços = nomes
    .map((nome) => {
      const pts = series[nome];
      const d = pts.map((p) => `${px(p.n)},${py(p[campo])}`).join(" ");
      const marcadores = pts
        .map(
          (p) => `<circle cx="${px(p.n)}" cy="${py(p[campo])}" r="4.5"
                   fill="${COR[nome]}" stroke="var(--superficie)" stroke-width="2">
                   <title>${nome} · n=${fmt(p.n)} · ${formatar(p[campo])}</title>
                  </circle>`
        )
        .join("");
      const ultimo = pts[pts.length - 1];
      const rotulo = `<text x="${px(ultimo.n) + 12}" y="${py(ultimo[campo]) + 4}"
          font-size="12" font-weight="600" fill="${COR[nome]}">${nome.split(" ")[0]}</text>`;
      return `<polyline points="${d}" fill="none" stroke="${COR[nome]}"
                stroke-width="2" stroke-linejoin="round"></polyline>
              ${marcadores}${rotulo}`;
    })
    .join("");

  alvo.innerHTML = `<svg class="grafico" viewBox="0 0 ${largura} ${altura}"
      role="img" aria-label="evolução com o tamanho da entrada">
      ${grade}${marcasX}${traços}</svg>`;
}

async function rodarEscala() {
  const cenario = $("cenario-escala").value;
  const botao = $("rodar-escala");
  botao.disabled = true;
  $("grafico-escala").innerHTML = `<p class="carregando">executando…</p>`;
  $("grafico-escala-comp").innerHTML = "";

  try {
    const d = await pedir("/api/escala", { cenario, teto: 25000 });
    const nomes = Object.keys(d.series);

    legenda($("legenda-escala"), nomes);
    legenda($("legenda-escala-2"), nomes);

    linhas($("grafico-escala"), d.series, "ms", (v) => `${v.toFixed(0)} ms`);
    linhas($("grafico-escala-comp"), d.series, "comparacoes", (v) => fmt(Math.round(v)));

    const corpo = d.tamanhos
      .map((n, i) => {
        const celulas = nomes
          .map((nome) => {
            const p = d.series[nome][i];
            return `<td class="num">${fmtMs(p.ms)}</td>
                    <td class="num">${fmt(p.comparacoes)}</td>`;
          })
          .join("");
        return `<tr><td class="num">${fmt(n)}</td>${celulas}</tr>`;
      })
      .join("");

    const cabecalho = nomes
      .map((nome) => `<th style="text-align:right">${nome} ms</th>
                      <th style="text-align:right">${nome} comp.</th>`)
      .join("");

    $("tabela-escala").innerHTML = `
      <table style="margin-top:20px">
        <thead><tr><th style="text-align:right">n</th>${cabecalho}</tr></thead>
        <tbody>${corpo}</tbody>
      </table>`;
  } catch (e) {
    $("grafico-escala").innerHTML = `<p class="aviso">${e.message}</p>`;
  } finally {
    botao.disabled = false;
  }
}

/* ----------------------------------------------------------------- liga */

function ligarSlider(idSlider, idValor, aoSoltar) {
  const slider = $(idSlider);
  slider.addEventListener("input", () => {
    $(idValor).textContent = fmt(Number(slider.value));
  });
  slider.addEventListener("change", aoSoltar);
}

ligarSlider("n-catalogo", "n-catalogo-valor", carregarCatalogo);
ligarSlider("n-comparar", "n-comparar-valor", carregarComparar);
$("cenario-catalogo").addEventListener("change", carregarCatalogo);
$("cenario-comparar").addEventListener("change", carregarComparar);
$("rodar-escala").addEventListener("click", rodarEscala);

(async function inicio() {
  try {
    const info = await pedir("/api/info");
    $("resumo").textContent = info.resumo;
    const teto = Math.min(50000, info.total);
    ["n-catalogo", "n-comparar"].forEach((id) => { $(id).max = teto; });
  } catch (e) {
    $("resumo").textContent = e.message;
  }
  carregarCatalogo();
  carregarComparar();
})();
