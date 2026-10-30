"""Build only public aggregate counts from the local audited study."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

CLASES = ("POSITIVO", "NEUTRAL", "NEGATIVO")
EXCLUIDOS = ("OTRO_IDIOMA", "FUERA_DE_TEMA", "NO_EVALUABLE")


def leer(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def construir(datos):
    redes, fuentes = [], {}
    resumen = {r["plataforma"]: r for r in leer(datos / "resumen_tres_redes_auditado.csv")}
    auditoria = leer(datos / "resumen_verificacion_v2.csv")
    if len(auditoria) != 3 or {r["plataforma"] for r in auditoria} != {"YouTube", "Bluesky", "Mastodon"}:
        raise ValueError("La verificación debe contener las tres redes sin duplicados.")
    if any(int(r["pendientes_v2"]) != 0 or int(r["validadas_v2"]) != int(r["alertas"]) for r in auditoria):
        raise ValueError("Quedan alertas sin verificar; no se actualiza el estudio publicado.")
    for red in ("YouTube", "Bluesky", "Mastodon"):
        path = datos / f"{red.lower()}_auditado.csv"
        rows = leer(path)
        ids = [r["comentario_id"] for r in rows]
        if len(ids) != len(set(ids)) or any(not i for i in ids):
            raise ValueError(f"IDs vacíos o duplicados en {red}.")
        counts = Counter(r["sentimiento_final"].strip().upper() for r in rows)
        if set(counts) - set(CLASES + EXCLUIDOS):
            raise ValueError(f"Etiquetas desconocidas o pendientes en {red}.")
        validos = sum(counts[c] for c in CLASES)
        item = dict(plataforma=red, total_csv=len(rows), positivos=counts["POSITIVO"], neutrales=counts["NEUTRAL"], negativos=counts["NEGATIVO"], validos=validos, excluidos=sum(counts[c] for c in EXCLUIDOS), pendientes=0)
        for nombre, clase in zip(("positivo", "neutral", "negativo"), CLASES):
            item[f"porcentaje_{nombre}"] = round(100 * counts[clase] / validos, 2) if validos else 0
        if any(abs(float(resumen[red][key]) - value) > .001 for key, value in item.items() if key != "plataforma"):
            raise ValueError(f"El resumen auditado no coincide con las filas de {red}.")
        redes.append(item)
        fuentes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"fuente": "resumen_tres_redes_auditado.csv", "redes": redes, "alertas_verificadas": sum(int(r["validadas_v2"]) for r in auditoria), "sha256_fuentes": fuentes, "nota": "Muestras exploratorias; no todas las etiquetas fueron validadas por humanos."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datos", required=True, type=Path)
    args = parser.parse_args()
    agregado = construir(args.datos)
    output = Path(__file__).resolve().parents[1] / "data" / "estudio.json"
    output.write_text(json.dumps(agregado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Agregado actualizado sin textos ni identificadores personales.")


if __name__ == "__main__":
    main()
