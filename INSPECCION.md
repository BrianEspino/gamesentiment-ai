# Inspección y adaptación de GameSentiment AI

Fecha: 30 de octubre de 2026. La implementación está en una carpeta nueva e independiente. La carpeta del escritorio y el ZIP de clase se conservaron sin modificaciones.

## Fuentes accesibles

El chat referido permitió recuperar `OneDrive_1_30-10-2026.zip` (143131 bytes). Las rutas `/mnt/data` del mensaje no existen en esta computadora Windows y `GameSentiment_AI.zip` no apareció como adjunto recuperable. El usuario confirmó que se use `C:\Users\HECTOR\Desktop\GameSentiment_AI` como fuente completa del proyecto. Esa diferencia de procedencia queda documentada: no se afirma haber inspeccionado un ZIP que no estaba disponible.

La carpeta GameSentiment tiene 15 scripts Python, datos CSV y gráficos, un entorno virtual, configuración del editor y `.env`. No se encontraron un servidor web, interfaz HTML, `requirements.txt`, notebook ni un modelo entrenado propio guardado en pickle/joblib. Los pesos usados corresponden al modelo público de Hugging Face `pysentimiento/robertuito-sentiment-analysis`.

Se extrajo y leyó el texto de `Ficha_Tecnica_ML_Studio.docx` del material de clase. La revisión fue de contenido; no se modificó ni se certificó su diagramación. Describe ML Studio v2, regresión de casas y K-Means de clientes ecommerce, con Flask, POO, servicios, DTO, Blueprints y cliente HTTP JavaScript. El Word específico de GameSentiment está pendiente: no apareció en la carpeta autorizada ni en el ZIP accesible.

## Proyecto de IA original

| Etapa | Archivos | Comportamiento observado |
|---|---|---|
| Prueba de modelo | 01 | `create_analyzer(task="sentiment", lang="es")`, clases POS/NEG/NEU y confianza |
| YouTube | 02, 03, 04 | YouTube Data API con clave en entorno; hasta 100 comentarios principales recientes del video; detección de idioma; predicción; revisión por consola y gráfico |
| Bluesky | 05 y prueba de conexión, 06, 07, 08 | Login con contraseña de aplicación; búsqueda GTA VI/GTA 6/Grand Theft Auto VI; respuestas de hilos; filtro manual de pertinencia; idioma; sentimiento y revisión |
| Mastodon | 09, 10 | Instancias públicas y hashtags; HTML a texto; publicaciones originales separadas de respuestas; detección de idioma; traducción automática, sentimiento y revisión |
| Consolidación | 11 | Resumen descriptivo, gráficos, conteos de exclusión y alertas específicas de idioma |
| Auditoría | 12 y dos variantes 13 | Correcciones de idioma, traducción y contexto; preservación de etiqueta previa; respaldo; segunda verificación y agregado auditado |

Dependencias identificadas por imports: pysentimiento, PyTorch y transformers; pandas y matplotlib; langdetect; deep-translator; requests; python-dotenv; atproto; beautifulsoup4. El entorno original usa Python 3.14.5, pysentimiento 0.7.3, PyTorch 2.14.1 y transformers 5.20.2. La aplicación nueva fija esas versiones centrales y ofrece un entorno independiente con Python 3.12 para distribución.

No se ejecutó entrenamiento. RoBERTuito infiere las probabilidades; las reglas de confianza menor a 0.65, palabras de contraste y emojis de sarcasmo generan alertas, no corrigen automáticamente la etiqueta. Los idiomas en scripts originales tienen umbrales distintos (0.90 en YouTube y 0.85 en otros). La adaptación unifica en 0.85, exige cinco palabras para intentar detección y mantiene alerta cuando no puede verificar el idioma. Los textos claramente extranjeros quedan pendientes salvo traducción autorizada. Los indeterminados se analizan con alerta.

La adaptación conserva limpieza de enlaces y menciones, similar a Mastodon. Esa limpieza y la unificación del idioma pueden producir diferencias respecto de una ejecución antigua de YouTube, donde se pasaba el texto original. No se sobrescriben los resultados históricos con esas nuevas inferencias.

## Material frontend y backend de clase

La carpeta frontend contiene tres HTML, un CSS y `api.js`, `regresion.js`, `kmeans.js`. Usa JavaScript puro, fetch y Chart.js. `api.js` tenía `http://localhost:5000/api` fijo. El backend implementa `create_app()`, Blueprints, servicios con carga o entrenamiento diferido, entidades de datasets sintéticos y DTO. Usaba CORS `*` y ejecución Flask en modo debug. El ZIP incluye `.pyc` de Python 3.14, pero no el requirements mencionado en el Word.

