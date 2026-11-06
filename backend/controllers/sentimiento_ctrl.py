import csv
import io
from collections import Counter

from flask import Blueprint, current_app, jsonify, request
from backend.services.sentimiento_service import ModeloNoDisponible, ServicioOcupado
from backend.services.youtube_service import ErrorYouTube, extraer_comentarios, obtener_video_id

bp = Blueprint("sentimiento", __name__, url_prefix="/api/sentimiento")
PLATAFORMAS = {"Manual", "YouTube", "Bluesky", "Mastodon"}


@bp.post("/predecir")
def predecir():
    traducir = False
    if request.mimetype == "multipart/form-data":
        archivo = request.files.get("archivo")
        if archivo is None:
            return jsonify(error="Selecciona un CSV UTF-8 con columna texto."), 422
        try:
            contenido = archivo.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(contenido), strict=True)
            if not reader.fieldnames or "texto" not in reader.fieldnames:
                raise ValueError()
            comentarios = []
            for fila in reader:
                if len(comentarios) >= 30 or None in fila:
                    raise ValueError()
                comentarios.append({"texto": fila.get("texto"), "plataforma": fila.get("plataforma") or "Manual", "comentario_id": fila.get("comentario_id") or "", "texto_publicacion_origen": fila.get("texto_publicacion_origen") or "", "texto_espanol": fila.get("texto_espanol") or ""})
        except (UnicodeError, csv.Error, ValueError):
            return jsonify(error="CSV inválido: usa UTF-8, coma, columna texto y entre 1 y 30 filas."), 422
        if request.form.get("traducir", "false") not in {"true", "false"}:
            return jsonify(error="traducir debe ser true o false."), 422
        traducir = request.form.get("traducir") == "true"
    else:
        if not request.is_json:
            return jsonify(error="Envía JSON o un archivo CSV."), 415
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or not isinstance(body.get("traducir", False), bool):
            return jsonify(error="JSON inválido; traducir debe ser booleano."), 422
        comentarios = body.get("comentarios")
        if comentarios is None and "texto" in body:
            comentarios = [body]
        traducir = body.get("traducir", False)
    if not isinstance(comentarios, list) or not 1 <= len(comentarios) <= 30:
        return jsonify(error="Envía entre 1 y 30 comentarios."), 422
    normalizados = []
    for c in comentarios:
        if not isinstance(c, dict) or not isinstance(c.get("texto"), str) or not 1 <= len(c["texto"].strip()) <= 1000:
            return jsonify(error="Cada texto debe contener entre 1 y 1000 caracteres."), 422
        plataforma = c.get("plataforma", "Manual")
        if not isinstance(plataforma, str) or plataforma not in PLATAFORMAS:
            return jsonify(error="Plataforma inválida: Manual, YouTube, Bluesky o Mastodon."), 422
        metadata = {"comentario_id": c.get("comentario_id", ""), "texto_publicacion_origen": c.get("texto_publicacion_origen", ""), "texto_espanol": c.get("texto_espanol", "")}
        if any(not isinstance(value, str) or len(value) > limit for value, limit in ((metadata["comentario_id"], 200), (metadata["texto_publicacion_origen"], 2000), (metadata["texto_espanol"], 1000))):
            return jsonify(error="ID, contexto o traducción inválidos: máximo 200, 2000 y 1000 caracteres respectivamente."), 422
        normalizados.append({"texto": c["texto"].strip(), "plataforma": plataforma, **metadata})
    return analizar_comentarios(normalizados, traducir)


@bp.post("/youtube")
def predecir_youtube():
    if not request.is_json:
        return jsonify(error="Envía el enlace de YouTube en formato JSON."), 415
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("traducir", False), bool):
        return jsonify(error="JSON inválido; traducir debe ser booleano."), 422
    try:
        comentarios = extraer_comentarios(obtener_video_id(body.get("url")))
    except ErrorYouTube as error:
        return jsonify(error=str(error)), error.status
    return analizar_comentarios(comentarios, body.get("traducir", False))


def analizar_comentarios(comentarios, traducir):
    try:
        resultados = current_app.extensions["sentimiento"].analizar(comentarios, traducir) if comentarios else []
    except ServicioOcupado:
        return jsonify(error="El analizador está ocupado. Reintenta en unos segundos."), 503, {"Retry-After": "5"}
    except ModeloNoDisponible:
        current_app.logger.error("Modelo no disponible; comprobar instalación, memoria y caché Hugging Face.")
        return jsonify(error="No se pudo cargar o ejecutar RoBERTuito. Revisa la instalación del servidor."), 503
    return jsonify(resultados=resultados, resumen=dict(Counter(r["sentimiento_modelo"] for r in resultados)))
