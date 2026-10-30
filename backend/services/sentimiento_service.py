import re
from threading import Lock

from langdetect import DetectorFactory, LangDetectException, detect_langs

from backend.models.resultado import Resultado

DetectorFactory.seed = 0
ETIQUETAS = {"POS": "POSITIVO", "NEU": "NEUTRAL", "NEG": "NEGATIVO"}
MODEL = "pysentimiento/robertuito-sentiment-analysis"


class ModeloNoDisponible(Exception):
    pass


class ServicioOcupado(Exception):
    pass


class SentimientoService:
    def __init__(self, analyzer_factory=None, translator=None):
        self._analyzer = None
        self._factory = analyzer_factory
        self._translator = translator
        self._lock = Lock()

    @property
    def listo(self):
        return self._analyzer is not None

    def cargar(self):
        if self._analyzer is None:
            try:
                if self._factory:
                    self._analyzer = self._factory()
                else:
                    from pysentimiento import create_analyzer
                    self._analyzer = create_analyzer(task="sentiment", lang="es", model_name=MODEL)
            except Exception:
                raise ModeloNoDisponible() from None
        return self._analyzer

    def analizar(self, comentarios, traducir=False):
        # One request at a time bounds model memory and avoids an inference queue.
        if not self._lock.acquire(blocking=False):
            raise ServicioOcupado()
        try:
            return [self._uno(c, traducir).to_dict() for c in comentarios]
        finally:
            self._lock.release()

    def _uno(self, comentario, traducir):
        original = comentario["texto"]
        texto = re.sub(r"https?://\S+", " ", original)
        texto = re.sub(r"(?<!\w)@\s*[\w.\-]+(?:@[\w.\-]+)?", " ", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        idioma = "INDETERMINADO"
        if len(re.findall(r"[^\W\d_]+", texto)) >= 5:
            try:
                candidato = detect_langs(texto)[0]
                idioma = candidato.lang if candidato.prob >= .85 else "DUDOSO"
            except LangDetectException:
                pass
        r = Resultado(original, texto, idioma, plataforma=comentario["plataforma"], comentario_id=comentario.get("comentario_id", ""), texto_publicacion_origen=comentario.get("texto_publicacion_origen", ""))
        if not any(c.isalnum() for c in texto) and not any(c in texto for c in "❤️🔥😂😍😭🙄😡👍👎"):
            r.motivos_revision.append("Sin contenido interpretable")
            return r
        manual = comentario.get("texto_espanol", "").strip()
        if manual:
            texto = manual
            r.texto_modelo = manual
            r.fue_traducido = True
            r.metodo_traduccion = "MANUAL"
            r.motivos_revision.append("Verificar traducción manual y fidelidad al original")
        elif idioma not in ("es", "INDETERMINADO", "DUDOSO"):
            if not traducir:
                r.sentimiento_modelo = "PENDIENTE_IDIOMA"
                r.motivos_revision.append("Traducir al español o excluir por idioma")
                return r
            try:
                if self._translator:
                    texto = self._translator(texto)
                else:
                    from backend.services.traduccion_service import traducir_es
                    texto = traducir_es(texto)
                if not isinstance(texto, str) or not texto.strip() or len(texto) > 3000:
                    raise ValueError()
                r.texto_modelo = texto
                r.fue_traducido = True
                r.metodo_traduccion = "AUTOMATICA"
                r.motivos_revision.append("Verificar traducción automática")
            except Exception:
                r.sentimiento_modelo = "PENDIENTE_TRADUCCION"
                r.motivos_revision.append("Falló la traducción; traducir o excluir manualmente")
                return r
        elif idioma != "es":
            r.motivos_revision.append("Verificar idioma")
        try:
            pred = self.cargar().predict(texto)
            r.sentimiento_modelo = ETIQUETAS[pred.output]
            r.confianza = round(float(pred.probas[pred.output]), 4)
            r.probabilidades = {ETIQUETAS[k]: round(float(pred.probas[k]), 4) for k in ETIQUETAS}
        except ModeloNoDisponible:
            raise
        except Exception:
            raise ModeloNoDisponible() from None
        if r.confianza < .65:
            r.motivos_revision.append("Baja confianza")
        if re.search(r"\b(pero|aunque|sin embargo)\b", original.lower()):
            r.motivos_revision.append("Posible opinión mixta")
        if any(c in original for c in ("🙄", "🤡", "😒")):
            r.motivos_revision.append("Posible sarcasmo")
        if len(texto) > 700:
            r.motivos_revision.append("Texto largo: el modelo puede truncarlo")
        return r
