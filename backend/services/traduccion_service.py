"""Bounded Google Translate web adapter for the original optional workflow.

No URL is accepted from the visitor. Provider HTML can change; callers must
handle failure as PENDIENTE_TRADUCCION rather than inventing a translation.
"""
import requests
from bs4 import BeautifulSoup


def traducir_es(texto):
    with requests.get(
        "https://translate.google.com/m",
        params={"sl": "auto", "tl": "es", "q": texto},
        timeout=(3, 5),
        allow_redirects=False,
        stream=True,
    ) as response:
        if response.status_code != 200:
            raise ValueError("Proveedor de traducción no disponible")
        contenido = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            contenido.extend(chunk)
            if len(contenido) > 256 * 1024:
                raise ValueError("Respuesta de traducción excesiva")
        soup = BeautifulSoup(contenido.decode("utf-8"), "html.parser")
        resultado = soup.select_one("div.result-container, div.t0")
        if resultado is None or not resultado.get_text(strip=True):
            raise ValueError("Sin traducción verificable")
        return resultado.get_text(strip=True)
