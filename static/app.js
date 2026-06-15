"use strict";

const form = document.getElementById("search-form");
const statusEl = document.getElementById("status");
const demoBanner = document.getElementById("demo-banner");
const realSearch = document.getElementById("real-search");
const realSearchLinks = document.getElementById("real-search-links");
const summaryEl = document.getElementById("summary");
const resultsEl = document.getElementById("results");
const providerTag = document.getElementById("provider-tag");

const brl = (v) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const PARTNERS = {
  kayak: "Kayak",
  skyscanner: "Skyscanner",
  decolar: "Decolar",
  latam: "LATAM",
  google: "Google Voos",
};

// Botões mostrados em cada card de oferta (resto fica no topo, p/ não poluir).
const OFFER_PARTNERS = ["kayak", "decolar", "google"];

function showStatus(message) {
  if (!message) {
    statusEl.hidden = true;
    return;
  }
  statusEl.hidden = false;
  statusEl.textContent = message;
}

function renderRealSearch(links, calendarLink) {
  if (!links || !Object.keys(links).length) {
    realSearch.hidden = true;
    return;
  }
  realSearch.hidden = false;
  let html = Object.entries(links)
    .map(
      ([key, url]) =>
        `<a class="btn-real" href="${url}" target="_blank" rel="noopener">${
          PARTNERS[key] || key
        } ↗</a>`
    )
    .join("");
  if (calendarLink) {
    html += `<a class="btn-real btn-calendar" href="${calendarLink}" target="_blank" rel="noopener">📅 Calendário de preços ↗</a>`;
  }
  realSearchLinks.innerHTML = html;
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

function offerLinks(o) {
  if (!o.links || !Object.keys(o.links).length) return "";
  const label = o.estimated ? "Ver preço real" : "Reservar";
  const keys = OFFER_PARTNERS.filter((k) => o.links[k]);
  return keys
    .map(
      (key, i) =>
        `<a class="btn-link" href="${o.links[key]}" target="_blank" rel="noopener">${
          i === 0 ? label + " — " : ""
        }${PARTNERS[key] || key} ↗</a>`
    )
    .join("");
}

function offerCard(o) {
  const badges = [];
  if (o.estimated)
    badges.push('<span class="badge sim">simulação</span>');
  if (o.is_flash_deal)
    badges.push('<span class="badge flash">⚡ Promoção relâmpago</span>');
  if (o.is_deal)
    badges.push(`<span class="badge deal">↓ ${o.discount_pct}% abaixo da mediana</span>`);
  badges.push(`<span class="badge stops">${stopsLabel(o.stops)}</span>`);

  const priceLabel = o.estimated
    ? '<span class="price-tag">preço estimado</span>'
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
        ${priceLabel}
        ${discount}
        <div class="offer-links">${offerLinks(o)}</div>
      </div>
    </article>`;
}

async function runSearch(params) {
  resultsEl.innerHTML = '<div class="loading">Procurando as melhores tarifas…</div>';
  summaryEl.hidden = true;
  demoBanner.hidden = true;
  showStatus("");

  try {
    const qs = new URLSearchParams(params).toString();
    const resp = await fetch(`/api/search?${qs}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    const isDemo = data.provider !== "amadeus";
    providerTag.textContent = isDemo
      ? "Fonte: modo demonstração (preços simulados)"
      : "Fonte: API Amadeus (preços reais)";
    demoBanner.hidden = !isDemo;

    renderRealSearch(data.search_links, data.calendar_link);
    if (data.notice) showStatus(data.notice);

    if (!data.offers.length) {
      resultsEl.innerHTML =
        '<div class="loading">Nenhuma oferta encontrada. Use os links acima para ver os preços reais.</div>';
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
