"use strict";
window.GameAPI = {
  async request(path, options = {}) {
    const response = await fetch(`/api${path}`, options);
    let data;
    try { data = await response.json(); }
    catch {
      if (response.status >= 500 || (response.ok && response.headers.get("Content-Type")?.includes("text/html"))) {
        throw new Error("El servidor se está iniciando o interrumpió el análisis. Espera un momento y vuelve a intentarlo.");
      }
      throw new Error("El servidor no devolvió una respuesta válida. Reintenta más tarde.");
    }
    if (!response.ok) throw new Error(data.error || `Error ${response.status}`);
    return data;
  },
  predecir(body) {
    return this.request("/sentimiento/predecir", body instanceof FormData
      ? { method: "POST", body }
      : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }
};
