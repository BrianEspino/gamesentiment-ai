import os
import re
from urllib.parse import parse_qs, urlsplit

import requests

LIMITE_COMENTARIOS = 30
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
API_COMENTARIOS = "https://www.googleapis.com/youtube/v3/commentThreads"


class ErrorYouTube(Exception):
    def __init__(self, mensaje, status):
        super().__init__(mensaje)
        self.status = status


def obtener_video_id(enlace):
    invalido = "Pega un enlace válido a un video, Short o directo de YouTube."
    if not isinstance(enlace, str) or len(enlace) > 2048:
        raise ErrorYouTube(invalido, 422)
    try:
        partes = urlsplit(enlace.strip())
        dominio = partes.hostname
    except ValueError:
        raise ErrorYouTube(invalido, 422) from None
    if partes.scheme not in ("http", "https") or partes.username is not None:
        raise ErrorYouTube(invalido, 422)

    segmentos = partes.path.strip("/").split("/")
    video_id = ""
    if dominio in ("youtu.be", "www.youtu.be") and len(segmentos) == 1:
        video_id = segmentos[0]
    elif dominio in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
        if partes.path == "/watch":
            video_id = parse_qs(partes.query).get("v", [""])[0]
        elif len(segmentos) == 2 and segmentos[0] in ("shorts", "live", "embed"):
            video_id = segmentos[1]
    if not VIDEO_ID.fullmatch(video_id):
        raise ErrorYouTube(invalido, 422)
    return video_id


def extraer_comentarios(video_id):
    clave = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not clave:
        raise ErrorYouTube("El servidor todavía no tiene configurado el acceso a YouTube.", 503)

    try:
        respuesta = requests.get(
            API_COMENTARIOS,
            headers={"X-Goog-Api-Key": clave},
            params={
                "part": "snippet",
                "videoId": video_id,
                "maxResults": LIMITE_COMENTARIOS,
                "order": "time",
                "textFormat": "plainText",
                "fields": "items(snippet(topLevelComment(id,snippet(textDisplay))))",
            },
            timeout=(3, 10),
            allow_redirects=False,
        )
        datos = respuesta.json()
        if respuesta.status_code != 200:
            errores = datos.get("error", {}).get("errors", [])
            motivo = errores[0].get("reason") if errores else None
            if motivo == "commentsDisabled":
                raise ErrorYouTube("El video tiene los comentarios desactivados.", 422)
            if motivo == "videoNotFound":
                raise ErrorYouTube("El video no está disponible para consultar sus comentarios.", 404)
            if motivo in ("quotaExceeded", "dailyLimitExceeded"):
                raise ErrorYouTube("Se agotó la cuota de YouTube. Intenta más tarde.", 503)
            raise ErrorYouTube("YouTube rechazó la consulta de comentarios.", 502)

        comentarios = []
        for item in datos["items"][:LIMITE_COMENTARIOS]:
            comentario = item["snippet"]["topLevelComment"]
            texto = comentario["snippet"]["textDisplay"].strip()
            comentarios.append({
                "texto": texto,
                "plataforma": "YouTube",
                "comentario_id": comentario["id"],
            })
        return comentarios
    except requests.Timeout:
        raise ErrorYouTube("YouTube tardó demasiado en responder. Intenta de nuevo.", 504) from None
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
        raise ErrorYouTube("No se pudieron obtener los comentarios de YouTube.", 502) from None
