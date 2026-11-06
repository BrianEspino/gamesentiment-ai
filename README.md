# GameSentiment AI web

**Aplicación publicada:** https://gamesentiment-ai.onrender.com/ — Render Free (US$0/mes). El 30 de octubre de 2026 se verificaron una predicción real, un CSV de tres comentarios, revisión humana y exportación desde el servidor público. Consulta `DESPLIEGUE_RENDER.md` para operación y actualización.

Aplicación independiente para analizar sentimientos de comentarios sobre videojuegos. Conserva RoBERTuito, las probabilidades de las tres clases, detección de idioma, traducción opcional y revisión humana. Incluye el estudio histórico de GTA VI de YouTube, Bluesky y Mastodon en forma agregada. No contiene código ni datos de Telco.

## Ejecutar en Windows

Instala Python **3.12 de 64 bits**. Abre PowerShell dentro de esta carpeta, donde están `requirements.txt` y `wsgi.py`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.preparar_modelo
.\.venv\Scripts\python.exe -m backend.app
```

Abre http://127.0.0.1:5000. No abras `index.html` directamente: la página necesita su API. No hace falta activar el entorno virtual ni cambiar la política de ejecución de PowerShell. El modelo público se descarga de Hugging Face durante la preparación; hace falta internet y espacio en disco. La primera descarga puede tardar varios minutos. Después se reutiliza la caché. Si el puerto está ocupado, usa `$env:PORT="5001"` antes del último comando.

## Ejecutar en Linux o macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m scripts.preparar_modelo
.venv/bin/gunicorn wsgi:app --bind 127.0.0.1:5000 --workers 1 --threads 4 --timeout 300
```

Para una instalación CPU más pequeña en Linux, instala primero `torch==2.14.1` desde `https://download.pytorch.org/whl/cpu`, igual que en el Dockerfile. El servidor usa un único proceso para no duplicar el modelo en memoria.

## Probar la aplicación

En **YouTube**, pega un enlace a un video público, Short o directo y pulsa **Analizar comentarios**. La web consulta hasta 30 comentarios principales recientes, muestra las etiquetas de RoBERTuito y cuenta positivos, neutrales y negativos en un gráfico de barras. Los comentarios que quedan pendientes de idioma, traducción o interpretación se cuentan por separado. Para activar la función en la web pública, consulta los requisitos de YouTube y la configuración del servidor en `DESPLIEGUE_RENDER.md`.

1. Comprueba que `/api/health` devuelve `status: ok`. `modelo_cargado: false` significa que el servidor funciona y el modelo aún no se ha cargado en ese proceso; no es una comprobación de inferencia.
2. En la página, pulsa **Probar un ejemplo** y **Analizar con RoBERTuito**. Deben aparecer probabilidades, confianza y señales de opinión mixta/sarcasmo.
3. Selecciona una etiqueta final. El contador de revisados debe aumentar; el resultado original de la IA se conserva.
4. Descarga el CSV y verifica sus columnas. Guarda ese archivo antes de cerrar o recargar la pestaña. No existe una base de datos de sesiones.
5. Carga `ejemplo.csv`: deben aparecer tres comentarios. La plataforma es procedencia declarada, no prueba de extracción en vivo.
6. Prueba un comentario largo en inglés sin traducción: debe quedar `PENDIENTE_IDIOMA`. Activa la traducción solo si aceptas enviar el texto al servicio externo.

Si Google bloquea la traducción automática, abre **Usar una traducción manual** y pega una traducción española fiel del comentario. En CSV se acepta la columna `texto_espanol` por fila. La traducción manual tiene prioridad, se identifica como MANUAL y nunca se envía a Google. No uses ese campo para cambiar la opinión del comentario original.

La API acepta CSV UTF-8 separado por comas, una columna obligatoria `texto` y columnas opcionales `plataforma`, `comentario_id`, `texto_publicacion_origen` y `texto_espanol`. Valores permitidos de plataforma: Manual, YouTube, Bluesky y Mastodon. Un archivo seleccionado tiene prioridad sobre el texto del formulario. No se eliminan duplicados automáticamente: cada fila es una observación. El contexto se muestra para la revisión, pero el modelo clasifica solo el comentario limpio.

El CSV exportado es una evidencia de la sesión, no un archivo para reanudarla: al volver a cargar un CSV se generan predicciones nuevas y se reinicia la revisión. Las fórmulas de hojas de cálculo se neutralizan con un apóstrofo inicial.

