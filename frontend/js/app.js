"use strict";
const $ = (id) => document.getElementById(id);
const LABELS = ["POSITIVO", "NEUTRAL", "NEGATIVO", "FUERA_DE_TEMA", "OTRO_IDIOMA", "NO_EVALUABLE"];
let resultados = [];
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
const pct = (n) => `${(100 * n).toFixed(1)} %`;
$("texto").addEventListener("input", () => { $("counter").textContent = `${$("texto").value.length} / 1000`; });
$("example").addEventListener("click", () => {
  $("texto").value = "Los gráficos son hermosos, pero tiene muchos errores 🙄";
  $("texto-espanol").value = "";
  $("archivo").value = "";
  $("texto").dispatchEvent(new Event("input"));
});
$("clear-file").addEventListener("click", () => { $("archivo").value = ""; });
$("analyze-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("archivo").files[0];
  if (!file && !$("texto").value.trim()) { $("message").textContent = "Escribe un comentario o elige un CSV."; return; }
  if (file && file.size > 200 * 1024) { $("message").textContent = "El CSV debe pesar menos de 200 KB."; return; }
  $("submit").disabled = true;
  $("message").textContent = "Analizando… La primera carga del modelo puede tardar unos minutos.";
  // Clear previous data so a failed request cannot leave a misleading result.
  resultados = [];
  $("results").hidden = true;
  try {
    let body;
    if (file) {
      body = new FormData(); body.append("archivo", file); body.append("traducir", String($("traducir").checked));
    } else {
      body = { texto: $("texto").value, texto_espanol: $("texto-espanol").value, plataforma: $("plataforma").value, traducir: $("traducir").checked };
    }
    const response = await GameAPI.predecir(body);
    resultados = response.resultados;
    renderResults();
    $("message").textContent = `${resultados.length} comentario(s) procesado(s). Revisa las etiquetas finales.`;
  } catch (error) { $("message").textContent = error instanceof TypeError ? "No se pudo conectar con el servidor." : error.message; }
  finally { $("submit").disabled = false; }
});
function renderSummary() {
  $("session-summary").replaceChildren();
  const counts = {};
  for (const r of resultados) { const label = r.sentimiento_final || r.sentimiento_modelo; counts[label] = (counts[label] || 0) + 1; }
  for (const [name, count] of Object.entries(counts)) $("session-summary").append(el("span", `${name}: ${count}`));
  $("session-summary").append(el("span", `REVISADOS: ${resultados.filter(r => r.estado_revision === "REVISADO").length} / ${resultados.length}`));
}
function renderResults() {
  $("results").hidden = false;
  $("result-list").replaceChildren();
  resultados.forEach((r, index) => {
    const card = el("article", undefined, "result-card");
    if (r.texto_publicacion_origen) card.append(el("p", `Publicación original (contexto): ${r.texto_publicacion_origen}`, "hint"));
    card.append(el("blockquote", r.texto));
    const meta = el("div", undefined, "result-meta");
    meta.append(el("span", r.plataforma), el("span", `Idioma: ${r.idioma}`), el("strong", `IA: ${r.sentimiento_modelo}`));
    card.append(meta);
    if (Object.keys(r.probabilidades).length) {
      card.append(el("p", `Confianza de la etiqueta: ${pct(r.confianza)}`, "hint"));
      const probs = el("div", undefined, "probabilities");
      ["POSITIVO", "NEUTRAL", "NEGATIVO"].forEach((name, i) => probs.append(el("span", `${name}: ${pct(r.probabilidades[name])}`, ["pos", "neu", "neg"][i])));
      card.append(probs);
    }
    if (r.fue_traducido) card.append(el("p", `Traducción ${r.metodo_traduccion.toLowerCase()} usada: ${r.texto_modelo}`, "hint"));
    card.append(el("p", r.motivos_revision.length ? `Revisar: ${r.motivos_revision.join(" · ")}` : "Sin alertas automáticas. Verifica el contexto antes de aprobar.", "hint"));
    const label = el("label", "Etiqueta final (revisión humana)"); label.htmlFor = `revision-${index}`;
    const select = el("select"); select.id = label.htmlFor;
    const pending = el("option", "Pendiente de revisión"); pending.value = ""; select.append(pending);
    LABELS.forEach(name => { const option = el("option", name); option.value = name; select.append(option); });
    select.addEventListener("change", () => { r.sentimiento_final = select.value; r.estado_revision = select.value ? "REVISADO" : "PENDIENTE"; renderSummary(); });
    card.append(label, select); $("result-list").append(card);
  });
  renderSummary();
}
// Quote CSV and neutralize spreadsheet formulas, including leading whitespace.
function csvCell(value) {
  let text = String(value ?? "");
  if (/^[\s\uFEFF]*[=+\-@]/u.test(text) || /^[\t\r\n]/u.test(text)) text = "'" + text;
  return `"${text.replaceAll('"', '""')}"`;
}
$("export").addEventListener("click", () => {
  const columns = ["comentario_id", "texto", "plataforma", "texto_publicacion_origen", "texto_modelo", "idioma", "sentimiento_modelo", "confianza", "prob_positivo", "prob_neutral", "prob_negativo", "fue_traducido", "metodo_traduccion", "motivos_revision", "sentimiento_final", "estado_revision"];
  const rows = resultados.map(r => ({ ...r, motivos_revision: r.motivos_revision.join("; "), prob_positivo: r.probabilidades.POSITIVO ?? "", prob_neutral: r.probabilidades.NEUTRAL ?? "", prob_negativo: r.probabilidades.NEGATIVO ?? "" }));
  const text = "\uFEFF" + [columns, ...rows.map(r => columns.map(c => r[c]))].map(row => row.map(csvCell).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const a = el("a"); a.href = url; a.download = "gamesentiment_revision.csv"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
GameAPI.request("/health").then(data => { $("health").textContent = data.modelo_cargado ? "● RoBERTuito cargado" : "● API disponible"; }).catch(() => { $("health").textContent = "API no disponible"; });
GameAPI.request("/estudio").then(data => {
  for (const row of data.redes) {
    const card = el("article", undefined, "study-card");
    card.append(el("h3", row.plataforma), el("p", `${row.validos} válidos · ${row.excluidos} excluidos · ${row.total_csv} en archivo final`));
    const stack = el("div", undefined, "stack");
    stack.setAttribute("role", "img");
    stack.setAttribute("aria-label", `Positivo ${row.porcentaje_positivo} %, neutral ${row.porcentaje_neutral} %, negativo ${row.porcentaje_negativo} %`);
    const values = el("div", undefined, "study-values");
    ["positivo", "neutral", "negativo"].forEach((name, index) => {
      const value = row[`porcentaje_${name}`]; const cls = ["pos", "neu", "neg"][index];
      const segment = el("span", undefined, `segment ${cls}`); segment.style.width = `${value}%`; stack.append(segment);
      values.append(el("span", `${value.toFixed(1)} %`, cls));
    });
    card.append(stack, values); $("study-chart").append(card);
  }
}).catch(() => { $("study-chart").textContent = "No se pudo cargar el estudio histórico. Recarga la página."; });
