"""Real inference smoke test; deliberately separate from isolated unit tests."""
import json
from pathlib import Path
from backend.app import create_app


def main():
    app = create_app()
    body = {"comentarios": [
        {"texto": "Este videojuego es increíble y me encanta jugarlo", "plataforma": "YouTube"},
        {"texto": "La actualización es horrible y arruinó toda la experiencia", "plataforma": "Bluesky"},
        {"texto": "Los gráficos son hermosos, pero tiene muchos errores 🙄", "plataforma": "Mastodon"},
        {"texto": "This video game is really wonderful and I absolutely love playing it", "texto_espanol": "Este videojuego es increíble y me encanta jugarlo", "plataforma": "Manual"},
    ]}
    response = app.test_client().post("/api/sentimiento/predecir", json=body)
    assert response.status_code == 200, response.json
    rows = response.json["resultados"]
    assert len(rows) == 4
    assert all(abs(sum(r["probabilidades"].values()) - 1) < .001 for r in rows)
    assert all(r["sentimiento_final"] == "" and r["estado_revision"] == "PENDIENTE" for r in rows)
    assert rows[3]["metodo_traduccion"] == "MANUAL"
    assert rows[0]["sentimiento_modelo"] == rows[3]["sentimiento_modelo"]
    path = Path(__file__).resolve().parents[1] / "PRUEBA_MODELO_REAL.json"
    path.write_text(json.dumps(response.json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Inferencia real correcta: 4 comentarios; traducción manual, probabilidades y estados verificados.")


if __name__ == "__main__":
    main()