Límites: 30 filas por petición, 1000 caracteres por texto, 200 por ID, 2000 por contexto; máximo 256 KiB por petición (la interfaz limita el archivo a 200 KiB). Textos largos pueden ser truncados internamente por el modelo. Revisa estos casos. La detección de idioma de textos con menos de cinco palabras queda indeterminada y no activa traducción automática; se permite inferencia con alerta, como en el proyecto original.

### Pruebas automatizadas

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
node --test tests/test_frontend.cjs
```

Las pruebas de API usan un analizador simulado para verificar validación y estados sin descargar el modelo. Las predicciones reales se comprueban aparte. Node es opcional y solo se necesita para las pruebas de JavaScript, no para ejecutar la web.

## Publicar online en Render con Docker

El backend necesita Python y PyTorch: un alojamiento de páginas estáticas por sí solo no ejecutará la IA. Se incluye Docker para servir frontend y API en una misma URL.

1. Crea un repositorio **nuevo e independiente** en GitHub y sube solo el contenido de esta carpeta. No subas el directorio de trabajo completo, el proyecto original, `.env`, `.venv`, cachés ni los datos crudos.
2. En Render, selecciona **New → Web Service** y conecta ese repositorio.
3. Elige **Docker**, rama principal y contexto raíz `.`. Si esta carpeta está dentro de otro repositorio, configura **Root Directory** con su ruta relativa.
4. Usa el Dockerfile incluido, sin sobrescribir el comando de inicio. Define `PORT=7860`. El servidor escucha en `0.0.0.0:$PORT`. La ruta de salud es `/api/health`.
5. Selecciona **Free (US$0/mes, 512 MB)** para reproducir el despliegue actual, donde se comprobó inferencia real con esta versión. La carga inicial puede ser lenta; vigila memoria y errores si aumentas las longitudes o el tráfico. Las pruebas acotadas no garantizan capacidad sostenida. No es necesario contratar un plan de pago para repetir lo verificado.
6. Inicia el despliegue. La construcción instala las dependencias y descarga el modelo con el usuario sin privilegios que lo ejecutará. Si falla la descarga, la construcción falla en lugar de publicar una web que no puede cargar el modelo.
7. Cuando Render entregue la URL HTTPS, abre la página y repite las pruebas de texto, CSV, traducción y exportación. Verifica una predicción real: la ruta de salud solo certifica que el servidor responde.

`render.yaml` fija explícitamente `plan: free` para un Blueprint. La instancia gratuita se probó con éxito en el despliegue actual; revisa la memoria ante cambios o mayor carga. La caché del modelo queda dentro de la imagen Docker; no se requiere volumen persistente para este diseño sin base de datos.

El comando de producción es:

```bash
gunicorn wsgi:app --bind 0.0.0.0:${PORT:-7860} --workers 1 --threads 4 --timeout 300 --access-logfile -
```

### Probar la imagen Docker localmente

Con Docker Desktop iniciado en modo Linux:

```powershell
docker build -t gamesentiment-ai .
docker run --rm -p 7860:7860 -e PORT=7860 gamesentiment-ai
```

Abre http://localhost:7860. La construcción local no se ejecutó porque el motor Docker no estaba iniciado. La construcción Linux sí se completó en Render y la aplicación pública fue verificada.

## API

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/health` | Estado del servidor y carga del modelo |
| GET | `/api/estudio` | Agregados históricos sin comentarios crudos |
| POST | `/api/sentimiento/predecir` | Texto JSON, lista de comentarios o CSV multipart |
| POST | `/api/sentimiento/youtube` | JSON con `url` y, opcionalmente, `traducir` booleano |

Ejemplo con PowerShell:

