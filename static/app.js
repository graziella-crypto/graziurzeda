"use strict";

const form = document.getElementById("search-form");
const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary");
const resultsEl = document.getElementById("results");
const providerTag = document.getElementById("provider-tag");

const brl = (v) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function showStatus(message, kind = "info") {
  if (!message) {
    statusEl.hidden = true;
    return;
  }
  statusEl.hidden = false;
  statusEl.textContent = message;
}

function renderSummary(data) {
  summaryEl.hidden = false;
  document.getElementById("stat-cheapest").textContent = data.cheapest
    ? brl(data.cheapest.price)
    : "—";
  document.getElementById("stat-median").textContent = brl(data.median_price);
  document.getElementById("stat-flash").textContent = data.flash_deals_count;
  document.getElementById("stat-deals").textContent = data.deals_count;
}

function stopsLabel(stops) {
  if (stops === 0) return "Direto";
  if (stops === 1) return "1 parada";
  return `${stops} paradas`;
}

function offerCard(o) {
  const badges = [];
  if (o.is_flash_deal)
    badges.push('<span class="badge flash">⚡ Promoção relâmpago</span>');
  if (o.is_deal)
    badges.push(`<span class="badge deal">↓ ${o.discount_pct}% abaixo da mediana</span>`);
  badges.push(`<span class="badge stops">${stopsLabel(o.stops)}</span>`);

  const link = o.deep_link
    ? `<a class="btn-link" href="${o.deep_link}" target="_blank" rel="noopener">Ver oferta ↗</a>`
    : "";

  const discount =
    o.discount_pct > 0
      ? `<span class="price-discount">economia de ${o.discount_pct}%</span>`
      : "";

  return `
    <article class="offer ${o.is_flash_deal ? "flash" : ""}">
      <div class="offer-main">
        <span class="offer-airline">${o.airline}</span>
        <span class="offer-route">${o.origin} → ${o.destination} · ${o.departure_date} ↔ ${o.return_date}</span>
        <span class="offer-times">Ida ${o.outbound_departure_time}–${o.outbound_arrival_time} (${o.duration_outbound}) · Volta ${o.inbound_departure_time}–${o.inbound_arrival_time} (${o.duration_inbound})</span>
        <div class="badges">${badges.join("")}</div>
      </div>
      <div class="offer-price">
        <span class="price-value">${brl(o.price)}</span>
        ${discount}
        ${link}
      </div>
    </article>`;
}

async function runSearch(params) {
  resultsEl.innerHTML = '<div class="loading">Procurando as melhores tarifas…</div>';
  summaryEl.hidden = true;
  showStatus("");

  try {
    const qs = new URLSearchParams(params).toString();
    const resp = await fetch(`/api/search?${qs}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    providerTag.textContent =
      data.provider === "amadeus"
        ? "Fonte: API Amadeus (dados reais)"
        : "Fonte: modo demonstração";

    if (data.notice) showStatus(data.notice);

    if (!data.offers.length) {
      resultsEl.innerHTML =
        '<div class="loading">Nenhuma oferta encontrada para esse trecho/datas.</div>';
      return;
    }

    renderSummary(data);
    resultsEl.innerHTML = data.offers.map(offerCard).join("");
  } catch (err) {
    resultsEl.innerHTML = "";
    showStatus(`Erro ao buscar ofertas: ${err.message}`);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  runSearch(Object.fromEntries(fd.entries()));
});

// Busca automática ao abrir, com os valores padrão (GYN → MCZ, ago/2026).
window.addEventListener("DOMContentLoaded", () => {
  const fd = new FormData(form);
  runSearch(Object.fromEntries(fd.entries()));
});
