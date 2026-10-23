// Eco Sertão — frontend
// Busca dados da API Flask e desenha mapa, gráfico, ranking e notificações.

const API = {
  atual: "/api/focos/atual?dias=2",
  historico: "/api/focos/historico?dias=30",
  ranking: "/api/focos/ranking?dias=30&limite=10",
  status: "/api/status",
  atualizar: "/api/atualizar",
};

const INTERVALO_POLLING_MS = 5 * 60 * 1000; // 5 minutos
const CHAVE_ULTIMO_TOTAL = "eco-sertao:ultimoTotalFocos";

let mapa;
let camadaFocos;
let grafico;

// ---------- Inicialização ----------

document.addEventListener("DOMContentLoaded", () => {
  executarComSeguranca(inicializarMapa, "mapa");
  executarComSeguranca(inicializarGrafico, "gráfico");
  executarComSeguranca(configurarBotaoNotificacoes, "notificações");
  atualizarTudo();
  setInterval(atualizarTudo, INTERVALO_POLLING_MS);
});

function executarComSeguranca(funcao, nome) {
  try {
    funcao();
  } catch (erro) {
    console.error(`Falha ao iniciar "${nome}" — as outras partes do app continuam normalmente.`, erro);
  }
}

function inicializarMapa() {
  mapa = L.map("mapa", { zoomControl: true }).setView([-11.5, -41.5], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(mapa);

  camadaFocos = L.layerGroup().addTo(mapa);
}

function inicializarGrafico() {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js não carregou (provavelmente bloqueado na rede) — o gráfico de tendência ficará oculto, mas o resto do app funciona normalmente.");
    grafico = null;
    return;
  }

  const ctx = document.getElementById("grafico-historico").getContext("2d");
  grafico = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "Focos por dia",
        data: [],
        borderColor: "#B4502A",
        backgroundColor: "rgba(180, 80, 42, 0.15)",
        fill: true,
        tension: 0.25,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } } },
        y: { beginAtZero: true, ticks: { font: { size: 10 } } },
      },
    },
  });
}

// ---------- Busca e atualização ----------

async function atualizarTudo() {
  try {
    const [focos, historico, ranking, status] = await Promise.all([
      buscarJSON(API.atual),
      buscarJSON(API.historico),
      buscarJSON(API.ranking),
      buscarJSON(API.status),
    ]);

    desenharFocos(focos);
    desenharGrafico(historico);
    desenharRanking(ranking);
    atualizarCartoes(focos);
    atualizarStatus(status);
    verificarNovosFocos(focos.length);
  } catch (erro) {
    document.getElementById("status-texto").textContent =
      "Não foi possível carregar os dados agora.";
    console.error(erro);
  }
}

async function buscarJSON(url) {
  const resposta = await fetch(url);
  if (!resposta.ok) throw new Error(`Falha ao buscar ${url}`);
  return resposta.json();
}

// ---------- Mapa ----------

// Cor única para todo foco confirmado: o ponto no mapa representa uma
// detecção de calor por satélite, que é um fato binário (houve ou não
// detecção). A cor não varia por "gravidade", porque a única informação
// oficial disponível (Risco de Fogo) não mede a gravidade do foco em si
// — veja a explicação em rotuloRiscoDeFogo() logo abaixo.
const COR_FOCO = "#B4502A";

function desenharFocos(focos) {
  camadaFocos.clearLayers();

  focos.forEach((foco) => {
    L.circleMarker([foco.lat, foco.lon], {
      radius: 5,
      color: COR_FOCO,
      fillColor: COR_FOCO,
      fillOpacity: 0.75,
      weight: 1,
    })
      .bindPopup(popupDoFoco(foco))
      .addTo(camadaFocos);
  });
}

// O Risco de Fogo do INPE (escala 0 a 1: Mínimo <0.15, Baixo 0.15–0.4,
// Médio 0.4–0.7, Alto 0.7–0.95, Crítico >0.95) NÃO é uma nota de gravidade
// do foco detectado. É um índice meteorológico calculado por região e por
// dia, baseado principalmente em "Dias de Secura" (dias seguidos sem
// chuva) — ele mede o quanto a vegetação da região está seca e propensa a
// pegar fogo e a se espalhar, independente de já existir ou não um foco
// confirmado ali. Por isso ele é mostrado como contexto ambiental, nunca
// como cor do foco em si. Fonte: INPE, "Risco de Fogo: Metodologia do
// Cálculo".
function rotuloRiscoDeFogo(riscoFogo) {
  const valor = parseFloat(riscoFogo);
  if (isNaN(valor)) return "sem informação para este foco";
  if (valor < 0.15) return `Mínimo (${valor.toFixed(2)})`;
  if (valor < 0.4) return `Baixo (${valor.toFixed(2)})`;
  if (valor < 0.7) return `Médio (${valor.toFixed(2)})`;
  if (valor < 0.95) return `Alto (${valor.toFixed(2)})`;
  return `Crítico (${valor.toFixed(2)})`;
}

