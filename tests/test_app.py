import io
from types import SimpleNamespace

import pytest
from backend.app import create_app
from backend.services.sentimiento_service import SentimientoService


class FakeAnalyzer:
    def predict(self, text):
        return SimpleNamespace(output="POS", probas={"POS": .6, "NEG": .3, "NEU": .1})


@pytest.fixture
def service():
    return SentimientoService(analyzer_factory=FakeAnalyzer)


@pytest.fixture
def client(service):
    app = create_app(service)
    app.config["TESTING"] = True
    return app.test_client()


def test_real_page_and_private_paths(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200
    for path in ("/.env", "/backend/app.py", "/static/../wsgi.py", "/datos/youtube_comentarios.csv"):
        assert client.get(path).status_code == 404
    health = client.get("/api/health")
    assert health.json["modelo_cargado"] is False
    assert "frame-ancestors 'none'" in health.headers["Content-Security-Policy"]


@pytest.mark.parametrize("body", [[], None, {"texto": 1}, {"texto": " "}, {"texto": "a" * 1001}, {"texto": "hola", "plataforma": []}, {"texto": "hola", "traducir": "false"}, {"comentarios": []}, {"comentarios": [{}] * 31}])
def test_invalid_json(client, body):
    assert client.post("/api/sentimiento/predecir", json=body).status_code in (415, 422)


def test_flags_and_original_label(client):
    response = client.post("/api/sentimiento/predecir", json={"texto": "Es hermoso pero falla 🙄"})
    assert response.status_code == 200
    r = response.json["resultados"][0]
    assert r["sentimiento_modelo"] == "POSITIVO"
    assert r["sentimiento_final"] == ""
    assert r["estado_revision"] == "PENDIENTE"
    assert {"Baja confianza", "Posible opinión mixta", "Posible sarcasmo", "Verificar idioma"}.issubset(r["motivos_revision"])
    assert abs(sum(r["probabilidades"].values()) - 1) < 1e-6


def test_youtube_link_extracts_and_classifies_comments(client, monkeypatch):
    from backend.services import youtube_service

    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")

    def get_comments(url, *, headers, params, **options):
        assert url == youtube_service.API_COMENTARIOS
        assert headers["X-Goog-Api-Key"] == "test-key"
        assert params["videoId"] == "QdBZY2fkU-0"
        assert params["maxResults"] == 30
        assert options["allow_redirects"] is False
        return SimpleNamespace(status_code=200, json=lambda: {"items": [
            {"snippet": {"topLevelComment": {"id": "one", "snippet": {"textDisplay": "Gran juego"}}}},
            {"snippet": {"topLevelComment": {"id": "two", "snippet": {
                "textDisplay": "This is an amazing video and I absolutely love it."
            }}}},
        ]})

    monkeypatch.setattr(youtube_service.requests, "get", get_comments)
    response = client.post("/api/sentimiento/youtube", json={"url": "https://youtu.be/QdBZY2fkU-0?t=12"})
    assert response.status_code == 200
    assert response.json["resumen"] == {"POSITIVO": 1, "PENDIENTE_IDIOMA": 1}
    assert response.json["resultados"][0]["comentario_id"] == "one"


def test_youtube_validation_and_missing_configuration(client, monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    invalid = client.post("/api/sentimiento/youtube", json={"url": "https://youtube.com.example/watch?v=QdBZY2fkU-0"})
    assert invalid.status_code == 422
    missing_key = client.post("/api/sentimiento/youtube", json={"url": "https://www.youtube.com/shorts/QdBZY2fkU-0"})
    assert missing_key.status_code == 503


def test_csv_and_injection_remains_plain_text(client):
    text = 'texto,plataforma\n"<script>alert(1)</script>",YouTube\n"=SUM(A1:A2)",Bluesky\n'
    response = client.post("/api/sentimiento/predecir", data={"archivo": (io.BytesIO(text.encode()), "datos.csv")})
    assert response.status_code == 200
    assert len(response.json["resultados"]) == 2
    assert response.json["resultados"][0]["texto"].startswith("<script>")


@pytest.mark.parametrize("content", [b"nombre\na", b"texto\n", b"texto\n\xff", ("texto\n" + "hola\n" * 31).encode(), b'texto\n"sin cerrar'])
def test_invalid_csv(client, content):
    assert client.post("/api/sentimiento/predecir", data={"archivo": (io.BytesIO(content), "x.csv")}).status_code == 422


def test_non_spanish_pending_and_optional_translation():
    service = SentimientoService(FakeAnalyzer, translator=lambda t: "Este juego es muy bueno y entretenido")
    comments = [{"texto": "This video game is really wonderful and I absolutely love playing it", "plataforma": "Manual"}]
    first = service.analizar(comments)[0]
    assert first["sentimiento_modelo"] == "PENDIENTE_IDIOMA"
    assert not service.listo
    translated = service.analizar(comments, True)[0]
    assert translated["fue_traducido"] is True
    assert translated["sentimiento_modelo"] == "POSITIVO"


def test_translation_failure_is_not_a_prediction():
    service = SentimientoService(FakeAnalyzer, translator=lambda t: "")
    result = service.analizar([{"texto": "This video game is really wonderful and I absolutely love playing it", "plataforma": "Manual"}], True)[0]
    assert result["sentimiento_modelo"] == "PENDIENTE_TRADUCCION"
    assert not result["probabilidades"]


def test_failure_and_concurrency(client, service):
    service._lock.acquire()
    try:
        assert client.post("/api/sentimiento/predecir", json={"texto": "hola"}).status_code == 503
    finally:
        service._lock.release()
    def broken():
        raise RuntimeError("secret must not appear")
    service._factory = broken
    response = client.post("/api/sentimiento/predecir", json={"texto": "hola"})
    assert response.status_code == 503
    assert "secret" not in response.text


def test_limits(client):
    assert client.post("/api/sentimiento/predecir", data=b"a" * (257 * 1024), content_type="application/json").status_code == 413
    for _ in range(19):
        client.post("/api/sentimiento/predecir", json={"texto": "hola"})
    response = client.post("/api/sentimiento/predecir", json={"texto": "hola"})
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_historical_counts(client):
    rows = client.get("/api/estudio").json["redes"]
    assert sum(r["total_csv"] for r in rows) == 169
    assert sum(r["validos"] for r in rows) == 161
    for r in rows:
        assert r["positivos"] + r["neutrales"] + r["negativos"] == r["validos"]
        assert r["validos"] + r["excluidos"] + r["pendientes"] == r["total_csv"]


def test_manual_translation_and_context(client):
    response = client.post("/api/sentimiento/predecir", json={"texto": "This video game is really wonderful and I absolutely love playing it", "texto_espanol": "Este juego es muy bueno y entretenido", "comentario_id": "abc", "texto_publicacion_origen": "Un anuncio del videojuego"})
    assert response.status_code == 200
    result = response.json["resultados"][0]
    assert result["metodo_traduccion"] == "MANUAL"
    assert result["sentimiento_modelo"] == "POSITIVO"
    assert result["comentario_id"] == "abc"
    assert result["texto_publicacion_origen"] == "Un anuncio del videojuego"


def test_translation_timeout_is_pending(monkeypatch):
    import requests
    from backend.services import traduccion_service
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == (3, 5)
        assert kwargs["allow_redirects"] is False
        raise requests.Timeout()
    monkeypatch.setattr(traduccion_service.requests, "get", timeout)
    service = SentimientoService(FakeAnalyzer)
    result = service.analizar([{"texto": "This video game is really wonderful and I absolutely love playing it", "plataforma": "Manual"}], True)[0]
    assert result["sentimiento_modelo"] == "PENDIENTE_TRADUCCION"