Se reutilizó el diseño de responsabilidades y comunicación JSON, sin arrastrar sus modelos de casas o ecommerce. La nueva API se importa como paquete sin modificar `sys.path`. Las clases se adaptaron a un resultado de sentimiento; el servicio es independiente de Flask y admite inyección del analizador para pruebas. La instancia vive por aplicación y se carga de forma diferida bajo un bloqueo. La web usa gráficos de barras HTML/CSS con texto accesible y ninguna CDN; no necesita Chart.js para mostrar estos agregados.

## Flujo web implementado

```text
Formulario o CSV
  → cliente frontend/js/api.js con /api relativo
  → Blueprint valida estructura, tamaño y plataforma
  → SentimientoService limpia texto y detecta idioma
  → traducción opcional de idiomas identificados como extranjeros
  → RoBERTuito calcula POS/NEU/NEG
  → Resultado conserva texto, probabilidades, alertas, ID y contexto
  → navegador muestra predicción y permite etiqueta final independiente
  → exportación CSV de revisión
```

Solo el comentario limpio entra al modelo. El contexto de la publicación se muestra a la persona revisora; no se usa para inferencia. Una etiqueta final indica una decisión del usuario de esa sesión; no constituye una validación independiente del estudio ni entrena el modelo.

La extracción de redes sigue disponible en los scripts originales locales y se integra por CSV. No se expusieron credenciales del investigador ni un endpoint público para consumir sus cuotas. No hay extracción en vivo dentro de la interfaz, persistencia central ni reanudación automática del CSV exportado. Estas diferencias están explicitadas en el README y la interfaz.

## Datos del estudio

Se tomó el resumen auditado posterior a la segunda verificación. Se recalcularon y cotejaron sus conteos con los tres archivos `*_auditado.csv`, verificando IDs únicos y ausencia de etiquetas pendientes. Las 25 alertas originales constan resueltas en el CSV de verificación v2. Los agregados públicos incluyen huellas SHA-256 de los CSV fuente para trazabilidad, sin sus comentarios ni identificadores.

| Red | Filas finales | Positivos | Neutrales | Negativos | Válidos | Excluidos |
|---|---:|---:|---:|---:|---:|---:|
| YouTube | 100 | 46 | 23 | 24 | 93 | 7 |
| Bluesky | 55 | 11 | 23 | 20 | 54 | 1 |
| Mastodon | 14 | 10 | 0 | 4 | 14 | 0 |
| Total | 169 | 67 | 46 | 48 | 161 | 8 |

Bluesky tiene 60 respuestas extraídas y 55 en el archivo final tras el filtro de pertinencia. Mastodon contiene 379 publicaciones originales en su archivo aparte, que no se contabilizan como comentarios. La comparación no es una muestra aleatoria y no permite afirmar representatividad, exactitud o causalidad. La ausencia de alertas pendientes no convierte todas las filas en validaciones humanas.

## Revisión de seguridad

Se identificaron tres variables con valor en el `.env` original: clave YouTube, usuario Bluesky y contraseña de aplicación Bluesky. No se mostraron sus valores ni se copiaron al proyecto nuevo. Se añadieron exclusiones para Git y Docker. Las fuentes y datos de la carpeta original permanecen fuera del paquete desplegable. No se usaron sus credenciales para realizar consultas.

Los archivos de backend no se sirven como estáticos; no hay carga de pickle ni archivos del usuario en disco. Las entradas tienen límites y validación de tipos; se controlan errores de JSON, CSV, codificación, traducción, modelo y servicio ocupado. Los textos se dibujan con `textContent`, y las celdas CSV peligrosas para hojas de cálculo se neutralizan. CSP restringe código y conexiones del navegador al mismo origen. El límite de solicitudes es global por proceso, no una defensa distribuida contra abuso.

## Entrega y límites de verificación

Se incluyen código de frontend y backend, dependencias fijadas, configuración Docker y Render, ejemplo CSV, scripts de preparación y actualización del estudio, y pruebas de errores y reglas de revisión. El README describe ejecución, verificación y despliegue paso a paso.

Las pruebas no constituyen una evaluación científica de precisión. La inferencia real se comprueba por separado usando el modelo original, sin alterar sus pesos. La traducción externa y la construcción Linux necesitan comprobación en el entorno de despliegue. Actualización posterior: se publicó el repositorio BrianEspino/gamesentiment-ai y se desplegó https://gamesentiment-ai.onrender.com/ en Render Free, sin contratar un plan de pago. La construcción Linux, inferencia pública, CSV, revisión y descarga se verificaron; consulta DESPLIEGUE_RENDER.md.

La web añade traducción manual verificada por el usuario, como la variante original 13 de traducción manual. Conserva la procedencia MANUAL/AUTOMATICA. Para la traducción automática se reemplazó la llamada sin timeout de deep-translator por un adaptador de Google con tiempos de espera, respuesta limitada y sin seguir redirecciones. Google bloqueó la prueba desde esta conexión; el fallo quedó pendiente, sin clasificación inventada.
