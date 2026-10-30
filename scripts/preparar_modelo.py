from backend.services.sentimiento_service import SentimientoService

if __name__ == "__main__":
    service = SentimientoService()
    service.cargar()
    print("RoBERTuito descargado y cargado correctamente.")
