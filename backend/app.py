import json
import os
import time
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from backend.controllers.sentimiento_ctrl import bp
from backend.services.sentimiento_service import MODEL, SentimientoService

ROOT = Path(__file__).resolve().parents[1]


def create_app(service=None):
    app = Flask(__name__, static_folder=str(ROOT / "frontend"), static_url_path="/static")
    app.config.update(MAX_CONTENT_LENGTH=256 * 1024, JSON_SORT_KEYS=False)
    app.extensions["sentimiento"] = service or SentimientoService()
    app.register_blueprint(bp)
    rate_lock = Lock()
    window = {"inicio": time.monotonic(), "cantidad": 0}

    @app.before_request
    def limite_global():
        if request.method == "POST" and request.path.startswith("/api/"):
            with rate_lock:
                now = time.monotonic()
                if now - window["inicio"] >= 60:
                    window.update(inicio=now, cantidad=0)
                if window["cantidad"] >= 20:
                    return jsonify(error="Límite global de 20 solicitudes por minuto. Reintenta después."), 429, {"Retry-After": "60"}
                window["cantidad"] += 1

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return send_from_directory(ROOT / "frontend", "index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", modelo=MODEL, modelo_cargado=app.extensions["sentimiento"].listo)

    @app.get("/api/estudio")
    def estudio():
        return jsonify(json.loads((ROOT / "data" / "estudio.json").read_text(encoding="utf-8")))

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error="Archivo o petición demasiado grande." if error.code == 413 else error.name), error.code

    @app.errorhandler(Exception)
    def unexpected(error):
        app.logger.error("Error interno de tipo %s", type(error).__name__)
        return jsonify(error="Error interno del servidor."), 500

    return app


if __name__ == "__main__":
    from waitress import serve
    serve(create_app(), host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), threads=4)
