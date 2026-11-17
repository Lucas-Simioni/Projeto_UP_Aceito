/* Gráfico "Gastos por categoria" do painel (Chart.js).
   Duas séries: planejado (linho, referência) e contratado (eucalipto).
   Os mesmos números estão numa tabela para leitores de tela. */
(function () {
  "use strict";
  const canvas = document.getElementById("grafico-categorias");
  if (!canvas || typeof Chart === "undefined") return;

  const dados = JSON.parse(canvas.dataset.grafico);
  const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
  const estreito = window.matchMedia("(max-width: 600px)").matches;

  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  Chart.defaults.font.size = 12;
  Chart.defaults.color = "#525d55";

  // Espera a fonte Hanken Grotesk carregar: o Chart.js mede os rótulos ao desenhar, e medir com a fonte
  // reserva cortava nomes longos como "Convites e papelaria".
  const pronto = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
  pronto.then(desenhar);

  function desenhar() { new Chart(canvas, {
    type: "bar",
    data: {
      labels: dados.rotulos,
      datasets: [
        {
          label: "Planejado",
          data: dados.planejado,
          // Barra vazada com contorno: o planejado se distingue do contratado pela forma, não só pela cor.
          backgroundColor: "#eef2ec",
          hoverBackgroundColor: "#e3ebe2",
          borderColor: "#7d887f",
          borderWidth: 1.5,
          borderRadius: 4,
          borderSkipped: "start",
          barPercentage: 0.9,
          categoryPercentage: 0.7,
        },
        {
          label: "Contratado",
          data: dados.contratado,
          backgroundColor: "#4f6b55",
          hoverBackgroundColor: "#3f5745",
          borderRadius: 4,
          borderSkipped: "start",
          barPercentage: 0.9,
          categoryPercentage: 0.7,
        },
      ],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      animation: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : { duration: 400 },
      interaction: { mode: "index", intersect: false, axis: "y" },
      scales: {
        x: {
          beginAtZero: true,
          border: { display: false },
          grid: { color: "#e4e8e1" },
          ticks: {
            callback: (v) => (estreito ? "" : "R$ ") + compacto.format(v),
            maxTicksLimit: estreito ? 3 : 6,
            maxRotation: 0,
          },
        },
        y: {
          border: { display: false },
          grid: { display: false },
          ticks: { color: "#263027", autoSkip: false },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
          align: "start",
          labels: { usePointStyle: true, pointStyle: "rectRounded", boxWidth: 10, boxHeight: 10, padding: 16 },
        },
        tooltip: {
          backgroundColor: "#263027",
          padding: 10,
          cornerRadius: 8,
          boxPadding: 4,
          callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${moeda.format(ctx.parsed.x)}` },
        },
      },
      layout: { padding: { left: 4, right: 8 } },
    },
  }); }
})();
