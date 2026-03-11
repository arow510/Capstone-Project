const YEARS = 5;

const $ = (id) => document.getElementById(id);

function clampNumber(n, { min = -Infinity, max = Infinity } = {}) {
  if (!Number.isFinite(n)) return 0;
  return Math.min(max, Math.max(min, n));
}

function parseMoneyInput(el) {
  return clampNumber(Number(el.value), { min: 0 });
}

function parsePercentInput(el) {
  return clampNumber(Number(el.value), { min: -100, max: 1000 });
}

function moneyFmt(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return "—";
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function computePlan({ year1Opex, year1Capex, annualChangePct }) {
  const rate = annualChangePct / 100;
  const rows = [];
  let cum = 0;

  for (let i = 0; i < YEARS; i += 1) {
    const year = i + 1;
    const factor = Math.pow(1 + rate, i);
    const opex = year1Opex * factor;
    const capex = year1Capex * factor;
    const total = opex + capex;
    cum += total;

    rows.push({
      year,
      opex,
      capex,
      total,
      cumulative: cum,
    });
  }

  const totals = rows.reduce(
    (acc, r) => {
      acc.opex += r.opex;
      acc.capex += r.capex;
      acc.all += r.total;
      return acc;
    },
    { opex: 0, capex: 0, all: 0 }
  );

  return { rows, totals };
}

function buildCsv(rows) {
  const header = ["Year", "OpEx ($)", "CapEx ($)", "Total ($)", "Cumulative ($)"];
  const lines = [header.join(",")];

  for (const r of rows) {
    lines.push(
      [
        r.year,
        Math.round(r.opex),
        Math.round(r.capex),
        Math.round(r.total),
        Math.round(r.cumulative),
      ].join(",")
    );
  }

  return lines.join("\n");
}

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  window.clearTimeout(toast._t);
  toast._t = window.setTimeout(() => {
    el.textContent = "";
  }, 1800);
}

let chart;

function renderChart(rows) {
  const ctx = $("planChart");
  const labels = rows.map((r) => `Year ${r.year}`);
  const opex = rows.map((r) => Math.round(r.opex));
  const capex = rows.map((r) => Math.round(r.capex));
  const totals = rows.map((r) => Math.round(r.total));

  const data = {
    labels,
    datasets: [
      {
        label: "OpEx ($)",
        data: opex,
        borderWidth: 1,
        backgroundColor: "rgba(124, 92, 255, 0.75)",
        borderColor: "rgba(124, 92, 255, 1)",
      },
      {
        label: "CapEx ($)",
        data: capex,
        borderWidth: 1,
        backgroundColor: "rgba(46, 229, 157, 0.65)",
        borderColor: "rgba(46, 229, 157, 1)",
      },
      {
        label: "Total ($)",
        data: totals,
        borderWidth: 1,
        backgroundColor: "rgba(255, 204, 102, 0.55)",
        borderColor: "rgba(255, 204, 102, 0.95)",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: "y", // <-- x = dollars, y = year
    scales: {
      x: {
        ticks: {
          callback: (v) => Number(v).toLocaleString(),
          color: "rgba(255,255,255,.75)",
        },
        grid: { color: "rgba(255,255,255,.08)" },
      },
      y: {
        ticks: { color: "rgba(255,255,255,.78)" },
        grid: { color: "rgba(255,255,255,.06)" },
      },
    },
    plugins: {
      legend: {
        labels: { color: "rgba(255,255,255,.82)" },
      },
      tooltip: {
        callbacks: {
          label: (ctx2) => `${ctx2.dataset.label}: $${Number(ctx2.parsed.x).toLocaleString()}`,
        },
      },
    },
  };

  if (chart) chart.destroy();
  chart = new Chart(ctx, { type: "bar", data, options });
}

function renderTable(rows, totals) {
  const body = $("cashflowBody");
  body.innerHTML = "";

  for (const r of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>Year ${r.year}</td>
      <td class="num">$${moneyFmt(r.opex)}</td>
      <td class="num">$${moneyFmt(r.capex)}</td>
      <td class="num"><strong>$${moneyFmt(r.total)}</strong></td>
      <td class="num">$${moneyFmt(r.cumulative)}</td>
    `;
    body.appendChild(tr);
  }

  $("totalOpex").textContent = `$${moneyFmt(totals.opex)}`;
  $("totalCapex").textContent = `$${moneyFmt(totals.capex)}`;
  $("totalAll").textContent = `$${moneyFmt(totals.all)}`;
}

function readInputs() {
  return {
    year1Opex: parseMoneyInput($("year1Opex")),
    year1Capex: parseMoneyInput($("year1Capex")),
    annualChangePct: parsePercentInput($("annualChangePct")),
  };
}

function recalc() {
  const { rows, totals } = computePlan(readInputs());
  renderTable(rows, totals);
  renderChart(rows);
  recalc._lastRows = rows;
}

function setExample() {
  $("year1Opex").value = "18000";
  $("year1Capex").value = "5000";
  $("annualChangePct").value = "5";
}

function setup() {
  ["year1Opex", "year1Capex", "annualChangePct"].forEach((id) => {
    $(id).addEventListener("input", recalc);
  });

  $("resetBtn").addEventListener("click", () => {
    setExample();
    recalc();
    toast("Reset to example values.");
  });

  $("copyBtn").addEventListener("click", async () => {
    const rows = recalc._lastRows ?? computePlan(readInputs()).rows;
    const csv = buildCsv(rows);
    try {
      await navigator.clipboard.writeText(csv);
      toast("Copied CSV to clipboard.");
    } catch {
      toast("Copy failed (browser permissions).");
    }
  });

  recalc();
}

setup();