function popupDoFoco(foco) {
  const data = new Date(foco.data_hora_gmt.replace(" ", "T") + "Z");
  return `
    <strong>${foco.municipio || "—"} / ${foco.estado || "—"}</strong><br>
    Bioma: ${foco.bioma || "—"}<br>
    Satélite: ${foco.satelite || "—"}<br>
    Data (GMT): ${data.toLocaleString("pt-BR")}<br>
    <span style="font-size:0.85em">Vegetação seca/propensa ao fogo na região: <strong>${rotuloRiscoDeFogo(foco.risco_fogo)}</strong></span>
  `;
}


// ---------- Gráfico ----------

function desenharGrafico(historico) {
  if (!grafico) return;
  grafico.data.labels = historico.map((h) =>
    new Date(h.dia).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })
  );
  grafico.data.datasets[0].data = historico.map((h) => h.total);
  grafico.update();
}

// ---------- Ranking ----------

function desenharRanking(ranking) {
  const lista = document.getElementById("lista-ranking");
  lista.innerHTML = "";

  if (ranking.length === 0) {
    lista.innerHTML = '<li class="ranking__vazio">Sem focos no período.</li>';
    return;
  }

  ranking.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="ranking__municipio">${item.municipio} / ${item.estado}</span>
      <span class="ranking__total">${item.total}</span>
    `;
    lista.appendChild(li);
  });
}

// ---------- Cartões e status ----------

function atualizarCartoes(focos) {
  document.getElementById("numero-total").textContent = focos.length;

  const hojeStr = new Date().toISOString().slice(0, 10);
  const focosHoje = focos.filter((f) => f.data_hora_gmt.startsWith(hojeStr));
  document.getElementById("numero-hoje").textContent = focosHoje.length;

  const municipios = new Set(focos.map((f) => f.municipio));
  document.getElementById("numero-municipios").textContent = municipios.size;
}

function atualizarStatus(status) {
  const ponto = document.querySelector("#status-atualizacao .ponto");
  const texto = document.getElementById("status-texto");

  ponto.classList.remove("ponto--carregando");

  if (status.erro) {
    texto.textContent = "Última atualização falhou — exibindo dados salvos.";
    return;
  }

  if (status.ultima_atualizacao) {
    const data = new Date(status.ultima_atualizacao);
    texto.textContent = `Atualizado às ${data.toLocaleTimeString("pt-BR")}`;
  } else {
    texto.textContent = "Aguardando primeira atualização...";
  }
}

// ---------- Notificações no navegador ----------

function configurarBotaoNotificacoes() {
  const botao = document.getElementById("botao-notificacoes");
  const statusTexto = document.getElementById("notificacoes-status");

  if (!("Notification" in window)) {
    botao.disabled = true;
    statusTexto.textContent = "Seu navegador não suporta notificações.";
    return;
  }

  atualizarTextoPermissao();

  botao.addEventListener("click", async () => {
    const permissao = await Notification.requestPermission();
    atualizarTextoPermissao();
    if (permissao === "granted") {
      new Notification("Eco Sertão", {
        body: "Alertas ativados. Você será avisado sobre novos focos.",
      });
    }
  });

  function atualizarTextoPermissao() {
    if (Notification.permission === "granted") {
      statusTexto.textContent = "Alertas ativados neste navegador.";
      botao.disabled = true;
      botao.textContent = "Alertas ativos";
    } else if (Notification.permission === "denied") {
      statusTexto.textContent = "Notificações bloqueadas nas configurações do navegador.";
    } else {
      statusTexto.textContent = "Alertas ainda não ativados.";
    }
  }
}

function verificarNovosFocos(totalAtual) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;

  const totalAnterior = Number(localStorage.getItem(CHAVE_ULTIMO_TOTAL) || 0);

  if (totalAnterior > 0 && totalAtual > totalAnterior) {
    const diferenca = totalAtual - totalAnterior;
    new Notification("Novos focos de queimada detectados", {
      body: `+${diferenca} foco(s) na região monitorada nas últimas 48h.`,
    });
  }

  localStorage.setItem(CHAVE_ULTIMO_TOTAL, String(totalAtual));
}
