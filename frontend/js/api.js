"use strict";
window.GameAPI = {
  async request(path, options = {}) {
    const response = await fetch(`/api${path}`, options);
    let data;
    try { data = await response.json(); }
    catch { throw new Error("El servidor no devolvió una respuesta válida. Reintenta más tarde."); }
    if (!response.ok) throw new Error(data.error || `Error ${response.status}`);
    return data;
  },
  predecir(body) {
    return this.request("/sentimiento/predecir", body instanceof FormData
      ? { method: "POST", body }
      : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }
};
