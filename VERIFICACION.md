# Verificación de la entrega

30 de octubre de 2026.

| Comprobación | Resultado |
|---|---|
| Instalación independiente | Python 3.12.14, dependencias de requirements-dev instaladas; `pip check` sin incompatibilidades declaradas |
| Pruebas de API y servicio | 24 aprobadas: entradas, CSV, tamaños, límites, errores, concurrencia, idiomas, traducción manual y fallo de traducción |
| Pruebas JavaScript | 2 aprobadas: neutralización de fórmulas CSV y representación de texto sin HTML |
| Inferencia real | Modelo RoBERTuito cargado; texto positivo, negativo y mixto/sarcasmo; probabilidades válidas. Evidencia en PRUEBA_MODELO_REAL.json |
| Agregado histórico | Conteos recalculados desde 169 filas auditadas y cotejados con resumen; 161 sentimientos válidos y 25 alertas verificadas |
| Navegador | Página, formulario, resultado real, cambio de etiqueta final y descarga CSV comprobados |
| Secretos | No se copió el .env original. Credenciales originales fuera de la carpeta desplegable |
| Traducción automática externa | Google redirigió la petición a una página de bloqueo; no se siguió ni se evitó la restricción. Estado pendiente y traducción manual disponibles |
| Docker Linux | No construido: Docker Desktop estaba instalado pero su motor Linux no estaba iniciado |
| Hosting público | No realizado; configuración e instrucciones incluidas |

La evidencia de inferencia usa textos de ejemplo, no datos privados ni respuestas extraídas. El porcentaje de confianza no mide exactitud en el conjunto del estudio. No se realizó entrenamiento ni validación científica de precisión.

Para repetir la inferencia real desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m scripts.verificar_modelo
```

El snapshot `DEPENDENCIAS_PROBADAS_WINDOWS.txt` registra todas las versiones observadas en el entorno de pruebas Windows, incluidos paquetes de desarrollo y auxiliares. Para instalar la aplicación utiliza `requirements.txt`; la construcción Linux todavía requiere verificación propia.
