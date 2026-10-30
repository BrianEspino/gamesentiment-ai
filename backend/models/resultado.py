from dataclasses import asdict, dataclass, field


@dataclass
class Resultado:
    texto: str
    texto_modelo: str
    idioma: str
    sentimiento_modelo: str = "NO_EVALUABLE"
    confianza: float = 0.0
    probabilidades: dict = field(default_factory=dict)
    motivos_revision: list = field(default_factory=list)
    fue_traducido: bool = False
    metodo_traduccion: str = "NINGUNO"
    plataforma: str = "Manual"
    sentimiento_final: str = ""
    estado_revision: str = "PENDIENTE"
    comentario_id: str = ""
    texto_publicacion_origen: str = ""

    def to_dict(self):
        return asdict(self)