```powershell
$body = @{texto="Este videojuego es increíble y me encanta jugarlo"; plataforma="Manual"; traducir=$false} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/sentimiento/predecir' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

Para un lote JSON: `{"comentarios":[{"texto":"Me encanta","plataforma":"YouTube"}],"traducir":false}`. Para CSV usa el campo multipart `archivo` y `traducir` como texto `true` o `false`.

Errores: 413 para exceso de tamaño, 415 para formato HTTP incorrecto, 422 para validación, 429 para límite de uso, 503 para modelo no disponible o analizador ocupado. La API no devuelve rastros internos ni credenciales.

## Seguridad y privacidad

El modelo público no requiere token de Hugging Face. El análisis por enlace usa `YOUTUBE_API_KEY` en el servidor. Mantén la clave fuera de GitHub y del navegador. El análisis de texto y CSV está disponible aunque esa clave no esté configurada.

El servidor solo publica `frontend/` y los agregados autorizados. No guarda los comentarios ni las correcciones en disco y no incluye textos en los mensajes de error propios. La inferencia es local al servidor. La traducción opcional usa Google Translate mediante un adaptador HTTP con tiempos de espera y tamaño máximo: los textos detectados en otro idioma salen del servidor, el servicio puede fallar o limitar solicitudes y la traducción debe verificarse. Las peticiones HTTP pueden constar en los registros del proveedor, pero sus cuerpos no se registran por esta aplicación.

Se usan rutas relativas `/api`, sin CORS abierto ni dependencias externas en el navegador; contenido de usuario con `textContent`; CSP, protección contra inclusión en marcos y contra interpretación incorrecta de tipos. No se habilita el modo de depuración de Flask.

La API es pública: tiene un límite **global de 20 peticiones POST/minuto por proceso** y una sola inferencia a la vez. No autentica usuarios ni ofrece cuotas individuales. Mantén un worker: con varios procesos esos límites y el modelo se duplican. Para tráfico real sostenido, añade protección y cuotas en el proveedor, y una cola externa si se necesitan trabajos largos. Este diseño es una demo académica pública acotada, sin persistencia compartida de revisiones.

## Extracción original y actualización del estudio

La carpeta original del escritorio contiene el pipeline local que generó el estudio histórico. La consulta por enlace en la web se realiza por separado con la clave configurada en el servidor.

- YouTube: `02_extraccion_youtube.py`, después `03_analisis_sentimientos.py` y `04_revision_manual.py`.
- Bluesky: `05_extraccion_bluesky.py`, `06_filtro_pertinencia_bluesky.py`, `07_analisis_bluesky.py` y `08_revision_bluesky.py`.
- Mastodon: `09_extraccion_mastodon.py` y `10_analisis_mastodon.py`.
- Consolidación y auditoría: `11_consolidacion_resultados.py`, `12_auditoria_final.py`, `13_correccion_y_cierre.py`. El otro archivo 13 permite traducción manual; no ejecutes ambos indiscriminadamente porque modifican datos de auditoría.

Ese pipeline requiere además pandas, matplotlib, requests, python-dotenv, atproto y beautifulsoup4. Lee `YOUTUBE_API_KEY`, `BLUESKY_HANDLE` y `BLUESKY_APP_PASSWORD` en el entorno local. Mastodon consulta instancias públicas.

Para llevar comentarios originales a la web, divide los CSV en lotes de hasta 30 filas. Revisa textos demasiado largos antes de importarlos. La interfaz conserva ID y contexto si existen, pero solo exporta las columnas documentadas; conserva los CSV originales como fuente completa.

Para regenerar el agregado público desde resultados auditados:

```powershell
.\.venv\Scripts\python.exe -m scripts.actualizar_estudio --datos 'C:\Users\HECTOR\Desktop\GameSentiment_AI\datos'
```

Este comando valida los conteos y las 25 alertas resueltas del estudio actual y sobrescribe solo `data/estudio.json`. No publica textos ni cambia los CSV originales. Si cambias el muestreo o el número de alertas, actualiza también los indicadores de la página y la documentación antes de desplegar.

## Documentos y pendientes

Se leyó la ficha `Ficha_Tecnica_ML_Studio.docx` del ZIP de clase. Describe Flask, Blueprints, DTO, servicios y frontend HTML/CSS/JS; esa arquitectura fue reutilizada con lógica de sentimientos. No se incluyeron regresión de casas, K-Means ni Telco. El documento Word propio de GameSentiment no apareció en las fuentes accesibles y queda pendiente de cotejo.

Consulta `INSPECCION.md` para procedencia, decisiones de adaptación y límites de la evaluación. La imagen Linux se construyó en Render y la URL pública se verificó en el plan gratuito. Queda comprobar comportamiento ante mayor carga y disponibilidad sostenida. La prueba de traducción automática desde esta conexión fue bloqueada por Google; queda como dependencia externa y se ofrece traducción manual como alternativa. No se inventaron métricas de exactitud sobre GTA VI: las probabilidades del modelo y los porcentajes del estudio no equivalen a accuracy ni F1.

## Referencias técnicas

- Modelo y etiquetas: https://huggingface.co/pysentimiento/robertuito-sentiment-analysis
- Biblioteca: https://github.com/pysentimiento/pysentimiento
- Despliegue Flask: https://render.com/docs/deploy-flask
- Gunicorn (Linux; no funciona directamente en Windows): https://flask.palletsprojects.com/en/stable/deploying/gunicorn/
